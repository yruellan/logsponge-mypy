from typing import TypedDict, Iterator
import logicsponge.core as ls

# 1. Define the Types
class IntMsg(TypedDict):
    msg: int

class StrMsg(TypedDict):
    msg: str

# 2. Annotate the Classes
class Source(ls.SourceTerm):
    # Source produces IntMsg
    Output = IntMsg
    
    def generate(self) -> Iterator[ls.DataItem]:
        yield ls.DataItem({"msg": 42})

class IntFun(ls.FunctionTerm):
    # Expects Int, Returns Int (Increment)
    Input = IntMsg
    Output = IntMsg

    def f(self, di: ls.DataItem) -> ls.DataItem:
        return ls.DataItem({"msg": di["msg"] + 1})
    
class StrFun(ls.FunctionTerm):
    # Expects Str, Returns Str (Duplication)
    Input = StrMsg
    Output = StrMsg

    def f(self, di: ls.DataItem) -> ls.DataItem:
        new_val = f"{di['msg']}{di['msg']}"
        return ls.DataItem({"msg": new_val})
    
class To_str(ls.FunctionTerm):
    # Converts Int -> Str
    Input = IntMsg
    Output = StrMsg

    def f(self, di: ls.DataItem) -> ls.DataItem:
        return ls.DataItem({"msg": str(di["msg"])})
    
class To_int(ls.FunctionTerm):
    # Converts Str -> Int
    Input = StrMsg
    Output = IntMsg

    def f(self, di: ls.DataItem) -> ls.DataItem:
        return ls.DataItem({"msg": int(di["msg"])})
    
class RequireExtra(ls.FunctionTerm):
    Input = TypedDict('Input', {'msg': int, 'extra': bool})
    Output = IntMsg
    def f(self, di: ls.DataItem) -> ls.DataItem: return di



# 3. Main with Test Cases
def main() -> None:

    # --- Valid Pipelines (Should Pass) ---
    s1 = Source() * IntFun() * ls.Print() * ls.Stop()
    s2 = Source() * To_str() * StrFun() * To_int() * ls.Print() * ls.Stop()

    # --- Invalid Pipelines (Should Fail) ---
    
    # CASE 1: Mismatch immediately after Source
    # Source outputs IntMsg (msg: int), but StrFun expects StrMsg (msg: str)
    # E: Stream mismatch
    fail1 = Source() * StrFun() * ls.Stop()

    # CASE 2: Mismatch in the middle of a chain
    # To_str outputs StrMsg, but IntFun expects IntMsg
    # E: Stream mismatch
    fail2 = Source() * To_str() * IntFun() * ls.Stop()

    # CASE 3: Wrong converter order
    # Source outputs Int, To_int expects Str
    # E: Stream mismatch
    fail3 = Source() * To_int() * ls.Stop()
    
    # CASE 4: Missing keys (Structural mismatch)
    # If we tried to pipe into a component requiring extra keys
    # Source provides {'msg': int}, but RequireExtra needs {'msg': int, 'extra': bool}
    # E: Stream mismatch
    fail4 = Source() * RequireExtra() * ls.Stop()


    s1.start()
    s2.start()
    fail1.start()
    fail2.start()
    fail3.start()
    fail4.start()

if __name__ == "__main__":
    main()