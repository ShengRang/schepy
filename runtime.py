# coding: utf-8
"""
运行时环境
"""

from __future__ import division
import math
import operator as op
from functools import partial

from util import colorful
from util import args_restore
import crash_on_ipy

crash_on_ipy.init()


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
            'append':  op.add,
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
        print('利用规则' + colorful('%s -> %s' % (grammar[0], ' '.join(grammar[1])), "Green"))
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
        if self.stype == 'number':
            res = self.child[0].calc_value(env)
        elif self.stype == 'integer':
            res = int(self._value)
        elif self.stype == 'string':
            res = self._value
        elif self.stype == 'bool':
            res = True if self._value == '$T' else False
        elif self.stype == 'symbol':
            self._value = self.child[0].raw_value
            res = self.child[0].calc_value(env)
        elif self.stype == 'identifier':
            # print 'i will find [%s]' % self._value
            res = env.find(self._value)
            # print 'res is ', res
        elif self.stype == 'op':
            res = env.find(self._value)
        elif self.stype == 'atom' or self.stype == 'func':
            res = self.child[0].calc_value(env)
        elif self.stype == 'lexp':
            res = self.child[0].calc_value(env)
            if self.child[0].stype == 'list':
                res = [res, ]
                res = args_restore(res)
        elif self.stype == 'lexp-seq':
            if len(self.child) > 1:
                res = (self.child[0].calc_value(env), ) + self.child[1].calc_value(env)
            else:
                res = (self.child[0].calc_value(env), )
            # print 'this lexp-seq:', res
        elif self.stype == 'list':
            if len(self.child) == 3:
                res = self.child[1].calc_value(env)
            else:
                res = tuple()
        elif self.stype == 's-exp':
            func = self.child[1].calc_value(env)
            args = self.child[2].calc_value(env)
            # print func
            # print args
            res = func(*[args_restore(arg) for arg in args])
        elif self.stype == 'define-exp':
            # <define-exp> ::= <(> <define> <symbol> <lexp> <)>
            symbol = self.child[2].child[0].raw_value
            # env[symbol] = partial(dynamic_exp, self.child[3], env)
            # env.dynamic_bind[symbol] = True
            define(env, symbol, self.child[3])
            res = symbol
        elif self.stype == 'args':
            if self.child[0].stype == 'symbol':
                res = (self.child[0].child[0].raw_value, )
            else:
                res = self.child[0].calc_value(env) + (self.child[1].child[0].raw_value, )
        elif self.stype == 'proc-body':
            if len(self.child) <= 1:
                res = self.child[0].calc_value(env)
            else:
                # 用语句块的最后一个语句作为语句块的值
                _ = self.child[0].calc_value(env)
                res = self.child[1].calc_value(env)
        elif self.stype == 'lambda-exp':
            # <lambda-exp> ::= <(> <lambda> <(> <args> <)> <proc-body> <)>
            args = self.child[3].calc_value(env)
            body = self.child[5]
            # print 'args: ', args
            # print 'body:', body
            res = Procedure(args, body, env)
        elif self.stype == 'var-exps':
            if len(self.child) == 4:
                define(env, self.child[1].child[0].raw_value, self.child[2])
            else:
                self.child[0].calc_value(env)
                define(env, self.child[2].child[0].raw_value, self.child[3])
        elif self.stype == 'let-exp':
            # <let-exp> ::= <(> <let> <(> <var-exps> <)> <proc-body> <)
            let_env = Env.std_env(outer=env)
            self.child[3].calc_value(let_env)
            res = self.child[5].calc_value(let_env)
        elif self.stype == 'proc-define-exp':
            # <proc-define-exp> ::= <(> <define> <(> <symbol> <args> <)> <proc-body> <)>
            # <proc-define-exp> ::= <(> <define> <(> <symbol> <)> <proc-body> <)>
            if len(self.child) > 7:
                # 有参函数
                symbol = self.child[3].child[0].raw_value
                args = self.child[4].calc_value(env)
                body = self.child[6]
                proc = Procedure(args, body, env)
                env[symbol] = proc
            else:
                symbol = self.child[2].child[0].raw_value
                args = tuple()
                body = self.child[5]
                proc = Procedure(args, body, env)
                env[symbol] = proc
            res = symbol
        elif self.stype == 'predicate':
            if self.child[0].calc_value(env):
                res = True
            else:
                res = False
        elif self.stype in ['consequent', 'alternate']:
            res = self.child[0].calc_value(env)
        elif self.stype == 'if-exp':
            # <if-exp> ::= <(> <if> <predicate> <consequent> <alternate> <)>
            if self.child[2].calc_value(env):
                res = self.child[3].calc_value(env)
            else:
                res = self.child[4].calc_value(env)
        elif self.stype == 'or-exp':
            # <or-exp> ::= <(> <or> <lexp-seq> <)>
            cnode = self.child[2]
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
        elif self.stype == 'and-exp':
            # <and-exp> ::= <(> <and> <lexp-seq> <)>
            cnode = self.child[2]
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
