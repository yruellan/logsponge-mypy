# My MyPy plugin

Documentation: https://mypy.readthedocs.io/en/stable/extending_mypy.html

This plugin is registered in `mypy.ini` so that mypy loads it when checking the code.

## Overview

A mypy plugin is a Python class inheriting from `mypy.plugin.Plugin`. It exposes **hook methods** that intercept type checking at specific points:

1. **Type Analysis** — customize how type annotations are interpreted.
2. **Function/Method Calls** — adjust return types or signatures based on arguments.
3. **Special Methods** — handle operator overloading and magic methods.

Each hook method returns a callback (or `None` to skip) that receives a context object with type information and mypy's API helpers.

---

## Plugin Hooks

### 1. `get_type_analyze_hook(fullname: str)`

**Purpose:** Customize behavior when mypy encounters an annotation like `MyType[...]`.

**Use Cases:**
- Implement non-standard generic syntax (e.g., variadic generics like `Vector[int, int, int]`).
- Map custom type syntax to built-in types.
- Validate or transform type annotations at analysis time.

**Signature:**
```python
def get_type_analyze_hook(self, fullname: str) -> Optional[Callable[[AnalyzeTypeContext], Type]]:
```

**Context Object (`AnalyzeTypeContext`):**
- `ctx.type` — the AST node representing the type annotation.
- `ctx.api` — mypy's API with methods like:
  - `ctx.api.analyze_type(node)` — convert an AST node to a mypy Type.
  - `ctx.api.named_type(fullname, args)` — create an Instance type.

**How to Write It:**

```python
def get_type_analyze_hook(self, fullname: str):
    if fullname == "lib.Vector":
        def analyze_vector(ctx: AnalyzeTypeContext):
            try:
                # Extract argument ASTs from the type annotation
                raw_args = getattr(ctx.type, "args", [])
                
                # Convert each argument to a mypy Type
                arg_types = [ctx.api.analyze_type(arg) for arg in raw_args]
                
                # Build a TupleType to represent Vector[T1, T2, ...]
                fallback = ctx.api.named_type("builtins.tuple", [AnyType(TypeOfAny.unannotated)])
                return TupleType(items=arg_types, fallback=fallback)
            except Exception:
                # Gracefully fall back to Any if parsing fails
                return AnyType(TypeOfAny.special_form)
        
        return analyze_vector
    
    return None
```

**Result:** `a: Vector[int, str]` is type-checked as `a: tuple[int, str]`.

---

### 2. `get_function_hook(fullname: str)`

**Purpose:** Adjust the **return type** of a function call based on its arguments.

**Use Cases:**
- Infer complex return types (e.g., `make_pair(1, "x")` returns `tuple[int, str]`).
- Conditionally change return type based on argument types or values.
- Implement protocol-like behaviors for dynamic libraries.

**Signature:**
```python
def get_function_hook(self, fullname: str) -> Optional[Callable[[FunctionContext], Type]]:
```

**Context Object (`FunctionContext`):**
- `ctx.arg_types` — list of lists of argument types (grouped by argument).
- `ctx.args` — the argument AST nodes.
- `ctx.default_return_type` — the inferred return type from the function's annotation.
- `ctx.api` — mypy's API helpers.

**How to Write It:**

```python
def get_function_hook(self, fullname: str):
    if fullname == "mylib.make_pair":
        def make_pair_hook(ctx: FunctionContext):
            # Flatten arg types and get the first two
            arg_types = [t for arg in ctx.arg_types for t in arg]
            
            if len(arg_types) >= 2:
                t0, t1 = arg_types[0], arg_types[1]
                # Build tuple[t0, t1]
                fallback = ctx.api.named_type("builtins.tuple", [AnyType(TypeOfAny.unannotated)])
                return TupleType(items=[t0, t1], fallback=fallback)
            
            # Fall back to default if we can't determine types
            return ctx.default_return_type
        
        return make_pair_hook
    
    return None
```

**Result:** `x = make_pair(1, "hi")` infers `x: tuple[int, str]` instead of the declared return type.

---

### 3. `get_function_signature_hook(fullname: str)`

**Purpose:** Modify the **signature** of a function (parameters, return type, argument kinds).

**Use Cases:**
- Reshape variadic functions into fixed signatures for better type checking.
- Add or remove parameters dynamically.
- Mark arguments as keyword-only or positional-only based on context.

**Signature:**
```python
def get_function_signature_hook(self, fullname: str) -> Optional[Callable[[FunctionSigContext], CallableType]]:
```

**Context Object (`FunctionSigContext`):**
- `ctx.arg_types` — current argument types.
- `ctx.arg_names` — parameter names.
- `ctx.arg_kinds` — parameter kinds (POSITIONAL_ONLY, POSITIONAL_OR_KEYWORD, VAR_POSITIONAL, KEYWORD_ONLY, VAR_KEYWORD).
- `ctx.default_return_type` — declared return type.
- `ctx.api` — mypy's API.

