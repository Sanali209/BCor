import sys
import os
import json
import asyncio
import qasync
from loguru import logger
from typing import Any, List, Optional, Dict, Type
from unittest.mock import MagicMock 

# Ensure project root is in path for 'src' imports
sys.path.append(os.getcwd())

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QHBoxLayout, QVBoxLayout, 
    QPushButton, QLabel, QFrame, QLineEdit, QListWidget, QListWidgetItem,
    QScrollArea, QFormLayout, QGroupBox, QTabWidget, QTableWidget, 
    QTableWidgetItem, QHeaderView, QFileDialog
)
from PySide6 import QtWidgets as QtW
from PySide6.QtCore import Qt, Signal, Slot, QRect, QPoint, QSize, QProcess, QObject

from src.core.system import System
from src.core.loop_policies import WindowsLoopManager
from src.modules.agm.module import AGMModule
from src.modules.assets.module import AssetsModule
from src.apps.asset_explorer.module import AssetExplorerModule
from src.apps.asset_explorer.presentation.viewmodels.explorer import AssetExplorerViewModel
from src.apps.asset_explorer.presentation.viewmodels.metadata import PropertyCategory, MetadataViewModel

# --- Polymorphic UI Widgets ---

class FlowLayout(QtW.QLayout):
    """A standard PySide6 FlowLayout implementation for wrapping widgets."""
    def __init__(self, parent=None, margin=0, spacing=-1):
        super().__init__(parent)
        if parent is not None:
            self.setContentsMargins(margin, margin, margin, margin)
        self.setSpacing(spacing)
        self.items = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.items.append(item)

    def count(self):
        return len(self.items)

    def itemAt(self, index):
        if 0 <= index < len(self.items):
            return self.items[index]
        return None

    def takeAt(self, index):
        if 0 <= index < len(self.items):
            return self.items.pop(index)
        return None

    def expandingDirections(self):
        return Qt.Orientations(0)

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        return self._do_layout(QRect(0, 0, width, 0), True)

    def setGeometry(self, rect):
        super().setGeometry(rect)
        self._do_layout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QSize()
        for item in self.items:
            size = size.expandedTo(item.minimumSize())
        margins = self.contentsMargins()
        size += QSize(margins.left() + margins.right(), margins.top() + margins.bottom())
        return size

    def _do_layout(self, rect, test_only):
        x = rect.x()
        y = rect.y()
        line_height = 0
        spacing = self.spacing()

        for item in self.items:
            style = item.widget().style()
            layout_spacing_x = style.layoutSpacing(QtW.QSizePolicy.PushButton, QtW.QSizePolicy.PushButton, Qt.Horizontal)
            layout_spacing_y = style.layoutSpacing(QtW.QSizePolicy.PushButton, QtW.QSizePolicy.PushButton, Qt.Vertical)
            space_x = spacing if spacing != -1 else layout_spacing_x
            space_y = spacing if spacing != -1 else layout_spacing_y
            
            next_x = x + item.sizeHint().width() + space_x
            if next_x - space_x > rect.right() and line_height > 0:
                x = rect.x()
                y = y + line_height + space_y
                next_x = x + item.sizeHint().width() + space_x
                line_height = 0

            if not test_only:
                item.setGeometry(QRect(QPoint(x, y), item.sizeHint()))

            x = next_x
            line_height = max(line_height, item.sizeHint().height())

        return y + line_height - rect.y()

class UrlWidget(QWidget):
    def __init__(self, value, field_name, vm: MetadataViewModel):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.edit = QLineEdit(str(value))
        self.edit.textChanged.connect(lambda val: vm.update_property(field_name, val))
        layout.addWidget(self.edit)
        
        btn = QPushButton("🌐")
        btn.setFixedWidth(30)
        btn.setToolTip("Open in Browser/Shell")
        btn.clicked.connect(self._open_url)
        layout.addWidget(btn)
    
    def _open_url(self):
        url = self.edit.text()
        if url:
            import webbrowser
            # Handle file:// specifically for local explorer
            if url.startswith("file://"):
                path = url.replace("file://", "").replace("/", os.sep)
                if os.path.exists(path):
                    import subprocess
                    subprocess.Popen(f'explorer /select,"{path}"' if os.path.isfile(path) else f'explorer "{path}"')
                else:
                    webbrowser.open(url)
            else:
                webbrowser.open(url)

