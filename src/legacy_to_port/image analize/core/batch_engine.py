import logging
import os
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum, auto
from pathlib import Path
from typing import Any

from PIL import Image

logger = logging.getLogger(__name__)


class ConflictStrategy(Enum):
    SKIP = auto()
    OVERWRITE = auto()
    RENAME_NEW = auto()  # image_1.jpg
    RENAME_EXISTING = auto()  # image.jpg -> image_old.jpg, new write to image.jpg


@dataclass
class ProcessingResult:
    original_path: str
    action_taken: str
    success: bool
    new_path: str | None = None
    error_message: str | None = None
    saved_bytes: int = 0


class Condition(ABC):
    @abstractmethod
    def evaluate(self, image_record: dict[str, Any]) -> bool:
        pass

    @abstractmethod
    def description(self) -> str:
        pass


class AreaCondition(Condition):
    def __init__(self, min_area: int = 0, max_area: int = float("inf")):
        self.min_area = min_area
        self.max_area = max_area

    def evaluate(self, image_record: dict[str, Any]) -> bool:
        area = image_record.get("area", 0)
        return self.min_area <= area <= self.max_area

    def description(self) -> str:
        return f"Area between {self.min_area} and {self.max_area}"


class SizeCondition(Condition):
    def __init__(self, min_bytes: int = 0, max_bytes: int = float("inf")):
        self.min_bytes = min_bytes
        self.max_bytes = max_bytes

    def evaluate(self, image_record: dict[str, Any]) -> bool:
        size = image_record.get("size_bytes", 0)
        return self.min_bytes <= size <= self.max_bytes

    def description(self) -> str:
        return f"Size between {self.min_bytes}B and {self.max_bytes}B"


class FormatCondition(Condition):
    def __init__(self, target_formats: list[str], invert: bool = False):
        # Normalize formats to have leading dot and be lowercase
        normalized = []
        for f in target_formats:
            f = f.strip().lower()
            if not f.startswith("."):
                f = "." + f
            normalized.append(f)
        self.target_formats = normalized
        self.invert = invert

    def evaluate(self, image_record: dict[str, Any]) -> bool:
        ext = image_record.get("extension", "").lower()
        match = ext in self.target_formats
        return not match if self.invert else match

    def description(self) -> str:
        op = "NOT in" if self.invert else "IN"
        return f"Format {op} {self.target_formats}"


class Action(ABC):
    @abstractmethod
    def execute(self, image_record: dict[str, Any], dry_run: bool = False) -> ProcessingResult:
        pass

    @abstractmethod
    def description(self) -> str:
        pass


class DeleteAction(Action):
    def execute(self, image_record: dict[str, Any], dry_run: bool = False) -> ProcessingResult:
        path = image_record["path"]
        size = image_record.get("size_bytes", 0)

        if dry_run:
            return ProcessingResult(path, "DELETE", True, saved_bytes=size)

        try:
            os.remove(path)
            return ProcessingResult(path, "DELETE", True, saved_bytes=size)
        except Exception as e:
            return ProcessingResult(path, "DELETE", False, error_message=str(e))

    def description(self) -> str:
        return "Delete File"


