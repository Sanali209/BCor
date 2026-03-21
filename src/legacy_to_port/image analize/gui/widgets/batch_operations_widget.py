import logging
import os

from core.batch_engine import BatchEngine
from core.database import DatabaseManager
from core.image_scanner import scan_file
from core.preset_manager import PresetManager
from gui.widgets.rule_editor_widget import RuleEditorWidget
from PySide6.QtCore import QObject, Qt, QThread, Signal, Slot
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSplitter,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

logger = logging.getLogger(__name__)


class BatchWorker(QObject):
    """Worker to run batch engine in background thread."""

    progress = Signal(int)
    log_message = Signal(str)
    finished = Signal()

    def __init__(self, engine, db, images, rules, dry_run=False):
        super().__init__()
        self.engine = engine
        self.db = db
        self.images = images
        self.rules = rules
        self.dry_run = dry_run
        self._stop_requested = False

    def run(self):
        total = len(self.images)
        if total == 0:
            self.finished.emit()
            return

        self.log_message.emit(f"Starting batch process on {total} images...")
        if self.dry_run:
            self.log_message.emit("--- DRY RUN MODE (No changes will be applied) ---")

        processed = 0

        for img in self.images:
            if self._stop_requested:
                self.log_message.emit("Batch cancelled by user.")
                break

            # Execute logic for single image
            triggered = False
            for rule in self.rules:
                if rule.condition.evaluate(img):
                    res = rule.action.execute(img, dry_run=self.dry_run)
                    if res.success:
                        self.log_message.emit(f"[OK] {res.original_path} -> {res.action_taken}")
                        if res.new_path:
                            self.log_message.emit(f"     New file: {res.new_path}")

                        # Record Savings
                        if not self.dry_run and res.saved_bytes > 0:
                            act_type = "UNKNOWN"
                            if "DELETE" in res.action_taken:
                                act_type = "DELETE"
                            elif "CONVERT" in res.action_taken:
                                act_type = "CONVERT"
                            elif "SCALE" in res.action_taken:
                                act_type = "SCALE"

                            self.db.record_saving(act_type, res.saved_bytes, res.original_path)
                            self.log_message.emit(f"     Saved: {res.saved_bytes / 1024:.1f} KB")

                        # --- Sync Database ---
                        if not os.path.exists(res.original_path):
                            self.db.delete_image(res.original_path)

                        if res.new_path and os.path.exists(res.new_path):
                            data = scan_file(res.new_path)
                            if data:
                                self.db.upsert_image(data)
                        elif res.action_taken == "SCALE" and os.path.exists(res.original_path):
                            data = scan_file(res.original_path)
                            if data:
                                self.db.upsert_image(data)

                    else:
                        self.log_message.emit(f"[ERR] {res.original_path}: {res.error_message}")

                    if res.action_taken == "DELETE":
                        break
                    triggered = True

            processed += 1
            if processed % 10 == 0:
                self.progress.emit(int(processed / total * 100))

        self.progress.emit(100)
        self.log_message.emit("Batch processing complete.")
        self.finished.emit()

    def stop(self):
        self._stop_requested = True


