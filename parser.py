# coding: utf-8

from collections import defaultdict
from Queue import Queue

from fa import DFA, DFANode
from util import bnf_reader, frozen_items


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
        self._first = defaultdict(set)

    @property
    def alphabet(self):
        return self.terminators + self.non_terminators

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

    def get_eps(self):
        """
        返回能推导出 ep 的非终结符
        """
        grammar = defaultdict(list)
        for symbol, exps in self.grammar.iteritems():
            grammar[symbol] = [[e for e in exp] for exp in exps]
        eps = dict()
        vt = {key: 1 for key in self.terminators}
        vt.update({key: 0 for key in self.non_terminators})
        for symbol, exps in grammar.iteritems():
            if filter(lambda exp: len(exp) == 1 and exp[0] == "ep", exps):
                # 存在 symbol ::= ε , 则标记 True 并删除所有产生式
                eps[symbol] = True
                grammar[symbol] = []
                continue
            grammar[symbol] = filter(lambda exp: not sum(vt[e] for e in exp), exps) # 删除所有含有终结符的产生式
            if not len(grammar[symbol]):
                eps[symbol] = False
        while sum(len(exps) for exps in grammar.itervalues()):
            # 只要产生式没有被删光就继续
            for symbol, exps in grammar.iteritems():
                if not exps:
                    continue
                for i in range(len(exps)):
                    exps[i] = filter(lambda e: not(not vt[e] and eps.get(e, False)), exps[i])
                if filter(lambda exp: not exp, exps):
                    grammar[symbol] = []
                    eps[symbol] = True
                    continue
                # grammar[symbol] = filter(lambda exp: not sum(not eps.get(e, True) for e in exp), exps)
                grammar[symbol] = filter(lambda exp: sum(eps.get(e, True) for e in exp) == len(exp), exps)
                # 如果右部存在为非空的非终结符, 则删除该产生式
                if not len(grammar[symbol]):
                    eps[symbol] = False
        eps.update(ep=True)
        eps.update({key: False for key in self.terminators if key != "ep"})
        return eps

    def calc_first(self):
        """
        计算出字母表里所有元素的first集合
        """
        first = self._first
        first.clear()
        eps = self.get_eps()
        g_in, g_out = defaultdict(int), defaultdict(int)
        grap = defaultdict(list) # First集合的邻接表
        terminators, non_terminators = self.terminators, self.non_terminators
        grammar = self.grammar
        for symbol, exps in grammar.iteritems():
            for exp in exps:
                for i in range(len(exp)):
                    if i == sum(eps.get(e, False) for e in exp[:i]):
                        if exp[i] == "ep":
                            continue
                        grap[exp[i]].append(symbol)
                        g_in[symbol] += 1
                        g_out[exp[i]] += 1
        for ter in self.terminators:
            first[ter].add(ter)
        stack = [ter for ter in terminators]
        while len(stack):
            # 拓扑排序构造first集合, 暂时不管空弧
            top = stack.pop()
            for symbol in grap[top]:
                first[symbol].update(first[top])
                g_in[symbol] -= 1
                if g_in[symbol] == 0:
                    stack.append(symbol)
        for symbol in first.keys():
            # 处理空弧
            if eps.get(symbol, False):
                first[symbol].add("ep")
        first["ep"] = {"ep"}

    def first(self, symbols):
        """
        :return: 返回first集.
        """
        if isinstance(symbols, str):
            return self._first[symbols]
        if isinstance(symbols, set):
            symbols = list(symbols)
        if isinstance(symbols, list):
            res = set()
            for i in range(len(symbols)):
                res.update(self.first(symbols[i]))
                if symbols[i] in self.terminators and symbols[i] != "ep":
                    break
                if sum(1 for s in symbols[:i] if "ep" in self._first[s]) != i:
                    break
            if "ep" in res and sum(1 for s in symbols if "ep" in self._first[s]) != len(symbols):
                res.remove("ep")
            return res

    def closure(self, item):
        """
        item: 四元组, 表示一个项目("start", (), ("A", ), {'$'}), 即 start ::= 丶 'A', $
        [A -> α•Bγ, a] -> B in VN , b in First(γa), 都有 ε -> [B -> ▪β, b]
        :return: 这个item所在的项目集
        """
        que = Queue()
        que.put(item)
        self._first['$'] = '$'
        grammar = self.grammar
        res = []
        vis = defaultdict(set)
        while not que.empty():
            top = que.get()
            vis[(top[0], top[1], top[2])].update(top[3])
            # res.append(top)
            if not top[2]:
                # 这是一个规约项目, 例如 start -> A•
                continue
            B, gama = top[2][0], top[2][1:] or ("ep", )
            if B not in self.non_terminators:
                # B 是非终结符才产生转换
                continue
            for exp in grammar[B]:
                _exp = tuple(exp)
                if _exp == ("ep", ):
                    _exp = tuple()
                for a in top[3]:
                    fst = self.first(list(gama) + [a])
                    if not fst.issubset(vis[(B, tuple(), _exp)]):   # 如果曾经出现过, 不再入队
                        vis[(B, tuple(), _exp)].update(fst)
                        que.put((B, tuple(), _exp, fst))
        return [core + (head, ) for core, head in vis.iteritems()]

    def compile(self):
        """
        利用 self.grammar 编译出dfa, 并构造分析表
        :return:
        """
        alloc = 0
        grammar = self.grammar
        dfa = DFA()
        dfa.start = None
        que = Queue()
        que.put(self.closure(("start", tuple(), tuple(grammar["start"][0]), {'$'})))
        vis = dict()
        while not que.empty():
            lr_items = que.get()
            if frozen_items(lr_items) in vis:
                continue
            dfa_node = DFANode(lr_items=lr_items)
            vis[frozen_items(lr_items)] = dfa_node
            if not dfa.start:
                dfa.start = dfa_node
            for item in lr_items:
                if item[2]:
                    u_item = (item[0], item[1] + item[2][:1], item[2][1:], item[3])
                    u_items = self.closure(u_item)
                    que.put(u_items)
        que.put(dfa.start)
        vis2 = dict()
        while not que.empty():
            dfa_node = que.get()
            if dfa_node in vis2:
                continue
            vis2[dfa_node] = 1
            for item in dfa_node.lr_items:
                if item[2]:
                    u_item = (item[0], item[1] + item[2][:1], item[2][1:], item[3])
                    u_items = self.closure(u_item)
                    dfa_node.next[item[2][0]] = vis[frozen_items(u_items)]
                    que.put(vis[frozen_items(u_items)])
        return dfa

    def parser(self):
        pass


if __name__ == "__main__":
    l = LRParser()
    l.read_grammar("grammar.txt")
    l.calc_first()
    l.get_eps()
    """
    print l.first("S")
    print l.first(['A', 'B'])
    print l.first(['b', 'C'])
    print l.first(['a', 'D'])
    print l.first(["A", "D"])
    print l.first(['a', 'S'])
    """
    # print l.closure(("start", tuple(), ("A", ), {'$'}))
    print l.closure(("S", ("A", "d"), ("D", ), {'$'}))  #造成无限循环
    # print l.first(['ep', '$'])
    # print l.first(['A', 'b'])
    print l.closure(("start", tuple(), ("S", ), ['$']))
    l.compile()