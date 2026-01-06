from typing import List, Callable, TypedDict

# mypy plugins

def get_fst[T](pair: List[T]) -> T:
    """Get the first element of a pair (2-element list)."""
    return pair[0]

def compose[T,U,V](f: Callable[[T], U], g: Callable[[U], V]) -> Callable[[T], V]:
    """Compose two functions."""
    return lambda x: g(f(x))

class dict1(TypedDict):
    a: int
    b: str
    c: List[int]

def dict_double_a(d: dict1) -> dict1:
    """Double the value of 'a' in the dictionary."""
    return {
        "a": d["a"] * 2,
        "b": d["b"],
        "c": d["c"]
    }

def dict_stringify_a(d: dict1) -> TypedDict['dict2', {'a': str, 'b': str, 'c': List[int]}]:
    """Stringify the value of 'a' in the dictionary."""
    return {
        "a": str(d["a"]),
        "b": d["b"],
        "c": d["c"]
    }

my_dict: dict1 = {
    "a" : 1,
    "b" : "abc",
    "c" : [1,2,3]
}

a = my_dict["a"]
b = my_dict["b"]
c = my_dict["c"]