class BatchOperationsWidget(QWidget):
    def __init__(self, batch_engine: BatchEngine, db_manager: DatabaseManager, parent=None):
        super().__init__(parent)
        self.engine = batch_engine
        self.db = db_manager
        self.preset_manager = PresetManager()
        self.worker = None
        self.worker_thread = None
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        splitter = QSplitter(Qt.Vertical)

        # Top: Rule Editor
        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        top_layout.setContentsMargins(0, 0, 0, 0)

        # Preset Controls
        preset_layout = QHBoxLayout()
        preset_layout.addWidget(QLabel("Preset:"))
        self.combo_presets = QComboBox()
        self.combo_presets.addItem("Custom (Unsaved)")
        self.combo_presets.addItems(self.preset_manager.get_preset_names())
        self.combo_presets.currentTextChanged.connect(self.load_preset)
        preset_layout.addWidget(self.combo_presets)

        btn_save_preset = QPushButton("Save Preset")
        btn_save_preset.clicked.connect(self.save_preset)
        preset_layout.addWidget(btn_save_preset)

        btn_del_preset = QPushButton("Delete")
        btn_del_preset.clicked.connect(self.delete_preset)
        preset_layout.addWidget(btn_del_preset)

        top_layout.addLayout(preset_layout)

        self.rule_editor = RuleEditorWidget()
        top_layout.addWidget(self.rule_editor)

        # Control Bar
        control_layout = QHBoxLayout()
        self.chk_dry_run = QCheckBox("Dry Run (Simulate only)")
        self.chk_dry_run.setChecked(True)
        control_layout.addWidget(self.chk_dry_run)

        self.btn_run = QPushButton("Run Batch Process")
        self.btn_run.setStyleSheet("background-color: #e15759; color: white; padding: 8px; font-weight: bold;")
        self.btn_run.clicked.connect(self.start_batch)
        control_layout.addWidget(self.btn_run)

        self.btn_cancel = QPushButton("Cancel")
        self.btn_cancel.setStyleSheet("background-color: #ff6b35; color: white; padding: 8px; font-weight: bold;")
        self.btn_cancel.clicked.connect(self.cancel_batch)
        self.btn_cancel.setVisible(False)
        control_layout.addWidget(self.btn_cancel)

        top_layout.addLayout(control_layout)
        splitter.addWidget(top_widget)

        # Bottom: Logs & Progress
        bottom_widget = QWidget()
        bottom_layout = QVBoxLayout(bottom_widget)
        bottom_layout.setContentsMargins(0, 0, 0, 0)

        self.progress_bar = QProgressBar()
        bottom_layout.addWidget(self.progress_bar)

        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        self.log_area.setStyleSheet("background-color: #1e1e1e; color: #aaaaaa; font-family: Consolas;")
        bottom_layout.addWidget(self.log_area)

        splitter.addWidget(bottom_widget)

        main_layout.addWidget(splitter)

    def load_preset(self, name):
        if name == "Custom (Unsaved)":
            return

        rules = self.preset_manager.get_rules(name)
        if rules:
            self.rule_editor.set_rules(rules)
            self.log(f"Loaded preset: {name}")

    def save_preset(self):
        name, ok = QInputDialog.getText(self, "Save Preset", "Preset Name:")
        if ok and name:
            rules = self.rule_editor.rules
            if not rules:
                QMessageBox.warning(self, "Error", "Cannot save empty ruleset.")
                return

            self.preset_manager.add_preset(name, rules)
            self.refresh_presets()
            self.combo_presets.setCurrentText(name)
            self.log(f"Saved preset: {name}")

    def delete_preset(self):
        name = self.combo_presets.currentText()
        if name == "Custom (Unsaved)":
            return

        confirm = QMessageBox.question(self, "Confirm Delete", f"Delete preset '{name}'?")
        if confirm == QMessageBox.Yes:
            self.preset_manager.remove_preset(name)
            self.refresh_presets()
            self.log(f"Deleted preset: {name}")

    def refresh_presets(self):
        current = self.combo_presets.currentText()
        self.combo_presets.blockSignals(True)
        self.combo_presets.clear()
        self.combo_presets.addItem("Custom (Unsaved)")
        self.combo_presets.addItems(self.preset_manager.get_preset_names())

        if current in self.preset_manager.get_preset_names():
            self.combo_presets.setCurrentText(current)
        else:
            self.combo_presets.setCurrentIndex(0)

        self.combo_presets.blockSignals(False)

    def start_batch(self):
        rules = self.rule_editor.rules
        if not rules:
            self.log("No rules defined. Add a rule first.")
            return

        self.log("Fetching images from database...")
        conn = self.db.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM images")
        rows = cursor.fetchall()
        images = [dict(row) for row in rows]
        conn.close()

        self.log(f"Loaded {len(images)} images to process.")

        # Create thread and worker using QThread pattern
        self.worker_thread = QThread()
        self.worker = BatchWorker(self.engine, self.db, images, rules, self.chk_dry_run.isChecked())
        self.worker.moveToThread(self.worker_thread)

        # Connect signals
        self.worker_thread.started.connect(self.worker.run)
        self.worker.log_message.connect(self.log)
        self.worker.progress.connect(self.progress_bar.setValue)
        self.worker.finished.connect(self.on_finished)
        self.worker.finished.connect(self.worker_thread.quit)
        self.worker.finished.connect(self.worker.deleteLater)
        self.worker_thread.finished.connect(self.worker_thread.deleteLater)

        self.btn_run.setEnabled(False)
        self.btn_cancel.setVisible(True)
        self.rule_editor.setEnabled(False)
        self.worker_thread.start()

    def log(self, msg):
        self.log_area.append(msg)

    def cancel_batch(self):
        """Cancel the running batch process."""
        if self.worker:
            self.log("Cancelling batch process...")
            self.worker.stop()

    @Slot()
    def on_finished(self):
        self.btn_run.setEnabled(True)
        self.btn_cancel.setVisible(False)
        self.rule_editor.setEnabled(True)
        self.log("--- Done ---")