class TagCloudWidget(QWidget):
    def __init__(self, tags, field_name, vm: MetadataViewModel):
        super().__init__()
        self.vm = vm
        self.field_name = field_name
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        
        # Tag Container
        self.container = QWidget()
        self.flow_layout = FlowLayout(self.container)
        self.flow_layout.setContentsMargins(0, 0, 0, 0)
        self.flow_layout.setSpacing(5)
        self.layout.addWidget(self.container)
        
        # Add Tag Row
        add_layout = QHBoxLayout()
        self.new_tag_input = QLineEdit()
        self.new_tag_input.setPlaceholderText("Add tag...")
        self.new_tag_input.returnPressed.connect(self._add_tag)
        add_layout.addWidget(self.new_tag_input)
        add_btn = QPushButton("➕")
        add_btn.setFixedWidth(30)
        add_btn.clicked.connect(self._add_tag)
        add_layout.addWidget(add_btn)
        self.layout.addLayout(add_layout)
        
        self.refresh_tags(tags)

    def refresh_tags(self, tags):
        # Clear existing
        while self.flow_layout.count():
            item = self.flow_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        # Add chips
        for tag in tags:
            name = tag.name if hasattr(tag, "name") else str(tag)
            chip = QFrame()
            chip.setStyleSheet("background: #3e3e42; border-radius: 10px; padding: 2px 8px; border: 1px solid #555;")
            chip_layout = QHBoxLayout(chip)
            chip_layout.setContentsMargins(5, 2, 5, 2)
            lbl = QLabel(name)
            lbl.setStyleSheet("border: none; background: transparent;")
            chip_layout.addWidget(lbl)
            del_btn = QPushButton("×")
            del_btn.setFixedWidth(15)
            del_btn.setStyleSheet("border: none; background: transparent; color: #f14c4c; font-weight: bold;")
            del_btn.clicked.connect(lambda checked=False, t=tag: self._remove_tag(t))
            chip_layout.addWidget(del_btn)
            self.flow_layout.addWidget(chip)

    def _add_tag(self):
        tag_name = self.new_tag_input.text().strip()
        if tag_name:
            current_tags = list(getattr(self.vm._asset, self.field_name, []))
            # Check if exists
            if not any((t.name if hasattr(t, "name") else str(t)) == tag_name for t in current_tags):
                # In a real app we'd create a Tag object via a factory
                from src.modules.assets.domain.models import Tag
                new_tag = Tag(name=tag_name)
                current_tags.append(new_tag)
                self.vm.update_property(self.field_name, current_tags)
                self.refresh_tags(current_tags)
                self.new_tag_input.clear()

    def _remove_tag(self, tag_to_remove):
        current_tags = list(getattr(self.vm._asset, self.field_name, []))
        new_tags = [t for t in current_tags if t != tag_to_remove]
        self.vm.update_property(self.field_name, new_tags)
        self.refresh_tags(new_tags)

class NumericWidget(QWidget):
    def __init__(self, value, field_name, vm: MetadataViewModel, is_float=True):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        from PySide6.QtWidgets import QDoubleSpinBox, QSpinBox
        if is_float:
            self.spin = QDoubleSpinBox()
            self.spin.setDecimals(3)
        else:
            self.spin = QSpinBox()
        self.spin.setRange(-99999999, 99999999)
        self.spin.setValue(value or 0)
        self.spin.valueChanged.connect(lambda val: vm.update_property(field_name, val))
        layout.addWidget(self.spin)

class TimestampWidget(QWidget):
    def __init__(self, value, field_name, vm: MetadataViewModel):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        from PySide6.QtWidgets import QDateTimeEdit
        from PySide6.QtCore import QDateTime
        self.dt_edit = QDateTimeEdit()
        self.dt_edit.setCalendarPopup(True)
        if value:
            self.dt_edit.setDateTime(QDateTime.fromSecsSinceEpoch(int(value)))
        self.dt_edit.dateTimeChanged.connect(lambda dt: vm.update_property(field_name, float(dt.toMSecsSinceEpoch() / 1000)))
        layout.addWidget(self.dt_edit)

