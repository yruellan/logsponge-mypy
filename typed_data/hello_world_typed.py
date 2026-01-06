from collections.abc import Iterator
from typing import cast

from type import TypedDataItem, TypedSourceTerm

import logicsponge.core as ls

T1 = ls.DataItem
T2 = TypedDataItem

class Hello(TypedSourceTerm):
    def generate(self) -> Iterator[T2]:
        incomplete_message = "Hello"
        out = T2({"message": incomplete_message})
        yield out


class World(ls.FunctionTerm):
    def f(self, di: T1) -> T1 | None:
        typed_di = cast(T2, di)
        incomplete_message = typed_di["message"]
        complete_message = incomplete_message + " World!"
        out = {"message": complete_message}
        return T2(out)

def main() -> None:
    """Run a simple Hello World circuit."""

    sponge = Hello() * World() * ls.Print() * ls.Stop()

    sponge.start()

if __name__ == "__main__":
    main()