class ConvertAction(Action):
    def __init__(
        self,
        target_format: str,
        quality: int = 90,
        conflict_strategy: ConflictStrategy = ConflictStrategy.RENAME_NEW,
        delete_original: bool = False,
    ):
        self.target_format = target_format.lower()  # e.g. .jpg
        self.quality = quality
        self.conflict_strategy = conflict_strategy
        self.delete_original = delete_original

        # Map extension to PIL format name
        self.pil_format_map = {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
            ".webp": "WEBP",
            ".bmp": "BMP",
            ".tiff": "TIFF",
        }

    def _resolve_conflict(self, target_path: Path) -> Path:
        if not target_path.exists():
            return target_path

        if self.conflict_strategy == ConflictStrategy.OVERWRITE:
            return target_path

        if self.conflict_strategy == ConflictStrategy.SKIP:
            return None

        if self.conflict_strategy == ConflictStrategy.RENAME_NEW:
            # incremental rename: file_1.jpg
            stem = target_path.stem
            parent = target_path.parent
            suffix = target_path.suffix
            counter = 1
            while True:
                new_name = f"{stem}_{counter}{suffix}"
                new_path = parent / new_name
                if not new_path.exists():
                    return new_path
                counter += 1

        return target_path  # Fallback

    def execute(self, image_record: dict[str, Any], dry_run: bool = False) -> ProcessingResult:
        src_path = Path(image_record["path"])
        original_size = image_record.get("size_bytes", 0)

        # Don't convert if already target format
        if src_path.suffix.lower() == self.target_format:
            return ProcessingResult(str(src_path), "CONVERT", True, error_message="Source matches target format")

        target_path = src_path.with_suffix(self.target_format)

        # Check for name collision (same name, different extension)
        # This handles case like: image.png -> image.jpg when image.jpg already exists
        final_path = self._resolve_conflict(target_path)
        if final_path is None:
            return ProcessingResult(str(src_path), "CONVERT", False, error_message="Skipped due to conflict")

        # Build action description
        action_desc = f"CONVERT -> {final_path.name}"
        if self.delete_original:
            action_desc += " (delete original)"

        if dry_run:
            # Estimate savings? Hard to guess without running. Let's assume 0 for dry run or typical compression?
            # User wants to know "clined space", real data needed.
            return ProcessingResult(str(src_path), action_desc, True, new_path=str(final_path), saved_bytes=0)

        try:
            with Image.open(src_path) as img:
                # Convert RGBA -> RGB for JPEG
                if self.target_format in [".jpg", ".jpeg"] and img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                pil_format = self.pil_format_map.get(self.target_format, self.target_format[1:].upper())
                img.save(final_path, format=pil_format, quality=self.quality)

            saved = 0
            # Calculate savings
            if final_path.exists():
                new_size = final_path.stat().st_size
                if self.delete_original:
                    saved = max(0, original_size - new_size)

            # Delete original if requested and paths are different
            if self.delete_original and src_path != final_path:
                os.remove(src_path)

            return ProcessingResult(str(src_path), "CONVERT", True, new_path=str(final_path), saved_bytes=saved)
        except Exception as e:
            return ProcessingResult(str(src_path), "CONVERT", False, error_message=str(e))

    def description(self) -> str:
        desc = f"Convert to {self.target_format}"
        if self.delete_original:
            desc += " (delete original)"
        return desc


class ScaleAction(Action):
    def __init__(self, max_width: int, max_height: int, preserve_ratio: bool = True):
        self.max_width = max_width
        self.max_height = max_height
        self.preserve_ratio = preserve_ratio

    def execute(self, image_record: dict[str, Any], dry_run: bool = False) -> ProcessingResult:
        path = image_record["path"]
        w, h = image_record["width"], image_record["height"]
        original_size = image_record.get("size_bytes", 0)

        if w <= self.max_width and h <= self.max_height:
            return ProcessingResult(path, "SCALE", True, error_message="Image smaller than limits")

        if dry_run:
            return ProcessingResult(path, f"SCALE to {self.max_width}x{self.max_height}", True)

        try:
            with Image.open(path) as img:
                if self.preserve_ratio:
                    img.thumbnail((self.max_width, self.max_height), Image.Resampling.LANCZOS)
                else:
                    img = img.resize((self.max_width, self.max_height), Image.Resampling.LANCZOS)

                img.save(path)  # Overwrite original

            # Calculate savings
            new_size = os.path.getsize(path)
            saved = max(0, original_size - new_size)

            return ProcessingResult(path, "SCALE", True, saved_bytes=saved)
        except Exception as e:
            return ProcessingResult(path, "SCALE", False, error_message=str(e))

    def description(self) -> str:
        return f"Scale to max {self.max_width}x{self.max_height}"


@dataclass
class Rule:
    condition: Condition
    action: Action
    name: str = "Rule"


class BatchEngine:
    def __init__(self):
        pass

    def execute_rules(
        self, images: list[dict[str, Any]], rules: list[Rule], dry_run: bool = False
    ) -> list[ProcessingResult]:
        results = []
        for img in images:
            for rule in rules:
                if rule.condition.evaluate(img):
                    res = rule.action.execute(img, dry_run=dry_run)
                    results.append(res)
                    # For now, we assume one action per image per batch run, or we chain?
                    # If action generates new file (Convert), should we chain rules?
                    # Simplest approach: One pass, first matching rule applies, or all matching rules apply?
                    # Let's say all matching rules apply, but check existence.
                    if res.action_taken == "DELETE":
                        break  # Stop processing deleted file
        return results
