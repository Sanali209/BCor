import sys
import asyncio
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QPushButton, QLabel, QFrame, QLineEdit, QListWidget, QListWidgetItem,
    QScrollArea, QFormLayout, QGroupBox
)
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtGui import QPixmap

from src.apps.asset_explorer.presentation.viewmodels.explorer import AssetExplorerViewModel
from src.apps.asset_explorer.presentation.viewmodels.metadata import MetadataViewModel, PropertyDescriptor
from src.modules.agm.mapper import AGMMapper
from unittest.mock import MagicMock

# ─── UI Components ───────────────────────────────────────────────────────────

class AssetListItem(QListWidgetItem):
    def __init__(self, asset):
        super().__init__(asset.name or asset.uri)
        self.asset = asset
        self.setData(Qt.UserRole, asset.id)

class SearchPanel(QGroupBox):
    search_requested = Signal(str)

    def __init__(self):
        super().__init__("Search & Filter")
        layout = QVBoxLayout(self)
        
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Enter search query (e.g. nature, forest)...")
        layout.addWidget(self.query_input)
        
        self.search_btn = QPushButton("Search Assets")
        layout.addWidget(self.search_btn)
        
        layout.addStretch()
        
        self.search_btn.clicked.connect(lambda: self.search_requested.emit(self.query_input.text()))

class ResultsPanel(QGroupBox):
    asset_selected = Signal(str)

    def __init__(self):
        super().__init__("Results")
        layout = QVBoxLayout(self)
        
        self.list_widget = QListWidget()
        layout.addWidget(self.list_widget)
        
        self.list_widget.itemClicked.connect(self._on_item_clicked)

    def update_results(self, assets):
        self.list_widget.clear()
        for asset in assets:
            self.list_widget.addItem(AssetListItem(asset))

    def _on_item_clicked(self, item):
        asset_id = item.data(Qt.UserRole)
        self.asset_selected.emit(asset_id)

class AutoMetadataPanel(QGroupBox):
    """Dynamically generated form based on MetadataViewModel."""
    def __init__(self):
        super().__init__("Metadata Inspector")
        self.layout = QVBoxLayout(self)
        
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.form_layout = QFormLayout(self.scroll_content)
        self.scroll.setWidget(self.scroll_content)
        
        self.layout.addWidget(self.scroll)

    def set_metadata_vm(self, vm: MetadataViewModel):
        # Clear existing
        while self.form_layout.count():
            child = self.form_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
        
        if not vm:
            self.form_layout.addRow(QLabel("No asset selected"))
            return

        for desc in vm.descriptors:
            label = QLabel(desc.display_name)
            
            if desc.is_relation:
                # Relationship Tag Cloud placeholder
                widget = QFrame()
                h_layout = QHBoxLayout(widget)
                h_layout.setContentsMargins(0, 0, 0, 0)
                
                tags_str = ", ".join([str(v) for v in desc.value]) if isinstance(desc.value, list) else str(desc.value)
                line = QLineEdit(tags_str)
                line.setReadOnly(True) 
                line.setStyleSheet("background-color: #f0f0f0; border: none; padding: 2px;")
                h_layout.addWidget(line)
                
                self.form_layout.addRow(label, widget)
            
            elif desc.is_stored:
                # Stored field with optional recompute button
                widget = QFrame()
                h_layout = QHBoxLayout(widget)
                h_layout.setContentsMargins(0, 0, 0, 0)
                
                edit = QLineEdit(str(desc.value))
                edit.setReadOnly(True) # Stored fields are typically derived
                h_layout.addWidget(edit, 4)
                
                recompute_btn = QPushButton("↺")
                recompute_btn.setToolTip(f"Recompute via {desc.handler}")
                recompute_btn.setFixedWidth(30)
                h_layout.addWidget(recompute_btn, 1)
                
                self.form_layout.addRow(label, widget)
            else:
                # Standard field
                edit = QLineEdit(str(desc.value))
                edit.textChanged.connect(lambda val, fn=desc.id: vm.update_property(fn, val))
                self.form_layout.addRow(label, edit)

# ─── Main Window ─────────────────────────────────────────────────────────────

class AssetExplorerWindow(QMainWindow):
    def __init__(self, vm: AssetExplorerViewModel):
        super().__init__()
        self.vm = vm
        self.setWindowTitle("BCor Asset Explorer")
        self.resize(1200, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        
        self.search_panel = SearchPanel()
        self.results_panel = ResultsPanel()
        self.metadata_panel = AutoMetadataPanel()
        
        main_layout.addWidget(self.search_panel, 1)
        main_layout.addWidget(self.results_panel, 2)
        main_layout.addWidget(self.metadata_panel, 1)
        
        # Wiring Signals
        self.search_panel.search_requested.connect(self._on_search)
        self.results_panel.asset_selected.connect(self.vm.select_asset)
        
        self.vm.results_updated.connect(self.results_panel.update_results)
        self.vm.asset_selected.connect(self._on_asset_selected)

    def _on_search(self, text):
        # We need an async task to run vm.search
        asyncio.create_task(self.vm.search(text))

    def _on_asset_selected(self, asset):
        self.metadata_panel.set_metadata_vm(self.vm.current_metadata)
