# coding: utf-8
"""
词法分析用的正则库

regex表示如下几种: (按顺序递归解析即可满足优先级)
1. 基本 由单个字符组成
2. r|s型, L(r|s) = L(r) | L(r)
3. rs型, L(rs) = L(r)L(s)
4. r*型, L(r*) = L(r)*
5. r+型, L(r+) = L(r)L(r*)
6. r?型, L(r?) = L(r) | phi
7. (r)型, L((r)) = L(r), 只调整优先级

Extend Regex Expression:    (r?, r+型更适合放在基本类型中处理)
1. [a-c0-3] : (a|b|c|0|1|2|3)
"""
import crash_on_ipy


from operator import and_

from fa import NFA, NFANode
from util import char_range


class RegexError(Exception):
    pass


class Regex(object):

    _cache = {}
    meta_bases = ["\(", "\)", "\*", "\?", "\+", r"\\", "\|"]
    alphabet = char_range('a', 'z') + char_range('A', 'Z') + char_range('0', '9') + ["+", "-", "*", "/"]

    def __init__(self):
        pass

    @classmethod
    def is_regex(cls, pattern):
        if pattern in cls._cache:
            return cls._cache[pattern]
        cache = cls._cache
        print 'is_regex: ', pattern
        if len(pattern) < 1:
            return False
        if cls.is_base(pattern):
            cache[pattern] = True
            return True
        for i in range(1, len(pattern)):
            # print pattern[:i], pattern[i:]
            tmp = cls.is_regex(pattern[:i])
            if pattern[i] == '|' and tmp and cls.is_regex(pattern[i+1:]):
                cache[pattern] = True
                return True
            if cls.is_regex(pattern[i:]) and tmp:
                cache[pattern] = True
                return True
        if pattern[-1] in ['*', '?', '+']:
            cache[pattern] = cls.is_regex(pattern[:-1])
            return cache[pattern]
        if pattern[0] == '(' and pattern[-1] == ')':
            cache[pattern] = cls.is_regex(pattern[1:-1])
            return cache[pattern]
        cache[pattern] = False
        return False

    @classmethod
    def is_base(cls, pattern):
        if len(pattern) == 1:
            return pattern not in [base[1:] for base in cls.meta_bases]
        return pattern in cls.meta_bases

    @classmethod
    def _extend(cls, pattern):
        """
        返回拓展regex对应的raw regex exp.
        如[a-c] -> (a|b|c)
        """
        i = 0
        tmp = []
        res = []
        stat = 0
        while i < len(pattern):
            if pattern[i] == '[':
                i += 1
                stat = 1
                tmp = []
                if i == ']':
                    i += 1
                    stat = 0
                    continue
            if pattern[i] == ']':
                i += 1
                stat = 0
                res.append("(" + "|".join(tmp) + ")")
                continue
            if stat == 1:
                if pattern[i] == '-':
                    i += 1
                    x = tmp.pop()
                    tmp.extend(char_range(x, pattern[i]))
                else:
                    tmp.append(pattern[i])
                i += 1
            else:
                res.append(pattern[i])
                i += 1
        return "".join(res)

    @classmethod
    def compile_nfa(cls, pattern, extend=False, **kwargs):
        if extend:
            pattern = cls._extend(pattern)
        res = compile_nfa(pattern)
        for node in res.end:
            node.meta.update(kwargs)
        return res

    @classmethod
    def compile_dfa(cls, pattern, extend=False):
        if extend:
            pattern = cls._extend(pattern)
        return compile_dfa(pattern)

is_regex = Regex.is_regex
is_base = Regex.is_base


