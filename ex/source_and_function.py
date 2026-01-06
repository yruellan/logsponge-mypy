"""Example for a simple source and subsequent compute Term."""

import time
from collections.abc import Iterator
from typing import TypedDict

import logicsponge.core as ls


class SourceState(TypedDict):
    time: float  # pint.Quantity
    cells: float  # pint.Quantity


class Source(ls.SourceTerm):
    """A simple source that provides time and cells at the time."""

    def __init__(self, *args, **kwargs) -> None:
        """Create a new Source and set its initial state."""
        super().__init__(*args, **kwargs)
        self.state = {
            "time": 0,  # * u.min,
            "cells": 10,  # / u.mL,
        }

    def generate(self) -> Iterator[ls.DataItem]:
        """Generate DataItems and terminate after 10 items."""
        for _ in range(10):
            # time to measure...
            time.sleep(0.1)

            # send measurement
            out = ls.DataItem(
                {
                    "time": self.state["time"],
                    "cells": self.state["cells"],
                }
            )
            yield out

            # update state
            self.state["time"] += 5  # * u.min
            self.state["cells"] *= 1.1


class Compute(ls.FunctionTerm):
    """Simple compute that duplicates the cells."""

    def f(self, di: ls.DataItem) -> ls.DataItem:
        """The function called on all new data items."""
        return ls.DataItem({"time": di["time"], "cells": di["cells"] * 2})


circuit = Source() * Compute() * ls.Print()
circuit.start()
circuit.join()
