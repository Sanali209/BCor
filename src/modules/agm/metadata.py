from dataclasses import dataclass
from typing import Any, TypeVar

T = TypeVar("T")


@dataclass(frozen=True)
class Stored:
    source_field: str


@dataclass(frozen=True)
class Live:
    handler: Any


@dataclass(frozen=True)
class Rel:
    type: str
    direction: str = "OUTGOING"  # OUTGOING or INCOMING
