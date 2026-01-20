from typing import TypedDict, Iterator, Any, TYPE_CHECKING
import logicsponge.core as ls

# 1. Define the Data Schemas
class HelloMsg(TypedDict):
    message: str
class HelloMsg2(TypedDict):
    message: str

HelloMsg3 = TypedDict('HelloMsg3', {'message': str})

class WorldMsg(TypedDict):
    message: str

VoidMsg = TypedDict('VoidMsg', {})

# 2. Annotate the Classes
class Hello(ls.SourceTerm):
    # The plugin will read this attribute
    Output = HelloMsg

    def generate(self) -> Iterator[ls.DataItem]:
        # Implementation remains the same
        out = ls.DataItem({"message": "Hello"})
        yield out

def global_f(self: Any, di: ls.DataItem) -> ls.DataItem:
    # Implementation remains the same
    return ls.DataItem({"message": di["message"] + " World!"})

class World1(ls.FunctionTerm):
    Input = HelloMsg
    Output = WorldMsg
    f = global_f
class World2(ls.FunctionTerm):
    Input = HelloMsg2
    Output = WorldMsg
    f = global_f
class World3(ls.FunctionTerm):
    Input = HelloMsg3
    Output = WorldMsg
    f = global_f
class World4(ls.FunctionTerm):
    Input = TypedDict('Input', {'message': str})
    Output = VoidMsg
    f = global_f

class Analyse(ls.FunctionTerm):
    Input = WorldMsg
    Output = VoidMsg

    def f(self, di: ls.DataItem) -> ls.DataItem:
        print(f"Analyse: {list(di.items())}")
        return ls.DataItem({})

class SinkTerm(ls.FunctionTerm):
    Input = Any
    Output = VoidMsg

    def f(self, di: ls.DataItem) -> ls.DataItem:
        return ls.DataItem({})

# 3. Define the Main Function
def main() -> None:

    s = [
        Hello() * World1(),
        Hello() * World2(),
        Hello() * World3(),
        Hello() * World4(),
        Hello() * SinkTerm(),
        Hello() * ls.Stop(),
    ]
    
    # sponge = (
    #     Hello()                 # message : str
    #     # * World1()              # message : str           
    #     * ls.Print()            # identity
    #     * Analyse()             # message : str
    #     * ls.Stop()             # None
    # )

    if not TYPE_CHECKING:
        print(len(s))
        # sponge.start()

if __name__ == "__main__":
    main()