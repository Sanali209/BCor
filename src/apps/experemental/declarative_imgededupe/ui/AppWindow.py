import asyncio
from typing import Optional
from PySide6.QtWidgets import (
    QMainWindow, QStackedWidget, QVBoxLayout, QWidget, QStatusBar, QToolBar
)
from PySide6.QtGui import QAction, QIcon
from src.modules.assets.ui.widgets import AGMTableView
from ..models import DedupeSession
from .SessionSetup import SessionSetupWidget
from .ClusterExplorer import ClusterExplorerWidget
from .PairwiseView import PairwiseWidget

class AppWindow(QMainWindow):
    """
    Main application window for the declarative imgededupe app.
    Uses a modern dark aesthetic and a reactive, metadata-driven UI.
    """
    def __init__(self, bus):
        super().__init__()
        self.bus = bus
        self.setWindowTitle("BCor Declarative Deduper")
        self.resize(1100, 800)
        
        # Apply modern dark theme
        self.setStyleSheet("""
            QMainWindow { background-color: #121212; color: white; }
            QStatusBar { background-color: #1e1e1e; color: #888; }
            QToolBar { background-color: #1e1e1e; border: none; }
            QAction { color: white; }
            QWidget { color: white; }
        """)

        # Central Stack
        self.stack = QStackedWidget()
        self.setCentralWidget(self.stack)
        
        # Components
        self.setup_view = SessionSetupWidget()
        self.explorer_view = ClusterExplorerWidget()
        self.pairwise_view = PairwiseWidget()
        
        self.stack.addWidget(self.setup_view)
        self.stack.addWidget(self.explorer_view)
        self.stack.addWidget(self.pairwise_view)
        
        # Navigation
        self.create_toolbar()
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage("System Ready.")

    def create_toolbar(self):
        toolbar = QToolBar("Navigation")
        self.addToolBar(toolbar)
        
        setup_act = QAction("Setup", self)
        setup_act.triggered.connect(lambda: self.stack.setCurrentIndex(0))
        toolbar.addAction(setup_act)
        
        explore_act = QAction("Explore Clusters", self)
        explore_act.triggered.connect(lambda: self.stack.setCurrentIndex(1))
        toolbar.addAction(explore_act)
        
        self.undo_act = QAction("Undo (Ctrl+Z)", self)
        self.undo_act.setShortcut("Ctrl+Z")
        toolbar.addAction(self.undo_act)
        
    def show_progress(self, message: str):
        self.statusBar.showMessage(message)
