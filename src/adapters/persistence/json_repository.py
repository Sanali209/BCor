"""Generic JSON-based persistence repository.

Inspired by legacy appGlue/DAL/DAL.py and MongoDataModel but simplified for BCor's DDD architecture.
"""
from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Generic, TypeVar

from pydantic import TypeAdapter

from src.core.domain import Aggregate
from src.core.repository import AbstractRepository

T = TypeVar("T", bound=Aggregate)

logger = logging.getLogger(__name__)


class JsonRepository(AbstractRepository[T], Generic[T]):
    """Concrete implementation of AbstractRepository using a local JSON file.
    
    Ideal for simple project-based storage or configuration management.
    """

    def __init__(self, file_path: str | Path, model_class: type[T]) -> None:
        """Initialize the repository.
        
        Args:
            file_path: Path to the JSON file.
            model_class: The Pydantic/Domain class for the aggregate.
        """
        super().__init__()
        self.file_path = Path(file_path)
        self.model_class = model_class
        self._items: dict[str, T] = {}
        self._adapter = TypeAdapter(list[model_class])
        self._load()

    def _load(self) -> None:
        """Load data from disk."""
        if not self.file_path.exists():
            self._items = {}
            return

        try:
            with open(self.file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
                items = self._adapter.validate_python(data)
                # Map by reference (id or specific ref attribute)
                for item in items:
                    ref = getattr(item, "ref", getattr(item, "id", None))
                    if ref:
                        self._items[str(ref)] = item
                    else:
                        logger.warning(f"Item in {self.file_path} missing 'ref' or 'id'. Skipping.")
        except Exception as e:
            logger.error(f"Failed to load JSON repository from {self.file_path}: {e}")
            self._items = {}

    def _save(self) -> None:
        """Commit data to disk."""
        try:
            self.file_path.parent.mkdir(parents=True, exist_ok=True)
            data = [item for item in self._items.values()]
            with open(self.file_path, "w", encoding="utf-8") as f:
                # Use pydantic model_dump for clean JSON serialization
                json_data = [
                    item.model_dump(mode="json") if hasattr(item, "model_dump") else item.__dict__ 
                    for item in data
                ]
                json.dump(json_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Failed to save JSON repository to {self.file_path}: {e}")

    def _add(self, aggregate: T) -> None:
        """Add or update an aggregate in the store."""
        ref = getattr(aggregate, "ref", getattr(aggregate, "id", None))
        if not ref:
            raise ValueError("Aggregate must have a 'ref' or 'id' attribute for persistence.")
        self._items[str(ref)] = aggregate
        self._save()

    def _get(self, reference: str) -> T | None:
        """Retrieve an aggregate by its reference string."""
        return self._items.get(reference)

    def list(self) -> list[T]:
        """Get all items in the repository."""
        return list(self._items.values())

    def remove(self, reference: str) -> bool:
        """Remove an item by reference."""
        if reference in self._items:
            del self._items[reference]
            self._save()
            return True
        return False
