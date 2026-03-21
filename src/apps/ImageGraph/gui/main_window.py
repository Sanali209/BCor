from __future__ import annotations
from PySide6.QtWidgets import QMainWindow, QTabWidget, QToolBar, QStatusBar, QLabel
from PySide6.QtGui import QAction
from .widgets.graph_widget import ImageGraphWidget

class ImageGraphMainWindow(QMainWindow):
    def __init__(self, graph_widget: ImageGraphWidget) -> None:
        super().__init__()
        self.setWindowTitle("BCor - Image Graph")
        self.resize(1200, 800)
        self.setCentralWidget(graph_widget)
        
        self.init_menu()
        self.init_status_bar()

    def init_menu(self) -> None:
        menu_bar = self.menuBar()
        file_menu = menu_bar.addMenu("&File")
        
        exit_action = QAction("E&xit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

    def init_status_bar(self) -> None:
        self.setStatusBar(QStatusBar())
        self.statusBar().showMessage("Ready")
