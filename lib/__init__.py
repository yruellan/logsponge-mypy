from typing import Any

class Vector:
    # Allow subscripting at runtime: Vector[int, int]
    def __class_getitem__(cls, item):
        return cls
    
    def __init__(self, *args: Any) -> None:
        pass

    def __add__(self, other: "Vector") -> "Vector":
        
        raise NotImplementedError("Vector addition not implemented yet")