# coding: utf-8

import readline
if 'libedit' in readline.__doc__:
    readline.parse_and_bind("bind ^I rl_complete")
else:
    readline.parse_and_bind("tab: complete")

import crash_on_ipy

crash_on_ipy.init()

from lex import Lex
from parser import LRParser
from util import print_with_color, colorful
from runtime import ParseHandler, Env

lex = Lex()
lex.keyword = ['lambda', '[', ']', 'let', 'define', 'if', 'cond', 'or', 'and', '(', ')']
lex.read_lex('regular_lex.txt')
lex.compile(grammar_type="regular")
print(colorful('词法编译完成...', 'Yellow'))

parser = LRParser()
parser.read_grammar('schepy_grammar.txt')
parser.compile()
print(colorful('语法编译完成...', 'Yellow'))

global_env = Env.std_env()
global_env['add'] = 'add~'

while True:
    exp = raw_input(colorful('schepy>', 'Cyan'))
    handler = ParseHandler()
    parser.parse(lex.lex(exp, ignore=["limit"]), handler)
    print_with_color('表达式的值: ' + repr(handler.ast.calc_value(env=global_env)), "Magenta")
