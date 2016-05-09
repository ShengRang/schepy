# coding: utf-8

from collections import defaultdict

from fa import DFA, DFANode
from util import bnf_reader


class SExpNode(object):
    """
    stype: 类型, 如"op", "number"
    value: 值, 如"+", "6"
    child: 子节点的list
    parent: 父节点
    """
    def __init__(self, stype="", value="", parent=None):
        self.stype = stype
        self._value = value
        self.child = []
        self.parent = parent

    def ddd(self):
        pass


class LRParser(object):
    """
    LR语法分析器, 接受token流, 分析出语法树 (所以tokens应该不是parser的一部分)
    grammar: defaultdict(list), 解析器语法
    analysis_table: LR1 分析表
    """

    def __init__(self):
        self.grammar = defaultdict(list)
        self.terminators = []
        self.non_terminators = []

    def read_grammar(self, filename):
        """
        语法读入
        """
        grammar = self.grammar
        grammar.clear()
        self.terminators, self.non_terminators = [], []
        g_in, g_out = defaultdict(int), defaultdict(int)
        for l_hand, r_hand in bnf_reader(filename):
            symbol = l_hand[1:-1]
            __exp__ = [r[1:-1] for r in r_hand.split()]
            for exp in __exp__:
                g_in[exp] += 1
            g_out[symbol] += 1
            grammar[symbol].append(__exp__)
        for k, v in g_in.iteritems():
            if not g_out[k]:
                self.terminators.append(k)
        self.non_terminators.extend([k for k, v in g_out.iteritems() if v])
        # print g_in
        # print g_out

    def compile(self):
        """
        利用 self.grammar 编译出dfa, 并构造分析表
        :return:
        """
        dfa = DFA()

    def parser(self):
        pass


if __name__ == "__main__":
    l = LRParser()
    l.read_grammar("grammar.txt")