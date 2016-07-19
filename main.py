# coding: utf-8
"""
组合其他模块解释读入代码
个别变量名.. 只是无聊为了刷pylint
"""

from __future__ import print_function

import readline
if 'libedit' in readline.__doc__:
    readline.parse_and_bind("bind ^I rl_complete")
else:
    readline.parse_and_bind("tab: complete")

import crash_on_ipy

crash_on_ipy.init()

from lex import Lex
from parser import LRParser
from util import colorful
from runtime import ParseHandler, Env

LEX = Lex()
LEX.keyword = ['lambda', '[', ']', 'let', 'define', 'if',
               'cond', 'or', 'and', '(', ')', '$T', '$F']
LEX.read_lex('regular_lex.txt')
LEX.compile(grammar_type="regular")
# lex.read_lex('regex_lex.txt')
# lex.compile()
print(colorful('词法编译完成...', 'Yellow'))
PARSER = LRParser()
PARSER.read_grammar('schepy_grammar.txt')
PARSER.compile()
print(colorful('语法编译完成...', 'Yellow'))
GLOBAL_ENV = Env.std_env()
while True:
    try:
        HANDLER = ParseHandler()
        EXP = raw_input(colorful('schepy => ', 'Cyan'))
        PARSER.parse(LEX.lex(EXP, ignore=["limit"]), HANDLER)
        print(';VALUE: ' +
              colorful(repr(HANDLER.ast.calc_value(env=GLOBAL_ENV)), "Magenta"))
    except (EOFError, KeyboardInterrupt) as e:
        CHOICE = raw_input(colorful('Do you really want to exit ([y]/n)?',
                                    "Red"))
        if CHOICE in ['y', 'Y', '']:
            break

