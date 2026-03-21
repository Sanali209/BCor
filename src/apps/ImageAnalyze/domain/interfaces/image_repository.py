from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any

from ..models import ImageAnalysisRecord


class IImageRepository(ABC):
    """Порт для хранения и поиска метаданных изображений."""

    @abstractmethod
    def bulk_insert(self, records: list[ImageAnalysisRecord]) -> None:
        """Массовая вставка записей."""
        pass

    @abstractmethod
    def get_stats(self) -> dict[str, Any]:
        """Получение общей статистики."""
        pass

    @abstractmethod
    def record_saving(self, action_type: str, saved_bytes: int, path: str) -> None:
        """Запись факта экономии места."""
        pass

    @abstractmethod
    def get_total_savings(self) -> int:
        """Общая экономия в байтах."""
        pass

    @abstractmethod
    def get_all(self) -> list[ImageAnalysisRecord]:
        """Возвращает все метаданные."""
        pass

    @abstractmethod
    def get_extension_stats(self) -> dict[str, dict[str, Any]]:
        """Статистика по расширениям."""
        pass

    @abstractmethod
    def get_chart_data(self) -> dict[str, Any]:
        """Данные для графиков."""
        pass

    @abstractmethod
    def get_savings_history(self, limit: int = 100) -> list[dict[str, Any]]:
        """История экономии."""
        pass