def compile_nfa(pattern):
    """
    :param pattern: 正则
    :return: NFA
    """
    print 'compile nfa [%s]' % (pattern, )
    assert isinstance(pattern, str)
    if is_base(pattern):
        if pattern in Regex.meta_bases:
            pattern = pattern[1:]
        nfa = NFA()
        enode = NFANode()
        enode.end = True
        nfa.start.next[pattern] = {enode}
        nfa.end.add(enode)
        return nfa
    elif 0 < pattern.find('|') and and_(*map(is_regex, pattern.split('|', 1))):
    # elif 0 < pattern.find('|'):
    #     pdb.set_trace()
        # if not and_(*map(is_regex, pattern.split('|', 1))):
        #     pass
        # pdb.set_trace()
        print 'r|s型'
        l = pattern.find('|')
        s1, s2 = pattern[:l], pattern[l+1:]
        nfa1, nfa2 = map(compile_nfa, [s1, s2])
        nfa = NFA()
        nfa.start.next["ep"] = set()
        nfa.start.next["ep"].update([nfa1.start, nfa2.start])
        enode = NFANode()
        enode.end = True
        nfa.end.add(enode)
        for node in nfa1.end | nfa2.end:
            if "ep" not in node.next:
                node.next["ep"] = set()
            node.next["ep"].add(enode)
            node.end = False
        nfa1.end, nfa2.end = set(), set()
        return nfa
    else:
        for i in range(1, len(pattern)):
            s1, s2 = pattern[:i], pattern[i:]
            if is_regex(s1) and is_regex(s2):
                print 'rs 连接型'
                nfa1, nfa2 = map(compile_nfa, [s1, s2])
                nfa = NFA()
                snode = nfa.start
                enode = NFANode()
                enode.end = True
                nfa.end = {enode}
                for node in nfa1.end:
                    node.end = False
                    if "ep" not in node.next:
                        node.next["ep"] = set()
                    node.next["ep"].add(nfa2.start)
                for node in nfa2.end:
                    node.end = False
                    if "ep" not in node.next:
                        node.next["ep"] = set()
                    node.next["ep"].add(enode)
                snode.next["ep"] = {nfa1.start}   #虽然我觉得nfa.start = {nfa1.start} 也可以 , 还是按照教材把
                return nfa
        if pattern[-1] == '*' and is_regex(pattern[:-1]):
            print 'r* 型'
            nfa0 = compile_nfa(pattern[:-1])
            nfa = NFA()
            snode = nfa.start
            enode = NFANode()
            enode.end = True
            nfa.end.add(enode)
            snode.next["ep"] = {enode, nfa0.start}
            for node in nfa0.end:
                if "ep" not in node.next:
                    node.next["ep"] = set()
                node.next["ep"].update([nfa0.start, enode])
                node.end = False
            nfa0.end = set()
            return nfa
        elif pattern[-1] == '+' and is_regex(pattern[:-1]):
            print 'r+型'
            nfa0 = compile_nfa(pattern[:-1])
            for node in nfa0.end:
                if "ep" not in node.next:
                    node.next["ep"] = set()
                node.next["ep"].add(nfa0.start)
            return nfa0
        elif pattern[-1] == '?' and is_regex(pattern[:-1]):
            print 'r?型'
            nfa0 = compile_nfa(pattern[:-1])
            if "ep" not in nfa0.start.next:
                nfa0.start.next["ep"] = set()
            nfa0.start.next["ep"].update(nfa0.end)
            return nfa0
        elif pattern[-1] == ')' and pattern[0] == '(' and is_regex(pattern):
            print '(r)型'
            return compile_nfa(pattern[1:-1])
        else:
            print 'Excuse me? What a fucking regex exp?'
            #print Regex._cache
            #raise RegexError()
            raise Exception()


def compile_dfa(pattern):
    return compile_nfa(pattern).convert_dfa()


if __name__ == '__main__':
    #print Regex.is_regex("(")
    #print is_regex("(ab")
    #print Regex.is_regex("(*djwjevsfsfsfswsfafasdasdanr3us)")
    #print Regex._cache
    #print len(Regex._cache)
    nfa = Regex.compile_nfa(raw_input(), extend=True)
    for nend in nfa.end:
        nend.meta["type"] = "expression"
    print 'nfa done!'
    nfa.draw()
    dfa = nfa.convert_dfa(copy_meta=["type"])
    dfa.draw(show_meta=True)
    print 'done!'
