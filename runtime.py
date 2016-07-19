# coding: utf-8
"""
解释执行
"""

from __future__ import division
import math
import operator as op
from functools import partial

from util import colorful
from util import args_restore
# import crash_on_ipy

# crash_on_ipy.init()


class BuildIn(object):

    @staticmethod
    def add(*args):
        return reduce(op.add, args, 0)

    @staticmethod
    def mul(*args):
        return reduce(op.mul, args, 1)

    @staticmethod
    def sub(*args):
        if len(args) == 1:
            return -args[0]
        return reduce(op.sub, args[1:], args[0])

    @staticmethod
    def append(*args):
        return reduce(op.add, args, [])

    @staticmethod
    def filter(fn, s):
        # 用scheme写也行.. 就是没有实现尾递归效率有点捉急..
        return filter(fn, s)


class Env(object):

    def __init__(self, outer=None):
        self.outer = outer
        self.dynamic_bind = dict()
        self._dict = dict()
        super(Env, self).__init__()

    def __getitem__(self, item):
        if self.dynamic_bind.get(item, False):
            return self._dict[item]()
        return self._dict[item]

    def __setitem__(self, key, value):
        self._dict[key] = value

    def find(self, name):
        """
        沿着作用于链查找name的value
        """
        try:
            return self[name] if (name in self._dict) else self.outer.find(name)
        except AttributeError as e:
            print(colorful('{0} 在作用域链上不存在!'.format(name), 'Red'))
            return 'not-define-yet'

    def update(self, *args, **kwargs):
        return self._dict.update(*args, **kwargs)

    @staticmethod
    def std_env(outer=None):
        env = Env(outer=outer)
        env.update(vars(math))
        env.update({
            '+': BuildIn.add, '-': BuildIn.sub, '*': BuildIn.mul, '/': op.div,
            '>': op.gt, '<': op.lt, '>=': op.ge, '<=': op.le, '=': op.eq,
            'define': partial(define, env),
            'abs':     abs,
            'append':  BuildIn.append,
            'filter': BuildIn.filter,
            'apply':   apply,
            'begin':   lambda *x: x[-1],
            'car':     lambda x: x[0],
            'cdr':     lambda x: x[1:],
            'cons':    lambda x, y: [x] + y,
            'eq?':     op.is_,
            'equal?':  op.eq,
            'length':  len,
            'list':    lambda *x: list(x),
            'list?':   lambda x: isinstance(x,list),
            'map':     map,
            'max':     max,
            'min':     min,
            'not':     op.not_,
            'null?':   lambda x: x == [],
            'number?': lambda x: isinstance(x, int),
            'procedure?': callable,
            'round':   round,
            'symbol?': lambda x: isinstance(x, str),
        })
        return env


class ParseHandler(object):

    def __init__(self):
        self.ast = None
        self.exps = []

    def shift(self, token):
        # print(colorful('移近 {0} {1}'.format(token[0], token[1]), "Cyan"))
        self.exps.append(SExp(stype=token[0], value=token[1]))

    def reduce(self, grammar):
        """
        规约动作, grammar为规约用的产身世
        """
        # print('reduce with ' + colorful('%s -> %s' % (grammar[0], ' '.join(grammar[1])), "Green"))
        if grammar[0] == 'start':
            self.ast = self.exps[0]
            return
        new_node = SExp(stype=grammar[0])
        new_node.child = self.exps[-len(grammar[1]):]
        self.exps = self.exps[:-len(grammar[1])] + [new_node]


def dynamic_exp(sexp, env):
    return sexp.calc_value(env)


def define(env, symbol, sexp):
    env[symbol] = partial(dynamic_exp, sexp, env)
    env.dynamic_bind[symbol] = True
    return 'define [%s] in env' % symbol


class Procedure(object):

    def __init__(self, params, body, outer_env):
        self.params = params
        self.body = body
        self.outer_env = outer_env

    def __call__(self, *args):
        func_env = Env.std_env(outer=self.outer_env)
        for param, arg in zip(self.params, args):
            func_env[param] = arg
        return self.body.calc_value(func_env)


