"""Run a single test and print full traceback. Usage: python run_one_test.py"""
from lark import Lark

with open('bibtex.lark', 'r') as f:
    grammar = f.read()

parser = Lark(grammar, start='bibtex', parser='lalr')

# First test case - standard article
bibtex = '''
@article{Smith2020,
    author = {John Smith},
    title = {A Study of Something Interesting and Novel},
    journal = {Journal of Important Studies},
    year = {2020},
    volume = {10},
    number = {2},
    pages = {100-120},
    doi = {10.1234/example.doi}
}
'''

try:
    result = parser.parse(bibtex)
    print("Parse OK")
except Exception as e:
    print("ERROR:", type(e).__name__, e)
    import traceback
    traceback.print_exc()
