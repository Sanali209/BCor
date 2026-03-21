from __future__ import annotations
from typing import Any
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QComboBox, QLabel, QFileDialog, QToolBar, QStatusBar
)
from PySide6.QtGui import QAction
from ...infrastructure.graph_engine import GraphView, BCorGraphScene
from ...infrastructure.specialized_elements import ImageNode, TagNode, PinNode, RelationEdge
from ...use_cases import SearchRelatedImagesUseCase, UpdateRelationUseCase

class ImageGraphWidget(QWidget):
    def __init__(self, search_use_case: SearchRelatedImagesUseCase, update_use_case: UpdateRelationUseCase) -> None:
        super().__init__()
        self.search_use_case = search_use_case
        self.update_use_case = update_use_case
        self.scene = BCorGraphScene()
        self.view = GraphView(self.scene)
        self.init_ui()

    def init_ui(self) -> None:
        layout = QVBoxLayout(self)
        
        # Toolbar
        toolbar = QHBoxLayout()
        arrange_btn = QPushButton("Auto Arrange")
        arrange_btn.clicked.connect(lambda: self.scene.auto_arrange("spring"))
        toolbar.addWidget(arrange_btn)
        
        clear_btn = QPushButton("Clear Scene")
        clear_btn.clicked.connect(self.scene.clear_scene)
        toolbar.addWidget(clear_btn)
        
        toolbar.addStretch()
        layout.addLayout(toolbar)
        
        # Graph View
        layout.addWidget(self.view)

    async def add_image_node(self, file_record: Any) -> ImageNode:
        node = ImageNode(0, 0, 64, file_record)
        self.scene.addItem(node)
        return node
