# coding: utf-8

from collections import defaultdict
from Queue import Queue

from fa import DFA, DFANode
from util import bnf_reader, frozen_items
from lex import Lex
from util import colorful


class LRConflict(Exception):

    def __init__(self):
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
        self.lr_dfa = None
        self.lr_table = None
        self.idx_items = []     # DFA节点项目集索引

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
                if sum(1 for s in symbols[:i+1] if "ep" in self._first[s]) != i+1:
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
        self.calc_first()
        alloc = 0
        grammar = self.grammar
        dfa = DFA()
        que = Queue()
        dfa.start = DFANode(id=alloc, lr_items=self.closure(("start", tuple(), tuple(grammar["start"][0]), {'$'})))
        self.idx_items = [dfa.start]
        que.put(dfa.start.lr_items)
        vis = dict()
        vis[frozen_items(dfa.start.lr_items)] = dfa.start
        while not que.empty():
            lr_items = que.get()
            # if frozen_items(lr_items) in vis:
            #     continue
            dfa_node = vis[frozen_items(lr_items)]
            # print 'u_items:'
            # print lr_items
            tmp = defaultdict(list)
            for item in lr_items:
                if item[2]:
                    u_item = (item[0], item[1] + item[2][:1], item[2][1:], item[3])
                    tmp[item[2][0]].append(u_item)
                    # 可能该状态有两个以上项目可以通过 item[2][0] 转换到新项目, 而新的项目集应该是他们的合集
            for l_hand, items in tmp.iteritems():
                vitem = defaultdict(set)
                for item in items:
                    u_items = self.closure(item)
                    for u_item in u_items:
                        vitem[u_item[:-1]].update(u_item[3])
                next_items = [core + (head, ) for core, head in vitem.iteritems()]
                if frozen_items(next_items) not in vis:
                    que.put(next_items)
                    alloc += 1
                    dfa_node.next[l_hand] = DFANode(id=alloc, lr_items=next_items)
                    self.idx_items.append(dfa_node.next[l_hand])        # 插入新节点
                    vis[frozen_items(next_items)] = dfa_node.next[l_hand]
                else:
                    dfa_node.next[l_hand] = vis[frozen_items(next_items)]
        # dfa.draw("LR", show_meta=["lr_items"], generate_id=False)
        self.lr_dfa = dfa
        # DFA 构造完成
        # 构造分析表
        lr_table = defaultdict(dict)
        que = Queue()
        que.put(dfa.start)
        vis = dict()
        while not que.empty():
            tmp = que.get()
            if tmp in vis:
                continue
            vis[tmp] = 1
            for item in tmp.lr_items:
                if item[2]:
                    # 移进状态
                    if item[2][0] in lr_table[tmp.id]:
                        if lr_table[tmp.id][item[2][0]]['action'] != 'shift':
                            print(colorful('移近规约冲突', 'Red'))
                            raise LRConflict()
                        elif lr_table[tmp.id][item[2][0]]['next'] != tmp.next[item[2][0]].id:
                            print(colorful('移近移近冲突', 'Red'))
                            raise LRConflict()
                    lr_table[tmp.id][item[2][0]] = dict(action="shift", next=tmp.next[item[2][0]].id)
                else:
                    # 规约状态
                    for a in item[3]:
                        if a in lr_table[tmp.id]:
                            if lr_table[tmp.id][a]['action'] != 'reduce':
                                print(colorful('移近规约冲突', 'Red'))
                                raise LRConflict()
                            elif lr_table[tmp.id][a]['grammar'] != item:
                                print(colorful('规约规约冲突', 'Red'))
                                raise LRConflict()
                        lr_table[tmp.id][a] = dict(action="reduce", grammar=item)
            for next_node in tmp.next.values():
                que.put(next_node)
        self.lr_table = lr_table
        return dfa

    def parse(self, tokens, handler):
        """
        接受token流, 并进行规约
        """
        # print '分析 tokens 流: ', tokens
        lr_table = self.lr_table
        stat_stack = [0, ]
        symbol_stack = ['$', ]
        input_stack = [('$', '$')] + tokens[::-1]
        # print input_stack
        while not (stat_stack == [0] and [x[0] for x in input_stack] == ['$', 'start'] and symbol_stack == ['$']):
            top_stat = stat_stack[-1]
            top_token_type = input_stack[-1][0]      # 取 token_type
            # top_token_type = input_stack.pop()[0]       # 取token
            action = lr_table[top_stat][top_token_type]
            if action["action"] == "shift":
                stat_stack.append(action["next"])
                if input_stack[-1][1] != 'no-sense':
                    handler.shift(input_stack[-1])
                symbol_stack.append(input_stack.pop()[0])
            elif action["action"] == "reduce":
                grammar = action["grammar"]
                handler.reduce(action["grammar"])
                # print 'reduce, 利用规则 %s -> %s' % (grammar[0], ' '.join(grammar[1]))
                for _ in range(len(grammar[1])):
                    stat_stack.pop()
                    symbol_stack.pop()
                input_stack.append((grammar[0], 'no-sense'))
        print '规约成功, 符合语法规则!'

    def show_dfa(self):
        """
        输出编译好的dfa, dot格式
        """
        que = Queue()
        vis = dict()
        que.put(self.lr_dfa.start)
        while not que.empty():
            tmp = que.get()
            if tmp in vis:
                continue
            vis[tmp] = 1
            lr_items = tmp.lr_items
            tmp.meta["items"] = '\n'.join(['%s -> %s ` %s, %s' % (item[0], ''.join(item[1]), ''.join(item[2]), '/'.join(item[3])) for item in lr_items])
            for a in tmp.next.keys():
                que.put(tmp.next[a])
        self.lr_dfa.draw("LR", show_meta=["items"])


if __name__ == "__main__":

    import readline
    if 'libedit' in readline.__doc__:
        readline.parse_and_bind("bind ^I rl_complete")
    else:
        readline.parse_and_bind("tab: complete")

    class ParseHandler(object):

        def __init__(self):
            self.ast = None
            self.exps = []

        def shift(self, token):
            print(colorful('移近 {0} {1}'.format(token[0], token[1]), "Cyan"))

        def reduce(self, grammar):
            """
            规约动作, grammar为规约用的产身世
            """
            print('利用规则' + colorful('%s -> %s' % (grammar[0], ' '.join(grammar[1])), "Green"))

    from util import colorful
    lex = Lex()
    lex.keyword = ['lambda', '[', ']', 'let', 'define', 'if', 'cond', 'or', 'and', '(', ')']
    lex.read_lex('regular_lex.txt')
    lex.compile(grammar_type="regular")
    print(colorful('词法编译完成...', 'Yellow'))

    parser = LRParser()
    parser.read_grammar('schepy_grammar.txt')
    parser.compile()
    print(colorful('语法编译完成...', 'Yellow'))
    parser.show_dfa()

    while True:
        parser.parse(lex.lex(raw_input(), ignore=["limit"]), ParseHandler())