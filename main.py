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
lex.keyword = ['lambda', '[', ']', 'let', 'define', 'if', 'cond', 'or', 'and', '(', ')', '$T', '$F']
lex.read_lex('regular_lex.txt')
lex.compile(grammar_type="regular")
# lex.read_lex('regex_lex.txt')
# lex.compile()
print(colorful('词法编译完成...', 'Yellow'))

parser = LRParser()
parser.read_grammar('schepy_grammar.txt')
parser.compile()
print(colorful('语法编译完成...', 'Yellow'))

global_env = Env.std_env()

while True:
    try:
        handler = ParseHandler()
        exp = raw_input(colorful('schepy => ', 'Cyan'))
        parser.parse(lex.lex(exp, ignore=["limit"]), handler)
        print(';VALUE: ' + colorful(repr(handler.ast.calc_value(env=global_env)), "Magenta"))
    except (EOFError, KeyboardInterrupt) as e:
        choice = raw_input(colorful('Do you really want to exit ([y]/n)?', "Red"))
        if choice in ['y', 'Y', '']:
            break

