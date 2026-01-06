from mypy.plugin import MethodContext
from mypy.types import Type

def term_mul_hook(ctx: MethodContext) -> Type:
    left_out = get_term_output(ctx.type)
    right_in = get_term_input(ctx.arg_types[0][0])

    if not ctx.api.check_subtype(left_out, right_in):
        ctx.api.fail(
            f"Incompatible composition: {left_out} -> {right_in}",
            ctx.context,
        )

    return composed_term_type(ctx)
