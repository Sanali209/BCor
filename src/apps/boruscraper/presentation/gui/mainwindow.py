from PySide6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QListWidget, QLabel, QSplitter, 
                               QTextEdit, QProgressBar, QMessageBox, QDialog,
                               QCheckBox, QGroupBox, QGridLayout, QListWidgetItem, QMenu, QFileDialog)
from PySide6.QtCore import Qt, Slot, QTimer
import os
import subprocess
import platform
from src.apps.experemental.boruscraper.common.database import DatabaseManager
from src.apps.experemental.boruscraper.common.deduplication import DeduplicationManager
from src.apps.experemental.boruscraper.presentation.gui.settings_dialog import SettingsDialog
from src.apps.experemental.boruscraper.presentation.gui.dupe_dialog import DupeDialog
from src.apps.experemental.boruscraper.presentation.gui.url_dialog import StartUrlsDialog
from PySide6.QtGui import QAction

from src.apps.experemental.boruscraper.application.messages import (
    StartScrapeCommand, StopScrapeCommand, PauseScrapeCommand, ResumeScrapeCommand, SetResolutionActionCommand
)
import asyncio

class MainWindow(QMainWindow):
    def __init__(self, db=None, dedup=None, task_manager=None, bus=None, adapter=None, loop=None, template_registry=None):
        super().__init__()
        self.setWindowTitle("Boru Scraper GUI")
        self.resize(1000, 700)
        
        self.db = db or DatabaseManager()
        self.dedup = dedup or DeduplicationManager(self.db)
        self.task_manager = task_manager
        self.bus = bus
        self.adapter = adapter
        self.loop = loop
        self.template_registry = template_registry
        
        if self.adapter:
            self.adapter.log_signal.connect(self.log_message)
            self.adapter.worker_finished_signal.connect(self.worker_finished)
            self.adapter.duplicate_found_signal.connect(self.handle_duplicate)
            self.adapter.captcha_detected_signal.connect(self.on_captcha_detected)
            self.adapter.debug_confirmation_signal.connect(self.on_debug_confirmation)
            self.adapter.min_content_warning_signal.connect(self.on_min_content_warning)
            self.adapter.stats_signal.connect(self.update_stats)

        self.current_queue_id = None
        self.current_project_id = None
        self.is_queue_running = False

        self._setup_ui()
        self._refresh_project_list()

    def _setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)

        # --- Left Panel: Project Queue ---
        # --- Left Panel: Project Queue ---
        left_layout = QVBoxLayout()
        
        # Header with Checkbox
        left_header = QHBoxLayout()
        left_header.addWidget(QLabel("Project Queue"))
        self.chk_debug = QCheckBox("Debug Mode")
        left_header.addWidget(self.chk_debug)
        left_layout.addLayout(left_header)
        
        self.queue_list = QListWidget()
        self.queue_list.setContextMenuPolicy(Qt.CustomContextMenu)
        self.queue_list.customContextMenuRequested.connect(self.show_context_menu)
        left_layout.addWidget(self.queue_list)
        
        main_layout.addLayout(left_layout, 1)

        # --- Menu Bar ---
        self._create_menus()

        # --- Right Panel: Logs & Stats ---
        right_layout = QVBoxLayout()
        
        # Stats
        self.stats_label = QLabel("Stats: Session Images: 0 | Total DB Images: 0")
        right_layout.addWidget(self.stats_label)
        
        # Progress
        self.progress_bar = QProgressBar()
        right_layout.addWidget(self.progress_bar)

        # Stats Grid
        stats_group = QGroupBox("Real-time Statistics")
        stats_layout = QGridLayout()
        
        self.lbl_images_ok = QLabel("Images: 0")
        self.lbl_images_fail = QLabel("Failed: 0")
        self.lbl_pages = QLabel("Pages: 0")
        self.lbl_speed_pages = QLabel("Pages/min: 0.0")
        self.lbl_speed_images = QLabel("Images/min: 0.0")
        
        stats_layout.addWidget(self.lbl_images_ok, 0, 0)
        stats_layout.addWidget(self.lbl_images_fail, 0, 1)
        stats_layout.addWidget(self.lbl_pages, 1, 0)
        stats_layout.addWidget(self.lbl_speed_pages, 1, 1)
        stats_layout.addWidget(self.lbl_speed_images, 2, 0, 1, 2)
        
        stats_group.setLayout(stats_layout)
        right_layout.addWidget(stats_group)
        right_layout.addWidget(stats_group)


        # Logs
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        right_layout.addWidget(self.log_view)

        main_layout.addLayout(right_layout, 2)

    def _create_menus(self):
        menu_bar = self.menuBar()

        # File Menu
        file_menu = menu_bar.addMenu("File")
        
        import_action = QAction("Import Project...", self)
        import_action.triggered.connect(self.import_project)
        file_menu.addAction(import_action)
        
        export_action = QAction("Export Project...", self)
        export_action.triggered.connect(self.export_project)
        file_menu.addAction(export_action)
        
        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Project Menu
        project_menu = menu_bar.addMenu("Project")
        
        add_action = QAction("Add Project", self)
        add_action.triggered.connect(self.open_add_project_dialog)
        project_menu.addAction(add_action)

        remove_action = QAction("Remove Project", self)
        remove_action.triggered.connect(self.remove_project)
        project_menu.addAction(remove_action)
        
        project_menu.addSeparator()

        settings_action = QAction("Project Settings", self)
        settings_action.triggered.connect(self.open_settings)
        project_menu.addAction(settings_action)

        url_action = QAction("Manage Start URLs", self)
        url_action.triggered.connect(self.manage_start_urls)
        project_menu.addAction(url_action)

        # Queue Menu
        queue_menu = menu_bar.addMenu("Queue")
        
        start_action = QAction("Start Queue", self)
        start_action.triggered.connect(self.start_queue)
        queue_menu.addAction(start_action)

        stop_action = QAction("Stop Queue", self)
        stop_action.triggered.connect(self.stop_queue)
        queue_menu.addAction(stop_action)
        
        queue_menu.addSeparator()
        
        move_up_action = QAction("Move Up", self)
        move_up_action.triggered.connect(self.move_queue_item_up)
        queue_menu.addAction(move_up_action)
        
        move_down_action = QAction("Move Down", self)
        move_down_action.triggered.connect(self.move_queue_item_down)
        queue_menu.addAction(move_down_action)

    def _refresh_project_list(self):
        self.queue_list.clear()
        queue_items = self.db.get_queue()
        for item in queue_items:
            w_item = QListWidgetItem(f"{item['name']} ({item['status']})")
            w_item.setData(Qt.UserRole, item['project_id'])
            self.queue_list.addItem(w_item)

    @Slot(object)
    def show_context_menu(self, position):
        item = self.queue_list.itemAt(position)
        if not item: return
        
        menu = QMenu()
        open_folder_action = QAction("Find in Folder", self)
        open_folder_action.triggered.connect(lambda: self.open_project_folder(item))
        menu.addAction(open_folder_action)
        menu.exec(self.queue_list.mapToGlobal(position))

    def open_project_folder(self, item):
        project_id = item.data(Qt.UserRole)
        settings = self.db.get_project_settings(project_id)
        if settings and "save_path" in settings:
            path = settings["save_path"]
            if os.path.exists(path):
                # Open folder in explorer
                if platform.system() == "Windows":
                    os.startfile(path)
                elif platform.system() == "Darwin":
                    subprocess.Popen(["open", path])
                else:
                    subprocess.Popen(["xdg-open", path])
            else:
                QMessageBox.warning(self, "Error", f"Path does not exist:\n{path}")
        else:
             QMessageBox.warning(self, "Error", "Could not determine save path for this project.")

    @Slot()
    def start_queue(self):
        self.is_queue_running = True
        self.log_view.append("Starting queue...")
        self._process_next_in_queue()

    def _process_next_in_queue(self):
        if not self.is_queue_running:
            return

        queue_items = self.db.get_queue()
        if not queue_items:
            self.log_view.append("Queue is empty.")
            self.is_queue_running = False
            return

        item = queue_items[0]
        self.current_queue_id = item['id']
        project_id = item['project_id']
        self.current_project_id = project_id
        
        self.log_view.append(f"Starting Project: {item['name']}")
        
        self.log_view.append(f"Starting Project: {item['name']}")
        
        debug_mode = self.chk_debug.isChecked()
        if debug_mode: self.log_view.append("DEBUG MODE: ON (Will ask for confirmation)")

        if self.bus and self.loop:
            cmd = StartScrapeCommand(project_id=project_id, debug_mode=debug_mode)
            asyncio.run_coroutine_threadsafe(self.bus.dispatch(cmd), self.loop)
        else:
            self.log_view.append("ERROR: MessageBus not connected!")

    @Slot(int, str)
    def on_debug_confirmation(self, project_id, message):
        self.log_view.append(f"[DEBUG] {message}")
        res = QMessageBox.question(self, "Debug Confirmation", f"Step: {message}\n\nProceed?", QMessageBox.Yes | QMessageBox.No)
        
        if res == QMessageBox.Yes:
            if self.task_manager: 
                w = self.task_manager.get_worker(project_id)
                if w: w.confirm_step()
        else:
            if self.bus and self.loop:
                cmd = StopScrapeCommand(project_id=project_id)
                asyncio.run_coroutine_threadsafe(self.bus.dispatch(cmd), self.loop)

    @Slot(int)
    def on_captcha_detected(self, project_id):
        self.log_view.append(f"CAPTCHA Detected in Project {project_id}!")
        QMessageBox.information(
            self, 
            "CAPTCHA Detected", 
            "A CAPTCHA has been detected.\nPlease solve it in the browser window, then click OK to resume."
        )
        if self.current_project_id == project_id:
            self.log_view.append("Resuming scraper...")
            if self.bus and self.loop:
                cmd = ResumeScrapeCommand(project_id=project_id)
                asyncio.run_coroutine_threadsafe(self.bus.dispatch(cmd), self.loop)

    @Slot()
    def stop_queue(self):
        self.is_queue_running = False
        if self.current_project_id:
            if self.bus and self.loop:
                cmd = StopScrapeCommand(project_id=self.current_project_id)
                asyncio.run_coroutine_threadsafe(self.bus.dispatch(cmd), self.loop)
            elif self.task_manager:
                asyncio.run_coroutine_threadsafe(self.task_manager.stop_worker(self.current_project_id), self.loop)
        self.log_view.append("Queue stopped.")

    @Slot(str, str)
    def log_message(self, level, msg):
        self.log_view.append(f"[{level}] {msg}")

    @Slot(int, dict)
    def update_stats(self, project_id, stats):
        # Update labels in the grid
        self.lbl_images_ok.setText(f"Images: {stats.get('images', 0)}")
        self.lbl_images_fail.setText(f"Failed: {stats.get('images_failed', 0)}")
        self.lbl_pages.setText(f"Pages: {stats.get('pages', 0)}")
        self.lbl_speed_pages.setText(f"Pages/min: {stats.get('pages_per_min', 0.0):.1f}")
        self.lbl_speed_images.setText(f"Images/min: {stats.get('images_per_min', 0.0):.1f}")
        
        # Update the main stats label
        session_imgs = stats.get('images', 0)
        topics = stats.get('topics', 0)
        self.stats_label.setText(f"Stats: Session Images: {session_imgs} | Topics: {topics} | Pages: {stats.get('pages', 0)}")
        
        # Update progress bar (semi-fake but show activity)
        current_val = self.progress_bar.value()
        self.progress_bar.setValue((current_val + 1) % 101)

    @Slot(int)
    def worker_finished(self, project_id):
        self.log_view.append(f"Project {project_id} finished.")
        
        if self.current_queue_id:
            self.db.move_queue_item_to_end(self.current_queue_id)
            self._refresh_project_list()
        
        # Trigger next item
        if self.is_queue_running:
             QTimer.singleShot(1000, self._process_next_in_queue)

    @Slot(int, str, list)
    def handle_duplicate(self, project_id, new_image, conflicts):
        dialog = DupeDialog(new_image, conflicts, self)
        res_code = dialog.exec() # Returns 1 (Accepted) or 0 (Rejected)
        action = dialog.get_result()
        
        self.log_view.append(f"Resolution Action: {action}")
        
        # Resume worker
        if self.current_project_id == project_id:
            if self.bus and self.loop:
                cmd = SetResolutionActionCommand(project_id=project_id, action=action)
                asyncio.run_coroutine_threadsafe(self.bus.dispatch(cmd), self.loop)

    @Slot()
    def open_add_project_dialog(self):
        from PySide6.QtWidgets import QInputDialog
        
        if not getattr(self, "template_registry", None):
            QMessageBox.warning(self, "Error", "Template Registry not loaded.")
            return
            
        templates = self.template_registry.get_all_template_names()
        if not templates:
            QMessageBox.warning(self, "Error", "No scraping templates found in scraper/ directory.")
            return

        name, ok = QInputDialog.getText(self, "Add Project", "Project Name:")
        if ok and name:
            template_name, temp_ok = QInputDialog.getItem(self, "Select Template", "Template:", templates, 0, False)
            if temp_ok and template_name:
                raw_data = self.template_registry.get_raw_template_data(template_name)
                # Overwrite save_path to keep projects isolated
                raw_data["save_path"] = f"downloads/{name}"
                raw_data["db_path"] = "data.db"
                
                project_id = self.db.create_project(name, raw_data, raw_data.get("start_urls", []))
                if project_id != -1:
                    self.db.add_to_queue(project_id)
                    self._refresh_project_list()
                else:
                    QMessageBox.warning(self, "Error", "Project already exists.")

    @Slot()
    def open_settings(self):
        # Get selected project
        item = self.queue_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Select a project from the queue first.")
            return

        # Extract name from string "Name (status)" - purely for demo, ideally store ID in item data
        project_name = item.text().split(" (")[0]
        projects = self.db.get_all_projects()
        project = next((p for p in projects if p['name'] == project_name), None)
        
        if project:
            dlg = SettingsDialog(project['settings_json'], self)
            if dlg.exec():
                new_settings = dlg.get_settings()
                self.db.update_project_settings(project['id'], new_settings)
                self.log_view.append(f"Settings updated for project: {project_name}")


    @Slot()
    def remove_project(self):
        item = self.queue_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Select a project from the queue first.")
            return

        project_name = item.text().split(" (")[0]
        
        confirm = QMessageBox.question(
            self, 
            "Confirm Delete", 
            f"Are you sure you want to delete project '{project_name}'?\nThis will remove all scraped data and settings.",
            QMessageBox.Yes | QMessageBox.No
        )
        
        if confirm == QMessageBox.Yes:
            projects = self.db.get_all_projects()
            project = next((p for p in projects if p['name'] == project_name), None)
            
            if project:
                self.db.delete_project(project['id'])
                self._refresh_project_list()
                self.log_view.append(f"Deleted project: {project_name}")
            else:
                self.log_view.append(f"Error: Could not find project {project_name} to delete.")

    @Slot()
    def manage_start_urls(self):
        item = self.queue_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Select a project from the queue first.")
            return

        project_name = item.text().split(" (")[0]
        projects = self.db.get_all_projects()
        project = next((p for p in projects if p['name'] == project_name), None)
        
        if project:
            # We assume source of truth for start_urls is inside settings_json
            import json
            try:
                settings_dict = json.loads(project['settings_json'])
            except:
                settings_dict = {}
            
            start_urls = settings_dict.get('start_urls', [])
            
            dlg = StartUrlsDialog(start_urls, self)
            if dlg.exec():
                new_urls = dlg.get_urls()
                settings_dict['start_urls'] = new_urls
                
                # Update DB
                self.db.update_project_settings(project['id'], json.dumps(settings_dict))
                
                self.log_view.append(f"Updated Start URLs for {project_name}")
        else:
             QMessageBox.warning(self, "Error", "Project not found.")

    @Slot()
    def move_queue_item_up(self):
        self._move_queue_item(-1)

    @Slot()
    def move_queue_item_down(self):
        self._move_queue_item(1)

    def _move_queue_item(self, direction):
        row = self.queue_list.currentRow()
        if row < 0: return

        queue_items = self.db.get_queue()
        if row + direction < 0 or row + direction >= len(queue_items):
            return

        item_current = queue_items[row]
        item_target = queue_items[row + direction]

        self.db.update_queue_index(item_current['id'], item_target['order_index'])
        self.db.update_queue_index(item_target['id'], current_index := item_current['order_index']) # wait... logic fix
        # Actually it should be a proper swap
        self.db.update_queue_index(item_target['id'], item_current['order_index'])
        
        self._refresh_project_list()
        self.queue_list.setCurrentRow(row + direction)

    @Slot(int, str, int, int)
    def on_min_content_warning(self, project_id, url, current_size, min_size):
        self.log_view.append(f"WARNING: Content too small ({current_size} < {min_size}) on {url}")
        res = QMessageBox.warning(
            self,
            "Min Content Length Warning",
            f"Page content is smaller than minimum setting!\n\nURL: {url}\nSize: {current_size} bytes\nMin: {min_size} bytes\n\nContinue scraping?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if res == QMessageBox.Yes:
            if self.current_project_id == project_id and self.bus and self.loop:
                self.log_view.append("Resuming scraper...")
                cmd = ResumeScrapeCommand(project_id=project_id)
                asyncio.run_coroutine_threadsafe(self.bus.dispatch(cmd), self.loop)
        else:
            if self.current_project_id == project_id and self.bus and self.loop:
                self.log_view.append("Stopping scraper.")
                cmd = StopScrapeCommand(project_id=project_id)
                asyncio.run_coroutine_threadsafe(self.bus.dispatch(cmd), self.loop)

    def closeEvent(self, event):
        if self.task_manager and self.current_project_id:
            asyncio.run_coroutine_threadsafe(self.task_manager.stop_worker(self.current_project_id), self.loop)
        event.accept()

    @Slot()
    def export_project(self):
        item = self.queue_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Select a project from the queue first.")
            return

        project_id = item.data(Qt.UserRole)
        project_name = item.text().split(" (")[0]
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Project",
            f"{project_name}_export.db",
            "SQLite Database (*.db *.sqlite);;All Files (*)"
        )
        
        if file_path:
            success = self.db.export_project(project_id, file_path)
            if success:
                QMessageBox.information(self, "Success", f"Project exported to:\n{file_path}")
            else:
                QMessageBox.critical(self, "Error", "Export failed. Check logs.")


    @Slot()
    def export_project(self):
        item = self.queue_list.currentItem()
        if not item:
            QMessageBox.warning(self, "Warning", "Select a project from the queue first.")
            return

        project_id = item.data(Qt.UserRole)
        project_name = item.text().split(" (")[0]
        
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "Export Project",
            f"{project_name}_export.db",
            "SQLite Database (*.db *.sqlite);;All Files (*)"
        )
        
        if file_path:
            success = self.db.export_project(project_id, file_path)
            if success:
                QMessageBox.information(self, "Success", f"Project exported to:\n{file_path}")
            else:
                QMessageBox.critical(self, "Error", "Export failed. Check logs.")

    @Slot()
    def import_project(self):
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Project",
            "",
            "SQLite Database (*.db *.sqlite);;All Files (*)"
        )
        
        if file_path:
            # Conflict Resolution Callback
            def ask_user(name: str) -> str:
                box = QMessageBox(self)
                box.setWindowTitle("Project Conflict")
                box.setText(f"A project named '{name}' already exists.")
                box.setInformativeText("What would you like to do?")
                
                btn_rename = box.addButton("Rename (Create New)", QMessageBox.ActionRole)
                btn_merge = box.addButton("Merge into Existing", QMessageBox.ActionRole)
                btn_skip = box.addButton("Skip", QMessageBox.ActionRole)
                
                box.exec()
                
                if box.clickedButton() == btn_rename:
                    return 'rename'
                elif box.clickedButton() == btn_merge:
                    return 'merge'
                else:
                    return 'skip'

            success = self.db.import_project(file_path, conflict_callback=ask_user)
            
            if success:
                self._refresh_project_list()
                QMessageBox.information(self, "Success", "Project imported successfully.")
            else:
                QMessageBox.critical(self, "Error", "Import failed. Check logs.")
