# coding: utf-8

import regex
import fa
from regex import Regex
from fa import NFA


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
        #print 'cur_node: %s, char: %s' % (repr({key: cur_node.meta[key] for key in cur_node.meta if key != 'nfa_set'}), text[i])
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


if __name__ == '__main__':
    nfas = []
    nfas.append(Regex.compile_nfa("[a-z][a-z0-9]*", extend=True, type="identifier"))
    nfas.append(Regex.compile_nfa("\(", extend=True, type="lpl"))
    nfas.append(Regex.compile_nfa("\)", extend=False, type="rpl"))
    nfas.append(Regex.compile_nfa("(\+|-|\*|/)", type="op"))
    nfas.append(Regex.compile_nfa("[ \t\n]", extend=True, type="limit"))
    nfas.append(Regex.compile_nfa("[0-9][0-9]*", extend=True, type="number"))
    nfa = NFA.combine(*nfas)
    nfa.draw()
    dfa = nfa.convert_dfa(copy_meta=["type"])
    dfa.draw(show_meta=False)
    print 'compile dfa done!'
    while True:
        search(dfa, raw_input(), test_handler)