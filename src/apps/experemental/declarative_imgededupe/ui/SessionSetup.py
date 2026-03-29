from typing import Optional, List
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QFileDialog, QDoubleSpinBox, QListWidget, QGroupBox, QComboBox
)
from PySide6.QtCore import Signal, Qt
from ..settings import SettingsManager, DedupeUISettings

class SessionSetupWidget(QWidget):
    """
    Widget for configuring a deduplication session.
    Allows user to select multiple root folders and set similarity thresholds.
    """
    start_scan = Signal(list, float, str)  # roots, threshold, engine

    def __init__(self, parent: Optional[QWidget] = None):
        super().__init__(parent)
        self.settings_manager = SettingsManager()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(40, 40, 40, 40)
        layout.setSpacing(20)

        # Title
        title = QLabel("New Deduplication Session")
        title.setStyleSheet("font-size: 24px; font-weight: bold; color: #4fc3f7;")
        layout.addWidget(title)

        # Folder Selection
        folder_group = QGroupBox("Scan Locations")
        group_layout = QVBoxLayout(folder_group)
        
        self.root_list = QListWidget()
        self.root_list.setMinimumHeight(150)
        group_layout.addWidget(self.root_list)
        
        btn_layout = QHBoxLayout()
        self.add_btn = QPushButton("Add Folder")
        self.add_btn.clicked.connect(self.on_add_folder)
        btn_layout.addWidget(self.add_btn)
        
        self.clear_btn = QPushButton("Clear")
        self.clear_btn.clicked.connect(self.root_list.clear)
        btn_layout.addWidget(self.clear_btn)
        group_layout.addLayout(btn_layout)
        
        layout.addWidget(folder_group)

        # Thresholds
        threshold_group = QGroupBox("Similarity Settings")
        thresh_layout = QHBoxLayout(threshold_group)
        
        thresh_layout.addWidget(QLabel("Precision Threshold:"))
        self.threshold_spin = QDoubleSpinBox()
        self.threshold_spin.setRange(0.0, 1.0)
        self.threshold_spin.setValue(0.85)
        self.threshold_spin.setSingleStep(0.05)
        thresh_layout.addWidget(self.threshold_spin)
        
        thresh_layout.addWidget(QLabel("Engine:"))
        self.engine_combo = QComboBox()
        self.engine_combo.addItems(["phash", "clip", "blip"])
        self.engine_combo.currentTextChanged.connect(self.on_engine_changed)
        thresh_layout.addWidget(self.engine_combo)
        
        layout.addWidget(threshold_group)

        # Action
        self.start_btn = QPushButton("Launch BCor Analysis")
        self.start_btn.setFixedHeight(50)
        self.start_btn.setStyleSheet("""
            QPushButton { 
                background-color: #0277bd; 
                font-size: 16px; 
                font-weight: bold; 
                border-radius: 4px;
            }
            QPushButton:hover { background-color: #0288d1; }
        """)
        self.start_btn.clicked.connect(self.on_start)
        layout.addWidget(self.start_btn)
        
        layout.addStretch()
        self.load_settings()

    def load_settings(self):
        """Loads and applies persisted settings."""
        self.settings = self.settings_manager.load()
        for root in self.settings.root_folders:
            self.root_list.addItem(root)
        
        idx = self.engine_combo.findText(self.settings.engine)
        if idx >= 0:
            self.engine_combo.setCurrentIndex(idx)
        
        # This will trigger on_engine_changed and set the threshold from settings
        self.on_engine_changed(self.engine_combo.currentText())

    def on_engine_changed(self, engine: str):
        """Adjusts threshold range and default value based on engine."""
        if engine == "phash":
            self.threshold_spin.setRange(0, 64)
            self.threshold_spin.setDecimals(0)
            self.threshold_spin.setSingleStep(1)
        else:
            self.threshold_spin.setRange(0.0, 1.0)
            self.threshold_spin.setDecimals(2)
            self.threshold_spin.setSingleStep(0.05)
        
        # Set value from settings for this engine
        if hasattr(self, 'settings'):
            val = self.settings.thresholds.get(engine, 0.85 if engine != "phash" else 10.0)
            self.threshold_spin.setValue(val)

    def on_add_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Folder to Scan")
        if folder:
            self.root_list.addItem(folder)

    def on_start(self):
        roots = [self.root_list.item(i).text() for i in range(self.root_list.count())]
        if not roots:
            return
        
        engine = self.engine_combo.currentText()
        threshold = self.threshold_spin.value()

        # Update and save settings
        self.settings.root_folders = roots
        self.settings.engine = engine
        self.settings.thresholds[engine] = threshold
        self.settings_manager.save(self.settings)
        
        self.start_scan.emit(roots, threshold, engine)
