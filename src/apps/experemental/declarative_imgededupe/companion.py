import sys
import os
import json
import shlex
import shutil
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, 
    QPushButton, QPlainTextEdit, QLabel, QFrame, QSplitter,
    QTabWidget, QTableWidget, QTableWidgetItem, QHeaderView
)
from PySide6.QtCore import QProcess, QProcessEnvironment, Qt, Signal, Slot
from PySide6.QtGui import QFont, QColor, QPalette

# VERSION: 1.3.0 (CAS Storage & Stability Update)

# Find project root (BCor directory)
try:
    PROJECT_ROOT = Path(__file__).resolve().parents[4]
except Exception:
    PROJECT_ROOT = Path.cwd()

class LogViewer(QPlainTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setMaximumBlockCount(2000)
        self.setLineWrapMode(QPlainTextEdit.NoWrap)
        self.setFont(QFont("Consolas", 10))
        self.setStyleSheet("""
            QPlainTextEdit {
                background-color: #1e1e1e;
                color: #d4d4d4;
                border: 1px solid #333;
                border-radius: 4px;
            }
        """)

class TaskMonitor(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(5)
        self.setHorizontalHeaderLabels(["Task ID", "Name", "Status", "Time", "Details"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setSelectionBehavior(QTableWidget.SelectRows)
        self.setAlternatingRowColors(True)
        self.setSortingEnabled(True)
        self.setStyleSheet("""
            QTableWidget {
                background-color: #252526;
                color: #cccccc;
                gridline-color: #3e3e42;
                border: none;
            }
            QHeaderView::section {
                background-color: #333333;
                color: #ffffff;
                padding: 4px;
                border: 1px solid #3e3e42;
            }
        """)
        self.tasks = {} # task_id -> row_index

    @Slot(dict)
    def update_task(self, event):
        task_id = event.get("task_id")
        if not task_id: return
        
        event_type = event.get("event")
        
        if task_id not in self.tasks:
            row = self.rowCount()
            self.insertRow(row)
            self.tasks[task_id] = row
            self.setItem(row, 0, QTableWidgetItem(str(task_id)[:8] + "..."))
            self.setItem(row, 1, QTableWidgetItem(event.get("task_name", "Unknown")))
            self.setItem(row, 2, QTableWidgetItem("Queued"))
            self.setItem(row, 3, QTableWidgetItem("-"))
            self.setItem(row, 4, QTableWidgetItem(""))
        
        row = self.tasks[task_id]
        
        if event_type == "started":
            self.item(row, 2).setText("Running")
            self.item(row, 2).setForeground(QColor("#007acc"))
        elif event_type == "executed":
            status = event.get("status", "Unknown")
            self.item(row, 2).setText(status.capitalize())
            if status == "success":
                self.item(row, 2).setForeground(QColor("#89d185"))
            else:
                self.item(row, 2).setForeground(QColor("#f14c4c"))
            
            self.item(row, 3).setText(f"{event.get('execution_time', 0):.2f}s")
            self.item(row, 4).setText(event.get("error") or "Success")

class AIProgressMonitor(QTableWidget):
    """Monitors structured [BCOR_AI] logs from TaskIQ workers."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setColumnCount(4)
        self.setHorizontalHeaderLabels(["Model", "Task", "File / Length", "Status"])
        self.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.setEditTriggers(QTableWidget.NoEditTriggers)
        self.setAlternatingRowColors(True)
        self.setStyleSheet("""
            QTableWidget { background-color: #252526; color: #cccccc; gridline-color: #3e3e42; border: none; }
            QHeaderView::section { background-color: #333333; color: #ffffff; padding: 4px; border: 1px solid #3e3e42; }
        """)
        self.active_tasks = {} # task_key -> row_index

    @Slot(str)
    def parse_log_line(self, line: str):
        if "[BCOR_AI:" not in line: return
        
        try:
            # Format: [BCOR_AI:STARTED] model=moondream task=describe file=example.webp
            parts = line.split("] ", 1)
            header = parts[0].split(":")[-1]
            params = {}
            if len(parts) > 1:
                # Naive param parser
                for p in parts[1].split():
                    if "=" in p:
                        k, v = p.split("=", 1)
                        params[k] = v
            
            task_type = params.get("task", "unknown")
            model = params.get("model", "unknown")
            
            key = f"{model}_{task_type}"
            
            if header == "STARTED":
                if key not in self.active_tasks:
                    row = self.rowCount()
                    self.insertRow(row)
                    self.active_tasks[key] = row
                    self.setItem(row, 0, QTableWidgetItem(f"🤖 {model}"))
                    self.setItem(row, 1, QTableWidgetItem(task_type.capitalize()))
                
                row = self.active_tasks[key]
                file_info = params.get("file") or f"Len: {params.get('text_len', '0')}"
                self.setItem(row, 2, QTableWidgetItem(file_info))
                self.setItem(row, 3, QTableWidgetItem("⚡ Processing..."))
                self.item(row, 3).setForeground(QColor("#007acc"))
            
            elif header == "FINISHED" and key in self.active_tasks:
                row = self.active_tasks[key]
                self.setItem(row, 3, QTableWidgetItem("✅ Ready"))
                self.item(row, 3).setForeground(QColor("#89d185"))
            
            elif header == "FAILED" and key in self.active_tasks:
                row = self.active_tasks[key]
                self.setItem(row, 3, QTableWidgetItem(f"❌ Error: {params.get('error', 'Unknown')}"))
                self.item(row, 3).setForeground(QColor("#f14c4c"))
                
        except Exception:
            pass

class ServicePanel(QFrame):
    taskEvent = Signal(dict)
    aiLogEvent = Signal(str)

    def __init__(self, name, command, parent=None):
        super().__init__(parent)
        self.name = name
        self.command = command
        self.process = QProcess(self)
        self.process.setProcessChannelMode(QProcess.MergedChannels)
        self.process.readyReadStandardOutput.connect(self.handle_output)
        self.process.finished.connect(self.handle_finished)
        self.process.errorOccurred.connect(self.handle_error)
        
        self.setFrameShape(QFrame.StyledPanel)
        self.setStyleSheet("""
            ServicePanel {
                background-color: #252526;
                border: 1px solid #3e3e42;
                border-radius: 8px;
            }
            QLabel { color: #cccccc; font-weight: bold; }
        """)
        
        layout = QVBoxLayout(self)
        header = QHBoxLayout()
        self.status_label = QLabel("●")
        self.status_label.setStyleSheet("color: #555;")
        header.addWidget(self.status_label)
        header.addWidget(QLabel(name))
        header.addStretch()
        
        self.start_btn = QPushButton("Start")
        self.start_btn.clicked.connect(self.start_service)
        header.addWidget(self.start_btn)
        
        self.stop_btn = QPushButton("Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_service)
        header.addWidget(self.stop_btn)

        self.restart_btn = QPushButton("Restart")
        self.restart_btn.setEnabled(False)
        self.restart_btn.clicked.connect(self.restart_service)
        header.addWidget(self.restart_btn)
        
        layout.addLayout(header)
        self.log_viewer = LogViewer()
        layout.addWidget(self.log_viewer)

    def handle_output(self):
        data = self.process.readAllStandardOutput()
        stdout = data.data().decode("utf-8", errors="replace")
        for line in stdout.splitlines():
            # Check for monitoring events
            if "[BCOR_TASK]" in line:
                try:
                    json_str = line.split("[BCOR_TASK] ", 1)[1]
                    event = json.loads(json_str)
                    self.taskEvent.emit(event)
                except Exception:
                    pass
            
            # Check for AI logging tags
            if "[BCOR_AI:" in line:
                self.aiLogEvent.emit(line)

            self.log_viewer.appendPlainText(line)

    def handle_error(self, error):
        self.log_viewer.appendPlainText(f"\n[ERROR] Process Error ({error}): {self.process.errorString()}")

    def handle_finished(self):
        self.status_label.setStyleSheet("color: #f14c4c;")
        self.start_btn.setEnabled(True)
        self.stop_btn.setEnabled(False)
        self.restart_btn.setEnabled(False)
        self.log_viewer.appendPlainText(f"\n[SYSTEM] {self.name} finished.")

    def start_service(self):
        self.log_viewer.clear()
        env = QProcessEnvironment.systemEnvironment()
        env.insert("PYTHONPATH", str(PROJECT_ROOT))
        env.insert("BCOR_GUI_MONITOR", "1") # Enable the local monitor middleware
        
        uv_exe = shutil.which("uv") or r"C:\Users\User\.local\bin\uv.exe"
        if not os.path.exists(uv_exe):
            self.log_viewer.appendPlainText(f"[ERROR] 'uv' not found at {uv_exe}")
            return

        self.process.setProcessEnvironment(env)
        self.process.setWorkingDirectory(str(PROJECT_ROOT))
        
        clean_cmd = self.command[3:] if self.command.startswith("uv ") else self.command
        args = shlex.split(clean_cmd)
        
        self.log_viewer.appendPlainText(f"[SYSTEM] Executing: {uv_exe} {' '.join(args)}")
        self.process.start(uv_exe, args)
        
        if self.process.waitForStarted(10000):
            self.status_label.setStyleSheet("color: #89d185;")
            self.start_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.restart_btn.setEnabled(True)

    def stop_service(self):
        self.process.terminate()

    def restart_service(self):
        self.log_viewer.appendPlainText(f"\n[SYSTEM] Restarting {self.name}...")
        self.process.terminate()
        # Wait for finish signal to re-start, or force it if it takes too long
        if self.process.waitForFinished(3000):
            self.start_service()
        else:
            self.process.kill()
            self.start_service()

class CompanionWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BCor Unified Management Console [v1.3.0]")
        self.resize(1100, 800)
        
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)
        
        self.setStyleSheet("""
            QMainWindow { background-color: #1e1e1e; }
            QTabWidget::pane { border: 1px solid #3e3e42; background: #252526; }
            QTabBar::tab { background: #2d2d2d; color: #888; padding: 10px 20px; }
            QTabBar::tab:selected { background: #1e1e1e; color: #fff; border-bottom: 2px solid #007acc; }
        """)
        
        self.tabs = QTabWidget()
        
        # TAB 1: SERVICES
        service_tab = QWidget()
        service_layout = QVBoxLayout(service_tab)
        self.worker_panel = ServicePanel(
            "TaskIQ Worker", 
            "uv run taskiq worker src.modules.agm.tasks:broker --reload"
        )
        service_layout.addWidget(self.worker_panel)
        self.tabs.addTab(service_tab, "Services")
        
        # TAB 2: MONITORING
        monitor_tab = QWidget()
        monitor_layout = QVBoxLayout(monitor_tab)
        self.task_monitor = TaskMonitor()
        monitor_layout.addWidget(self.task_monitor)
        self.tabs.addTab(monitor_tab, "Task Live View")

        # TAB 3: OLLAMA / AI STATUS
        ai_tab = QWidget()
        ai_layout = QVBoxLayout(ai_tab)
        self.ai_monitor = AIProgressMonitor()
        ai_layout.addWidget(QLabel("Ollama / local-AI Live Observability"))
        ai_layout.addWidget(self.ai_monitor)
        self.tabs.addTab(ai_tab, "AI Status")
        
        # Connect worker events
        self.worker_panel.taskEvent.connect(self.task_monitor.update_task)
        self.worker_panel.aiLogEvent.connect(self.ai_monitor.parse_log_line)
        
        main_layout.addWidget(self.tabs)
        
        # Footer
        footer = QHBoxLayout()
        footer.addWidget(QLabel("Infrastructure: NATS (4222) / Redis (6380) | Local Monitor: ENABLED"))
        main_layout.addLayout(footer)

def main():
    app = QApplication(sys.argv)
    window = CompanionWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
