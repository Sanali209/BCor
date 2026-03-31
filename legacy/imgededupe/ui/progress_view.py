from PySide6.QtWidgets import QWidget, QVBoxLayout, QProgressBar, QLabel, QPushButton, QTextEdit
from PySide6.QtCore import Signal
from PySide6.QtGui import QTextCursor
# from src.apps.experemental.imgededupe.core.scanner import ScanWorker
from src.apps.experemental.imgededupe.core.logger import qt_log_handler
from loguru import logger

class ProgressWidget(QWidget):
    scan_finished = Signal(object)

    def __init__(self, session, db_manager, adapter):
        super().__init__()
        self.session = session
        self.db = db_manager
        self.layout = QVBoxLayout(self)
        
        self.status_label = QLabel("Initializing...")
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: Consolas;")
        
        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.clicked.connect(self.cancel_scan)
        
        self.layout.addWidget(self.status_label)
        self.layout.addWidget(self.progress_bar)
        self.layout.addWidget(self.log_view)
        self.layout.addWidget(self.btn_cancel)
        
        # Connect Logger
        qt_log_handler.log_signal.connect(self.append_log)
        
        self.adapter = adapter
        
        # Connect Adapter Signals
        self.adapter.scan_started.connect(self.on_bus_scan_started)
        self.adapter.scan_completed.connect(self.on_bus_scan_completed)
        self.adapter.dedupe_started.connect(self.on_bus_dedupe_started)
        
        self.worker = None # No longer used

    def append_log(self, text):
        self.log_view.append(text)
        # Autoscroll
        cursor = self.log_view.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.log_view.setTextCursor(cursor)

    def on_bus_scan_started(self, roots):
        self.status_label.setText(f"Scanning: {', '.join(roots)}")
        self.progress_bar.setRange(0, 0) # Indeterminate until count known
        self.btn_cancel.setEnabled(True)

    def on_bus_scan_completed(self, count):
        self.status_label.setText(f"Scan complete: {count} files found. Starting deduplication...")
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(100)
        # We no longer emit scan_finished here because deduplication starts automatically.
        # MainWindow handles switching to results via on_bus_duplicates_found.

    def on_bus_dedupe_started(self, engine):
        self.status_label.setText(f"Deduplicating with {engine}...")
        self.progress_bar.setRange(0, 0)

    def start_scan(self):
        # This was legacy direct call. Now handled via MessageBus/Adapter.
        pass

    def update_progress(self, current, total):
        self.progress_bar.setMaximum(total)
        self.progress_bar.setValue(current)
        self.status_label.setText(f"Processed {current}/{total}")

    def update_file_label(self, path):
        # Optional: showing fast changing text might lag UI
        pass

    def on_results_ready(self, results):
        self.scan_results = results

    def on_finished(self):
        self.worker.deleteLater()
        self.worker = None
        results = getattr(self, 'scan_results', None)
        self.scan_finished.emit(results)

    def cancel_scan(self):
        if self.worker:
            self.status_label.setText("Stopping...")
            self.btn_cancel.setEnabled(False)
            self.worker.stop()
