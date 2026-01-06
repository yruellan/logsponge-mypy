from collections.abc import Iterator

import logicsponge.core as ls

key1: str = "msg"

class Source(ls.SourceTerm):
    def generate(self) -> Iterator[ls.DataItem]:
        val: int = 42
        out = ls.DataItem({key1: val})
        yield out


class F(ls.FunctionTerm):
    def f(self, di: ls.DataItem) -> ls.DataItem:
        new_value: int = di[key1] + 1
        return ls.DataItem({key1: new_value})
    
# class G(ls.FunctionTerm):
#     def f(self, di: ls.DataItem) -> ls.DataItem:
#         new_value: str = f"{di[key1]}{di[key1]}"
#         return ls.DataItem({key1: new_value})
    
# class To_str(ls.FunctionTerm):
#     def f(self, di: ls.DataItem) -> ls.DataItem:
#         new_value: str = str(di[key1])
#         return ls.DataItem({key1: new_value})
    
# class To_int(ls.FunctionTerm):
#     def f(self, di: ls.DataItem) -> ls.DataItem:
#         new_value: int = int(di[key1])
#         return ls.DataItem({key1: new_value})

# Source : None -> int
# F      : int  -> int
# G      : str  -> str
# To_str : int  -> str
# To_int : str  -> int
# Print  : 'a  -> 'a
# Stop   : 'a  -> None

# def main() -> None:
#     """Run a simple Hello World circuit."""

#     # Simple int pipeline
s1 = Source() * F() * ls.Print() * ls.Stop()

#     # More complex int pipeline
#     s2 = Source() * F() * F() * F() * ls.Print() * ls.Stop()

#     # Mixed type pipeline
#     s3 = Source() * To_str() * G() * To_int() * ls.Print() * ls.Stop()

#     # More complex pipeline
#     s4 = Source() * F() * To_str() * G() * To_int() * F() * ls.Print() * ls.Stop()

#     s1.start() # = 43
#     s2.start() # = 45
#     s3.start() # = 4242
#     s4.start() # = 4344

#     # a: str = 1.0 + 2
#     # print(f"{a = }")

# if __name__ == "__main__":
#     main()