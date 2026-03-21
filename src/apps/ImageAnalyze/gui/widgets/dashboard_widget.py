from __future__ import annotations

from typing import Any

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QVBoxLayout, QWidget

from src.common.formatters import format_size
from ...use_cases import GetCollectionStatsUseCase


class DashboardWidget(QWidget):
    def __init__(self, stats_use_case: GetCollectionStatsUseCase) -> None:
        super().__init__()
        self.stats_use_case = stats_use_case
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Collection Insights")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #e94560;")
        layout.addWidget(title)
        
        # Stats Cards
        cards_layout = QHBoxLayout()
        self.total_images_card = self._create_card("Total Images", "0", "lbl_total_images")
        self.total_size_card = self._create_card("Total Volume", "0 MB", "lbl_total_size")
        self.formats_card = self._create_card("Formats", "-", "lbl_formats")
        
        cards_layout.addWidget(self.total_images_card)
        cards_layout.addWidget(self.total_size_card)
        cards_layout.addWidget(self.formats_card)
        layout.addLayout(cards_layout)
        
        layout.addStretch()

    def _create_card(self, title: str, value: str, object_name: str) -> QFrame:
        card = QFrame()
        card.setFrameShape(QFrame.Shape.StyledPanel)
        card.setStyleSheet("""
            QFrame {
                background-color: #16213e;
                border: 1px solid #0f3460;
                border-radius: 8px;
                padding: 15px;
            }
        """)
        
        card_layout = QVBoxLayout(card)
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #e0e0e0; font-size: 14px;")
        
        value_label = QLabel(value)
        value_label.setStyleSheet("color: #ffffff; font-size: 20px; font-weight: bold;")
        value_label.setObjectName(object_name)
        
        card_layout.addWidget(title_label)
        card_layout.addWidget(value_label)
        return card

    def refresh_data(self) -> None:
        stats = self.stats_use_case.execute()
        
        lbl_total_images = self.total_images_card.findChild(QLabel, "lbl_total_images")
        if lbl_total_images:
            lbl_total_images.setText(str(stats.get("total_images", 0)))
        
        lbl_total_size = self.total_size_card.findChild(QLabel, "lbl_total_size")
        if lbl_total_size:
            lbl_total_size.setText(format_size(stats.get("total_size_bytes", 0)))
        
        lbl_formats = self.formats_card.findChild(QLabel, "lbl_formats")
        if lbl_formats:
            formats_data = stats.get("formats", {})
            formats_str = ", ".join([f"{k}: {v}" for k, v in formats_data.items()])
            lbl_formats.setText(formats_str if formats_str else "-")
