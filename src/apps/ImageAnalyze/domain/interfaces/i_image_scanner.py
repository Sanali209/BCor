from abc import ABC, abstractmethod

from src.apps.ImageAnalyze.domain.entities.image_metadata import ImageMetadata


class IImageScanner(ABC):
    """Порт для сканирования изображений.
    Абстрагирует PIL и multiprocessing от домена.
    """

    @abstractmethod
    def scan_file(self, path: str) -> ImageMetadata | None:
        """Сканирует один файл."""
        pass

    @abstractmethod
    def scan_directory(self, directory: str) -> list[ImageMetadata]:
        """Сканирует директорию."""
        pass
