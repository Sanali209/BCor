"""PairwiseView — Side-by-side asset comparison and triage."""
from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QScrollArea, QFrame, QGridLayout
)
from PySide6.QtGui import QPixmap, QImage
from src.modules.assets.domain.models import Asset, RelationType


class ImagePreview(QFrame):
    """Simple image preview with scale-to-fit."""
    def __init__(self):
        super().__init__()
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        layout = QVBoxLayout(self)
        self.label = QLabel("No Image")
        self.label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.label)
        self.setMinimumSize(300, 300)

    def set_asset(self, asset: Asset):
        path = asset.uri.replace("file://", "")
        pixmap = QPixmap(path)
        if not pixmap.isNull():
            self.label.setPixmap(pixmap.scaled(
                self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation
            ))
        else:
            self.label.setText("Failed to load")


class PairwiseWidget(QWidget):
    """Main pairwise comparison interface."""
    
    annotated = Signal(str, str)  # asset_id, relation_type
    deleted = Signal(str)         # asset_id
    
    def __init__(self):
        super().__init__()
        self.asset_a: Asset | None = None
        self.asset_b: Asset | None = None
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        
        # 1. Image Area
        images_layout = QHBoxLayout()
        self.preview_a = ImagePreview()
        self.preview_b = ImagePreview()
        images_layout.addWidget(self.preview_a)
        images_layout.addWidget(self.preview_b)
        main_layout.addLayout(images_layout)
        
        # 2. Comparison Metadata
        self.info_label = QLabel("Compare assets")
        self.info_label.setAlignment(Qt.AlignCenter)
        self.info_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        main_layout.addWidget(self.info_label)
        
        # 3. Actions Area (Annotation Grid)
        actions_layout = QHBoxLayout()
        
        # Left: Annotation Grid
        grid_container = QWidget()
        grid = QGridLayout(grid_container)
        relations = [
            (RelationType.DUPLICATE, "1: Duplicate"),
            (RelationType.NEAR_DUPLICATE, "2: Near Dupe"),
            (RelationType.CROP_DUPLICATE, "3: Crop"),
            (RelationType.SIMILAR_STYLE, "4: Style"),
            (RelationType.SAME_PERSON, "5: Person"),
            (RelationType.SAME_IMAGE_SET, "6: Burst"),
            (RelationType.OTHER, "7: Other"),
            (RelationType.NOT_DUPLICATE, "8: Not Dupe"),
        ]
        
        for i, (rel, label) in enumerate(relations):
            btn = QPushButton(label)
            btn.clicked.connect(lambda _, r=rel: self._on_annotate(r))
            grid.addWidget(btn, i // 4, i % 4)
            
        actions_layout.addWidget(grid_container)
        
        # Right: Critical Actions
        critical_layout = QVBoxLayout()
        self.btn_del_a = QPushButton("Delete Left")
        self.btn_del_b = QPushButton("Delete Right")
        self.btn_diff = QPushButton("Visual Diff")
        
        self.btn_del_a.setStyleSheet("background-color: #442222;")
        self.btn_del_b.setStyleSheet("background-color: #442222;")
        
        self.btn_del_a.clicked.connect(lambda: self._on_delete("a"))
        self.btn_del_b.clicked.connect(lambda: self._on_delete("b"))
        
        critical_layout.addWidget(self.btn_del_a)
        critical_layout.addWidget(self.btn_del_b)
        critical_layout.addWidget(self.btn_diff)
        actions_layout.addLayout(critical_layout)
        
        main_layout.addLayout(actions_layout)

    def set_pair(self, a: Asset, b: Asset, score: float = 0.0):
        self.asset_a = a
        self.asset_b = b
        self.preview_a.set_asset(a)
        self.preview_b.set_asset(b)
        self.info_label.setText(f"Distance: {score:.4f}")

    def _on_annotate(self, rel_type: str):
        if self.asset_a and self.asset_b:
            self.annotated.emit(self.asset_b.id, str(rel_type))

    def _on_delete(self, side: str):
        asset = self.asset_a if side == "a" else self.asset_b
        if asset:
            self.deleted.emit(asset.id)
