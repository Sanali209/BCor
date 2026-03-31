import os
from PySide6.QtWidgets import QDialog, QVBoxLayout, QHBoxLayout, QLabel, QPushButton
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt

class DupeDialog(QDialog):
    def __init__(self, new_image_path, conflicts, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Duplicate Resolved Required")
        self.resize(800, 400)
        self.result_action = None
        
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("A similar image was found in another project/location."))
        
        # Image Comparison Area
        img_layout = QHBoxLayout()
        
        # New Image
        new_layout = QVBoxLayout()
        new_layout.addWidget(QLabel("New Candidate"))
        lbl_new_img = QLabel()
        pm_new = QPixmap(new_image_path)
        if not pm_new.isNull():
            lbl_new_img.setPixmap(pm_new.scaled(300, 300, Qt.KeepAspectRatio))
        else:
            lbl_new_img.setText(f"Failed to load: {new_image_path}")
        new_layout.addWidget(lbl_new_img)
        img_layout.addLayout(new_layout)
        
        # Existing Image(s) - Just show first conflict for now
        existing_layout = QVBoxLayout()
        existing_conf = conflicts[0]
        existing_layout.addWidget(QLabel(f"Existing (Project: {existing_conf.get('project_name')})"))
        lbl_ex_img = QLabel()
        # Existing might be relative, need absolute. conflict dict has 'absolute_path' usually if we stored it?
        # Database.get_all_other_hashes alias file_path as relative_path.
        # But for 'existing' conflicts, we need to know the ROOT path to reconstruct absolute. 
        # Actually deduplication.py 'row' data comes from DB. 
        # We might need to query the project save_path or if 'absolute_path' is empty in DB?
        # Let's try 'absolute_path' key first (added in my recent check in scraper logic?)
        # Wait, get_all_other_hashes did NOT select absolute_path in my fix step 564. I REMOVED it.
        # So we only have 'relative_path' and 'project_id'. 
        # But we need ABSOLUTE path to display.
        # We can try to guess it or pass project root map? 
        # For now, let's just try to display path text if image fails. 
        # Or, we can fetch project path on the fly? That's slow.
        # Let's assume 'file_path' stored IS the full path? No, standard is relative.
        # Compromise: Just show path text for existing if we can't easily resolve.
        # WAIT! User said "preview both".
        # I need to fetch the project save path.
        
        ex_path_rel = existing_conf.get('file_path') or existing_conf.get('relative_path')
        save_path = existing_conf.get('save_path')
        
        ex_full_path = None
        if save_path and ex_path_rel:
            ex_full_path = os.path.join(save_path, ex_path_rel)
            
        if ex_full_path and os.path.exists(ex_full_path):
             pm_ex = QPixmap(ex_full_path)
             if not pm_ex.isNull():
                 lbl_ex_img.setPixmap(pm_ex.scaled(300, 300, Qt.KeepAspectRatio))
             else:
                 lbl_ex_img.setText(f"Failed to load: {ex_full_path}")
        else:
             lbl_ex_img.setText(f"[Existing Image]\n{ex_path_rel}\n(File not found or path missing)\nFull: {ex_full_path}")
        
        existing_layout.addWidget(lbl_ex_img)
        img_layout.addLayout(existing_layout)
        
        layout.addLayout(img_layout)
        
        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_keep_existing = QPushButton("Keep Existing (Skip New)")
        btn_replace = QPushButton("Replace Existing")
        btn_keep_both = QPushButton("Keep Both")
        
        btn_layout.addWidget(btn_keep_existing)
        btn_layout.addWidget(btn_replace)
        btn_layout.addWidget(btn_keep_both)
        layout.addLayout(btn_layout)
        
        # Connections
        btn_keep_existing.clicked.connect(lambda: self.done_with_action("SKIP"))
        btn_replace.clicked.connect(lambda: self.done_with_action("REPLACE"))
        btn_keep_both.clicked.connect(lambda: self.done_with_action("BOTH"))

    def done_with_action(self, action):
        self.result_action = action
        self.accept()

    def get_result(self):
        return self.result_action
