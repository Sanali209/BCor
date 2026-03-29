"""Pyexiv2SmartHandler — Normalized metadata extraction for search and filtering."""
from __future__ import annotations

import pathlib
from datetime import datetime
from typing import Any
import pyexiv2
from loguru import logger


class Pyexiv2SmartHandler:
    """Enhanced metadata handler that normalizes cryptic EXIF tags.
    
    Standardizes:
    - Dates: '2023:01:01 12:00:00' -> '2023-01-01T12:00:00'
    - Fractions: '1/500' -> 0.002
    - Typings: Ensures numeric fields are actual numbers.
    """

    # Tag Mapping (Standardize the chaos of EXIF names)
    TAG_MAP = {
        "captured_at": "Exif.Photo.DateTimeOriginal",
        "camera_make": "Exif.Image.Make",
        "camera_model": "Exif.Image.Model",
        "iso": "Exif.Photo.ISOSpeedRatings",
        "f_number": "Exif.Photo.FNumber",
        "exposure_time": "Exif.Photo.ExposureTime",
        "focal_length": "Exif.Photo.FocalLength",
        "software": "Exif.Image.Software",
    }

    @classmethod
    async def run(cls, uri: str, context: dict[str, Any] | None = None) -> Any:
        """Extract a specific searchable tag or a full smart summary."""
        field_name = (context or {}).get("field_name")
        from src.core.storage import uri_to_path
        path = str(uri_to_path(uri).absolute())


        if not pathlib.Path(path).exists():
            return None

        img = None
        try:
            img = pyexiv2.Image(path)
            exif = img.read_exif()
            
            # If the AGM field name is in our map, return just THAT normalized tag
            if field_name in cls.TAG_MAP:
                raw_tag = cls.TAG_MAP[field_name]
                val = exif.get(raw_tag)
                normalized = cls._normalize(field_name, val)
                logger.debug(f"Pyexiv2SmartHandler: {field_name} -> {raw_tag} = {val} (norm: {normalized})")
                return normalized
            
            # If no field_name or unknown field, return the full standard summary
            summary = {}
            for field, tag in cls.TAG_MAP.items():
                val = exif.get(tag)
                summary[field] = cls._normalize(field, val)
            return summary
            
        except Exception as e:
            logger.error(f"Pyexiv2SmartHandler failed for {path}: {e}")
            return None
        finally:
            if img:
                img.close()

    @staticmethod
    def _normalize(field: str, value: Any) -> Any:
        """Normalize EXIF values to standardized primitive types."""
        if value is None:
            return None
            
        # 1. Normalize Dates
        if field == "captured_at":
            try:
                # EXIF format: 'YYYY:MM:DD HH:MM:SS'
                dt = datetime.strptime(str(value), "%Y:%m:%d %H:%M:%S")
                return dt.isoformat()
            except (ValueError, TypeError):
                return str(value)

        # 2. Normalize Fractions (Rationales)
        if field in ("f_number", "exposure_time", "focal_length"):
            try:
                s_val = str(value)
                if "/" in s_val:
                    num, den = map(float, s_val.split("/"))
                    return num / den if den != 0 else 0.0
                
                # pyexiv2 Rationals might be objects with .numerator/.denominator
                if hasattr(value, "numerator") and hasattr(value, "denominator"):
                    return float(value.numerator) / float(value.denominator) if value.denominator != 0 else 0.0
                
                return float(value)
            except (ValueError, TypeError, ZeroDivisionError):
                return 0.0

        # 3. Normalize ISO
        if field == "iso":
            try:
                # might be a list or a single int
                if isinstance(value, list) and value:
                    return int(value[0])
                return int(value)
            except (ValueError, TypeError):
                return 0

        # 4. Fallback: stringify
        return str(value).strip() if value is not None else None
