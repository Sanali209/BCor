import logging
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QComboBox, 
                             QPushButton, QLabel, QSpinBox, QListWidget, 
                             QGroupBox, QFormLayout, QLineEdit, QCheckBox,
                             QListWidgetItem)
from PySide6.QtCore import Qt, Signal

from core.batch_engine import (Rule, AreaCondition, SizeCondition, FormatCondition, 
                             DeleteAction, ConvertAction, ScaleAction, ConflictStrategy)

logger = logging.getLogger(__name__)

class RuleEditorWidget(QWidget):
    rules_changed = Signal(list) # Emits List[Rule]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.rules = []
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)
        
        # 1. Rule Creation Form
        form_group = QGroupBox("Create New Rule")
        form_layout = QVBoxLayout(form_group)
        
        # Condition Row
        cond_layout = QHBoxLayout()
        cond_layout.addWidget(QLabel("IF"))
        self.combo_cond = QComboBox()
        self.combo_cond.addItems(["Area Range", "File Size Range", "Format Matches"])
        self.combo_cond.currentIndexChanged.connect(self.update_cond_inputs)
        cond_layout.addWidget(self.combo_cond)
        
        self.cond_params_widget = QWidget() # Placeholder for params
        cond_layout.addWidget(self.cond_params_widget)
        
        form_layout.addLayout(cond_layout)
        self.cond_layout_container = cond_layout # Keep ref to add params
        
        # Action Row
        act_layout = QHBoxLayout()
        act_layout.addWidget(QLabel("THEN"))
        self.combo_act = QComboBox()
        self.combo_act.addItems(["Delete File", "Convert Format", "Scale Image"])
        self.combo_act.currentIndexChanged.connect(self.update_act_inputs)
        act_layout.addWidget(self.combo_act)
        
        self.act_params_widget = QWidget() # Placeholder
        act_layout.addWidget(self.act_params_widget)
        
        form_layout.addLayout(act_layout)
        self.act_layout_container = act_layout
        
        # Add Button
        btn_add = QPushButton("Add Rule to Chain")
        btn_add.setStyleSheet("background-color: #59a14f; color: white; font-weight: bold; padding: 5px;")
        btn_add.clicked.connect(self.add_rule)
        form_layout.addWidget(btn_add)
        
        layout.addWidget(form_group)
        
        # 2. Rule List (The "Tree" of logic)
        self.list_rules = QListWidget()
        self.list_rules.setStyleSheet("background-color: #2d2d2d; border: 1px solid #3d3d3d;")
        layout.addWidget(QLabel("Active Processing Rules:"))
        layout.addWidget(self.list_rules)
        
        # Remove Button
        btn_remove = QPushButton("Remove Selected Rule")
        btn_remove.clicked.connect(self.remove_rule)
        layout.addWidget(btn_remove)
        
        # Init inputs
        self.update_cond_inputs()
        self.update_act_inputs()

    def update_cond_inputs(self):
        # Clear old params
        if self.cond_params_widget:
            self.cond_params_widget.deleteLater()
            self.cond_layout_container.removeWidget(self.cond_params_widget)
            
        self.cond_params_widget = QWidget()
        layout = QHBoxLayout(self.cond_params_widget)
        layout.setContentsMargins(0,0,0,0)
        
        choice = self.combo_cond.currentText()
        if choice == "Area Range":
            # Min Area (Width x Height)
            layout.addWidget(QLabel("Min W:"))
            self.spin_min_w = QSpinBox()
            self.spin_min_w.setRange(0, 100000)
            self.spin_min_w.setValue(0)
            layout.addWidget(self.spin_min_w)
            
            layout.addWidget(QLabel("×"))
            self.spin_min_h = QSpinBox()
            self.spin_min_h.setRange(0, 100000)
            self.spin_min_h.setValue(0)
            layout.addWidget(self.spin_min_h)
            
            layout.addWidget(QLabel("  Max W:"))
            self.spin_max_w = QSpinBox()
            self.spin_max_w.setRange(0, 100000)
            self.spin_max_w.setValue(10000)
            layout.addWidget(self.spin_max_w)
            
            layout.addWidget(QLabel("×"))
            self.spin_max_h = QSpinBox()
            self.spin_max_h.setRange(0, 100000)
            self.spin_max_h.setValue(10000)
            layout.addWidget(self.spin_max_h)
        elif choice == "File Size Range":
            self.spin_size_min = QSpinBox()
            self.spin_size_min.setRange(0, 100_000_000_000)
            self.spin_size_max = QSpinBox()
            self.spin_size_max.setRange(0, 100_000_000_000)
            self.spin_size_max.setValue(100_000_000_000)
            layout.addWidget(QLabel("Min Bytes:"))
            layout.addWidget(self.spin_size_min)
            layout.addWidget(QLabel("Max Bytes:"))
            layout.addWidget(self.spin_size_max)
        elif choice == "Format Matches":
            self.edit_formats = QLineEdit("jpg, jpeg, png")
            self.chk_invert = QCheckBox("NOT")
            layout.addWidget(self.chk_invert)
            layout.addWidget(self.edit_formats)
            
        self.cond_layout_container.addWidget(self.cond_params_widget)

    def update_act_inputs(self):
        if self.act_params_widget:
            self.act_params_widget.deleteLater()
            self.act_layout_container.removeWidget(self.act_params_widget)
            
        self.act_params_widget = QWidget()
        layout = QHBoxLayout(self.act_params_widget)
        layout.setContentsMargins(0,0,0,0)
        
        choice = self.combo_act.currentText()
        if choice == "Convert Format":
            self.combo_fmt = QComboBox()
            self.combo_fmt.addItems([".jpg", ".png", ".webp", ".bmp", ".tiff"])
            layout.addWidget(QLabel("To:"))
            layout.addWidget(self.combo_fmt)
            
            self.chk_delete_original = QCheckBox("Delete Original")
            layout.addWidget(self.chk_delete_original)
        elif choice == "Scale Image":
            self.spin_w = QSpinBox()
            self.spin_w.setRange(1, 10000)
            self.spin_w.setValue(1920)
            self.spin_h = QSpinBox()
            self.spin_h.setRange(1, 10000)
            self.spin_h.setValue(1080)
            layout.addWidget(QLabel("Max W:"))
            layout.addWidget(self.spin_w)
            layout.addWidget(QLabel("Max H:"))
            layout.addWidget(self.spin_h)
            
        self.act_layout_container.addWidget(self.act_params_widget)

    def add_rule(self):
        # Build Condition
        cond_choice = self.combo_cond.currentText()
        condition = None
        if cond_choice == "Area Range":
            min_area = self.spin_min_w.value() * self.spin_min_h.value()
            max_area = self.spin_max_w.value() * self.spin_max_h.value()
            condition = AreaCondition(min_area, max_area)
        elif cond_choice == "File Size Range":
            condition = SizeCondition(self.spin_size_min.value(), self.spin_size_max.value())
        elif cond_choice == "Format Matches":
            fmts = [f.strip() for f in self.edit_formats.text().split(',')]
            condition = FormatCondition(fmts, self.chk_invert.isChecked())
            
        # Build Action
        act_choice = self.combo_act.currentText()
        action = None
        if act_choice == "Delete File":
            action = DeleteAction()
        elif act_choice == "Convert Format":
            delete_orig = self.chk_delete_original.isChecked()
            action = ConvertAction(self.combo_fmt.currentText(), delete_original=delete_orig)
        elif act_choice == "Scale Image":
            action = ScaleAction(self.spin_w.value(), self.spin_h.value())
            
        if condition and action:
            rule = Rule(condition, action)
            self.rules.append(rule)
            self.update_list()
            self.rules_changed.emit(self.rules)

    def remove_rule(self):
        row = self.list_rules.currentRow()
        if row >= 0:
            self.rules.pop(row)
            self.update_list()
            self.rules_changed.emit(self.rules)

    def update_list(self):
        self.list_rules.clear()
        for rule in self.rules:
            text = f"IF {rule.condition.description()} THEN {rule.action.description()}"
            item = QListWidgetItem(text)
            self.list_rules.addItem(item)

    def set_rules(self, rules: list):
        """Load a list of rules into the editor."""
        self.rules = list(rules) # Copy
        self.update_list()
        self.rules_changed.emit(self.rules)