class SExp(object):
    """
    stype: 类型, 如"op", "number"
    value: 值, 如"+", "6"
    child: 子节点的list
    parent: 父节点
    """
    def __init__(self, stype="", value="", parent=None):
        self.stype = stype
        self._value = value     # raw value
        self.value = None      # real value
        self.child = []
        self.parent = parent
        # self.static = (stype != "identifier")   #非静态表达式

    @property
    def raw_value(self):
        return self._value

    @property
    def static(self):
        if self.stype == "identifier":
            return True
        for node in self.child:
            if node.static:
                return True
        return False

    def append(self, node):
        self.child.append(node)

    def calc_value(self, env=Env.std_env()):
        """
        在指定环境中求值, 或者对环境造成改变
        :param env: 表达式所在环境
        :return:表达式的值
        """
        if self.static and self.value:
            print(colorful('静态表达式, 直接返回值', 'Bold'))
            return self.value
        res = None
        stype, child = self.stype, self.child
        if stype == 'number':
            res = child[0].calc_value(env)
        elif stype == 'integer':
            res = int(self._value)
        elif stype == 'decimal':
            res = float(self._value)
        elif stype == 'string':
            res = self._value
        elif stype == 'bool':
            res = True if self._value == '$T' else False
        elif stype == 'symbol':
            self._value = child[0].raw_value
            res = child[0].calc_value(env)
        elif stype == 'identifier':
            res = env.find(self._value)
        elif stype == 'op':
            res = env.find(self._value)
        elif stype == 'atom' or self.stype == 'func':
            res = child[0].calc_value(env)
        elif stype == 'lexp':
            res = child[0].calc_value(env)
            if child[0].stype == 'list':
                res = [res, ]
                res = args_restore(res)
        elif stype == 'lexp-seq':
            if len(child) > 1:
                res = (child[0].calc_value(env), ) + child[1].calc_value(env)
            else:
                res = (child[0].calc_value(env), )
            # print 'this lexp-seq:', res
        elif stype == 'list':
            if len(child) == 3:
                res = child[1].calc_value(env)
            else:
                res = tuple()
        elif stype == 's-exp':
            func = child[1].calc_value(env)
            args = child[2].calc_value(env)
            if len(child) == 3:
                res = func()
            else:
                res = func(*[args_restore(arg) for arg in args])
        elif stype == 'define-exp':
            # <define-exp> ::= <(> <define> <symbol> <lexp> <)>
            symbol = child[2].child[0].raw_value
            define(env, symbol, child[3])
            res = symbol
        elif stype == 'args':
            if child[0].stype == 'symbol':
                res = (child[0].child[0].raw_value, )
            else:
                res = child[0].calc_value(env) + (child[1].child[0].raw_value, )
        elif stype == 'proc-body':
            if len(child) <= 1:
                res = child[0].calc_value(env)
            else:
                # 用语句块的最后一个语句作为语句块的值
                _ = child[0].calc_value(env)
                res = child[1].calc_value(env)
        elif stype == 'lambda-exp':
            # <lambda-exp> ::= <(> <lambda> <(> <args> <)> <proc-body> <)>
            args = child[3].calc_value(env)
            body = child[5]
            # print 'args: ', args
            # print 'body:', body
            res = Procedure(args, body, env)
        elif stype == 'var-exps':
            if len(child) == 4:
                define(env, child[1].child[0].raw_value, child[2])
            else:
                child[0].calc_value(env)
                define(env, child[2].child[0].raw_value, child[3])
        elif stype == 'let-exp':
            # <let-exp> ::= <(> <let> <(> <var-exps> <)> <proc-body> <)
            let_env = Env.std_env(outer=env)
            child[3].calc_value(let_env)
            res = child[5].calc_value(let_env)
        elif stype == 'proc-define-exp':
            # <proc-define-exp> ::= <(> <define> <(> <symbol> <args> <)> <proc-body> <)>
            # <proc-define-exp> ::= <(> <define> <(> <symbol> <)> <proc-body> <)>
            if len(child) > 7:
                # 有参函数
                symbol = child[3].child[0].raw_value
                args = child[4].calc_value(env)
                body = child[6]
                proc = Procedure(args, body, env)
                env[symbol] = proc
            else:
                symbol = child[3].child[0].raw_value
                args = tuple()
                body = child[5]
                proc = Procedure(args, body, env)
                env[symbol] = proc
            if symbol in env.dynamic_bind:
                # 如果之前是动态绑定key, 移除
                del env.dynamic_bind[symbol]
            res = symbol
        elif stype == 'predicate':
            if child[0].calc_value(env):
                res = True
            else:
                res = False
        elif stype in ['consequent', 'alternate']:
            res = child[0].calc_value(env)
        elif stype == 'if-exp':
            # <if-exp> ::= <(> <if> <predicate> <consequent> <alternate> <)>
            if child[2].calc_value(env):
                res = child[3].calc_value(env)
            else:
                res = child[4].calc_value(env)
        elif stype == 'or-exp':
            # <or-exp> ::= <(> <or> <lexp-seq> <)>
            cnode = child[2]
            res = False
            while len(cnode.child) > 1:
                val = cnode.child[0].calc_value(env)
                if type(val) == list:
                    val = args_restore(val)
                if val:
                    res = val
                    break
                else:
                    cnode = cnode.child[1]
            else:
                val = cnode.calc_value(env)[0]
                if type(val) == list:
                    val = args_restore(val)
                if val:
                    res = val
        elif stype == 'and-exp':
            # <and-exp> ::= <(> <and> <lexp-seq> <)>
            cnode = child[2]
            res = True
            while len(cnode.child) > 1:
                val = cnode.child[0].calc_value(env)
                if type(val) == list:
                    val = args_restore(val)
                if not val:
                    res = val
                    break
                else:
                    cnode = cnode.child[1]
            else:
                val = cnode.calc_value(env)[0]
                if type(val) == list:
                    val = args_restore(val)
                if not val:
                    res = val
        if not self.static:
            self.value = res
        return res
