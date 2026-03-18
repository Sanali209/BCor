from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Stored:
    """Metadata to mark a field for background recalculation.
    
    Attributes:
        source_field: The name of the field that triggers recalculation 
            when changed.
    """
    source_field: str


@dataclass(frozen=True)
class Live:
    """Metadata to mark a field for live hydration via DI.
    
    Attributes:
        handler: The type to resolve from the container to populate 
            this field.
    """
    handler: Any


@dataclass(frozen=True)
class Rel:
    """Metadata to define graph relationships.
    
    Attributes:
        type: The Neo4j relationship type (e.g., 'WORKS_IN').
        direction: The relationship direction (OUTGOING or INCOMING).
    """
    type: str
    direction: str = "OUTGOING"  # OUTGOING or INCOMING
