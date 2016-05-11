# coding: utf-8
"""
something useful but ..
"""


def unions(sets):
    """
    :param sets: 集合的列表
    :return: 一些set的union
    """
    return reduce(lambda x, y: x.union(y), sets, set())


def char_range(l, r):
    """
    :param l: 字符左边界
    :param r: 字符右边界
    :return:[l, r]区间的字符
    """
    return [chr(i) for i in range(ord(l), ord(r)+1)]


def parse_convert(s):
    """
    :param s: 字符串
    :return: 转换转义符之后的字符串
    """
    s = s.replace(r"\n", "\n")
    s = s.replace(r"\r", "\r")
    s = s.replace(r"\t", "\t")
    return s


def bnf_reader(filename='test.txt'):
    """
    :param filename: 文件名
    :return: 返回一个每次迭代得到一行分割之后的二元组的生成器
    """
    with open(filename, 'rt') as reader:
        comment = False
        for line in reader:
            if line.startswith('#') or line.find("::=") <= 0:
                continue
            line = parse_convert(line).strip()
            if line == '"""' or line == "'''":
                comment = not comment
            if comment:
                continue
            yield tuple(line.split(" ::= "))


def frozen_item(item):
    return tuple([item[0], item[1], item[2], frozenset(item[3])])


def frozen_items(items):
    return frozenset([frozen_item(item) for item in items])
