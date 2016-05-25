# coding: utf-8
"""
运行时环境
"""

from __future__ import division
import math
import operator as op
from functools import partial

from util import colorful


def define(env, symbol, exp):
    pass


class Env(dict):

    def __init__(self, outer=None):
        self.outer = outer
        super(Env, self).__init__()

    def find(self, name):
        """
        沿着作用于链查找name的value
        """
        return self[name] if (name in self) else self.outer.find(name)

    @staticmethod
    def std_env():
        env = Env()
        env.update(vars(math))
        env.update({
            '+': sum, '-': op.sub, '*': op.mul, '/': op.div,
            '>': op.gt, '<': op.lt, '>=': op.ge, '<=': op.le, '=': op.eq,
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


class Expression(object):

    def __init__(self, params, body, env, etype):
        self.params, self.body, self.env = params, body, env
        self.etype = etype

    def __call__(self, *args):
        # return eval(self.body, Env(self.params, args, self.env))
        pass


class ParseHandler(object):

    def __init__(self):
        self.ast = None
        self.exps = []

    def shift(self, token):
        # if token[1] != 'no-sense':
            # print(colorful('移近 {0} {1}'.format(token[0], token[1]), "Cyan"))
        self.exps.append(SExp(stype=token[0], value=token[1]))

    def reduce(self, grammar):
        """
        规约动作, grammar为规约用的产身世
        """
        # print('利用规则' + colorful('%s -> %s' % (grammar[0], ' '.join(grammar[1])), "Green"))
        if grammar[0] == 'start':
            self.ast = self.exps[0]
            return
        new_node = SExp(stype=grammar[0])
        new_node.child = self.exps[-len(grammar[1]):]

        self.exps = self.exps[:-len(grammar[1])] + [new_node]


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

    def append(self, node):
        self.child.append(node)

    def parser_handler(self):
        """
        语法分析时的 handler, 用于生成语法树
        :return:
        """
        pass

    def calc_value(self, env=Env.std_env()):
        """
        在指定环境中求值, 或者对环境造成改变
        :param env: 表达式所在环境
        :return:表达式的值
        """
        if self.value:
            return self.value
        if self.stype == 'number':
            self.value = int(self._value)
        elif self.stype == 'string':
            self.value = self._value
        elif self.stype == 'identifier':
            self.value = env.find(self._value)
        elif self.stype == 'op':
            self.value = env.find(self._value)
        elif self.stype == 'atom' or self.stype == 'func':
            self.value = self.child[0].calc_value(env)
        elif self.stype == 'lexp':
            self.value = self.child[0].calc_value(env)
        elif self.stype == 'lexp-seq':
            # ..蜜汁处理. 很重要
            # 对于 lexp-seq -> lexp, 不转list
            # 对于lexp-seq -> lexp-seq lexp, 第二个转list. 如果第一个是lexp-seq -> lexp-seq lexp型, 不转list, 否则转
            if len(self.child) > 1:
                first = [self.child[0].calc_value(env)]
                if len(self.child[0].child) > 1:
                    first = first[0]
                self.value = first + [self.child[1].calc_value(env), ]
            else:
                self.value = self.child[0].calc_value(env)
            print 'this lexp-seq:', self.value
        elif self.stype == 'list':
            # 一致性处理, lexp-seq 已经做了list处理
            self.value = self.child[1].calc_value(env)
        elif self.stype == 's-exp':
            func = self.child[1].calc_value(env)
            args = self.child[2].calc_value(env)
            # print func
            # print args
            self.value = func(args)
        elif self.stype == 'lambda':
            pass
        return self.value
