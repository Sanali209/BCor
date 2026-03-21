from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

from .models import ConflictStrategy, ImageAnalysisRecord, ProcessingResult


class AreaCondition:
    def __init__(self, min_area: int = 0, max_area: int | float = float("inf")) -> None:
        self.min_area = min_area
        self.max_area = max_area

    def evaluate(self, record: ImageAnalysisRecord) -> bool:
        return self.min_area <= record.area <= self.max_area

    def description(self) -> str:
        return f"Area between {self.min_area} and {self.max_area}"

class SizeCondition:
    def __init__(self, min_bytes: int = 0, max_bytes: int | float = float("inf")) -> None:
        self.min_bytes = min_bytes
        self.max_bytes = max_bytes

    def evaluate(self, record: ImageAnalysisRecord) -> bool:
        return self.min_bytes <= record.size_bytes <= self.max_bytes

    def description(self) -> str:
        return f"Size between {self.min_bytes}B and {self.max_bytes}B"

class FormatCondition:
    def __init__(self, target_formats: list[str], invert: bool = False) -> None:
        normalized = []
        for f in target_formats:
            f = f.strip().lower()
            if not f.startswith("."):
                f = "." + f
            normalized.append(f)
        self.target_formats = normalized
        self.invert = invert

    def evaluate(self, record: ImageAnalysisRecord) -> bool:
        ext = record.extension.lower()
        match = ext in self.target_formats
        return not match if self.invert else match

    def description(self) -> str:
        op = "NOT in" if self.invert else "IN"
        return f"Format {op} {self.target_formats}"

class DeleteAction:
    def execute(self, record: ImageAnalysisRecord, dry_run: bool = False) -> ProcessingResult:
        if dry_run:
            return ProcessingResult(record.path, "DELETE", True, saved_bytes=record.size_bytes)
        try:
            os.remove(record.path)
            return ProcessingResult(record.path, "DELETE", True, saved_bytes=record.size_bytes)
        except Exception as e:
            return ProcessingResult(record.path, "DELETE", False, error_message=str(e))

    def description(self) -> str:
        return "Delete File"

class ConvertAction:
    def __init__(
        self,
        target_format: str,
        quality: int = 90,
        conflict_strategy: ConflictStrategy = ConflictStrategy.RENAME_NEW,
        delete_original: bool = False,
    ) -> None:
        self.target_format = target_format.lower()
        if not self.target_format.startswith("."):
            self.target_format = "." + self.target_format
        self.quality = quality
        self.conflict_strategy = conflict_strategy
        self.delete_original = delete_original
        self.pil_format_map = {
            ".jpg": "JPEG",
            ".jpeg": "JPEG",
            ".png": "PNG",
            ".webp": "WEBP",
            ".bmp": "BMP",
            ".tiff": "TIFF",
        }

    def _resolve_conflict(self, target_path: Path) -> Path | None:
        if not target_path.exists():
            return target_path
        if self.conflict_strategy == ConflictStrategy.OVERWRITE:
            return target_path
        if self.conflict_strategy == ConflictStrategy.SKIP:
            return None
        if self.conflict_strategy == ConflictStrategy.RENAME_NEW:
            stem = target_path.stem
            parent = target_path.parent
            suffix = target_path.suffix
            counter = 1
            while True:
                new_path = parent / f"{stem}_{counter}{suffix}"
                if not new_path.exists():
                    return new_path
                counter += 1
        return target_path

    def execute(self, record: ImageAnalysisRecord, dry_run: bool = False) -> ProcessingResult:
        src_path = Path(record.path)
        if src_path.suffix.lower() == self.target_format:
            return ProcessingResult(record.path, "CONVERT", True, error_message="Source matches target format")

        target_path = src_path.with_suffix(self.target_format)
        final_path = self._resolve_conflict(target_path)
        if final_path is None:
            return ProcessingResult(record.path, "CONVERT", False, error_message="Skipped due to conflict")

        if dry_run:
            return ProcessingResult(record.path, f"CONVERT -> {final_path.name}", True, new_path=str(final_path))

        try:
            with Image.open(src_path) as opened_img:
                img: Image.Image = opened_img
                if self.target_format in [".jpg", ".jpeg"] and img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")
                pil_format = self.pil_format_map.get(self.target_format, self.target_format[1:].upper())
                img.save(final_path, format=pil_format, quality=self.quality)

            saved = 0
            if final_path.exists():
                new_size = final_path.stat().st_size
                if self.delete_original:
                    saved = max(0, record.size_bytes - new_size)

            if self.delete_original and src_path != final_path:
                os.remove(src_path)

            return ProcessingResult(record.path, "CONVERT", True, new_path=str(final_path), saved_bytes=saved)
        except Exception as e:
            return ProcessingResult(record.path, "CONVERT", False, error_message=str(e))

    def description(self) -> str:
        desc = f"Convert to {self.target_format}"
        if self.delete_original:
            desc += " (delete original)"
        return desc
