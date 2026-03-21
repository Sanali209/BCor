from abc import ABC, abstractmethod

from src.apps.ImageAnalyze.domain.entities.batch_processing import Action, ProcessingResult
from src.apps.ImageAnalyze.domain.entities.image_metadata import ImageMetadata


class IImageProcessor(ABC):
    """Порт для выполнения физических операций над изображениями."""

    @abstractmethod
    def execute(self, image: ImageMetadata, action: Action, dry_run: bool = False) -> ProcessingResult:
        """Выполняет действие над изображением."""
        pass
