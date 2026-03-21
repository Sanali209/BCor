from __future__ import annotations

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from src.apps.ImageDedup.domain.interfaces.i_image_differ import IThumbnailCache
from src.apps.ImageDedup.domain.image_group import ImageGroup
from src.apps.ImageDedup.gui.widgets.image_group import ImageGroupWidget


class GroupListWidget(QWidget):
    """Widget to display a large list of image groups with pagination."""

    def __init__(
        self,
        groups: list[ImageGroup],
        thumbnail_cache: IThumbnailCache,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.groups = groups
        self.cache = thumbnail_cache
        self.current_page = 0
        self.page_size = 20
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Scroller
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        
        self.container = QWidget()
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.container_layout.setSpacing(20)
        
        self.scroll_area.setWidget(self.container)
        layout.addWidget(self.scroll_area)

        # Pagination Controls
        page_layout = QHBoxLayout()
        self.prev_btn = QPushButton("< Previous")
        self.next_btn = QPushButton("Next >")
        self.info_label = QLabel("Page 1 / 1")
        
        self.prev_btn.clicked.connect(self._prev_page)
        self.next_btn.clicked.connect(self._next_page)
        
        page_layout.addStretch()
        page_layout.addWidget(self.prev_btn)
        page_layout.addWidget(self.info_label)
        page_layout.addWidget(self.next_btn)
        page_layout.addStretch()
        
        layout.addLayout(page_layout)
        
        self._refresh()

    def _refresh(self) -> None:
        """Redraw the current page."""
        # Clear existing
        while self.container_layout.count():
            item = self.container_layout.takeAt(0)
            if item and (widget := item.widget()):
                widget.deleteLater()

        # Calculate pages
        total_pages = max(1, (len(self.groups) + self.page_size - 1) // self.page_size)
        self.current_page = min(self.current_page, total_pages - 1)
        
        self.info_label.setText(f"Page {self.current_page + 1} / {total_pages}")
        self.prev_btn.setEnabled(self.current_page > 0)
        self.next_btn.setEnabled(self.current_page < total_pages - 1)

        # Add current page groups
        start = self.current_page * self.page_size
        end = start + self.page_size
        for group in self.groups[start:end]:
            widget = ImageGroupWidget(group, self.cache)
            self.container_layout.addWidget(widget)

        # Scroll to top
        self.scroll_area.verticalScrollBar().setValue(0)

    def _next_page(self) -> None:
        self.current_page += 1
        self._refresh()

    def _prev_page(self) -> None:
        self.current_page -= 1
        self._refresh()

    def update_groups(self, groups: list[ImageGroup]) -> None:
        """Sets new groups and refreshes view."""
        self.groups = groups
        self.current_page = 0
        self._refresh()
