from typing import List, Optional
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
    QSplitter, QScrollArea, QFrame
)
from PySide6.QtCore import Qt, Signal
from src.modules.assets.ui.widgets import AGMTableView, AssetCard
from src.modules.assets.domain.models import Asset

class ClusterExplorerWidget(QWidget):
    """
    Advanced widget for exploring and resolving duplicate clusters.
    Uses a master-detail layout: 
    - Left: Table of duplicate pairs/groups.
    - Right: Visual comparison cards.
    """
    confirm_duplicate = Signal(str)  # asset_id
    compare_pair = Signal(object, object)  # asset_a, asset_b
    
    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        layout = QHBoxLayout(self)
        
        # Splitter for Master-Detail
        self.splitter = QSplitter(Qt.Horizontal)
        layout.addWidget(self.splitter)

        # 1. Master View (The Table)
        self.table_container = QWidget()
        master_layout = QVBoxLayout(self.table_container)
        
        title = QLabel("Discovered Clusters")
        title.setStyleSheet("font-size: 18px; font-weight: bold;")
        master_layout.addWidget(title)
        
        self.table = AGMTableView(Asset)
        self.table.clicked.connect(self.on_item_selected)
        master_layout.addWidget(self.table)
        
        self.splitter.addWidget(self.table_container)

        # 2. Detail View (Visual Comparison)
        self.detail_container = QWidget()
        detail_layout = QVBoxLayout(self.detail_container)
        
        detail_title = QLabel("Visual Verification")
        detail_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        detail_layout.addWidget(detail_title)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.card_container = QWidget()
        self.card_layout = QHBoxLayout(self.card_container)
        self.card_layout.setSpacing(10)
        self.scroll.setWidget(self.card_container)
        detail_layout.addWidget(self.scroll)
        
        # Buttons
        btn_layout = QHBoxLayout()
        self.merge_btn = QPushButton("Confirm Duplicate")
        self.merge_btn.setStyleSheet("background-color: #2e7d32;")
        self.merge_btn.clicked.connect(self.on_confirm)
        btn_layout.addWidget(self.merge_btn)
        
        self.ignore_btn = QPushButton("Not a Duplicate")
        self.ignore_btn.setStyleSheet("background-color: #c62828;")
        btn_layout.addWidget(self.ignore_btn)
        
        self.compare_btn = QPushButton("Compare Pairwise")
        self.compare_btn.setStyleSheet("background-color: #1976d2;")
        self.compare_btn.clicked.connect(self.on_compare)
        btn_layout.addWidget(self.compare_btn)
        
        detail_layout.addLayout(btn_layout)
        
        self.splitter.addWidget(self.detail_container)
        self.splitter.setStretchFactor(0, 1)
        self.splitter.setStretchFactor(1, 1)

    def on_item_selected(self, index):
        """React to selecting a cluster member in the table."""
        self.clear_cards()
        model = self.table.model()
        asset = model._items[index.row()]
        self.add_card(asset)
        
        # Also try to find a similar asset if any
        if asset.similar:
            # For now, just show the first one
            self.add_card_by_id(asset.similar[0].id)

    def on_compare(self):
        """Trigger pairwise comparison for selected item."""
        model = self.table.model()
        selection = self.table.selectionModel().currentIndex()
        if selection.isValid():
            asset_a = model._items[selection.row()]
            if asset_a.similar:
                # We need the full asset B, but we only have ID. 
                # This will be handled in gui.py via signal.
                self.compare_pair.emit(asset_a, asset_a.similar[0].id)

    def on_confirm(self):
        """User confirmed this as a duplicate."""
        model = self.table.model()
        selection = self.table.selectionModel().currentIndex()
        if selection.isValid():
            asset = model._items[selection.row()]
            self.confirm_duplicate.emit(asset.id)

    def add_card(self, asset: Asset):
        card = AssetCard(asset)
        self.card_layout.addWidget(card)

    def add_card_by_id(self, asset_id: str):
        # This is a placeholder; real hydration happens in gui.py
        pass

    def clear_cards(self):
        while self.card_layout.count():
            item = self.card_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
