from collections.abc import Iterator

import logicsponge.core as ls


class Hello(ls.SourceTerm):
    # def generate(self) -> Iterator[ls.DataItem]:
    def generate(self) -> Iterator[ls.DataItem]:
        incomplete_message = "Hello"
        out = ls.DataItem({"message": incomplete_message})

        yield out


class World(ls.FunctionTerm):
    def f(self, di: ls.DataItem) -> ls.DataItem:
        incomplete_message = di["message"]
        complete_message = incomplete_message + " World!"
        out = {"message": complete_message}
        return ls.DataItem(out)


# Hello : () → DataItem[T]
# World : DataItem[T] → DataItem[U]
# --------------------------------
# Hello * World : () → DataItem[U]


def main() -> None:
    """Run a simple Hello World circuit."""

    sponge = (
        Hello()                 # message : str
        * World()               # message : str           
        * ls.Print()            # identity
        * ls.Stop()             # None
    )

    sponge.start()

if __name__ == "__main__":
    main()