"""Typed wrappers for logicsponge with mypy type checking support."""

from typing import Any, Self, Dict, TypeVar, Generic, Iterator, cast
from abc import ABC, abstractmethod

import logicsponge.core as ls

# Type variable for generic typed data
T = TypeVar("T", bound=Dict[str, Any])
T_co = TypeVar("T_co", bound=Dict[str, Any], covariant=True)
T_in = TypeVar("T_in", bound=Dict[str, Any], contravariant=True)


class TypedDataItem(ls.DataItem, Generic[T]):
    """A DataItem with specific typed fields and generic type parameter.
    
    This class maintains type safety while wrapping logicsponge's DataItem.
    Use as TypedDataItem[YourTypedDictType] to get full type checking with mypy.
    
    Example:
        class MessageData(TypedDict):
            message: str
            count: int
        
        item: TypedDataItem[MessageData] = TypedDataItem({"message": "hello", "count": 1})
    """

    def __init__(self, data: T | Self | None = None) -> None:
        """Initialize a new TypedDataItem with type-safe data.
        
        Args:
            data: A dictionary matching the type parameter T, or another TypedDataItem.
        """
        super().__init__(data)

    @property
    def typed_data(self) -> T:
        """Access the underlying data with proper type hints.
        
        Returns:
            The data dictionary cast to type T.
        """
        return cast(T, dict(self))


class TypedSourceTerm(ls.SourceTerm, Generic[T_co], ABC):
    """A SourceTerm that generates TypedDataItems with type safety.
    
    Example:
        class MessageData(TypedDict):
            message: str
        
        class HelloSource(TypedSourceTerm[MessageData]):
            def generate(self) -> Iterator[TypedDataItem[MessageData]]:
                yield TypedDataItem({"message": "hello"})
    """

    @abstractmethod
    def generate(self) -> Iterator[TypedDataItem[T_co]]:
        """Generate TypedDataItems with guaranteed type.
        
        Returns:
            An iterator of TypedDataItem instances with type T_co.
        """
        raise NotImplementedError


class TypedFunctionTerm(ls.FunctionTerm, Generic[T_in, T_co], ABC):
    """A FunctionTerm that processes TypedDataItems with type safety.
    
    Enforces that input is a TypedDataItem and output is properly typed.
    
    Example:
        class InputData(TypedDict):
            message: str
        
        class OutputData(TypedDict):
            message: str
            length: int
        
        class LengthCompute(TypedFunctionTerm[InputData, OutputData]):
            def f(self, di: ls.DataItem) -> TypedDataItem[OutputData] | None:
                # Cast to TypedDataItem for type-safe access
                typed_di = cast(TypedDataItem[InputData], di)
                return TypedDataItem({
                    "message": typed_di["message"],
                    "length": len(typed_di["message"])
                })
    """

    @abstractmethod
    def f(self, di: ls.DataItem) -> ls.DataItem | None:
        """Process a single DataItem with type checking.

        Args:
        ----
            di: Input DataItem (will be a TypedDataItem in practice).
               If term has multiple inputs with wait-for-all semantics,
               this will be a hierarchical TypedDataItem.

        Returns:
        -------
            Processed DataItem (should be TypedDataItem), or None to filter out the item.
            
        Raises:
        ------
            TypeError: If input is not a TypedDataItem.
        """
        # Runtime type checking - mypy will verify types at static analysis time
        if not isinstance(di, TypedDataItem):
            raise TypeError(f"Input must be TypedDataItem, got {type(di).__name__}")
        # Subclasses must implement this method
        raise NotImplementedError


class TypedPrint(ls.Print):
    """Typed wrapper for ls.Print() - just passes through typed data."""
    pass


class TypedStop(ls.Stop):
    """Typed wrapper for ls.Stop() - just passes through."""
    pass


# Runtime validator for development/debugging
def validate_typed_data(di: ls.DataItem, expected_type: type) -> bool:
    """Validate that a DataItem conforms to an expected type at runtime.
    
    This is useful for debugging and runtime checks during development.
    Note: mypy will handle static type checking at compile time.
    
    Args:
        di: The DataItem to validate.
        expected_type: Expected TypedDict or type to validate against.
        
    Returns:
        True if valid, False otherwise.
        
    Example:
        class MessageData(TypedDict):
            message: str
        
        item = TypedDataItem({"message": "hello"})
        assert validate_typed_data(item, MessageData)
    """

    if hasattr(expected_type, "__annotations__"):
        annotations = getattr(expected_type, "__annotations__", {})
        for key in annotations:
            if key not in di:
                return False

    return True