class MultiLineTextWidget(QWidget):
    def __init__(self, value, field_name, vm: MetadataViewModel):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0,0,0,0)
        from PySide6.QtWidgets import QTextEdit
        self.text_edit = QTextEdit()
        self.text_edit.setPlainText(str(value or ""))
        self.text_edit.setMaximumHeight(100)
        self.text_edit.textChanged.connect(lambda: vm.update_property(field_name, self.text_edit.toPlainText()))
        layout.addWidget(self.text_edit)

# --- Ported Monitoring Widgets ---
class TaskMonitor(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Task ID", "Name", "Status", "Time", "Details"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("background-color: #252526; color: #cccccc;")
        self.tasks = {}

    @Slot(dict)
    def update_task(self, event):
        task_id = event.get("task_id")
        if not task_id: return
        if task_id not in self.tasks:
            row = self.rowCount()
            self.insertRow(row)
            self.tasks[task_id] = row
            self.setItem(row, 0, QTableWidgetItem(str(task_id)[:8] + "..."))
            self.setItem(row, 1, QTableWidgetItem(event.get("task_name", "Unknown")))
            self.setItem(row, 2, QTableWidgetItem("Queued"))
        
        row = self.tasks[task_id]
        event_type = event.get("event")
        if event_type == "started":
            self.item(row, 2).setText("Running")
        elif event_type == "executed":
            status = event.get("status", "Done")
            self.item(row, 2).setText(status.capitalize())
            if status == "SUCCESS":
                self.item(row, 2).setForeground(Qt.green)
            else:
                self.item(row, 2).setForeground(Qt.red)
        
        if "time" in event:
            self.setItem(row, 3, QTableWidgetItem(f"{event['time']:.2f}s"))
            if "details" in event:
                self.setItem(row, 4, QTableWidgetItem(str(event["details"])))

class WorkerManager(QObject):
    """Manages the lifecycle of the TaskIQ worker process (Background QObject)."""
    status_changed = Signal(str)
    task_event = Signal(dict)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.process = QProcess(self)
        self.process.readyReadStandardOutput.connect(self._handle_stdout)
        self.process.readyReadStandardError.connect(self._handle_stderr)
        self.process.finished.connect(self._on_finished)
        
    def start_worker(self):
        """Starts the TaskIQ worker via uv run."""
        if self.process.state() != QProcess.NotRunning:
            return
            
        cmd = "uv"
        args = [
            "run", "taskiq", "worker", 
            "src.adapters.taskiq_broker:broker", 
            "src.modules.agm.tasks",
            # "--reload" # Disable reload for production/integrated feel
        ]
        
        # Enable GUI monitoring middleware and force real broker for E2E stability
        env = os.environ.copy()
        env["BCOR_GUI_MONITOR"] = "1"
        env["TASKIQ_FORCE_REAL_BROKER"] = "1"
        # Ensure we are in the project root
        self.process.setWorkingDirectory(os.getcwd())
        
        env_list = [f"{k}={v}" for k, v in env.items()]
        self.process.setEnvironment(env_list)
        
        self.status_changed.emit("Starting...")
        self.process.start(cmd, args)
        if not self.process.waitForStarted(5000):
             self.status_changed.emit("Failed to Start")
             logger.error(f"Worker failed to start: {self.process.errorString()}")
        else:
             self.status_changed.emit("Running")
        
    def stop_worker(self):
        self.status_changed.emit("Stopping...")
        self.process.terminate()
        if not self.process.waitForFinished(3000):
            self.process.kill()

    def _handle_stdout(self):
        data = self.process.readAllStandardOutput().data().decode()
        for line in data.splitlines():
            # Skip progress bar noise to keep UI responsive
            if "|" in line and "%" in line: continue
            
            logger.info(f"[WORKER] {line}")
            if "[BCOR_TASK]" in line:
                try:
                    event_info = line.split("[BCOR_TASK]")[1].strip()
                    event = json.loads(event_info)
                    self.task_event.emit(event)
                except Exception as e:
                    logger.error(f"Failed to parse task event: {e}")

    def _handle_stderr(self):
        data = self.process.readAllStandardError().data().decode()
        for line in data.splitlines():
            # Skip progress bar noise (tqdm, model loading bars)
            if "|" in line and "it/s" in line: continue
            if "Loading weights:" in line: continue

            if "[taskiq.worker][INFO]" in line or "[taskiq.receiver.receiver][INFO]" in line:
                logger.info(f"[WORKER] {line}")
                continue
                
            if "[taskiq." in line and "[ERROR]" in line:
                logger.error(f"[WORKER ERROR] {line}")
                continue

            logger.info(f"[WORKER:STDERR] {line}")

    def _on_finished(self):
        self.status_changed.emit("Stopped")

# --- Dynamic Search GUI ---
class SearchConstructor(QWidget):
    """Dynamically builds search filters based on domain model metadata."""
    def __init__(self, search_callback):
        super().__init__()
        self.callback = search_callback
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        self.filters = {} # name -> widget(s)

    def set_schema(self, schema: List[Dict[str, Any]]):
        """Rebuilds the search form from the provided metadata schema."""
        # Clear existing
        while self.layout.count():
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
            elif item.layout():
                # Clear nested layouts
                l = item.layout()
                while l.count():
                    si = l.takeAt(0)
                    if si.widget(): si.widget().deleteLater()
        
        self.filters = {}
        for item in schema:
            name = item["name"]
            label_text = item["label"]
            widget_hint = item["widget"]
            
            lbl = QLabel(label_text)
            lbl.setStyleSheet("color: #aaa; font-size: 11px; margin-top: 5px;")
            self.layout.addWidget(lbl)
            
            if widget_hint == "range":
                h_layout = QHBoxLayout()
                min_edit = QLineEdit()
                min_edit.setPlaceholderText("Min")
                max_edit = QLineEdit()
                max_edit.setPlaceholderText("Max")
                h_layout.addWidget(min_edit)
                h_layout.addWidget(max_edit)
                self.filters[name] = (min_edit, max_edit)
                self.layout.addLayout(h_layout)
            elif widget_hint == "date":
                from PySide6.QtWidgets import QDateEdit
                date_edit = QDateEdit()
                date_edit.setCalendarPopup(True)
                date_edit.setSpecialValueText("Any Date")
                self.filters[name] = date_edit
                self.layout.addWidget(date_edit)
            else: # text, vector, etc
                edit = QLineEdit()
                edit.setPlaceholderText(f"Search {label_text}...")
                edit.returnPressed.connect(self._on_search)
                self.filters[name] = edit
                self.layout.addWidget(edit)

    def _on_search(self):
        query_data = {}
        for name, widget in self.filters.items():
            if isinstance(widget, tuple): # Range
                min_val = widget[0].text().strip()
                max_val = widget[1].text().strip()
                if min_val or max_val:
                    try:
                        query_data[name] = (float(min_val) if min_val else None, 
                                           float(max_val) if max_val else None)
                    except ValueError: pass
            elif isinstance(widget, QLineEdit):
                val = widget.text().strip()
                if val: query_data[name] = val
            elif hasattr(widget, "date") and widget.text() != "Any Date":
                query_data[name] = widget.date().toPython().isoformat()
        
        # In a real app we'd trigger the search via callback
        self.callback(query_data)

# --- Status HUD ---
class StatusHUD(QFrame):
    """Floating HUD for real-time ingestion and inference progress."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            StatusHUD {
                background-color: rgba(30, 30, 30, 220);
                border: 1px solid #444;
                border-radius: 8px;
                color: #eee;
            }
        """)
        layout = QVBoxLayout(self)
        self.label = QLabel("Idle")
        self.progress = QtW.QProgressBar()
        self.progress.setFixedHeight(10)
        self.progress.setTextVisible(False)
        layout.addWidget(self.label)
        layout.addWidget(self.progress)
        self.hide()

    @Slot(int, int, str)
    def update_status(self, current, total, status):
        self.show()
        self.label.setText(status)
        if total > 0:
            self.progress.setMaximum(total)
            self.progress.setValue(current)
        if current >= total and total > 0:
            asyncio.create_task(self._hide_delayed())

    async def _hide_delayed(self):
        await asyncio.sleep(3)
        self.hide()

