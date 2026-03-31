from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QListWidget, 
                               QPushButton, QInputDialog, QMessageBox, QListWidgetItem,
                               QFormLayout, QLineEdit, QLabel)
from PySide6.QtCore import Qt, Slot

class UrlPairDialog(QDialog):
    def __init__(self, forward="", backward="", parent=None):
        super().__init__(parent)
        self.setWindowTitle("Edit Start URLs")
        self.resize(500, 150)
        self.forward_url = forward
        self.backward_url = backward
        
        layout = QVBoxLayout(self)
        form = QFormLayout()
        
        self.inp_forward = QLineEdit(forward)
        form.addRow("Forward URL:", self.inp_forward)
        
        self.inp_backward = QLineEdit(backward)
        form.addRow("Backward URL:", self.inp_backward)
        
        layout.addLayout(form)
        
        btns = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        btns.addStretch()
        btns.addWidget(save_btn)
        btns.addWidget(cancel_btn)
        layout.addLayout(btns)
        
        save_btn.clicked.connect(self.accept)
        cancel_btn.clicked.connect(self.reject)

    def get_urls(self):
        return {
            "forward": self.inp_forward.text().strip(),
            "backward": self.inp_backward.text().strip()
        }

class StartUrlsDialog(QDialog):
    def __init__(self, urls: list, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Start URLs")
        self.resize(600, 400)
        # self.urls can contain strs or dicts
        self.urls = urls[:] 
        
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # List Widget
        self.url_list = QListWidget()
        self.url_list.doubleClicked.connect(self.edit_url)
        self.refresh_list()
        layout.addWidget(self.url_list)

        # Buttons
        btn_layout = QHBoxLayout()
        self.btn_add = QPushButton("Add")
        self.btn_edit = QPushButton("Edit")
        self.btn_remove = QPushButton("Remove")
        self.btn_up = QPushButton("Move Up")
        self.btn_down = QPushButton("Move Down")
        
        btn_layout.addWidget(self.btn_add)
        btn_layout.addWidget(self.btn_edit)
        btn_layout.addWidget(self.btn_remove)
        btn_layout.addWidget(self.btn_up)
        btn_layout.addWidget(self.btn_down)
        layout.addLayout(btn_layout)

        # Dialog Buttons
        dialog_btns = QHBoxLayout()
        self.btn_save = QPushButton("Save")
        self.btn_cancel = QPushButton("Cancel")
        dialog_btns.addStretch()
        dialog_btns.addWidget(self.btn_save)
        dialog_btns.addWidget(self.btn_cancel)
        layout.addLayout(dialog_btns)

        # Signals
        self.btn_add.clicked.connect(self.add_url)
        self.btn_edit.clicked.connect(self.edit_url)
        self.btn_remove.clicked.connect(self.remove_url)
        self.btn_up.clicked.connect(self.move_up)
        self.btn_down.clicked.connect(self.move_down)
        self.btn_save.clicked.connect(self.accept)
        self.btn_cancel.clicked.connect(self.reject)

    def refresh_list(self):
        self.url_list.clear()
        for item in self.urls:
            if isinstance(item, dict):
                label = f"[Fwd]: {item.get('forward','')} \n[Bwd]: {item.get('backward','')}"
            else:
                label = f"[Legacy]: {item}"
            self.url_list.addItem(label)

    @Slot()
    def add_url(self):
        dlg = UrlPairDialog(parent=self)
        if dlg.exec():
            self.urls.append(dlg.get_urls())
            self.refresh_list()

    @Slot()
    def edit_url(self):
        row = self.url_list.currentRow()
        if row < 0: return
        
        item = self.urls[row]
        fwd = item.get('forward', '') if isinstance(item, dict) else str(item)
        bwd = item.get('backward', '') if isinstance(item, dict) else ""
        
        dlg = UrlPairDialog(fwd, bwd, self)
        if dlg.exec():
            self.urls[row] = dlg.get_urls()
            self.refresh_list()

    @Slot()
    def remove_url(self):
        row = self.url_list.currentRow()
        if row >= 0:
            self.urls.pop(row)
            self.refresh_list()

    @Slot()
    def move_up(self):
        row = self.url_list.currentRow()
        if row > 0:
            self.urls[row], self.urls[row-1] = self.urls[row-1], self.urls[row]
            self.refresh_list()
            self.url_list.setCurrentRow(row-1)

    @Slot()
    def move_down(self):
        row = self.url_list.currentRow()
        if row < len(self.urls) - 1 and row >= 0:
            self.urls[row], self.urls[row+1] = self.urls[row+1], self.urls[row]
            self.refresh_list()
            self.url_list.setCurrentRow(row+1)

    def get_urls(self):
        return self.urls
