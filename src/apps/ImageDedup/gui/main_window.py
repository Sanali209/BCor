from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.apps.ImageDedup.domain.interfaces.i_image_differ import IThumbnailCache
    from src.apps.ImageDedup.domain.project import ImageDedupProject
    from src.core.messagebus import MessageBus

from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QScrollArea,
    QSlider,
    QVBoxLayout,
    QWidget,
)


class ImageDedupMainWindow(QMainWindow):
    """Modern Main Window for ImageDedup application."""
    group_list_widget: Any

    def __init__(self, project_aggregate: ImageDedupProject, bus: MessageBus | None = None) -> None:
        super().__init__()
        self.project = project_aggregate
        self.bus = bus
        self._setup_ui()
        self._apply_styles()

    def _setup_ui(self) -> None:
        """Build the UI structure manually for maximum control and BCor consistency."""
        self.setWindowTitle("BCor - Image Dedup")
        self.setMinimumSize(1200, 800)

        # Central Widget & Main Layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setSpacing(0)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # 1. Sidebar (Control Panel)
        sidebar = QFrame()
        sidebar.setFixedWidth(320)
        sidebar.setObjectName("sidebar")
        main_layout.addWidget(sidebar)

        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(20, 20, 20, 20)
        sidebar_layout.setSpacing(15)

        # --- Project Section ---
        project_group = QGroupBox("Project")
        project_layout = QVBoxLayout(project_group)
        
        self.project_name_input = QLineEdit(self.project.project_id if hasattr(self.project, 'project_id') else "")
        self.project_name_input.setPlaceholderText("Project Name...")
        project_layout.addWidget(QLabel("Name:"))
        project_layout.addWidget(self.project_name_input)

        project_btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Save Project")
        self.load_btn = QPushButton("Load Project")
        project_btn_layout.addWidget(self.save_btn)
        project_btn_layout.addWidget(self.load_btn)
        project_layout.addLayout(project_btn_layout)
        sidebar_layout.addWidget(project_group)

        # --- Duplicates Section ---
        dedup_group = QGroupBox("Duplicate Search")
        dedup_layout = QVBoxLayout(dedup_group)
        
        dedup_layout.addWidget(QLabel("Similarity Threshold:"))
        self.similarity_slider = QSlider(Qt.Orientation.Horizontal)
        self.similarity_slider.setRange(0, 100)
        self.similarity_slider.setValue(95)
        dedup_layout.addWidget(self.similarity_slider)

        self.find_dubs_btn = QPushButton("Find Duplicates")
        self.find_dubs_btn.setObjectName("primaryButton")
        self.find_dubs_btn.setFixedHeight(40)
        dedup_layout.addWidget(self.find_dubs_btn)
        sidebar_layout.addWidget(dedup_group)

        # --- Actions Section ---
        actions_group = QGroupBox("Actions")
        actions_layout = QVBoxLayout(actions_group)
        self.move_to_folder_btn = QPushButton("Move to Folder")
        self.delete_from_hdd_btn = QPushButton("Delete from HDD")
        self.delete_from_hdd_btn.setObjectName("dangerButton")
        self.tag_selected_btn = QPushButton("Tag Selected Images")
        self.tag_selected_btn.setObjectName("primaryButton")
        actions_layout.addWidget(self.move_to_folder_btn)
        actions_layout.addWidget(self.delete_from_hdd_btn)
        actions_layout.addWidget(self.tag_selected_btn)
        sidebar_layout.addWidget(actions_group)

        sidebar_layout.addStretch()

        # 2. Main Content Area (Group List)
        content_area = QWidget()
        main_layout.addWidget(content_area)
        content_layout = QVBoxLayout(content_area)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # --- Header ---
        header = QFrame()
        header.setFixedHeight(60)
        header.setObjectName("header")
        header_layout = QHBoxLayout(header)
        header_title = QLabel("Image Groups")
        header_title.setStyleSheet("font-size: 18px; font-weight: bold;")
        header_layout.addWidget(header_title)
        header_layout.addStretch()
        content_layout.addWidget(header)

        # --- Group List (Scrollable) ---
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self.group_container = QWidget()
        self.group_layout = QVBoxLayout(self.group_container)
        self.group_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        self.scroll_area.setWidget(self.group_container)
        content_layout.addWidget(self.scroll_area)

        # --- Footer (Pagination / Status) ---
        footer = QFrame()
        footer.setFixedHeight(40)
        footer_layout = QHBoxLayout(footer)
        self.status_label = QLabel("Ready")
        footer_layout.addWidget(self.status_label)
        footer_layout.addStretch()
        self.page_label = QLabel("Page 1 / 1")
        footer_layout.addWidget(self.page_label)
        content_layout.addWidget(footer)

        # Connections
        self.find_dubs_btn.clicked.connect(self._on_find_duplicates)
        self.tag_selected_btn.clicked.connect(self._on_tag_images)

    def _apply_styles(self) -> None:
        """Apply modern QSS styles."""
        self.setStyleSheet("""
            QMainWindow {
                background-color: #121212;
                color: #e0e0e0;
            }
            #sidebar {
                background-color: #1e1e1e;
                border-right: 1px solid #333333;
            }
            #header {
                background-color: #1e1e1e;
                border-bottom: 1px solid #333333;
            }
            QGroupBox {
                border: 1px solid #333333;
                border-radius: 8px;
                margin-top: 20px;
                font-weight: bold;
                color: #bb86fc;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #333333;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 8px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #444444;
            }
            #primaryButton {
                background-color: #6200ee;
            }
            #primaryButton:hover {
                background-color: #3700b3;
            }
            #dangerButton {
                background-color: #cf6679;
                color: #000000;
            }
            #dangerButton:hover {
                background-color: #b00020;
            }
            QLineEdit {
                background-color: #2c2c2c;
                border: 1px solid #333333;
                border-radius: 4px;
                padding: 6px;
                color: white;
            }
            QScrollArea {
                background-color: #121212;
            }
            QLabel {
                color: #e0e0e0;
            }
        """)

    def update_status(self, message: str) -> None:
        """Update the status bar message."""
        self.status_label.setText(message)

    def _on_find_duplicates(self) -> None:
        if not self.bus:
            return
        from src.apps.ImageDedup.messages import FindDuplicatesCommand
        cmd = FindDuplicatesCommand(
            project_id=self.project.project_id,
            similarity_threshold=self.similarity_slider.value() / 100.0
        )
        self.update_status("Searching for duplicates...")
        import asyncio
        asyncio.create_task(self.bus.dispatch(cmd))

    def _on_tag_images(self) -> None:
        if not self.bus:
            return
            
        selected_paths = []
        for group in self.project.groups:
            for item in group.items:
                if item.selected:
                    selected_paths.append(item.path)
        
        if not selected_paths:
            self.update_status("No images selected for tagging.")
            return

        from src.apps.ImageDedup.messages import TagImagesCommand
        cmd = TagImagesCommand(
            project_id=self.project.project_id,
            image_paths=selected_paths
        )
        self.update_status(f"Tagging {len(selected_paths)} images...")
        import asyncio
        asyncio.create_task(self.bus.dispatch(cmd))
        self.update_status(f"Tagged {len(selected_paths)} images successfully.")


def run_image_dedup_app(bus: MessageBus, thumbnail_cache: IThumbnailCache, project: ImageDedupProject) -> None:
    """Entry point to start the ImageDedup PySide6 application."""
    import sys

    app = QApplication.instance()
    if not app:
        app = QApplication(sys.argv)
    
    QApplication.setStyle("Fusion")
    
    window = ImageDedupMainWindow(project_aggregate=project, bus=bus)
    # Inject dependencies into the list widget (will be implemented in setup_ui)
    from src.apps.ImageDedup.gui.widgets.group_list import GroupListWidget
    group_list = GroupListWidget(groups=project.groups, thumbnail_cache=thumbnail_cache)
    window.group_layout.addWidget(group_list)
    window.group_list_widget = group_list

    window.show()
    app.exec()
