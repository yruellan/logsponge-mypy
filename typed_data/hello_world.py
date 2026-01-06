from collections.abc import Iterator

from type import TypedDataItem

import logicsponge.core as ls

T1 = ls.DataItem
T2 = TypedDataItem

class Hello(ls.SourceTerm):
    def generate(self) -> Iterator[T1]:
        incomplete_message = "Hello"
        out = T1({"message": incomplete_message})
        yield out


class World(ls.FunctionTerm):
    def f(self, di: T1) -> T1:
        incomplete_message = di["message"]
        complete_message = incomplete_message + " World!"
        out = {"message": complete_message}
        return T1(out)

def main() -> None:
    """Run a simple Hello World circuit."""

    sponge = Hello() * World() * ls.Print() * ls.Stop()

    sponge.start()

if __name__ == "__main__":
    main()