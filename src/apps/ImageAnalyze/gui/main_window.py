from __future__ import annotations

import asyncio

from PySide6.QtGui import QAction
from PySide6.QtWidgets import QFileDialog, QLabel, QMainWindow, QProgressBar, QStatusBar, QTabWidget, QToolBar

from ..use_cases import ExecuteBatchRulesUseCase, GetCollectionStatsUseCase, ScanDirectoryUseCase
from .widgets.batch_operations_widget import BatchOperationsWidget
from .widgets.dashboard_widget import DashboardWidget


class MainWindow(QMainWindow):
    def __init__(
        self, 
        scan_use_case: ScanDirectoryUseCase,
        stats_use_case: GetCollectionStatsUseCase,
        batch_use_case: ExecuteBatchRulesUseCase
    ) -> None:
        super().__init__()
        self.scan_use_case = scan_use_case
        self.stats_use_case = stats_use_case
        self.batch_use_case = batch_use_case
        
        self.setWindowTitle("BCor - Image Analysis Hub")
        self.resize(1200, 800)
        self.init_ui()

    def init_ui(self) -> None:
        # Toolbar
        toolbar = QToolBar("Main Toolbar")
        self.addToolBar(toolbar)
        
        scan_action = QAction("Scan Folder", self)
        scan_action.triggered.connect(self.select_folder)
        toolbar.addAction(scan_action)
        
        # Tabs
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        self.dashboard = DashboardWidget(self.stats_use_case)
        self.tabs.addTab(self.dashboard, "Dashboard")
        
        self.batch_ops = BatchOperationsWidget(self.batch_use_case)
        self.tabs.addTab(self.batch_ops, "Batch Operations")
        
        # Status Bar
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        self.status_bar.addPermanentWidget(self.progress_bar)
        
        self.status_label = QLabel("Ready")
        self.status_bar.addWidget(self.status_label)

    def select_folder(self) -> None:
        folder = QFileDialog.getExistingDirectory(self, "Select Image Directory")
        if folder:
            # We need to run the async use case in the event loop
            asyncio.create_task(self.run_scan(folder))

    async def run_scan(self, folder: str) -> None:
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        async def update_progress(current: int, total: int, msg: str) -> None:
            self.status_label.setText(msg)
            if total > 0:
                self.progress_bar.setValue(int((current / total) * 100))
        
        try:
            count = await self.scan_use_case.execute(folder, progress_callback=update_progress)
            self.status_label.setText(f"Scan complete. Found {count} images.")
            self.dashboard.refresh_data()
        except Exception as e:
            self.status_label.setText(f"Scan failed: {str(e)}")
        finally:
            self.progress_bar.setVisible(False)
