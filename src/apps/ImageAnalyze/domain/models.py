from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from typing import Any


class ConflictStrategy(Enum):
    SKIP = auto()
    OVERWRITE = auto()
    RENAME_NEW = auto()
    RENAME_EXISTING = auto()


@dataclass(frozen=True)
class ImageAnalysisRecord:
    path: str
    filename: str
    extension: str
    size_bytes: int
    width: int
    height: int
    id: int | None = None
    hash: str | None = None
    created_at: float = 0.0
    modified_at: float = 0.0

    @property
    def area(self) -> int:
        return self.width * self.height


@dataclass(frozen=True)
class ProcessingResult:
    original_path: str
    action_taken: str
    success: bool
    new_path: str | None = None
    error_message: str | None = None
    saved_bytes: int = 0


class Condition(ABC):
    @abstractmethod
    def evaluate(self, record: ImageAnalysisRecord) -> bool:
        pass

    @abstractmethod
    def description(self) -> str:
        pass


class AreaCondition(Condition):
    def __init__(self, min_area: int = 0, max_area: float = float("inf")) -> None:
        self.min_area = min_area
        self.max_area = max_area

    def evaluate(self, record: ImageAnalysisRecord) -> bool:
        return self.min_area <= record.area <= self.max_area

    def description(self) -> str:
        return f"Area between {self.min_area} and {self.max_area}"


class SizeCondition(Condition):
    def __init__(self, min_bytes: int = 0, max_bytes: float = float("inf")) -> None:
        self.min_bytes = min_bytes
        self.max_bytes = max_bytes

    def evaluate(self, record: ImageAnalysisRecord) -> bool:
        return self.min_bytes <= record.size_bytes <= self.max_bytes

    def description(self) -> str:
        return f"Size between {self.min_bytes}B and {self.max_bytes}B"


class FormatCondition(Condition):
    def __init__(self, target_formats: list[str], invert: bool = False) -> None:
        self.target_formats = [f.lower() if f.startswith(".") else f".{f.lower()}" for f in target_formats]
        self.invert = invert

    def evaluate(self, record: ImageAnalysisRecord) -> bool:
        match = record.extension.lower() in self.target_formats
        return not match if self.invert else match

    def description(self) -> str:
        op = "NOT in" if self.invert else "IN"
        return f"Format {op} {self.target_formats}"


class Action(ABC):
    @abstractmethod
    def description(self) -> str:
        pass


@dataclass(frozen=True)
class DeleteAction(Action):
    def description(self) -> str:
        return "Delete File"


@dataclass(frozen=True)
class ConvertAction(Action):
    target_format: str
    quality: int = 90
    conflict_strategy: ConflictStrategy = ConflictStrategy.RENAME_NEW
    delete_original: bool = False

    def description(self) -> str:
        desc = f"Convert to {self.target_format}"
        if self.delete_original:
            desc += " (delete original)"
        return desc


@dataclass(frozen=True)
class ScaleAction(Action):
    max_width: int
    max_height: int
    preserve_ratio: bool = True

    def description(self) -> str:
        return f"Scale to max {self.max_width}x{self.max_height}"


@dataclass
class Rule:
    condition: Condition
    action: Action
    name: str = "Rule"
