# coding: utf-8

import crash_on_ipy

crash_on_ipy.init()

from lex import Lex
from parser import LRParser
from util import print_with_color

lex = Lex()
lex.keyword = ['lambda']
lex.read_lex('regular_lex.txt')
lex.compile(grammar_type="regular")

parser = LRParser()
parser.read_grammar('schepy_grammar.txt')
parser.compile()

while True:
    print_with_color('schepy>', 'Cyan', new_line=False)
    exp = raw_input()
    try:
        parser.parse(lex.lex(exp, ignore=["limit"]))
    except Exception as e:
        # ..粗暴处理
        print_with_color('May be something wrong with your expression~', 'Red')