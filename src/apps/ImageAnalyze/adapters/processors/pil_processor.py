from __future__ import annotations

import os
from pathlib import Path

from PIL import Image

from src.apps.ImageAnalyze.domain.models import (
    Action,
    ConflictStrategy,
    ConvertAction,
    DeleteAction,
    ImageAnalysisRecord,
    ProcessingResult,
    ScaleAction,
)
from src.apps.ImageAnalyze.domain.interfaces.image_processor import IImageProcessor


class PILImageProcessor(IImageProcessor):
    """Адаптер для обработки изображений.
    Соединяет доменные намерения (Actions) с реализацией на PIL.
    """

    def execute(self, image: ImageAnalysisRecord, action: Action, dry_run: bool = False) -> ProcessingResult:
        if isinstance(action, DeleteAction):
            return self._handle_delete(image, action, dry_run)
        elif isinstance(action, ScaleAction):
            return self._handle_scale(image, action, dry_run)
        elif isinstance(action, ConvertAction):
            return self._handle_convert(image, action, dry_run)
        else:
            return ProcessingResult(image.path, "UNKNOWN", False, error_message="Unsupported action")

    def _handle_delete(self, image: ImageAnalysisRecord, action: DeleteAction, dry_run: bool) -> ProcessingResult:
        if dry_run:
            return ProcessingResult(image.path, "DELETE", True, saved_bytes=image.size_bytes)
        try:
            os.remove(image.path)
            return ProcessingResult(image.path, "DELETE", True, saved_bytes=image.size_bytes)
        except Exception as e:
            return ProcessingResult(image.path, "DELETE", False, error_message=str(e))

    def _handle_scale(self, image: ImageAnalysisRecord, action: ScaleAction, dry_run: bool) -> ProcessingResult:
        if dry_run:
            return ProcessingResult(image.path, "SCALE", True)
        try:
            with Image.open(image.path) as opened_img:
                img: Image.Image = opened_img
                if action.preserve_ratio:
                    img.thumbnail((action.max_width, action.max_height), Image.Resampling.LANCZOS)
                else:
                    img = img.resize((action.max_width, action.max_height), Image.Resampling.LANCZOS)
                img.save(image.path)

            new_size = os.path.getsize(image.path)
            saved = max(0, image.size_bytes - new_size)
            return ProcessingResult(image.path, "SCALE", True, saved_bytes=saved)
        except Exception as e:
            return ProcessingResult(image.path, "SCALE", False, error_message=str(e))

    def _handle_convert(self, image: ImageAnalysisRecord, action: ConvertAction, dry_run: bool) -> ProcessingResult:
        src_path = Path(image.path)
        target_path = src_path.with_suffix(action.target_format)

        # Conflict resolution logic (simplified for adapter)
        if target_path.exists() and action.conflict_strategy == ConflictStrategy.SKIP:
            return ProcessingResult(image.path, "CONVERT", False, error_message="Conflict skipped")

        if dry_run:
            return ProcessingResult(image.path, "CONVERT", True, new_path=str(target_path))

        try:
            with Image.open(src_path) as opened_img:
                img: Image.Image = opened_img
                if action.target_format.lower() in [".jpg", ".jpeg"] and img.mode in ("RGBA", "LA", "P"):
                    img = img.convert("RGB")

                fmt = action.target_format[1:].upper()
                if fmt == "JPG":
                    fmt = "JPEG"
                img.save(target_path, format=fmt, quality=action.quality)

            saved = 0
            if action.delete_original and src_path != target_path:
                saved = image.size_bytes
                os.remove(src_path)

            return ProcessingResult(image.path, "CONVERT", True, new_path=str(target_path), saved_bytes=saved)
        except Exception as e:
            return ProcessingResult(image.path, "CONVERT", False, error_message=str(e))
