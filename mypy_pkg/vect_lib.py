from mypy.plugin import AnalyzeTypeContext
from mypy.types import AnyType, TypeOfAny, TupleType, Type

def analyze_vector(ctx: AnalyzeTypeContext) -> Type:
    print(f"[plugin] analyze_vector called with {ctx.type = } {ctx.context = }")
    try:
        # Trace what mypy parsed for args
        raw_args = getattr(ctx.type, "args", [])
        # Convert the type argument ASTs into mypy Type objects
        arg_types = [ctx.api.analyze_type(t) for t in raw_args]
        # print(f"[plugin] Vector args count: {len(raw_args)} -> {arg_types}")

        # If no args provided, treat as tuple[Any, ...] to be permissive
        if not arg_types:
            any_t = AnyType(TypeOfAny.unannotated)
            fallback = ctx.api.named_type("builtins.tuple", [any_t])
            return TupleType(items=[any_t], fallback=fallback)

        # Map Vector[T1, T2, ...] -> Tuple[T1, T2, ...]
        any_t = AnyType(TypeOfAny.unannotated)
        fallback = ctx.api.named_type("builtins.tuple", [any_t])
        return TupleType(items=arg_types, fallback=fallback)
    except Exception as ex:
        # If anything goes wrong, fall back to Any to avoid spurious errors
        print(f"[plugin] analyze_vector failed: {ex}")
        return AnyType(TypeOfAny.special_form)