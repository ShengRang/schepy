# coding: utf-8
"""
something useful but ..
"""


def unions(sets):
    return reduce(lambda x, y: x.union(y), sets, set())


def char_range(l, r):
    return [chr(i) for i in range(ord(l), ord(r)+1)]