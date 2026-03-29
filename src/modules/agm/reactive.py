import asyncio
from typing import Any, List, Optional, Type, TypeVar
from PySide6.QtCore import QAbstractTableModel, Qt, QModelIndex
from .ui_metadata import Column, DisplayName, Hidden, IsThumbnail

T = TypeVar("T")

class ReactiveGraphModel(QAbstractTableModel):
    """
    A reactive model that bridges AGM domain objects to PySide6 views.
    Automatically discovers columns from type hints and UI-hints.
    """
    def __init__(self, item_type: Type[T], items: Optional[List[T]] = None):
        super().__init__()
        self._item_type = item_type
        self._items = items or []
        self._headers = self._discover_columns()

    def _discover_columns(self):
        headers = []
        from typing import get_type_hints, Annotated, get_origin, get_args
        
        hints = get_type_hints(self._item_type, include_extras=True)
        for field_name, hint in hints.items():
            # Check for Hidden
            if get_origin(hint) is Annotated:
                metadata = get_args(hint)[1:]
                if any(isinstance(m, Hidden) for m in metadata):
                    continue
                
                # Extract DisplayName and Column
                display_name = field_name
                column_meta = Column()
                
                for m in metadata:
                    if isinstance(m, DisplayName):
                        display_name = m.name
                    if isinstance(m, Column):
                        column_meta = m
                
                if column_meta.visible:
                    headers.append({
                        "id": field_name,
                        "name": display_name,
                        "meta": column_meta
                    })
        return headers

    def rowCount(self, parent=QModelIndex()):
        return len(self._items)

    def columnCount(self, parent=QModelIndex()):
        return len(self._headers)

    def data(self, index, role=Qt.DisplayRole):
        if not index.isValid() or role != Qt.DisplayRole:
            return None
        
        item = self._items[index.row()]
        field_id = self._headers[index.column()]["id"]
        return str(getattr(item, field_id, ""))

    def headerData(self, section, orientation, role=Qt.DisplayRole):
        if orientation == Qt.Horizontal and role == Qt.DisplayRole:
            return self._headers[section]["name"]
        return None

    def update_items(self, new_items: List[T]):
        """Update items and notify the view."""
        self.beginResetModel()
        self._items = new_items
        self.endResetModel()
