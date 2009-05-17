#!/usr/bin/python

__all__ = ('parse_checks', 'BooleanParser')

try: from pyparsing import *
except ImportError: from utils.pyparsing import *

def __make_parser():
    key = Word(alphas, alphanums+"_-")
    value = Word(alphanums + "-.,_=<>!@$%^&*[]{}:;|/'") | QuotedString('"')
    return Dict(ZeroOrMore(Group( key + Optional( Suppress("=") + value, default=True ) ) ))
__checkparser = __make_parser()

def parse_checks(string):
    """
from parsers import parse_checks
>>> parse_checks('dependent=5a,no dependent="5a && 4a" dog="Roaming Rover" name=Robert foo bar')
([(['dependent', '5a,no'], {}), (['dependent', '5a && 4a'], {}), (['dog', 'Roaming Rover'], {}), (['name', 'Robert'], {}), (['foo', True], {}), (['bar', True], {})], {'dependent': [('5a,no', 0), ('5a && 4a', 1)], 'foo': [(True, 4)], 'bar': [(True, 5)], 'dog': [('Roaming Rover', 2)], 'name': [('Robert', 3)]})
"""
    return __checkparser.parseString(string, parseAll=True)


# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-
# - Boolean Expression Parser -
# -=-=-=-=-=-=-=-=-=-=-=-=-=-=-

class BoolOperand(object):
    def __init__(self, t):
        self.args = t[0][0::2]
    def __str__(self):
        sep = " %s " % self.reprsymbol
        return "(" + sep.join(map(str, self.args)) + ")"

class BoolAnd(BoolOperand):
    reprsymbol = '&&'
    def __nonzero__(self):
        for a in self.args:
            if not bool(a):
                return False
        return True

class BoolOr(BoolOperand):
    reprsymbol = '||'    
    def __nonzero__(self):
        for a in self.args:
            if bool(a):
                return True
        return False

class BoolNot(BoolOperand):
    def __init__(self,t):
        self.arg = t[0][1]
    def __str__(self):
        return "!" + str(self.arg)
    def __nonzero__(self):
        return not bool(self.arg)

class Checker(object):
    "Simple wrapper to call a specific function, passing in args and kwargs each time"
    def __init__(self, func, expr, *args, **kwargs):
        self.func = func
        self.expr = expr
        self.args = args
        self.kwargs = kwargs

    def __nonzero__(self):
        return self.func(self.expr, *self.args, **self.kwargs)

    def __hash__(self):
        return hash(self.expr)

    def __unicode__(self):
        try: fname=self.func.func_name
        except: fname="TestExpr"
        return "%s('%s')" % (fname, self.expr)
    __str__ = __unicode__


class BooleanParser(object):
    """Simple boolean parser

>>> def foo(x):
...   if x == '1': return True
...   return False
... 
>>> foo('1')
True
>>> foo('0')
False
>>> p = BooleanParser(foo)
>>> p.parse('1 and 0')
False
>>> p.parse('1 and 1')
True
>>> p.parse('1 or 1')
True
>>> p.parse('0 or 1')
True
>>> p.parse('0 or 0')
False
>>> p.parse('(0 or 0) and 1')
False
>>> p.parse('(0 or 0) and (1)')
False
>>> p.parse('(0 or 1) and (1)')
True
>>> p.parse('(0 or 0) or (1)')
True
"""

    def __init__(self, func, *args, **kwargs): # treats kwarg boolOperand specially!
        self.args = args
        self.kwargs = kwargs
        self.func = func
        if "boolOperand" in kwargs:
            boolOperand = kwargs["boolOperand"]
            del kwargs["boolOperand"]
        else:
            boolOperand = Word(alphanums + "-.,_=<>!@$%^&*[]{}:;|/\\")
        boolOperand = boolOperand.setParseAction(self._check)
        self.boolExpr = operatorPrecedence( boolOperand,
        [
            ("not ", 1, opAssoc.RIGHT, BoolNot),
            ("or",  2, opAssoc.LEFT,  BoolOr),
            ("and", 2, opAssoc.LEFT,  BoolAnd),
        ])

    def _check(self, string, location, tokens):
        checker = Checker(self.func, tokens[0], *self.args, **self.kwargs)
        tokens[0] = checker

    def parse(self, code):
        if not code or not code.strip():
            return False
        return bool(self.boolExpr.parseString(code)[0])
    
    def toString(self, code):
        return str(self.boolExpr.parseString(code)[0])

if __name__ == '__main__':
    import doctest
    doctest.testmod()
