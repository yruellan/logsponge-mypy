"""A simple counter."""

import time
from collections.abc import Iterator

import logicsponge.core as ls
from logicsponge.core.logicsponge import Dump


class Source(ls.SourceTerm):
    """A simple source."""

    def generate(self) -> Iterator[ls.DataItem]:
        """Generate DataItems with incrementing count."""
        self.state["count"] = 0
        for _ in range(5):
            out = ls.DataItem({"data": self.state["count"]})
            print("\nSource: send", out)
            yield out
            self.state["count"] += 1
            time.sleep(2)


class Sink(ls.FunctionTerm):
    """A simple sink."""

    def f(self, item: ls.DataItem) -> ls.DataItem:
        """Call on new data."""
        time.sleep(1)
        print("Sink: received", item)
        return item


class Counter(ls.FunctionTerm):
    """The counter."""

    only_even: bool

    def __init__(self, *args, only_even: bool, **kwargs) -> None:
        """Create a Counter."""
        super().__init__(*args, only_even, **kwargs)
        self.state["counter"] = 0
        self.only_even = only_even

    def f(self, item: ls.DataItem) -> ls.DataItem:
        """Call on new data."""
        if item["data"] % 2 == 0 or not self.only_even:
            self.state["counter"] += 1
        print("Counter: ", self.state["counter"])

        new_item = {"num": self.state["counter"], **item}
        return ls.DataItem(new_item)


circuit = Source() * (Dump(name="source_dump") | (Sink() * Dump(name="sink_dump")) | Counter(only_even=True))
circuit.start()
