# coding: utf-8

from collections import defaultdict
from Queue import Queue

from regex import Regex
from fa import NFA, DFA, NFANode
from util import bnf_reader


def search(dfa, text, handler):
    """
    :param dfa: 在dfa上查找
    :param text: 文本字符串
    :param handler: 成功匹配之后的处理函数
    :return: pass
    """
    i = 0
    cur_token = []
    cur_node = dfa.start
    stat = 0    # 1: 已经到达过终结状态, 0: 尚未到达过终结态
    while i < len(text):
        if text[i] in cur_node.next:
            cur_token.append(text[i])
            cur_node = cur_node.next[text[i]]
            i += 1
            if cur_node.end:
                stat = 1
        else:
            """
            找不到匹配
            """
            if cur_node.end:
                #print '到达终结态'
                handler(token_type=cur_node.type, token="".join(cur_token))
                cur_token = []
                cur_node = dfa.start
            else:
                print '出错了!'
                break
    if cur_node.end:
        handler(token_type=cur_node.type, token="".join(cur_token))


def test_handler(token_type, token):
    print '捕获 %s: [%s]' % (token_type, token)


class Lex(object):
    """
    词法分析
    """

    def __init__(self):
        self.lexs = []
        self.lex_dfa = DFA()
        self.keyword = ['lambda']

    def read_lex(self, filename):
        self.lexs = bnf_reader(filename)

    def compile(self, grammar_type="regex"):
        """
        根据文法类型进行编译, 产生dfa. regex 表示 正则表达式, regular 表示 正规文法
        :param grammar: 文法类型
        :return:
        """
        if grammar_type == 'regex':
            nfas = []
            for le in self.lexs:
                # print le
                nfas.append(Regex.compile_nfa(le[1], extend=True, type=le[0]))
            nfa = NFA.combine(*nfas)
            self.lex_dfa = nfa.convert_dfa(copy_meta=["type"])
            return
        elif grammar_type == "regular":
            """
            本来没有想到会做三型文法解析, 由于parser里也有文法解析.. 此处应该跟那边合并..
            """
            nfas = []
            grammar = defaultdict(list)
            g_in, g_out = defaultdict(int), defaultdict(int)
            all_symbol = set()
            for l_hand, r_hand in self.lexs:
                l_hand = l_hand[1:-1]
                r_hands = [[x[1:-1] for x in r.strip().split()] for r in r_hand.split('|')]
                for hand in r_hands:
                    for h in hand:
                        g_in[h] += 1
                        all_symbol.add(h)
                g_out[l_hand] += 1
                all_symbol.add(l_hand)
                grammar[l_hand].extend(r_hands)
            grammar['limit'] = [[' '], ['\t'], ['\n']]
            ter, not_ter = [], []
            for sym in all_symbol:
                if g_in[sym] == 0:
                    not_ter.append(sym)
                if g_out[sym] == 0:
                    ter.append(sym)
            # print ter, not_ter
            nfas = []
            for token_type in not_ter:
                nfa = NFA()
                nfa.start = NFANode(r_name=token_type)
                end_node = NFANode(type=token_type)
                end_node.end = True
                nfa.end = {end_node}
                vis = {token_type: nfa.start}

                def get_node(name):
                    if name in vis:
                        return vis[name]
                    vis[name] = NFANode(r_name=name)
                    return vis[name]

                que = Queue()
                que.put(token_type)
                while not que.empty():
                    t = que.get()
                    node = get_node(t)
                    if node.meta.get('vis', 0) > 0:
                        continue
                    node.meta['vis'] = node.meta.get('vis', 0) + 1
                    for r_hand in grammar[t]:
                        node.next.setdefault(r_hand[0], set())
                        if len(r_hand) == 2:
                            node.next[r_hand[0]].add(get_node(r_hand[1]))
                            que.put(r_hand[1])
                        else:
                            node.next[r_hand[0]].add(end_node)
                nfas.append(nfa)
            nfa = NFA.combine(*nfas)
            self.lex_dfa = nfa.convert_dfa(copy_meta=["type"])
            return

    def lex(self, code, ignore=None):
        tokens = []
        ignore = ignore or []

        def lex_handler(token_type, token):
            if token_type[0] not in ignore:
                if token in self.keyword:
                    if token == '$T' or token == '$F':
                        tokens.append(('bool', token))
                    else:
                        tokens.append((token, token))
                else:
                    tokens.append((token_type[0], token))

        search(self.lex_dfa, code, lex_handler)
        return tokens


if __name__ == '__main__':
    l = Lex()
    l.read_lex("regex_lex.txt")
    l.compile()
    while True:
        print l.lex(raw_input(), ignore=["limit"])