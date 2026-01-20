from __future__ import annotations
from typing import Optional, Callable
from enum import Enum, auto
import sys

from mypy.plugin import Plugin, MethodContext
from mypy.types import (
    Type as MypyType, Instance, TypeVarType,
    AnyType, TypeOfAny, TypeType, CallableType, TypedDictType,
    get_proper_type,
)
from mypy.nodes import TypeInfo, Var, TypeAlias, Decorator
from mypy.subtypes import is_subtype
from mypy.expandtype import expand_type

# https://mypy.readthedocs.io/en/stable/extending_mypy.html

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
        if not ctx.arg_types or not ctx.arg_types[0]:
            return ctx.default_return_type
        rhs_type = ctx.arg_types[0][0] 

        print(f"\nAnalyzing stream {lhs_type} * {rhs_type}")

        # We only care if both sides are Instances (classes)
        if not isinstance(lhs_type, Instance) or not isinstance(rhs_type, Instance):
            return ctx.default_return_type
        
        class Behavior(Enum):
            SOURCE = auto()
            IDENTITY = auto()
            SINK = auto()
        
        LIBRARY_BEHAVIORS = {
            "logicsponge.core.logicsponge.Print": Behavior.IDENTITY,
            "logicsponge.core.logicsponge.Stop": Behavior.SINK,
            # "logicsponge.core.logicsponge.JsonParser": Behavior.IDENTITY,
        }

        rhs_fullname = rhs_type.type.fullname
        rhs_behavior = LIBRARY_BEHAVIORS.get(rhs_fullname)
        # lhs_fullname = lhs_type.type.fullname
        # lhs_behavior = LIBRARY_BEHAVIORS.get(lhs_fullname)

        if rhs_behavior is Behavior.SOURCE:
            ctx.api.fail(
                "Stream mismatch: Cannot compose into a SourceTerm.",
                ctx.context
            )
            return AnyType(TypeOfAny.from_error)
        if rhs_behavior is Behavior.IDENTITY:
            print(f"\tIdentity term detected: passing through type {lhs_type}")
            return lhs_type

        if rhs_behavior is Behavior.SINK:
            print(f"\tSink term detected: accepting any input, returning {rhs_type}")
            return rhs_type
        
        # CASE 3: Regular Terms

        # 1. Extract Output type from Left Hand Side (LHS)
        lhs_output = self._get_type_attribute(lhs_type.type, "Output")
        if lhs_output is None:
            print(f"\tNo Output type found for lhs: {lhs_type.type.name}")
            ctx.api.note("No Output type found on LHS of stream composition.", ctx.context)
            return rhs_type
        
        # 2. Extract Input type from Right Hand Side (RHS)
        rhs_input = self._get_type_attribute(rhs_type.type, "Input")
        if rhs_input is None:
            print(f"\tNo Input type found for rhs: {rhs_type.type.name}")
            ctx.api.note("No Input type found on RHS of stream composition.", ctx.context)
            return rhs_type
        
        # 3. Check Compatibility
        return self._check_stream_compatibility(ctx, rhs_type, lhs_output, rhs_input)


    def _check_stream_compatibility(self, ctx: MethodContext, rhs_type: Instance, lhs_output: TypeInfo, rhs_input: TypeInfo) -> MypyType:
        """
        Logic to check if LHS output matches RHS input using structural subtyping.
        """
        # TODO: Change return type to bool ?

        ctx.api.note("Running _check_stream_compatibility", ctx.context)

        if lhs_output.fullname == rhs_input.fullname:
            print(f"\tStream types match: {lhs_output.name} (identical names)")
            return rhs_type

        if rhs_input.fullname == 'typing.Any':
            print("\tStream types match: rhs_input is Any")
            return rhs_type

        lhs_out_inst = Instance(lhs_output, [])
        rhs_in_inst = Instance(rhs_input, [])
        if is_subtype(lhs_out_inst, rhs_in_inst):
            print(f"\tStream types match: {lhs_output.name} is subtype of {rhs_input.name}")

            return rhs_type

        # Compare the TypedDict structures
        if lhs_output.typeddict_type is None or rhs_input.typeddict_type is None:
            print(f"\tOne of the types is not a TypedDict: {lhs_output.name}, {rhs_input.name}")
            print(f"\tleft:{lhs_output}")
            print(f"\tright:{rhs_input}")
            ctx.api.fail(
                "Stream mismatch: Cannot compare non-TypedDict types.",
                ctx.context
            )
            return ctx.default_return_type
        
        rhs_map = dict(zip(rhs_type.type.type_vars, rhs_type.args))
        print(f"\tExpanding lhs_output and rhs_input with rhs_type args: {rhs_map}")
        print(f"\t-> {rhs_type.type.type_vars} mapped to {rhs_type.args}")
        
        for k, type_l in lhs_output.typeddict_type.items.items():
            type_r = rhs_input.typeddict_type.items.get(k)
            if type_r == type_l:
                continue
            expected_type = expand_type(type_r, rhs_map)
            if is_subtype(type_l, expected_type):
                print("\tStream types match")
                continue
            print(f"\tStream types mismatch : {type_r} ({type(type_r)})")
            ctx.api.fail(
                f"Stream mismatch: expected key '{k}' of type '{type_l}' "+
                f"but got type '{type_r}' from "+
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
            print("\tOutput/Input attribute is a TypeInfo.")
            return node
        
        # CASE B: It is a Type Alias
        if isinstance(node, TypeAlias):
            print("\tOutput/Input attribute is a TypeAlias.")
            print(f"{node = }")

            return None
        
        # CASE C: It is a Decorator
        if isinstance(node, Decorator):
            print("\tOutput/Input attribute is a Decorator.")

            if not isinstance(node.type, CallableType):
                print(f"Decorator type is not a CallableType : {type(node.type)}")
                return None
            
            print(f"Decorator type is CallableType: {node.type}")
            ret_type = get_proper_type(node.type.ret_type)
            print(f"\tRet_type is {ret_type}")
            if not isinstance(ret_type, TypeType):
                print("\tOutput/Input attribute does not reference a class")
                return None
            
            item_type = get_proper_type(ret_type.item)
            print(f"Decorator return type is TypeType: {ret_type.item} ({item_type})")
            print(type(item_type)) # mypy.types.TypedDictType

            if isinstance(item_type, Instance):
                return item_type.type
            elif isinstance(item_type, TypedDictType):
                return item_type.fallback.type
            else:
                print("Stream mismatch: Output/Input attribute does not reference a class.")
                return None

        # CASE D: It is a variable assignment
        # class Hello(...):
        #     Output = HelloMsg
        if not isinstance(node, Var):
            print("\tOutput/Input attribute is not of type 'Type[...]'.")
            print(f"{type(node) = }\n{node = }")
            return None
        
        # Unwrap the variable's type
        # The type of the variable 'Output' is 'Type[HelloMsg]'
        var_type = get_proper_type(node.type)
        
        # SUB-CASE 1: It's a TypeType (e.g. Output: Type[HelloMsg] = ...)
        if isinstance(var_type, TypeType):
            item_type = get_proper_type(var_type.item)
            if isinstance(item_type, Instance):
                return item_type.type
            else:
                print("\tOutput/Input attribute does not reference a class.")
                return None

        # SUB-CASE 2: It's a Callable (e.g. Output = HelloMsg)
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
        
        # SUB-CASE 3: Legacy Instance check (fallback)
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
    print(f"StreamPlugin loaded for mypy version {version} and python version {sys.version}")
    return StreamPlugin