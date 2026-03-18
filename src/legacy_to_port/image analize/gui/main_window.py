import os
import logging
from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QTabWidget, 
                             QFileDialog, QToolBar, QStatusBar, QMessageBox, QApplication,
                             QProgressBar, QLabel)
from PySide6.QtGui import QAction, QIcon
from PySide6.QtCore import Qt, QThread, Signal

from core.database import DatabaseManager
from core.image_scanner import scan_directory_parallel
from core.batch_engine import BatchEngine
from analytics.analytics_engine import AnalyticsEngine

from gui.widgets.dashboard_widget import DashboardWidget
from gui.widgets.batch_operations_widget import BatchOperationsWidget

logger = logging.getLogger(__name__)

class ScannerThread(QThread):
    finished_scan = Signal(int)  # count of new images
    progress_update = Signal(int, int, str)  # current, total, message
    
    def __init__(self, path, db: DatabaseManager):
        super().__init__()
        self.path = path
        self.db = db
        
    def run(self):
        from pathlib import Path
        from concurrent.futures import ProcessPoolExecutor, as_completed
        from core.image_scanner import get_supported_formats, scan_file
        
        directory = Path(self.path)
        if not directory.exists():
            self.finished_scan.emit(0)
            return
        
        # Phase 1: Traverse and find files
        self.progress_update.emit(0, 0, "Traversing directory structure...")
        image_extensions = set(get_supported_formats().keys())
        files_to_process = []
        
        for root, dirs, files in os.walk(directory):
            for file in files:
                _, ext = os.path.splitext(file)
                if ext.lower() in image_extensions:
                    files_to_process.append(os.path.join(root, file))
        
        total = len(files_to_process)
        self.progress_update.emit(0, total, f"Found {total} files. Scanning metadata...")
        
        if total == 0:
            self.finished_scan.emit(0)
            return
        
        # Phase 2: Process files with progress AND batch insert
        processed = 0
        chunk_size = 10000  # Process chunks
        BATCH_SIZE = 10000  # Insert trigger size
        
        batch_results = []
        total_inserted = 0
        
        with ProcessPoolExecutor(max_workers=os.cpu_count()) as executor:
            for i in range(0, total, chunk_size):
                chunk = files_to_process[i:i + chunk_size]
                future_to_file = {executor.submit(scan_file, f): f for f in chunk}
                
                for future in as_completed(future_to_file):
                    res = future.result()
                    if res:
                        batch_results.append(res)
                    processed += 1
                    
                    # Update progress
                    if processed % 100 == 0 or processed == total:
                        self.progress_update.emit(processed, total, f"Scanning & Inserting: {processed}/{total}")
                    
                    # Batch Insert Trigger
                    if len(batch_results) >= BATCH_SIZE:
                        self.db.bulk_insert_images(batch_results)
                        batch_results = [] # Clear memory
        
        # Phase 3: Insert remaining items
        if batch_results:
            self.progress_update.emit(total, total, "Inserting remaining records...")
            self.db.bulk_insert_images(batch_results)
            
        self.progress_update.emit(total, total, "Complete!")
        self.finished_scan.emit(processed)

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Astral Mariner - Image Analytics & Batch Processor")
        self.resize(1200, 800)
        
        # Core Components
        self.db = DatabaseManager() # Initialize DB
        self.analytics = AnalyticsEngine(self.db)
        self.batch_engine = BatchEngine()
        
        self.init_ui()
        self.apply_theme()

    def init_ui(self):
        # Menu & Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        action_open = QAction("Open Folder", self)
        action_open.setStatusTip("Scan a directory for images")
        action_open.triggered.connect(self.select_folder)
        toolbar.addAction(action_open)
        
        self.action_rescan = QAction("Rescan", self)
        self.action_rescan.setStatusTip("Rescan the last opened folder")
        self.action_rescan.triggered.connect(self.rescan_folder)
        self.action_rescan.setEnabled(False)  # Disabled until a folder is scanned
        toolbar.addAction(self.action_rescan)
        
        action_refresh = QAction("Refresh Analysis", self)
        action_refresh.triggered.connect(self.refresh_dashboard)
        toolbar.addAction(action_refresh)
        
        # Central Widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Tabs
        self.dashboard_tab = DashboardWidget(self.analytics)
        self.tabs.addTab(self.dashboard_tab, "Dashboard")
        
        self.batch_tab = BatchOperationsWidget(self.batch_engine, self.db)
        self.tabs.addTab(self.batch_tab, "Batch Operations")
        
        # Status Bar with Progress
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        
        self.scan_progress = QProgressBar()
        self.scan_progress.setMaximumWidth(200)
        self.scan_progress.setVisible(False)
        self.status.addPermanentWidget(self.scan_progress)
        
        self.status_label = QLabel("Ready. Select a folder to begin.")
        self.status.addWidget(self.status_label)
        
        # Track last scanned folder
        self.last_folder = None
        
        # Refresh on start (show existing DB data)
        self.refresh_dashboard()

    def apply_theme(self):
        # High-Contrast Dark Theme
        self.setStyleSheet("""
            /* Global */
            QMainWindow { background-color: #1a1a2e; color: #ffffff; }
            QWidget { color: #ffffff; }
            QLabel { color: #ffffff; }
            
            /* Tabs */
            QTabWidget::pane { border: 1px solid #16213e; background: #1a1a2e; }
            QTabBar::tab { 
                background: #16213e; 
                color: #e0e0e0; 
                padding: 10px 20px; 
                border: 1px solid #0f3460;
                border-bottom: none;
            }
            QTabBar::tab:selected { 
                background: #0f3460; 
                color: #ffffff; 
                font-weight: bold;
            }
            QTabBar::tab:hover { background: #1f4068; }
            
            /* Toolbar */
            QToolBar { 
                background: #16213e; 
                border-bottom: 2px solid #0f3460; 
                spacing: 10px;
                padding: 5px;
            }
            QToolBar QToolButton { 
                color: #ffffff; 
                background: #0f3460; 
                padding: 8px 16px; 
                border-radius: 4px;
                font-weight: bold;
            }
            QToolBar QToolButton:hover { background: #e94560; }
            
            /* Status Bar */
            QStatusBar { 
                background: #16213e; 
                color: #e0e0e0; 
                border-top: 2px solid #0f3460;
                padding: 5px;
            }
            
            /* Inputs */
            QLineEdit, QSpinBox, QComboBox {
                background: #16213e;
                color: #ffffff;
                border: 1px solid #0f3460;
                padding: 5px;
                border-radius: 4px;
            }
            QLineEdit:focus, QSpinBox:focus, QComboBox:focus {
                border: 1px solid #e94560;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background: #16213e;
                color: #ffffff;
                selection-background-color: #0f3460;
            }
            
            /* Buttons */
            QPushButton {
                background: #0f3460;
                color: #ffffff;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }
            QPushButton:hover { background: #1f4068; }
            QPushButton:pressed { background: #e94560; }
            
            /* Lists */
            QListWidget {
                background: #16213e;
                color: #ffffff;
                border: 1px solid #0f3460;
            }
            QListWidget::item:selected { background: #0f3460; }
            
            /* Text Areas */
            QTextEdit {
                background: #0d1117;
                color: #58a6ff;
                border: 1px solid #0f3460;
                font-family: 'Consolas', monospace;
            }
            
            /* Checkboxes */
            QCheckBox { color: #ffffff; }
            QCheckBox::indicator { 
                width: 16px; 
                height: 16px; 
                background: #16213e;
                border: 1px solid #0f3460;
            }
            QCheckBox::indicator:checked { background: #e94560; }
            
            /* Group Boxes */
            QGroupBox {
                color: #ffffff;
                border: 1px solid #0f3460;
                border-radius: 4px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                color: #ffffff;
                subcontrol-origin: margin;
                left: 10px;
            }
            
            /* Progress Bar */
            QProgressBar {
                background: #16213e;
                border: 1px solid #0f3460;
                border-radius: 4px;
                text-align: center;
                color: #ffffff;
            }
            QProgressBar::chunk { background: #e94560; }
            
            /* Scroll Areas */
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical {
                background: #16213e;
                width: 12px;
            }
            QScrollBar::handle:vertical {
                background: #0f3460;
                border-radius: 6px;
            }
        """)

    def select_folder(self):
        folder = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        if folder:
            self.start_scan(folder)

    def start_scan(self, folder):
        self.last_folder = folder  # Store for rescan
        self.action_rescan.setEnabled(True)  # Enable rescan button
        self.status_label.setText(f"Scanning {folder}...")
        
        # Show progress bar
        self.scan_progress.setVisible(True)
        self.scan_progress.setValue(0)
        
        # Clear existing data for fresh scan
        self.db.clear_database()
        
        self.scanner_thread = ScannerThread(folder, self.db)
        self.scanner_thread.progress_update.connect(self.on_scan_progress)
        self.scanner_thread.finished_scan.connect(self.on_scan_finished)
        self.scanner_thread.start()

    def rescan_folder(self):
        """Rescan the last opened folder."""
        if self.last_folder:
            self.start_scan(self.last_folder)

    def on_scan_progress(self, current, total, message):
        """Handle progress updates from scanner."""
        self.status_label.setText(message)
        if total > 0:
            percent = int((current / total) * 100)
            self.scan_progress.setValue(percent)
        else:
            self.scan_progress.setValue(0)

    def on_scan_finished(self, count):
        self.scan_progress.setVisible(False)
        self.status_label.setText(f"Scan Complete. Found {count} images.")
        self.refresh_dashboard()
        
    def refresh_dashboard(self):
        self.dashboard_tab.refresh_data()