class PaginationBar(QWidget):
    """Controls for explicit 500-item batch navigation."""
    next_requested = Signal()
    prev_requested = Signal()

    def __init__(self):
        super().__init__()
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 5, 0, 5)
        
        self.prev_btn = QPushButton("⬅️ Prev")
        self.prev_btn.setEnabled(False)
        self.prev_btn.clicked.connect(self.prev_requested)
        
        self.page_lbl = QLabel("Page 1")
        self.page_lbl.setAlignment(Qt.AlignCenter)
        self.page_lbl.setStyleSheet("font-weight: bold; color: #888;")
        
        self.next_btn = QPushButton("Next ➡️")
        self.next_btn.setEnabled(False)
        self.next_btn.clicked.connect(self.next_requested)
        
        layout.addWidget(self.prev_btn)
        layout.addWidget(self.page_lbl)
        layout.addWidget(self.next_btn)

    @Slot(int, bool, bool)
    def update_state(self, current_page, can_prev, can_next):
        self.page_lbl.setText(f"Page {current_page}")
        self.prev_btn.setEnabled(can_prev)
        self.next_btn.setEnabled(can_next)

# --- Explorer UI Components ---
class SearchPanel(QGroupBox):
    search_requested = Signal(str)
    clear_db_requested = Signal()
    mass_add_requested = Signal()
    add_image_requested = Signal()

    def __init__(self, search_callback):
        super().__init__("Query Constructor")
        layout = QVBoxLayout(self)
        
        # Dynamic Search
        self.constructor = SearchConstructor(search_callback)
        layout.addWidget(self.constructor)
        
        layout.addSpacing(10)
        search_btn = QPushButton("🔍 Universal Search")
        search_btn.setStyleSheet("background-color: #007acc; font-weight: bold;")
        search_btn.clicked.connect(self.constructor._on_search)
        layout.addWidget(search_btn)
        
        layout.addSpacing(20)
        layout.addWidget(QLabel("Pipeline Actions:"))
        self.add_btn = QPushButton("➕ Add Single Asset...")
        self.add_btn.clicked.connect(self.add_image_requested)
        layout.addWidget(self.add_btn)
        
        self.mass_add_btn = QPushButton("📁 Mass Ingest Directory...")
        self.mass_add_btn.clicked.connect(self.mass_add_requested)
        layout.addWidget(self.mass_add_btn)
        
        layout.addStretch()
        self.clear_btn = QPushButton("🗑️ Wipe Database")
        self.clear_btn.setStyleSheet("color: #f14c4c; font-weight: bold;")
        self.clear_btn.clicked.connect(self.clear_db_requested)
        layout.addWidget(self.clear_btn)

