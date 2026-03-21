from __future__ import annotations

from typing import Any

import pyexiv2
from loguru import logger

from ..domain.interfaces.i_xmp_metadata import IXmpMetadata


class XMPAdapter(IXmpMetadata):
    """ACL Adapter for XMP metadata management."""

    def read_metadata(self, image_path: str) -> dict[str, Any]:
        """Reads XMP tags from the image.
        
        Returns a dict with title, description, subjects (tags), and rating.
        """
        try:
            with pyexiv2.Image(image_path) as img:
                xmp = img.read_xmp()

            title = xmp.get('Xmp.dc.title')
            if isinstance(title, dict):
                title = title.get('lang="x-default"')

            description = xmp.get('Xmp.dc.description')
            if isinstance(description, dict):
                description = description.get('lang="x-default"')

            subject = xmp.get('Xmp.dc.subject', [])
            
            # Rating can be a string list in some XMP versions
            rating_raw = xmp.get('Xmp.xmp.Rating', ['0'])
            if isinstance(rating_raw, list) and rating_raw:
                rating = rating_raw[0]
            else:
                rating = str(rating_raw)

            return {
                'title': title,
                'description': description,
                'subjects': subject if isinstance(subject, list) else [subject] if subject else [],
                'rating': int(rating) if rating.isdigit() else 0,
            }
        except Exception as e:
            logger.warning(f"Failed to read XMP from {image_path}: {e}")
            return {'title': None, 'description': None, 'subjects': [], 'rating': 0}

    def write_metadata(
        self, 
        image_path: str, 
        title: str | None = None,
        description: str | None = None, 
        rating: int | None = None,
        subjects: list[str] | None = None
    ) -> bool:
        """Writes XMP metadata to the image."""
        try:
            with pyexiv2.Image(image_path) as img:
                modifications: dict[str, Any] = {}
                if title is not None:
                    modifications["Xmp.dc.title"] = title
                if description is not None:
                    modifications["Xmp.dc.description"] = description
                if rating is not None:
                    modifications["Xmp.xmp.Rating"] = str(rating)
                if subjects is not None:
                    modifications["Xmp.dc.subject"] = subjects
                
                if modifications:
                    img.modify_xmp(modifications)
            return True
        except Exception as e:
            logger.error(f"Failed to write XMP to {image_path}: {e}")
            return False
