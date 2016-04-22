# coding: utf-8
"""
something useful but ..
"""

#from functools import partial


def unions(sets):
    return reduce(lambda x, y: x.union(y), sets, set())