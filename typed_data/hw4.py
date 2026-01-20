from typing import TypedDict, Iterator, Any, TYPE_CHECKING, TypeVar, Generic
import logicsponge.core as ls

# 1. Define the Data Schemas
AnyX = TypedDict('AnyX', {'x': Any})
StrX = TypedDict('StrX', {'x': str})
IntX = TypedDict('IntX', {'x': int})

AnyY = TypedDict('AnyY', {'y': Any})
StrY = TypedDict('StrY', {'y': str})
IntY = TypedDict('IntY', {'y': int})

T = TypeVar('T')

# class GenX[T](TypedDict):
#     x: T
# class GenY[T](TypedDict):
#     y: T
class GenX(TypedDict, Generic[T]):
    x: T
class GenY(TypedDict, Generic[T]):
    y: T

# 2. Annotate the Classes
class CreateStrX(ls.SourceTerm):
    Output = StrX

    def generate(self) -> Iterator[ls.DataItem]:
        yield ls.DataItem({"x": "Hello"})
class CreateIntX(ls.SourceTerm):
    Output = IntX

    def generate(self) -> Iterator[ls.DataItem]:
        yield ls.DataItem({"x": 42})

class XtoY_Str(ls.FunctionTerm):
    Input = StrX
    Output = StrY
    def f(self, di: ls.DataItem) -> ls.DataItem:
        return ls.DataItem({"y": di["x"] + " World!"})
class XtoY_Int(ls.FunctionTerm):
    Input = IntX
    Output = IntY
    def f(self, di: ls.DataItem) -> ls.DataItem:
        return ls.DataItem({"y": di["x"] + 1})
class XtoY_Any(ls.FunctionTerm):
    Input = AnyX
    Output = AnyY
    def f(self, di: ls.DataItem) -> ls.DataItem:
        return ls.DataItem({"y": di["x"]})

class XtoY_Gen[T](ls.FunctionTerm):
    # Input = GenX[T]
    # Output = GenY[T]
    @property
    def Input(self) -> type[GenX[T]]:
        return GenX[T]
    @property
    def Output(self) -> type[GenY[T]]:
        return GenY[T]

    def f(self, di: ls.DataItem) -> ls.DataItem:
        return ls.DataItem({"y": di["x"]})
    
class PrintIntY(ls.FunctionTerm):
    Input = IntY
    def f(self, di: ls.DataItem) -> ls.DataItem:
        print(f"PrintIntY: {di['y']}")
        return di


# 3. Define the Main Function
def main() -> None:

    s = [
        # CreateStrX() * XtoY_Str() * ls.Print() * ls.Stop(),
        # CreateIntX() * XtoY_Int() * ls.Print() * ls.Stop(),
        # CreateStrX() * XtoY_Gen() * ls.Print() * ls.Stop(),
        # CreateIntX() * XtoY_Gen() * ls.Print() * ls.Stop(),
        CreateIntX() * XtoY_Gen() * PrintIntY() * ls.Stop(),  # Should be type error
        CreateIntX() * XtoY_Gen[int]() * PrintIntY() * ls.Stop(),  # Should be type error
    ]
    
    # sponge = (
    #     Hello()                 # message : str
    #     # * World1()              # message : str           
    #     * ls.Print()            # identity
    #     * Analyse()             # message : str
    #     * ls.Stop()             # None
    # )

    if not TYPE_CHECKING:
        print(GenX)
        for sp in s:
            sp.start()

if __name__ == "__main__":
    main()