class AutoMetadataPanel(QGroupBox):
    def __init__(self):
        super().__init__("Metadata Engine (Auto-GUI)")
        self.layout = QVBoxLayout(self)
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.scroll_content = QWidget()
        self.form_layout = QFormLayout(self.scroll_content)
        self.scroll.setWidget(self.scroll_content)
        self.layout.addWidget(self.scroll)
        
        self.save_btn = QPushButton("💾 Save Changes")
        self.save_btn.setEnabled(False)
        self.layout.addWidget(self.save_btn)

    def set_metadata_vm(self, vm: MetadataViewModel):
        self.child_vm = vm
        while self.form_layout.count():
            item = self.form_layout.takeAt(0)
            if item.widget(): item.widget().deleteLater()
        
        if not vm:
            self.form_layout.addRow(QLabel("Select an asset to view metadata"))
            return

        for desc in vm.descriptors:
            label = QLabel(desc.display_name)
            
            if desc.category == PropertyCategory.READ_ONLY:
                val = ", ".join([str(v) for v in desc.value]) if isinstance(desc.value, list) else str(desc.value)
                edit = QLineEdit(str(val))
                edit.setReadOnly(True)
                edit.setStyleSheet("background: #333; color: #888; border: 1px solid #444;")
                if desc.is_stored: # Add refresh button for stored hashes
                    container = QWidget()
                    h = QHBoxLayout(container)
                    h.setContentsMargins(0,0,0,0)
                    h.addWidget(edit)
                    btn = QPushButton("↺")
                    btn.setFixedWidth(25)
                    btn.setToolTip(f"Recalculate via {desc.handler}")
                    h.addWidget(btn)
                    self.form_layout.addRow(label, container)
                else:
                    self.form_layout.addRow(label, edit)
            
            elif desc.category == PropertyCategory.URL:
                widget = UrlWidget(desc.value, desc.id, vm)
                self.form_layout.addRow(label, widget)
                
            elif desc.category == PropertyCategory.TAGS:
                widget = TagCloudWidget(desc.value or [], desc.id, vm)
                self.form_layout.addRow(label, widget)
                
            elif desc.category == PropertyCategory.NUMBER:
                is_float = desc.data_type is float or isinstance(desc.value, float)
                widget = NumericWidget(desc.value, desc.id, vm, is_float=is_float)
                self.form_layout.addRow(label, widget)
                
            elif desc.category == PropertyCategory.DATE:
                widget = TimestampWidget(desc.value, desc.id, vm)
                self.form_layout.addRow(label, widget)
                
            elif desc.category == PropertyCategory.LONG_TEXT:
                widget = MultiLineTextWidget(desc.value, desc.id, vm)
                self.form_layout.addRow(label, widget)
                
            elif desc.category == PropertyCategory.BOOLEAN:
                from PySide6.QtWidgets import QCheckBox
                cb = QCheckBox()
                cb.setChecked(bool(desc.value))
                cb.toggled.connect(lambda checked, fn=desc.id: vm.update_property(fn, checked))
                self.form_layout.addRow(label, cb)
                
            else: # TEXT
                edit = QLineEdit(str(desc.value or ""))
                edit.textChanged.connect(lambda val, fn=desc.id: vm.update_property(fn, val))
                self.form_layout.addRow(label, edit)

        self.save_btn.setEnabled(True)
        try:
            self.save_btn.clicked.disconnect()
        except:
            pass
        self.save_btn.clicked.connect(lambda: asyncio.create_task(vm.save_changes()))

