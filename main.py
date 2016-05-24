import crash_on_ipy

crash_on_ipy.init()

from lex import Lex
from parser import LRParser

lex = Lex()
lex.read_lex('regular_lex.txt')
lex.compile(grammar_type="regular")

parser = LRParser()
parser.read_grammar('grammar.txt')
parser.compile()

while True:
    exp = raw_input('schepy>')
    parser.parse(lex.lex(exp, ignore=["limit"]))