**How to Write It:**

```python
def get_function_signature_hook(self, fullname: str):
    if fullname == "mylib.varargs_to_fixed":
        def varargs_hook(ctx: FunctionSigContext):
            # Create a fixed signature: (int, int) -> list[int]
            any_t = AnyType(TypeOfAny.unannotated)
            int_t = ctx.api.named_type("builtins.int", [])
            list_t = ctx.api.named_type("builtins.list", [int_t])
            
            # Build a CallableType with two int parameters
            # (Details depend on mypy version; use ctx.api helpers when available)
            return ctx.api.named_callable(
                "mylib.varargs_to_fixed",
                [int_t, int_t],
                list_t
            )
        
        return varargs_hook
    
    return None
```

**Result:** `varargs_to_fixed(1, 2, 3)` type-checks as if the signature were `(int, int) -> list[int]`.

---

### 4. `get_method_hook(fullname: str)`

**Purpose:** Like `get_function_hook`, but for **methods** bound to a class instance.

**Use Cases:**
- Customize method return types based on the receiver's type or generic arguments.
- Implement fluent APIs where methods return `self` or modified instances.

**Signature:**
```python
def get_method_hook(self, fullname: str) -> Optional[Callable[[MethodContext], Type]]:
```

**Context Object (`MethodContext`):**
- `ctx.type` — the type of the object instance (e.g., `Instance` of the class).
- `ctx.arg_types` — types of method arguments (excluding `self`).
- `ctx.default_return_type` — inferred return type.
- `ctx.api` — mypy's API.

**How to Write It:**

```python
def get_method_hook(self, fullname: str):
    if fullname == "mylib.SomeClass.compute":
        def compute_hook(ctx: MethodContext):
            # Inspect the receiver type
            self_type = ctx.type
            
            # If SomeClass is generic, we can use self_type.type.type_arguments()
            # to infer the return type based on type parameters.
            
            # Example: if SomeClass[T] has compute() -> T, we'd return T:
            # args = self_type.type.type_arguments()
            # if args: return args[0]
            
            return ctx.default_return_type
        
        return compute_hook
    
    return None
```

**Result:** `sc.compute(x)` returns a type inferred from `sc`'s generic type arguments or state.

---

### 5. `get_method_signature_hook(fullname: str)`

**Purpose:** Modify the **signature** of a method (similar to `get_function_signature_hook`).

**Use Cases:**
- Customize operator methods like `__add__`, `__mul__`, `__getitem__`.
- Enforce special typing rules for magic methods.

**Signature:**
```python
def get_method_signature_hook(self, fullname: str) -> Optional[Callable[[FunctionSigContext], CallableType]]:
```

**Context Object:** Same as `FunctionSigContext` (inherited from the base signature context).

**How to Write It:**

```python
def get_method_signature_hook(self, fullname: str):
    if fullname == "mylib.SomeClass.__add__":
        def add_hook(ctx: FunctionSigContext):
            # Define: __add__(self, other: int) -> str
            int_t = ctx.api.named_type("builtins.int", [])
            str_t = ctx.api.named_type("builtins.str", [])
            
            # Return a CallableType with the custom signature
            # (Exact construction depends on mypy version)
            return ctx.api.named_callable(
                "mylib.SomeClass.__add__",
                [int_t],  # just the 'other' param, self is implicit
                str_t
            )
        
        return add_hook
    
    return None
```

**Result:** `sc + 10` is type-checked expecting `__add__(int) -> str`.

---

## Integration & Testing

### Register the Plugin

In `mypy.ini`:
```ini
[mypy]
plugins = mypy_pkg.plugin
```

### Test the Plugin

Create a test file (e.g., `typed_data/hw4.py`):
```python
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from lib import Vector
    import mylib

# Triggers get_type_analyze_hook("lib.Vector")
a: "Vector[int, int]"

# Triggers get_function_hook("mylib.make_pair")
if TYPE_CHECKING:
    result = mylib.make_pair(1, "x")
```

Run mypy:
```bash
mypy typed_data/hw4.py
```

Watch the terminal for plugin debug output and mypy type-checking results.

---

## Tips & Caveats

1. **Always fall back gracefully:** If your hook cannot determine a type, return `ctx.default_return_type` or `AnyType(TypeOfAny.special_form)`.

2. **Use `ctx.api` helpers:** They handle mypy's internal APIs correctly:
   - `ctx.api.named_type(fullname, args)` — create an `Instance` type.
   - `ctx.api.analyze_type(node)` — convert an AST to a Type.

3. **Match fully-qualified names:** Always use the full module path (e.g., `"lib.Vector"`, not just `"Vector"`).

4. **Test incrementally:** Start by returning `Any` to ensure the hook is triggered, then refine the type inference.

5. **Version compatibility:** Mypy's plugin API changes between versions. Test your plugin against your target mypy version.