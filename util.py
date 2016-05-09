# coding: utf-8
"""
something useful but ..
"""


def unions(sets):
    return reduce(lambda x, y: x.union(y), sets, set())


def char_range(l, r):
    return [chr(i) for i in range(ord(l), ord(r)+1)]


def parse_convert(s):
    s = s.replace(r"\n", "\n")
    s = s.replace(r"\r", "\r")
    s = s.replace(r"\t", "\t")
    return s


def bnf_reader(filename='test.txt'):
    with open(filename, 'rt') as f:
        for line in f:
            if line.startswith('#') or line.find("::=") <= 0:
                continue
            line = parse_convert(line)
            yield tuple(line[:-1].split(" ::= "))
