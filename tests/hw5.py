from typing import TypedDict, Iterator, Any, TYPE_CHECKING
import logicsponge.core as ls

# 1. Define the Data Schemas
InputMsg = TypedDict('InputMsg', {"data": int})
OutputMsgA = TypedDict('OutputMsgA', {"a_processed": bool})
OutputMsgB = TypedDict('OutputMsgB', {"b_processed": bool})
VoidMsg = TypedDict('VoidMsg', {})

# 2. Annotate the Classes
class TestSource(ls.SourceTerm):
    """A simple source for the test."""
    Output = InputMsg

    def generate(self) -> Iterator[ls.DataItem]:
        """Generates a single data item."""
        yield ls.DataItem({"data": 10})

class ProcessorA(ls.FunctionTerm):
    """First parallel processor."""
    Input = InputMsg
    Output = OutputMsgA

    def f(self, di: ls.DataItem) -> ls.DataItem:
        """Processes the data item."""
        print(f"ProcessorA received: {di['data']}")
        return ls.DataItem({"a_processed": True})

class ProcessorB(ls.FunctionTerm):
    """Second parallel processor."""
    Input = InputMsg
    Output = OutputMsgB

    def f(self, di: ls.DataItem) -> ls.DataItem:
        """Processes the data item."""
        print(f"ProcessorB received: {di['data']}")
        return ls.DataItem({"b_processed": True})

class SinkA(ls.FunctionTerm):
    """Sink for branch A."""
    Input = OutputMsgA
    Output = VoidMsg
    def f(self, di: ls.DataItem) -> ls.DataItem:
        return ls.DataItem({})

class SinkB(ls.FunctionTerm):
    """Sink for branch B."""
    Input = OutputMsgB
    Output = VoidMsg
    def f(self, di: ls.DataItem) -> ls.DataItem:
        return ls.DataItem({})


# 3. Define the Main Function
def main() -> None:
    """Defines the circuit for testing the '|' operator."""

    # Data from TestSource is sent to both ProcessorA and ProcessorB
    parallel_circuit = TestSource() * (ProcessorA() * SinkA() | ProcessorB() * SinkB())

    if not TYPE_CHECKING:
        # The main purpose is static analysis, but we can show the setup.
        parallel_circuit.start()

# 4. Run Main
if __name__ == "__main__":
    main()
