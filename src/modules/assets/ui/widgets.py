from typing import Optional, Type, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QTableView, QHeaderView, QFrame
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QPixmap, QImage
from src.modules.agm.reactive import ReactiveGraphModel
from ..domain.models import Asset

class AGMTableView(QTableView):
    """
    A generic table view that automatically configures its columns
    from the provided AGM model type.
    """
    def __init__(self, item_type: Type, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.model_proxy = ReactiveGraphModel(item_type)
        self.setModel(self.model_proxy)
        
        # UI Styling
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.setAlternatingRowColors(True)
        self.setSelectionBehavior(QTableView.SelectRows)
        self.verticalHeader().setVisible(False)
        
        # Apply metadata-driven widths
        for i, header in enumerate(self.model_proxy._headers):
            self.setColumnWidth(i, header["meta"].width)

class AssetCard(QFrame):
    """
    A visual card for displaying an Asset's thumbnail and key information.
    """
    def __init__(self, asset: Asset, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setFixedSize(200, 260)
        
        layout = QVBoxLayout(self)
        
        # Thumbnail
        self.thumbnail_label = QLabel()
        self.thumbnail_label.setFixedSize(180, 180)
        self.thumbnail_label.setAlignment(Qt.AlignCenter)
        self.thumbnail_label.setStyleSheet("background-color: #2b2b2b;")
        
        if asset.thumbnail_bytes:
            image = QImage.fromData(asset.thumbnail_bytes)
            pixmap = QPixmap.fromImage(image)
            self.thumbnail_label.setPixmap(pixmap.scaled(
                180, 180, Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        else:
            self.thumbnail_label.setText("No Preview")
        
        layout.addWidget(self.thumbnail_label)
        
        # Info
        self.name_label = QLabel(asset.name)
        self.name_label.setStyleSheet("font-weight: bold;")
        self.name_label.setWordWrap(True)
        layout.addWidget(self.name_label)
        
        self.meta_label = QLabel(f"{asset.mime_type} | {asset.size // 1024} KB")
        self.meta_label.setStyleSheet("color: #888;")
        layout.addWidget(self.meta_label)
        
        layout.addStretch()
