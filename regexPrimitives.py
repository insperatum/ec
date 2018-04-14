from program import Primitive, Program
from grammar import Grammar
from type import tlist, tint, tbool, arrow, t0, t1, t2, tpregex

import math

# evaluation to regular regex form. then I can unflatten using Luke's stuff.
def _arrow(x): return "(" + x + ")*"
def _plus(x): return "(" + x + ")+"
def _maybe(x): return "(" + x + ")?"
def _alt(x): return lambda y: "(" + x + "|" + y + ")"
def _concat(x): return lambda y: "(" + x + y + ")"


def basePrimitives():
    return [Primitive("string:" + i, tpregex, i) for i in printable[:-4]
    ] + [
    	Primitive(".", tpregex, "."),
        Primitive("\\d", tpregex, "\\d"),
        Primitive("\\s", tpregex, "\\s"),
        Primitive("\\w", tpregex, "\\w"),
        Primitive("\\l", tpregex, "\\l"),
        Primitive("\\u", tpregex, "\\u"),
        Primitive("*", arrow(tpregex, tpregex), _arrow),
        Primitive("+", arrow(tpregex, tpregex), _plus),
        Primitive("?", arrow(tpregex, tpregex), _maybe),
        Primitive("|", arrow(tpregex, tpregex, tpregex), _alt),
        Primitive("concat", arrow(tpregex, tpregex, tpregex), _concat),
    ]


def altPrimitives():
