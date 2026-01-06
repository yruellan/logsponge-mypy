# from mypy.nodes import ClassDef
from mypy.plugin import ClassDefContext


def function_term_hook(ctx: ClassDefContext) -> None:
    cls = ctx.cls

    for stmt in cls.defs.body:
        if getattr(stmt, "name", None) == "f":
            arg_type = stmt.type.arg_types[1][0]  # DataItem[T]
            ret_type = stmt.type.ret_type         # DataItem[U]

            input_t = extract_dataitem_inner_type(arg_type)
            output_t = extract_dataitem_inner_type(ret_type)

            # Attach: Term[input_t, output_t]
