from dataclasses import dataclass
from typing import Any, Optional, TypeVar

T = TypeVar("T")

@dataclass(frozen=True)
class UiHint:
    """Base class for all UI metadata hints."""
    pass

@dataclass(frozen=True)
class DisplayName(UiHint):
    """Overrides the default display name of a field."""
    name: str

@dataclass(frozen=True)
class Column(UiHint):
    """Indicates that this field should be shown as a column in tables."""
    width: int = 150
    visible: bool = True
    sortable: bool = True
    filterable: bool = True

@dataclass(frozen=True)
class Hidden(UiHint):
    """Explicitly hides a field from automatic UI generators."""
    pass

@dataclass(frozen=True)
class IsThumbnail(UiHint):
    """Indicates that this field provides a path or URL for a thumbnail image."""
    width: int = 128
    height: int = 128

@dataclass(frozen=True)
class FormatAs(UiHint):
    """Specifies a formatter for the field value (e.g., 'bytes', 'date')."""
    formatter_type: str
