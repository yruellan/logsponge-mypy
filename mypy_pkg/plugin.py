from __future__ import annotations
from typing import Callable, Any
from mypy.plugin import Plugin, AnalyzeTypeContext, FunctionContext
from mypy.types import Type

from source_hook import source_term_hook
from function_hook import function_term_hook
from operation_hook import term_mul_hook
import vect_lib

# https://mypy.readthedocs.io/en/stable/extending_mypy.html

# 'FunctionTerm'
# 'KeyValueFilter', 
# 'Print', 
# 'Term', 
# 'VT', 
# 'SourceTerm', 
# 'SequentialTerm', 
# 'DataStream', 
# 'DataItem', 
# 'ParallelTerm', 
# 'KT', 
# 'CompositeTerm', 
# 'State'

names = set()

def is_ignored(fullname: str) -> bool:

    for builtin_prefix in ["typing.", "typing_", "builtins.", "enum.", "bytewax.", "dataclasses.", "datetime.", "logging.", "sys."]:
        if fullname.startswith(builtin_prefix):
            return True

    if fullname in ['<list>', '<dict>', '<set>', '<tuple>']:
        return True
    
    return False

class CustomPlugin(Plugin):
    def get_type_analyze_hook(self, fullname: str) -> Callable[[AnalyzeTypeContext], Type] | None:
        """Called whenever mypy analyzes a type annotation."""

        if fullname == "lib.Vector" or fullname.endswith(".Vector"):
            print(f"[plugin] get_type_analyze_hook engaged for: {fullname}")

            return vect_lib.analyze_vector
        


        return None
        
    def get_function_hook(self, fullname: str) -> None:
        """Called whenever mypy encounters a function call."""

        if is_ignored(fullname): return None

        print(f"get_function_hook called with {fullname = }")
        return None
    
    def get_function_signature_hook(self, fullname: str) -> None:
        """Called whenever mypy encounters a function call to analyze its signature."""

        if is_ignored(fullname): return None

        print(f"get_function_signature_hook called with {fullname = }")
        return None
    
    def get_method_hook(self, fullname: str) -> None:
        if is_ignored(fullname): return None

        print(f"get_method_hook called with {fullname = }")
        return None
    
    def get_method_signature_hook(self, fullname: str) -> None:
        if is_ignored(fullname): return None

        names.add(fullname)
        print(f"get_method_signature_hook called with {names = }")
        return None
    
class LogicSpongePlugin(Plugin):
    def get_base_class_hook(self, fullname: str) -> Any:
        if fullname == "logicsponge.core.logicsponge.SourceTerm":
            # print(f"get_base_class_hook called with {fullname = }")
            return source_term_hook
        # if fullname == "logicsponge.core.logicsponge.FunctionTerm":
        #     # print(f"get_base_class_hook called with {fullname = }")
        #     return function_term_hook
        # print(f"get_base_class_hook called with {fullname = } but no hook found")
        return None
    
    def get_method_hook(self, fullname: str) -> Any:
        if fullname == "logicsponge.core.logicsponge.Term.__mul__":
            print(f"get_method_hook called with {fullname = }")
            return term_mul_hook

def plugin(version: str) -> type[LogicSpongePlugin]:
    # print(f"CustomPlugin loaded for mypy version {version}")
    # return CustomPlugin

    print(f"LogicSpongePlugin loaded for mypy version {version}\n")
    return LogicSpongePlugin