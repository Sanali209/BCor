import json
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QLabel, QLineEdit, QPushButton, 
                               QHBoxLayout, QTextEdit, QTabWidget, QWidget, QFormLayout, 
                               QComboBox, QSpinBox, QDoubleSpinBox, QCheckBox, QMessageBox,
                               QListWidget, QListWidgetItem, QGroupBox)
from PySide6.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, settings_json_str, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Project Settings")
        self.resize(600, 500)
        
        try:
            self.settings = json.loads(settings_json_str)
        except:
            self.settings = {}

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        main_layout = QVBoxLayout(self)
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Tab 1: General
        self.tab_general = QWidget()
        form_gen = QFormLayout(self.tab_general)
        self.inp_save_path = QLineEdit()
        form_gen.addRow("Save Path:", self.inp_save_path)
        
        self.inp_filename_pattern = QLineEdit()
        self.inp_filename_pattern.setToolTip("Example: {tags_copyright}/{tags_artist}_{topic_id}.{ext}")
        form_gen.addRow("Filename Pattern:", self.inp_filename_pattern)

        self.tabs.addTab(self.tab_general, "General")

        # Tab 2: Scraping
        self.tab_scraping = QWidget()
        form_scr = QFormLayout(self.tab_scraping)
        
        self.combo_direction = QComboBox()
        self.combo_direction.addItems(["forward", "backward"])
        form_scr.addRow("Direction:", self.combo_direction)
        
        self.inp_delay_page = QDoubleSpinBox()
        self.inp_delay_page.setRange(0, 60)
        form_scr.addRow("Delay (List Pages) [s]:", self.inp_delay_page)
        
        self.inp_delay_topic = QDoubleSpinBox()
        self.inp_delay_topic.setRange(0, 60)
        form_scr.addRow("Delay (Topics) [s]:", self.inp_delay_topic)
        
        self.inp_threshold = QSpinBox()
        self.inp_threshold.setRange(0, 64)
        self.inp_threshold.setToolTip("0 = Exact Match. Higher = Looser Match (Hamming Distance)")
        form_scr.addRow("Deduplication Threshold:", self.inp_threshold)

        self.inp_threshold.setToolTip("0 = Exact Match. Higher = Looser Match (Hamming Distance)")
        form_scr.addRow("Deduplication Threshold:", self.inp_threshold)

        self.inp_exclude_ext = QLineEdit()
        self.inp_exclude_ext.setToolTip("Comma separated list, e.g. mp4, webm")
        form_scr.addRow("Exclude Extensions:", self.inp_exclude_ext)

        # Delays (Extra)
        form_scr.addRow(QLabel("<b>Advanced Delays</b>"))
        self.inp_delay_manual = QSpinBox()
        form_scr.addRow("Initial Manual Delay [s]:", self.inp_delay_manual)
        
        layout_dl = QHBoxLayout()
        self.inp_dl_min = QDoubleSpinBox()
        self.inp_dl_max = QDoubleSpinBox()
        layout_dl.addWidget(QLabel("Min:"))
        layout_dl.addWidget(self.inp_dl_min)
        layout_dl.addWidget(QLabel("Max:"))
        layout_dl.addWidget(self.inp_dl_max)
        form_scr.addRow("Download Delay Range [s]:", layout_dl)
        
        layout_pause = QHBoxLayout()
        self.inp_pause_pages = QSpinBox()
        self.inp_pause_sec = QSpinBox()
        layout_pause.addWidget(QLabel("Every N Pages:"))
        layout_pause.addWidget(self.inp_pause_pages)
        layout_pause.addWidget(QLabel("Pause [s]:"))
        layout_pause.addWidget(self.inp_pause_sec)
        form_scr.addRow("Long Pause:", layout_pause)

        # Limits & Timeouts
        form_scr.addRow(QLabel("<b>Limits & Timeouts</b>"))
        
        self.inp_nav_timeout = QSpinBox()
        self.inp_nav_timeout.setRange(1000, 300000)
        self.inp_nav_timeout.setSingleStep(1000)
        form_scr.addRow("Nav Timeout [ms]:", self.inp_nav_timeout)
        
        self.inp_dl_timeout = QSpinBox()
        self.inp_dl_timeout.setRange(1000, 300000)
        self.inp_dl_timeout.setSingleStep(1000)
        form_scr.addRow("Download Timeout [ms]:", self.inp_dl_timeout)
        
        self.inp_min_topic = QSpinBox()
        self.inp_min_topic.setRange(0, 999999)
        form_scr.addRow("Min Topic Content [bytes]:", self.inp_min_topic)
        
        self.inp_min_list = QSpinBox()
        self.inp_min_list.setRange(0, 999999)
        form_scr.addRow("Min List Content [bytes]:", self.inp_min_list)

        self.tabs.addTab(self.tab_scraping, "Scraping")

        # Tab 3: Selectors
        self.tab_selectors = QWidget()
        form_sel = QFormLayout(self.tab_selectors)
        self.inp_sel_next = QLineEdit()
        form_sel.addRow("Pagination Next:", self.inp_sel_next)
        self.inp_sel_prev = QLineEdit()
        form_sel.addRow("Pagination Prev:", self.inp_sel_prev)
        self.inp_sel_topic = QLineEdit()
        form_sel.addRow("Topic Preview:", self.inp_sel_topic)
        self.inp_sel_link = QLineEdit()
        form_sel.addRow("Topic Link:", self.inp_sel_link)
        self.inp_sel_captcha = QLineEdit()
        form_sel.addRow("Captcha Selector:", self.inp_sel_captcha)
        
        self.tabs.addTab(self.tab_selectors, "Selectors")

        # Tab 4: Fields (New)
        self.tab_fields = QWidget()
        layout_fields = QHBoxLayout(self.tab_fields)
        
        # Left: List
        layout_left = QVBoxLayout()
        self.list_fields = QListWidget()
        layout_left.addWidget(self.list_fields)
        
        btn_layout_f = QHBoxLayout()
        self.btn_add_field = QPushButton("Add")
        self.btn_remove_field = QPushButton("Remove")
        btn_layout_f.addWidget(self.btn_add_field)
        btn_layout_f.addWidget(self.btn_remove_field)
        layout_left.addLayout(btn_layout_f)
        
        layout_fields.addLayout(layout_left, 1) # Stretch 1
        
        # Right: Form
        self.grp_field = QGroupBox("Field Configuration")
        form_f = QFormLayout(self.grp_field)
        
        self.inp_f_name = QLineEdit()
        form_f.addRow("Name:", self.inp_f_name)
        
        self.inp_f_selector = QLineEdit()
        form_f.addRow("Selector:", self.inp_f_selector)
        
        self.inp_f_type = QComboBox()
        self.inp_f_type.addItems(["text", "resource_url", "html"])
        form_f.addRow("Type:", self.inp_f_type)
        
        self.inp_f_attr = QLineEdit()
        form_f.addRow("Attribute (opt):", self.inp_f_attr)
        
        self.inp_f_regex = QLineEdit()
        form_f.addRow("Regex Filter (opt):", self.inp_f_regex)
        
        self.chk_f_multi = QCheckBox("Multiple Results")
        form_f.addRow("Multiple:", self.chk_f_multi)
        
        self.chk_f_prepend = QCheckBox("Prepend Field Name to Value")
        form_f.addRow(self.chk_f_prepend)
        
        self.inp_f_delimiter = QLineEdit()
        self.inp_f_delimiter.setPlaceholderText("Delimiter (default: \\)")
        form_f.addRow("Prepend Delimiter:", self.inp_f_delimiter)
        
        self.chk_f_is_tag = QCheckBox("Is Tag (Write to Metadata)")
        form_f.addRow(self.chk_f_is_tag)
        
        layout_fields.addWidget(self.grp_field, 2) # Stretch 2
        self.tabs.addTab(self.tab_fields, "Fields")
        
        # Connects for Fields
        self.list_fields.currentItemChanged.connect(self.on_field_selected)
        self.btn_add_field.clicked.connect(self.add_field)
        self.btn_remove_field.clicked.connect(self.remove_field)
        
        # Update config on change
        self.inp_f_name.textChanged.connect(self.save_current_field)
        self.inp_f_selector.textChanged.connect(self.save_current_field)
        self.inp_f_type.currentTextChanged.connect(self.save_current_field)
        self.inp_f_attr.textChanged.connect(self.save_current_field)
        self.inp_f_regex.textChanged.connect(self.save_current_field)
        self.inp_f_regex.textChanged.connect(self.save_current_field)
        self.chk_f_multi.toggled.connect(self.save_current_field)
        self.chk_f_prepend.toggled.connect(self.save_current_field)
        self.inp_f_delimiter.textChanged.connect(self.save_current_field)
        self.chk_f_is_tag.toggled.connect(self.save_current_field)

        # Tab 4: JSON (Advanced)
        self.tab_json = QWidget()
        layout_json = QVBoxLayout(self.tab_json)
        self.editor = QTextEdit()
        layout_json.addWidget(self.editor)
        self.tabs.addTab(self.tab_json, "JSON (Advanced)")

        # Buttons
        btn_layout = QHBoxLayout()
        save_btn = QPushButton("Save")
        cancel_btn = QPushButton("Cancel")
        btn_layout.addWidget(save_btn)
        btn_layout.addWidget(cancel_btn)
        main_layout.addLayout(btn_layout)
        
        save_btn.clicked.connect(self.save)
        cancel_btn.clicked.connect(self.reject)
        
        # When switching TO JSON tab, update JSON from fields
        self.tabs.currentChanged.connect(self.on_tab_changed)

    def load_data(self):
        # General
        self.inp_save_path.setText(self.settings.get("save_path", ""))
        self.inp_filename_pattern.setText(self.settings.get("resource_save_path_pattern", ""))
        
        # Scraping
        direction = self.settings.get("scraping_direction", "forward")
        idx = self.combo_direction.findText(direction)
        if idx >= 0: self.combo_direction.setCurrentIndex(idx)
        
        delays = self.settings.get("delays", {})
        self.inp_delay_page.setValue(delays.get("delay_between_list_pages_s", 2.0))
        self.inp_delay_topic.setValue(delays.get("delay_between_topics_s", 1.0))
        self.inp_delay_manual.setValue(delays.get("initial_manual_action_delay_s", 0))
        
        dl_range = delays.get("download_delay_range_s", [0.5, 2.5])
        if len(dl_range) >= 2:
            self.inp_dl_min.setValue(dl_range[0])
            self.inp_dl_max.setValue(dl_range[1])
            
        long_pause = delays.get("long_pause_every_n_pages", {})
        self.inp_pause_pages.setValue(long_pause.get("pages", 10))
        self.inp_pause_sec.setValue(long_pause.get("seconds", 30))
        
        self.inp_nav_timeout.setValue(self.settings.get("navigation_timeout_ms", 60000))
        self.inp_dl_timeout.setValue(self.settings.get("download_timeout_ms", 45000))
        self.inp_min_topic.setValue(self.settings.get("min_topic_content_lent", 10000))
        self.inp_min_list.setValue(self.settings.get("min_list_content_lent", 5000))
        
        self.inp_threshold.setValue(self.settings.get("deduplication_threshold", 0))
        self.inp_exclude_ext.setText(", ".join(self.settings.get("exclude_extensions", [])))


        # Selectors
        selectors = self.settings.get("selectors", {})
        self.inp_sel_next.setText(selectors.get("pagination_next", ""))
        self.inp_sel_prev.setText(selectors.get("pagination_prev", ""))
        self.inp_sel_topic.setText(selectors.get("topic_preview", ""))
        self.inp_sel_link.setText(selectors.get("topic_link", ""))
        self.inp_sel_captcha.setText(self.settings.get("captcha_selector", ""))

        # Fields
        self.load_fields_list()

        # JSON
        self.editor.setText(json.dumps(self.settings, indent=2))

    def on_tab_changed(self, index):
        if self.tabs.tabText(index) == "JSON (Advanced)":
            self.update_settings_from_fields()
            self.editor.setText(json.dumps(self.settings, indent=2))
        else:
            # If leaving JSON tab, parse JSON back to settings
             try:
                self.settings = json.loads(self.editor.toPlainText())
                self.load_data() # Reload fields from JSON
             except json.JSONDecodeError:
                 pass # Or warn user

    def update_settings_from_fields(self):
        self.settings["save_path"] = self.inp_save_path.text()
        self.settings["resource_save_path_pattern"] = self.inp_filename_pattern.text()
        self.settings["scraping_direction"] = self.combo_direction.currentText()
        
        exts = [e.strip() for e in self.inp_exclude_ext.text().split(",") if e.strip()]
        self.settings["exclude_extensions"] = exts
        
        if "delays" not in self.settings: self.settings["delays"] = {}
        self.settings["delays"]["delay_between_list_pages_s"] = self.inp_delay_page.value()
        self.settings["delays"]["delay_between_topics_s"] = self.inp_delay_topic.value()
        self.settings["delays"]["initial_manual_action_delay_s"] = self.inp_delay_manual.value()
        self.settings["delays"]["download_delay_range_s"] = [self.inp_dl_min.value(), self.inp_dl_max.value()]
        self.settings["delays"]["long_pause_every_n_pages"] = {
            "pages": self.inp_pause_pages.value(),
            "seconds": self.inp_pause_sec.value()
        }

        self.settings["navigation_timeout_ms"] = self.inp_nav_timeout.value()
        self.settings["download_timeout_ms"] = self.inp_dl_timeout.value()
        self.settings["min_topic_content_lent"] = self.inp_min_topic.value()
        self.settings["min_list_content_lent"] = self.inp_min_list.value()

        self.settings["deduplication_threshold"] = self.inp_threshold.value()

        if "selectors" not in self.settings: self.settings["selectors"] = {}
        self.settings["selectors"]["pagination_next"] = self.inp_sel_next.text()
        self.settings["selectors"]["pagination_prev"] = self.inp_sel_prev.text()
        self.settings["selectors"]["topic_preview"] = self.inp_sel_topic.text()
        self.settings["selectors"]["topic_link"] = self.inp_sel_link.text()
        self.settings["captcha_selector"] = self.inp_sel_captcha.text()
        
        # Fields are updated in realtime/memory? No, list holds them.
        # We need to construct the list back to settings
        new_fields = []
        for i in range(self.list_fields.count()):
            item = self.list_fields.item(i)
            new_fields.append(item.data(Qt.UserRole))
        self.settings["fields_to_parse"] = new_fields
        
    # --- Field Helpers ---
    def load_fields_list(self):
        self.list_fields.clear()
        fields = self.settings.get("fields_to_parse", [])
        for f in fields:
            # handle dict vs obj? settings is dict
            item = QListWidgetItem(f.get("name", "New Field"))
            item.setData(Qt.UserRole, f)
            self.list_fields.addItem(item)
            
    def on_field_selected(self, current, previous):
        if not current:
            self.grp_field.setEnabled(False)
            return
            
        self.grp_field.setEnabled(True)
        data = current.data(Qt.UserRole)
        
        # Block signals to prevent feedback
        self.block_field_signals(True)
        self.inp_f_name.setText(data.get("name", ""))
        self.inp_f_selector.setText(data.get("selector", ""))
        self.inp_f_type.setCurrentText(data.get("type", "text"))
        self.inp_f_attr.setText(data.get("attribute") or "")
        self.inp_f_regex.setText(data.get("filter_regex") or "")
        self.inp_f_regex.setText(data.get("filter_regex") or "")
        self.chk_f_multi.setChecked(data.get("multiple", False))
        self.chk_f_prepend.setChecked(data.get("prepend_field_name", False))
        self.inp_f_delimiter.setText(data.get("prepend_delimiter", "\\"))
        self.chk_f_is_tag.setChecked(data.get("is_tag", False))
        self.block_field_signals(False)
        
    def save_current_field(self):
        item = self.list_fields.currentItem()
        if not item: return
        
        data = item.data(Qt.UserRole)
        data["name"] = self.inp_f_name.text()
        data["selector"] = self.inp_f_selector.text()
        data["type"] = self.inp_f_type.currentText()
        data["attribute"] = self.inp_f_attr.text() or None
        data["filter_regex"] = self.inp_f_regex.text() or None
        data["filter_regex"] = self.inp_f_regex.text() or None
        data["multiple"] = self.chk_f_multi.isChecked()
        data["prepend_field_name"] = self.chk_f_prepend.isChecked()
        data["prepend_delimiter"] = self.inp_f_delimiter.text()
        data["is_tag"] = self.chk_f_is_tag.isChecked()
        
        item.setText(data["name"])
        item.setData(Qt.UserRole, data)
        
    def add_field(self):
        new_data = {
            "name": "new_field",
            "selector": "",
            "type": "text",
            "multiple": False
        }
        item = QListWidgetItem("new_field")
        item.setData(Qt.UserRole, new_data)
        self.list_fields.addItem(item)
        self.list_fields.setCurrentItem(item)
        self.inp_f_name.setFocus()
        
    def remove_field(self):
        row = self.list_fields.currentRow()
        if row >= 0:
            self.list_fields.takeItem(row)
            
    def block_field_signals(self, block):
        self.inp_f_name.blockSignals(block)
        self.inp_f_selector.blockSignals(block)
        self.inp_f_type.blockSignals(block)
        self.inp_f_attr.blockSignals(block)
        self.inp_f_regex.blockSignals(block)
        self.chk_f_multi.blockSignals(block)
        self.chk_f_prepend.blockSignals(block)
        self.inp_f_delimiter.blockSignals(block)
        self.chk_f_is_tag.blockSignals(block)

    def save(self):
        # If currently in JSON tab, trust JSON editor
        if self.tabs.currentWidget() == self.tab_json:
            try:
                test_load = json.loads(self.editor.toPlainText())
                self.settings = test_load
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Invalid JSON", "Please fix errors in JSON before saving.")
                return
        else:
            self.update_settings_from_fields()
        
        self.accept()

    def get_settings(self):
        # Return JSON string
        return json.dumps(self.settings, indent=2)
