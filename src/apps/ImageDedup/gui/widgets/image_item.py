from __future__ import annotations

import os
from typing import Any

from PySide6.QtCore import QPoint, Qt, Signal
from PySide6.QtGui import QAction, QColor, QImage, QMouseEvent, QPainter, QPaintEvent, QPen, QPixmap
from PySide6.QtWidgets import QApplication, QLabel, QMenu, QVBoxLayout, QWidget

from src.apps.ImageDedup.domain.image_item import ImageItem
from src.apps.ImageDedup.domain.interfaces.i_image_differ import IThumbnailCache


class ImageWidget(QWidget):
    """Widget to display a single image item."""
    
    selected_changed = Signal(bool)

    def __init__(self, item: ImageItem, thumbnail_cache: IThumbnailCache, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.item = item
        self.cache = thumbnail_cache
        self.setFixedSize(220, 260)
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)

        # Image Label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(210, 210)
        self.image_label.setStyleSheet("background-color: #1a1a1a; border-radius: 4px;")
        layout.addWidget(self.image_label)

        # Path Label
        self.path_label = QLabel(os.path.basename(self.item.path))
        self.path_label.setStyleSheet("font-size: 10px; color: #aaaaaa;")
        self.path_label.setWordWrap(True)
        layout.addWidget(self.path_label)

        self._load_thumbnail()

    def _load_thumbnail(self) -> None:
        """Load thumbnail from cache and display."""
        pil_img: Any = self.cache.get_thumbnail(self.item.path, (200, 200))
        if pil_img:
            # Convert PIL to QImage
            # Note: We need to handle RGB vs BGR depending on format
            qimg = QImage(pil_img.tobytes("raw", "RGB"), pil_img.size[0], pil_img.size[1], QImage.Format.Format_RGB888)
            self.image_label.setPixmap(QPixmap.fromImage(qimg))

    def paintEvent(self, event: QPaintEvent) -> None:
        """Draw selection border."""
        super().paintEvent(event)
        if self.item.selected:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            pen = QPen(QColor("#bb86fc"))
            pen.setWidth(3)
            painter.setPen(pen)
            painter.drawRoundedRect(self.rect().adjusted(2, 2, -2, -2), 6, 6)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() == Qt.MouseButton.LeftButton:
            self.item.selected = not self.item.selected
            self.selected_changed.emit(self.item.selected)
            self.update()
        elif event.button() == Qt.MouseButton.RightButton:
            self._show_context_menu(event.globalPos())

    def _show_context_menu(self, pos: QPoint) -> None:
        menu = QMenu(self)
        
        open_action = QAction("Open in Explorer", self)
        open_action.triggered.connect(self._on_open_explorer)
        menu.addAction(open_action)
        
        copy_path = QAction("Copy Path", self)
        copy_path.triggered.connect(self._on_copy_path)
        menu.addAction(copy_path)
        
        menu.addSeparator()
        
        remove_action = QAction("Remove from Group", self)
        # remove_action.triggered.connect(...)
        menu.addAction(remove_action)
        
        menu.exec(pos)

    def _on_open_explorer(self) -> None:
        import subprocess
        subprocess.run(['explorer', '/select,', os.path.normpath(self.item.path)])

    def _on_copy_path(self) -> None:
        QApplication.clipboard().setText(self.item.path)
