from typing import TypedDict, Iterator, TYPE_CHECKING, Union, reveal_type
import logicsponge.core as ls

# 1. Define the Data Schemas
InputMsg = TypedDict('InputMsg', {"value": int})
ProcessedAMsg = TypedDict('ProcessedAMsg', {"a_val": str})
ProcessedBMsg = TypedDict('ProcessedBMsg', {"b_val": float})
FinalMsg = TypedDict('FinalMsg', {"final_val": str})
VoidMsg = TypedDict('VoidMsg', {})

# 2. Annotate the Classes
class InputSource(ls.SourceTerm):
    """Generates a stream of numbers."""
    Output = InputMsg
    def generate(self) -> Iterator[ls.DataItem]:
        """Generates a few data items."""
        for i in range(3):
            yield ls.DataItem({"value": i})

class ProcessorA(ls.FunctionTerm):
    """Processes the data in one way."""
    Input = InputMsg
    Output = ProcessedAMsg
    def f(self, di: ls.DataItem) -> ls.DataItem:
        """Processes the data item."""
        processed_val = f"Item-{di['value']}"
        print(f"ProcessorA created: {processed_val}")
        return ls.DataItem({"a_val": processed_val})

class ProcessorB(ls.FunctionTerm):
    """Processes the data in another way."""
    Input = InputMsg
    Output = ProcessedBMsg
    def f(self, di: ls.DataItem) -> ls.DataItem:
        """Processes the data item."""
        processed_val = float(di['value'] * 1.5)
        print(f"ProcessorB created: {processed_val}")
        return ls.DataItem({"b_val": processed_val})

class ProcessorMerge(ls.FunctionTerm):
    """Merges outputs from ProcessorA and ProcessorB."""
    Input = Union[ProcessedAMsg, ProcessedBMsg]
    Output = FinalMsg
    def f(self, di: ls.DataItem) -> ls.DataItem:
        """Merges the data items."""
        if "a_val" in di:
            final_val = f"Merged-{di['a_val']}"
        elif "b_val" in di:
            final_val = f"Merged-{di['b_val']}"
        else:
            final_val = "Merged-Unknown"
        print(f"ProcessorMerge created: {final_val}")
        return ls.DataItem({"final_val": final_val})

# 3. Define the Main Function
def main() -> None:
    """Defines a circuit for testing MergeToSingleStream."""

    # A source is split into two parallel processors, and their outputs are then merged back
    # into a single stream for the collector.
    circuit = (
        InputSource()
        * (ProcessorA() | ProcessorB())
        * ls.MergeToSingleStream(combine=True)
        * ls.Print()
        * ProcessorMerge()
        * ls.Stop()
    )

    reveal_type(circuit)  
    # Revealed type is 'logicsponge.core.logicsponge.CircuitTerm'

    if not TYPE_CHECKING:
        # The MergeCollector would receive 6 items in total (3 from A, 3 from B).
        circuit.start()

# 4. Run Main
if __name__ == "__main__":
    main()
