from collections.abc import Iterator

import logicsponge.core as ls


class Hello(ls.SourceTerm):
    def generate(self) -> Iterator[ls.DataItem]:
        incomplete_message = "Hello"
        out = ls.DataItem({"message": incomplete_message})
        yield out


class World(ls.FunctionTerm):
    def f(self, item: ls.DataItem) -> ls.DataItem:
        incomplete_message = item["message"]
        complete_message = incomplete_message + " World!"
        out = {"message": complete_message}
        return ls.DataItem(out)


def main() -> None:
    """Run a simple Hello World circuit."""

    sponge = Hello() * World() * ls.Print() * ls.Stop()

    sponge.start()

if __name__ == "__main__":
    main()