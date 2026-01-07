from typing import Optional
import traceback

from mypy.nodes import (
    # ClassDef,
    SymbolTableNode,
    TypeInfo,
    FuncDef,
    Var,
    GDEF,
    Context,
)
from mypy.plugin import ClassDefContext, SemanticAnalyzerPluginInterface
from mypy.types import (
    Type,
    Instance,
    NoneType,
    CallableType,
    UnboundType,
    # get_proper_type,
)
# from mypy.subtypes import is_subtype

def resolve_unbound_type(api: SemanticAnalyzerPluginInterface, ctx: Context, typ: Type) -> Type:
    """Recursively resolve UnboundType to Instance."""

    if isinstance(typ, UnboundType):
        # For UnboundType, try to look up using fully qualified name
        # First try the name as-is (in case it's already fully qualified)
        try:
            type_info = api.lookup_fully_qualified_or_none(typ.name)
        except ValueError:
            # Name is not fully qualified, can't resolve
            print(f"Could not resolve UnboundType {typ.name} as fully qualified name ({typ = })")
            # api.fail(
            #     f"Could not resolve UnboundType: (1)\n {typ = } {typ.name = } (not fully qualified)", 
            #     ctx
            # )
            return typ  # Return as-is if can't resolve
        
        # If that fails, the type might be from a module context
        # In that case, we can't easily resolve it here, so return as-is
        if type_info is not None and isinstance(type_info.node, TypeInfo):
            # Recursively resolve type arguments
            resolved_args = [resolve_unbound_type(api, ctx, arg) for arg in (typ.args or [])]
            return Instance(type_info.node, resolved_args)
        else:
            print(f"Could not resolve UnboundType {typ.name}, returning as-is")
            return typ  # Return as-is if can't resolve
    elif isinstance(typ, Instance):
        # Recursively resolve type arguments of Instance
        resolved_args = [resolve_unbound_type(api, ctx, arg) for arg in typ.args]
        return Instance(typ.type, resolved_args)
    else:
        print(f"resolve_unbound_type: returning {typ = } as is ({type(typ) = })")
    return typ


def make_warning(func):
    def wrapper(ctx: ClassDefContext) -> None:
        try:
            func(ctx)
            return 
        except Exception as e:
            api = ctx.api
            tb_str = ''.join(traceback.format_exception(type(e), e, e.__traceback__))
            api.fail(f"[source_hook] Exception in source_term_hook:\n{tb_str}\n", ctx.cls)
            return None
    return wrapper

_METADATA_KEY = "logicsponge_source_term"

def source_term_hook(ctx: ClassDefContext) -> None:
    """
    Infer the output type of a SourceTerm subclass from:

        def generate(self) -> Iterator[DataItem[T]]

    and rewrite the class so that it behaves like:

        Term[None, T]
    """

    info: TypeInfo = ctx.cls.info
    api = ctx.api

    # ------------------------------------------------------------------
    # 0. Idempotency guard
    # ------------------------------------------------------------------
    meta = info.metadata.setdefault("logicsponge", {})
    if meta.get(_METADATA_KEY):
        return

    # ------------------------------------------------------------------
    # 1. Locate generate()
    # ------------------------------------------------------------------
    generate_def: Optional[FuncDef] = None

    for stmt in ctx.cls.defs.body:
        if isinstance(stmt, FuncDef) and stmt.name == "generate":
            generate_def = stmt
            break

    if generate_def is None:
        api.fail(
            "SourceTerm subclasses must define generate()",
            ctx.cls,
        )
        return

    if generate_def.type is None:
        api.fail(
            "generate() must have an explicit return type",
            generate_def,
        )
        return


    if not isinstance(generate_def.type, CallableType):
        api.fail(
            "generate() must be a callable with an explicit return type",
            generate_def,
        )
        return
    
    ret_type: Type = generate_def.type.ret_type
    print(f"LOG1 : {ret_type = }, {type(ret_type) = }")
    # ret_type = resolve_unbound_type(api, generate_def, ret_type)
    # print(f"LOG2 : {ret_type = }, {type(ret_type) = }")

    # ------------------------------------------------------------------
    # 2. Defer if unresolved
    # ------------------------------------------------------------------
    if isinstance(ret_type, UnboundType):
        if api.final_iteration:
            api.fail(
                "generate() return type could not be resolved; "
                "expected Iterator[DataItem[T]]",
                generate_def,
            )
            return

        api.defer()
        return

    # 2. Expect Iterator[DataItem[T]]
    if not isinstance(ret_type, Instance):
        api.fail(
            f"""generate() must return Iterator[DataItem[T]] (1)
            {type(ret_type) = }
            {ret_type = }\n""",
            generate_def,
        )
        return

    if ret_type.type.fullname != "typing.Iterator":
        api.fail(
            f"generate() must return Iterator[DataItem[T]] (2)\n{ret_type.type.fullname = }",
            generate_def,
        )
        return

    item_type: Type = ret_type.args[0]

    # 3. Expect DataItem[T]
    if not isinstance(item_type, Instance):
        api.fail(
            "generate() must yield DataItem[T] (1)",
            generate_def,
        )
        return

    if item_type.type.fullname != "logicsponge.core.DataItem":
        api.fail(
            "generate() must yield DataItem[T] (2)",
            generate_def,
        )
        return

    output_type: Type = item_type.args[0]

    # 4. Construct Term[None, T]
    term_info = api.lookup_fully_qualified("logicsponge.core.Term")
    if term_info is None or not isinstance(term_info.node, TypeInfo):
        api.fail(
            "Could not resolve logicsponge.core.Term",
            ctx.cls,
        )
        return

    term_typeinfo: TypeInfo = term_info.node

    none_type = NoneType()

    specialized_term = Instance(
        term_typeinfo,
        [none_type, output_type],
    )

    # 5. Inject Term[None, T] as a base class
    #
    # This is the key step: we *teach mypy* that this class
    # IS a Term[None, T]
    info.bases = [specialized_term]
    # info.mro = []  # Force recomputation
    # info.calculate_mro()
    # MRO will be recomputed automatically by mypy

    # 6. Optional: expose Output type as a class attribute for debugging
    output_var = Var("_ls_output_type", output_type)
    output_var.info = info
    info.names["_ls_output_type"] = SymbolTableNode(GDEF, output_var)


    print(f"[source_hook] Inferred SourceTerm output type: {output_type}\n")