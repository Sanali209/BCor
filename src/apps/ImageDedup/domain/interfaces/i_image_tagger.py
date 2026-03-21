"""ImageDedup domain: IImageTagger port.

Abstracts image classification and tagging (e.g., using WD-Tagger).
"""
from __future__ import annotations

import abc


from src.modules.vision.domain.interfaces.vision import IVisionTagger


class IImageTagger(IVisionTagger):
    """Port: classify and extract tags from image files."""
    # Inherits predict_tags from IVisionTagger