# --- Asset Explorer Dashboard ---
class AssetExplorerDashboard(QMainWindow):
    def __init__(self, explorer_vm: AssetExplorerViewModel):
        super().__init__()
        self.vm = explorer_vm
        self.setWindowTitle("BCor Asset Explorer Dashboard [v1.0]")
        self.resize(1280, 850)
        
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        
        # Explorer Tab
        self.explorer_page = QWidget()
        self.tabs.addTab(self.explorer_page, "Asset Explorer")
        exp_layout = QHBoxLayout(self.explorer_page)
        
        self.search_panel = SearchPanel(self._on_search)
        
        # Combined Results and Pagination
        results_container = QWidget()
        results_layout = QVBoxLayout(results_container)
        results_layout.setContentsMargins(0, 0, 0, 0)
        
        self.results_panel = QListWidget()
        self.pagination_bar = PaginationBar()
        
        results_layout.addWidget(self.results_panel)
        results_layout.addWidget(self.pagination_bar)
        
        self.metadata_panel = AutoMetadataPanel()
        
        exp_layout.addWidget(self.search_panel, 1)
        exp_layout.addWidget(results_container, 2)
        exp_layout.addWidget(self.metadata_panel, 1)
        
        # Ingestion HUD
        self.hud = StatusHUD(self.explorer_page)
        self.hud.setGeometry(QRect(400, 700, 500, 80))

        # Infrastructure Tab
        self.infra_page = QWidget()
        self.tabs.addTab(self.infra_page, "Infrastructure Monitor")
        infra_layout = QVBoxLayout(self.infra_page)
        
        # Worker Control
        worker_ctrl = QGroupBox("TaskIQ Worker Management")
        worker_layout = QHBoxLayout(worker_ctrl)
        self.worker_status_lbl = QLabel("Worker: Offline")
        self.worker_status_lbl.setStyleSheet("font-weight: bold; color: #f14c4c;")
        self.start_worker_btn = QPushButton("🚀 Start Worker")
        self.stop_worker_btn = QPushButton("🛑 Stop")
        self.stop_worker_btn.setEnabled(False)
        worker_layout.addWidget(self.worker_status_lbl)
        worker_layout.addStretch()
        worker_layout.addWidget(self.start_worker_btn)
        worker_layout.addWidget(self.stop_worker_btn)
        infra_layout.addWidget(worker_ctrl)
        
        self.task_monitor = TaskMonitor()
        infra_layout.addWidget(QLabel("Live TaskIQ Worker Feed (Sequential VLM Pipeline)"))
        infra_layout.addWidget(self.task_monitor)
        infra_layout.addStretch() # Ensure widgets don't expand into the tab bar
        
        # Worker Manager Integration
        self.worker_manager = WorkerManager(self)
        self.worker_manager.status_changed.connect(self._on_worker_status)
        self.worker_manager.task_event.connect(self.task_monitor.update_task)
        
        self.start_worker_btn.clicked.connect(self.worker_manager.start_worker)
        self.stop_worker_btn.clicked.connect(self.worker_manager.stop_worker)
        
        # Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Wiring
        self.search_panel.add_image_requested.connect(self._on_add_single)
        self.search_panel.mass_add_requested.connect(self._on_mass_add)
        self.search_panel.clear_db_requested.connect(self._on_clear_db)
        self.results_panel.itemClicked.connect(self._on_item_clicked)
        
        self.vm.results_updated.connect(self._update_results)
        self.vm.asset_selected.connect(self._on_asset_selected)
        self.vm.progress_updated.connect(self.hud.update_status)
        self.vm.search_schema_updated.connect(self.search_panel.constructor.set_schema)
        self.vm.pagination_updated.connect(self.pagination_bar.update_state)
        self.vm.operation_started.connect(lambda name: self.status_bar.showMessage(f"Starting: {name}..."))
        self.vm.operation_finished.connect(self._on_operation_finished)
        
        # Pagination Wiring
        self.pagination_bar.next_requested.connect(lambda: asyncio.create_task(self.vm.next_page()))
        self.pagination_bar.prev_requested.connect(lambda: asyncio.create_task(self.vm.prev_page()))
        
        # Initial schema trigger
        self.vm.refresh_search_schema()

    def _on_worker_status(self, status):
        self.worker_status_lbl.setText(f"Worker: {status}")
        is_running = "Running" in status
        self.start_worker_btn.setEnabled(not is_running and "Starting" not in status)
        self.stop_worker_btn.setEnabled(is_running or "Starting" in status)
        if is_running:
            self.worker_status_lbl.setStyleSheet("font-weight: bold; color: #4ec9b0;")
        else:
            self.worker_status_lbl.setStyleSheet("font-weight: bold; color: #f14c4c;")

    def _on_operation_finished(self, name, success):
        msg = f"Finished: {name} ({'Success' if success else 'Failed'})"
        self.status_bar.showMessage(msg, 5000)

    def _update_results(self, assets):
        self.results_panel.clear()
        for a in assets:
            item = QListWidgetItem(a.name or a.uri)
            item.setData(Qt.UserRole, a.id)
            self.results_panel.addItem(item)

    def _on_item_clicked(self, item):
        self.vm.select_asset(item.data(Qt.UserRole))

    def _on_asset_selected(self, asset):
        self.metadata_panel.set_metadata_vm(self.vm.current_metadata)

    def _on_search(self, query):
        asyncio.create_task(self.vm.search(query))

    def _on_add_single(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Asset to Import")
        if file_path:
            asyncio.create_task(self.vm.add_single_asset(file_path))

    def _on_mass_add(self):
        dir_path = QFileDialog.getExistingDirectory(self, "Select Directory to Import")
        if dir_path:
            asyncio.create_task(self.vm.mass_add(dir_path))

    def _on_clear_db(self):
        asyncio.create_task(self.vm.clear_database())

async def async_main():
    """Bootstraps the framework-native system and launches the GUI."""
    # 1. System Setup
    system = System(modules=[AGMModule(), AssetsModule(), AssetExplorerModule()])
    await system.start()
    
    # 2. Resolve ViewModels from DISHKA (within a request scope)
    async with system.container() as scope:
        vm = await scope.get(AssetExplorerViewModel)
        
        # 3. Launch UI
        window = AssetExplorerDashboard(vm)
        window.show()
        
        # Auto-start worker for convenience
        window.worker_manager.start_worker()
        
        # 4. Wait for window close
        while window.isVisible():
            await asyncio.sleep(0.1)
            
        # Clean up worker
        window.worker_manager.stop_worker()
        
    await system.stop()
    await WindowsLoopManager.drain_loop()

def main():
    """Main entry point for the application."""
    WindowsLoopManager.setup_loop()
    app = QApplication(sys.argv)
    app.setApplicationName("BCor Asset Explorer")
    
    loop = qasync.QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    try:
        loop.run_until_complete(async_main())
    except KeyboardInterrupt:
        pass
    finally:
        loop.close()

if __name__ == "__main__":
    main()
