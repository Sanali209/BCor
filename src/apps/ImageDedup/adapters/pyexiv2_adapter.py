"""ImageDedup infrastructure: PyExiv2-based Metadata Adapter."""
from __future__ import annotations

from typing import Any

import pyexiv2
from loguru import logger

from src.apps.ImageDedup.domain.interfaces.i_xmp_metadata import IXmpMetadata


class PyExiv2MetadataAdapter(IXmpMetadata):
    """Concrete implementation of IXmpMetadata using pyexiv2."""

    def read_metadata(self, image_path: str) -> dict[str, Any]:
        """Read XMP metadata from image file."""
        try:
            with pyexiv2.Image(image_path) as img:
                xmp = img.read_xmp()

            title = xmp.get("Xmp.dc.title")
            if isinstance(title, dict):
                title = title.get('lang="x-default"')

            description = xmp.get("Xmp.dc.description")
            if isinstance(description, dict):
                description = description.get('lang="x-default"')

            subject = xmp.get("Xmp.dc.subject")

            rating_raw = xmp.get("Xmp.xmp.Rating", ["0"])
            rating = rating_raw[0] if isinstance(rating_raw, list) and rating_raw else "0"
            
            return {
                "title": title,
                "description": description,
                "subjects": subject if isinstance(subject, list) else [],
                "rating": int(rating) if str(rating).isdigit() else 0,
            }
        except Exception as e:
            logger.error(f"Failed to read XMP metadata from {image_path}: {e}")
            return {"title": None, "description": None, "subjects": [], "rating": 0}

    def write_metadata(
        self, 
        image_path: str, 
        title: str | None = None,
        description: str | None = None, 
        rating: int | None = None,
        subjects: list[str] | None = None
    ) -> bool:
        """Write XMP metadata directly to image file."""
        try:
            with pyexiv2.Image(image_path) as img:
                data: dict[str, Any] = {}
                if title is not None:
                    data["Xmp.dc.title"] = title
                if description is not None:
                    data["Xmp.dc.description"] = description
                if rating is not None:
                    data["Xmp.xmp.Rating"] = str(rating)
                if subjects is not None:
                    data["Xmp.dc.subject"] = subjects
                
                if data:
                    img.modify_xmp(data)
            
            logger.debug(f"Successfully wrote XMP metadata to {image_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to write XMP metadata to {image_path}: {e}")
            return False
