"""ImageDedup GUI: Image Group Widget.

Displays a group of images (duplicates or related) in a grid.
"""
from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from src.apps.ImageDedup.domain.image_group import ImageGroup
from src.apps.ImageDedup.domain.interfaces.i_image_differ import IThumbnailCache
from src.apps.ImageDedup.gui.widgets.image_item import ImageWidget


class ImageGroupWidget(QWidget):
    """Widget representing a group of images."""

    def __init__(self, group: ImageGroup, thumbnail_cache: IThumbnailCache, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.group = group
        self.cache = thumbnail_cache
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Header (Checkbox + Title + Tools)
        header_layout = QHBoxLayout()
        
        self.select_check = QCheckBox()
        self.select_check.setChecked(self.group.selected)
        self.select_check.stateChanged.connect(self._on_group_select_toggled)
        header_layout.addWidget(self.select_check)
        
        self.title_edit = QLineEdit(self.group.label)
        self.title_edit.setStyleSheet("font-weight: bold; font-size: 14px; border: none; background: transparent;")
        self.title_edit.textChanged.connect(self._on_label_changed)
        header_layout.addWidget(self.title_edit)
        
        header_layout.addStretch()
        
        self.invert_btn = QPushButton("Invert Selection")
        self.invert_btn.setFlat(True)
        self.invert_btn.clicked.connect(self._on_invert_selection)
        header_layout.addWidget(self.invert_btn)
        
        layout.addLayout(header_layout)

        # Image Grid
        self.grid_layout = QGridLayout()
        self.grid_layout.setSpacing(10)
        
        self.image_widgets: list[ImageWidget] = []
        for i, item in enumerate(self.group.items):
            widget = ImageWidget(item, self.cache)
            self.image_widgets.append(widget)
            self.grid_layout.addWidget(widget, i // 4, i % 4)
            
        layout.addLayout(self.grid_layout)
        
        # Separator line
        line = QWidget()
        line.setFixedHeight(1)
        line.setStyleSheet("background-color: #333333;")
        layout.addWidget(line)

    def _on_group_select_toggled(self, state: int) -> None:
        self.group.selected = (state == Qt.CheckState.Checked.value)

    def _on_label_changed(self, text: str) -> None:
        self.group.label = text

    def _on_invert_selection(self) -> None:
        for widget in self.image_widgets:
            widget.item.selected = not widget.item.selected
            widget.update()
