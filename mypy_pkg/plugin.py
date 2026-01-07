from __future__ import annotations
from typing import Optional, Callable, Any
from mypy.plugin import Plugin, AnalyzeTypeContext, MethodContext
from mypy.types import (
    Type, Type as MypyType, Instance, 
    AnyType, TypeOfAny, TypeType, CallableType, TypedDictType,
    get_proper_type
)
from mypy.nodes import TypeInfo, Var
from mypy.subtypes import is_subtype

from source_hook3 import source_term_hook
# from function_hook import function_term_hook
from operation_hook import term_mul_hook
import vect_lib

# from icecream import ic

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

        if is_ignored(fullname):
            return None

        print(f"get_function_hook called with {fullname = }")
        return None
    
    def get_function_signature_hook(self, fullname: str) -> None:
        """Called whenever mypy encounters a function call to analyze its signature."""

        if is_ignored(fullname):
            return None

        print(f"get_function_signature_hook called with {fullname = }")
        return None
    
    def get_method_hook(self, fullname: str) -> None:
        if is_ignored(fullname):
            return None

        print(f"get_method_hook called with {fullname = }")
        return None
    
    def get_method_signature_hook(self, fullname: str) -> None:
        if is_ignored(fullname):
            return None

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

class StreamPlugin(Plugin):
    def get_method_hook(self, fullname: str) -> Optional[Callable[[MethodContext], MypyType]]:
        """
        Trigger this hook whenever `__mul__` is called on a SourceTerm or FunctionTerm.
        """
        # Adjust these class names to match the actual fully qualified names in logicsponge
        # target_classes = {
        #     "logicsponge.core.SourceTerm", 
        #     "logicsponge.core.FunctionTerm",
        #     # Add your specific subclasses if they don't inherit __mul__ directly
        # }
        
        if "." in fullname and fullname.endswith("__mul__"):
            # Simple check: assuming if it ends in __mul__, we check it.
            # You might want to verify the class matches target_classes strictly.
            return self.check_stream_compatibility
        return None

    def check_stream_compatibility(self, ctx: MethodContext) -> MypyType:
        """
        Logic to check if LHS output matches RHS input.
        """
        lhs_type = ctx.type
        # The RHS is the first argument to __mul__
        # ctx.arg_types is a list of lists (for overloads), we take the first arg.
        if not ctx.arg_types or not ctx.arg_types[0]:
            return ctx.default_return_type
            
        rhs_type = ctx.arg_types[0][0] 

        print(f"\nAnalyzing stream {lhs_type} * {rhs_type}")

        # We only care if both sides are Instances (classes)
        if not isinstance(lhs_type, Instance) or not isinstance(rhs_type, Instance):
            return ctx.default_return_type

        # 1. Extract Output type from Left Hand Side (LHS)
        lhs_output = self._get_type_attribute(lhs_type.type, "Output")
        if lhs_output is None:
            print(f"\tNo Output type found for lhs: {lhs_type.type.name}")
            return rhs_type
        
        # 2. Extract Input type from Right Hand Side (RHS)
        rhs_input = self._get_type_attribute(rhs_type.type, "Input")
        if rhs_input is None:
            print(f"\tNo Input type found for rhs: {rhs_type.type.name}")
            return rhs_type

        if lhs_output.fullname == rhs_input.fullname:
            print(f"\tStream types match: {lhs_output.name} (identical names)")
            return rhs_type

        # print(f"{lhs_output.name = }, {rhs_input.name = }")
        # print(lhs_output.typeddict_type, rhs_input.typeddict_type)

        # lhs_out_inst = Instance(lhs_output, [])
        # rhs_in_inst = Instance(rhs_input, [])
        # if is_subtype(lhs_out_inst, rhs_in_inst):
        #     print(f"\tStream types match: {lhs_output.name} is subtype of {rhs_input.name}")

        #     return rhs_type

        # Compare the TypedDict structures
        if lhs_output.typeddict_type is None or rhs_input.typeddict_type is None:
            ctx.api.fail(
                "Stream mismatch: Cannot compare non-TypedDict types.",
                ctx.context
            )
            return ctx.default_return_type
        
        for k, v in lhs_output.typeddict_type.items.items():
            if rhs_input.typeddict_type.items.get(k) != v:
                ctx.api.fail(
                    f"Stream mismatch: expected key '{k}' of type '{v}' "+
                    f"but got type '{rhs_input.typeddict_type.items.get(k)}' from "+
                    f"'{rhs_type.type.name}'",
                    ctx.context
                )
                    
                return AnyType(TypeOfAny.from_error)
        
        print(f"\tStream types match: {lhs_output.name} (identical TypedDict structure)")

        return rhs_type
        

    def _get_type_attribute(self, type_info: TypeInfo, attr_name: str) -> Optional[TypeInfo]:
        """
        Searches for a class attribute (e.g., 'Input', 'Output') in the class 
        and its parents, returning the TypeInfo of the value assigned to it.
        """
        
        # 1. Search the Class and its Parents (MRO)
        # type_info.get() only checks the class itself. 
        # We iterate MRO to find inherited attributes.
        sym = None
        for base in type_info.mro:
            sym = base.get(attr_name)
            if sym:
                break
                
        if not sym or not sym.node:
            # Debug tip: If this hits, the line 'Output = ...' is missing from your python code.
            return None

        node = sym.node

        # CASE A: It is a nested class definition
        # class Hello(...):
        #     class Output(TypedDict): ...
        if isinstance(node, TypeInfo):
            return node

        # CASE B: It is a variable assignment
        # class Hello(...):
        #     Output = HelloMsg
        if not isinstance(node, Var):
            print("\tOutput/Input attribute is not of type 'Type[...]'.")
            return None
        
        # Unwrap the variable's type
        # The type of the variable 'Output' is 'Type[HelloMsg]'
        var_type = get_proper_type(node.type)
        
        # SUB-CASE B1: It's a TypeType (e.g. Output: Type[HelloMsg] = ...)
        if isinstance(var_type, TypeType):
            item_type = get_proper_type(var_type.item)
            if isinstance(item_type, Instance):
                return item_type.type
            else:
                print("\tOutput/Input attribute does not reference a class.")
                return None

        # SUB-CASE B2: It's a Callable (e.g. Output = HelloMsg)
        # Mypy treats the class symbol 'HelloMsg' as its constructor.
        if isinstance(var_type, CallableType):
            # We want the return type of the constructor: "-> HelloMsg"
            ret_type = get_proper_type(var_type.ret_type)
            if isinstance(ret_type, Instance):
                return ret_type.type
            elif isinstance(ret_type, TypedDictType):
                return ret_type.fallback.type
            else:
                print("\tOutput/Input attribute does not reference a class.")
                print(f"{type(ret_type) = }\n{ret_type = }")
                return None
        
        # SUB-CASE B3: Legacy Instance check (fallback)
        if isinstance(var_type, Instance):
            
            if var_type.type.fullname != 'builtins.type':
                print("\tOutput/Input attribute is not of type 'Type[...]'.")
                return None

            # The argument to Type[...] is the actual class (HelloMsg)
            if not var_type.args:
                print("\tOutput/Input attribute has no type arguments.")
                return None

            actual_type = get_proper_type(var_type.args[0])
            if isinstance(actual_type, Instance):
                return actual_type.type
            else:
                print("\tOutput/Input attribute does not reference a class.")
                return None
            
        print("\tOutput/Input attribute is nor TypeType nor Instance.")
        print(f"{type(var_type) = }\n{var_type = }")
        return None
        
    

def plugin(version: str) -> type[Plugin]:
    # print(f"CustomPlugin loaded for mypy version {version}")
    # return CustomPlugin

    # print(f"LogicSpongePlugin loaded for mypy version {version}\n")
    # return LogicSpongePlugin

    print(f"StreamPlugin loaded for mypy version {version}")
    return StreamPlugin