from __future__ import annotations
from typing import TYPE_CHECKING

"""
This file contains minimal expressions/annotations that illustrate which mypy
plugin hooks would be called, assuming the plugin returns callbacks for the
fully-qualified names used below.

Notes:
- We import inside `TYPE_CHECKING` to avoid runtime import requirements.
- Mypy still analyzes these references and will invoke the corresponding hooks.
"""

if TYPE_CHECKING:
	# Hypothetical packages that the plugin targets
	from lib import Vector  # fullname: "lib.Vector"
	import mylib            # functions/methods under: "mylib.*"


# --- get_type_analyze_hook("lib.Vector") ------------------------------------
# When mypy analyzes these annotations, it will call
#   get_type_analyze_hook("lib.Vector")
# and then your returned AnalyzeTypeContext callback.
if TYPE_CHECKING:
    a: "Vector[int, int]"
    b: "Vector[int, int, int]"


# --- get_function_hook("mylib.make_pair") -----------------------------------
# On analyzing this call expression, mypy will call
#   get_function_hook("mylib.make_pair")
# and then your FunctionContext callback.
if TYPE_CHECKING:
	pair_result = mylib.make_pair(1, "x")


# --- get_function_signature_hook("mylib.varargs_to_fixed") ------------------
# Before type-checking the call, mypy will ask the plugin for a signature hook
# via get_function_signature_hook("mylib.varargs_to_fixed"). If provided, the
# returned FunctionSigContext callback can reshape the callable's signature.
if TYPE_CHECKING:
	sig_fixed = mylib.varargs_to_fixed(1, 2, 3)


# --- get_method_hook("mylib.SomeClass.compute") -----------------------------
# For method calls, mypy uses get_method_hook with the method's fullname.
# Here it would invoke get_method_hook("mylib.SomeClass.compute").
if TYPE_CHECKING:
	sc = mylib.SomeClass()
	computed = sc.compute(42)


# --- get_method_signature_hook("mylib.SomeClass.__add__") -------------------
# Special methods (except __init__ and __new__) can have their signatures
# adjusted via get_method_signature_hook. An expression like sc + 10 resolves
# to __add__, so mypy will look up
#   get_method_signature_hook("mylib.SomeClass.__add__").
if TYPE_CHECKING:
	plus_result = sc + 42 # triggers __add__ on SomeClass
