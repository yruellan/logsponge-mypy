from typing import Optional

from mypy.nodes import (
    SymbolTableNode,
    TypeInfo,
    FuncDef,
    Var,
    GDEF,
)
from mypy.plugin import ClassDefContext
from mypy.types import (
    Type,
    Instance,
    NoneType,
    UnboundType,
    # get_proper_type,
)

_METADATA_KEY = "logicsponge_source_term"


def source_term_hook(ctx: ClassDefContext) -> None:
    api = ctx.api
    info: TypeInfo = ctx.cls.info

    

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

    ret_type: Type = generate_def.type.ret_type

    # ------------------------------------------------------------------
    # 2. Defer if unresolved
    # ------------------------------------------------------------------
    if isinstance(ret_type, UnboundType):
        if api.is_final_iteration:
            api.fail(
                "generate() return type could not be resolved; "
                "expected Iterator[DataItem[T]]",
                generate_def,
            )
            return

        api.defer()
        return

    # ------------------------------------------------------------------
    # 3. Validate Iterator[DataItem[T]]
    # ------------------------------------------------------------------
    if not isinstance(ret_type, Instance):
        api.fail(
            "generate() must return Iterator[DataItem[T]]",
            generate_def,
        )
        return

    if ret_type.type.fullname != "typing.Iterator":
        api.fail(
            "generate() must return Iterator[DataItem[T]]",
            generate_def,
        )
        return

    item_type: Type = ret_type.args[0]

    if isinstance(item_type, UnboundType):
        if api.is_final_iteration:
            api.fail(
                "generate() yield type could not be resolved",
                generate_def,
            )
            return

        api.defer()
        return

    if not isinstance(item_type, Instance):
        api.fail(
            "generate() must yield DataItem[T]",
            generate_def,
        )
        return

    if item_type.type.fullname != "logicsponge.core.DataItem":
        api.fail(
            "generate() must yield DataItem[T]",
            generate_def,
        )
        return

    output_type: Type = item_type.args[0]

    # ------------------------------------------------------------------
    # 4. Resolve Term
    # ------------------------------------------------------------------
    term_sym = api.lookup_fully_qualified("logicsponge.core.Term")
    if term_sym is None or not isinstance(term_sym.node, TypeInfo):
        api.fail(
            "Could not resolve logicsponge.core.Term",
            ctx.cls,
        )
        return

    term_info: TypeInfo = term_sym.node

    # ------------------------------------------------------------------
    # 5. Rewrite base classes: Term[None, T]
    # ------------------------------------------------------------------
    specialized_term = Instance(
        term_info,
        [NoneType(), output_type],
    )

    info.bases = [specialized_term]
    info.mro = []
    info.calculate_mro()

    # ------------------------------------------------------------------
    # 6. Optional: expose inferred output type (debugging / introspection)
    # ------------------------------------------------------------------
    output_var = Var("_ls_output_type", output_type)
    output_var.info = info
    info.names["_ls_output_type"] = SymbolTableNode(GDEF, output_var)

    # ------------------------------------------------------------------
    # 7. Mark as processed
    # ------------------------------------------------------------------
    meta[_METADATA_KEY] = True