import sys
import os
import asyncio
import qasync
from typing import Any, List, Optional
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
from PySide6.QtCore import Qt, Signal, Slot, QRect, QPoint, QSize

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
            self.item(row, 2).setText(event.get("status", "Done").capitalize())

# --- Explorer UI Components ---
class SearchPanel(QGroupBox):
    search_requested = Signal(str)
    clear_db_requested = Signal()
    mass_add_requested = Signal()

    def __init__(self):
        super().__init__("Query Constructor")
        layout = QVBoxLayout(self)
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText("Search assets...")
        layout.addWidget(self.query_input)
        
        search_btn = QPushButton("🔍 Run Search")
        search_btn.clicked.connect(lambda: self.search_requested.emit(self.query_input.text()))
        layout.addWidget(search_btn)
        
        layout.addSpacing(20)
        layout.addWidget(QLabel("Pipeline Actions:"))
        self.add_btn = QPushButton("➕ Add Image...")
        layout.addWidget(self.add_btn)
        
        self.mass_add_btn = QPushButton("📁 Mass Add (Dir)...")
        self.mass_add_btn.clicked.connect(self.mass_add_requested)
        layout.addWidget(self.mass_add_btn)
        
        layout.addStretch()
        self.clear_btn = QPushButton("🗑️ Clear Database")
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
        self.search_panel = SearchPanel()
        self.results_panel = QListWidget()
        self.metadata_panel = AutoMetadataPanel()
        
        exp_layout.addWidget(self.search_panel, 1)
        exp_layout.addWidget(self.results_panel, 2)
        exp_layout.addWidget(self.metadata_panel, 1)
        
        # Infrastructure Tab
        self.infra_page = QWidget()
        self.tabs.addTab(self.infra_page, "Infrastructure Monitor")
        infra_layout = QVBoxLayout(self.infra_page)
        self.task_monitor = TaskMonitor()
        infra_layout.addWidget(QLabel("Live TaskIQ Worker Feed (Ported from Companion)"))
        infra_layout.addWidget(self.task_monitor)
        
        # Status Bar
        self.status_bar = self.statusBar()
        self.status_bar.showMessage("Ready")
        
        # Wiring
        self.search_panel.search_requested.connect(self._on_search)
        self.search_panel.mass_add_requested.connect(self._on_mass_add)
        self.search_panel.clear_db_requested.connect(self._on_clear_db)
        self.results_panel.itemClicked.connect(self._on_item_clicked)
        
        self.vm.results_updated.connect(self._update_results)
        self.vm.asset_selected.connect(self._on_asset_selected)
        self.vm.operation_started.connect(lambda name: self.status_bar.showMessage(f"Starting: {name}..."))
        self.vm.operation_finished.connect(self._on_operation_finished)

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
        
        # 4. Wait for window close
        while window.isVisible():
            await asyncio.sleep(0.1)
        
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
