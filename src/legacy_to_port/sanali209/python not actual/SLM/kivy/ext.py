# import kiwy widget
from kivy.uix.label import Label
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.splitter import Splitter
from kivy.uix.stacklayout import StackLayout

from SLM.appGlue.DAL.binding.bind import BindingProperty


class KivyAppLayoutTemplate:
    @staticmethod
    def build(debug=False):
        main_column = BoxLayout(orientation="vertical")
        header_row = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        if debug:
            label = Label(text="header row")
            header_row.add_widget(label)
        main_column.add_widget(header_row)
        content_row = BoxLayout(orientation="horizontal")
        main_column.add_widget(content_row)
        left_column = Splitter(sizable_from='right')
        left_column.min_size = "50pt"
        left_column.strip_size = "5pt"
        left_column_layout = BoxLayout(orientation="vertical", size_hint=(1, 1))
        left_column.add_widget(left_column_layout)
        if debug:
            label = Label(text="left column", size_hint=(1, 0.05))
            left_column_layout.add_widget(label)
        content_row.add_widget(left_column)
        center_column = BoxLayout(orientation="vertical", size_hint=(3, 1))
        if debug:
            label = Label(text="center column", size_hint=(1, 0.05))
            center_column.add_widget(label)
        content_row.add_widget(center_column)
        right_column = Splitter(sizable_from='left')
        right_column.min_size = "50pt"
        right_column.strip_size = "5pt"
        right_column_layout = BoxLayout(orientation="vertical", size_hint=(1, 1))
        right_column.add_widget(right_column_layout)
        if debug:
            label = Label(text="right column", size_hint=(1, 0.05))
            right_column_layout.add_widget(label)
        content_row.add_widget(right_column)
        footer_row = BoxLayout(orientation="horizontal", size_hint=(1, 0.1))
        if debug:
            label = Label(text="footer row")
            footer_row.add_widget(label)
        main_column.add_widget(footer_row)
        named_controls = {
            "main_column": main_column,
            "header_row": header_row,
            "content_row": content_row,
            "left_column": left_column_layout,
            "center_column": center_column,
            "right_column": right_column_layout,
            "footer_row": footer_row
        }
        return named_controls


class KivyLabelBind:

    @staticmethod
    def create(value,formatter=None):
        label = Label()
        label.size_hint = (1, None)
        label.text = str(value)
        label.height = 20
        binding = BindingProperty()
        binding.set_value(value)
        kivy_label_bind = KivyLabelBind(label, binding)
        if formatter is not None:
            kivy_label_bind.formatter = formatter
        return kivy_label_bind

    @staticmethod
    def format_value(value):
        return value

    def __init__(self, label: Label, binding: BindingProperty):
        self.label: Label = label
        self.binding = binding
        self.binding.add_listener(self.update_label)
        self.formatter = self.format_value

    def update_label(self, value):
        self.label.text = self.formatter(value)


class ItemObjectPropEditorAttrWidget(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (1, None)
        self.height = 0
        self.spacing = 5
        self.bind(minimum_height=self.setter('height'))


class ObjPropEditorObjectEditSchema:

    def bild(self, obj):
        widget = ItemObjectPropEditorAttrWidget()
        return self.bild_gui(obj, widget)

    def bild_gui(self, obj, widget):
        return widget


class ObjectPropEditor(ScrollView):
    def __init__(self, **kwargs):
        super(ObjectPropEditor, self).__init__(**kwargs)
        self.size_hint = (1, 1)
        self.editors_layout = StackLayout(orientation="tb-lr")
        self.editors_layout.size_hint = (1, None)
        self.editors_layout.height = 0
        self.editors_layout.padding = [5, 5, 5, 5]
        self.editors_layout.bind(minimum_height=self.editors_layout.setter('height'))
        self.add_widget(self.editors_layout)
        # self.orientation = "vertical"
        self.selected_object = None
        self.Schemas = {}

    def add_schema(self, obj_type, schema: ObjPropEditorObjectEditSchema):
        self.Schemas[obj_type] = schema

    def set_selected_object(self, obj):
        self.selected_object = obj
        self.selected_object_changed()

    def selected_object_changed(self):
        self.rebild_gui()

    def rebild_gui(self):
        self.editors_layout.clear_widgets()
        if self.selected_object is None:
            return
        schema = self.get_schema(self.selected_object)
        if schema is not None:
            widget = schema.bild(self.selected_object)
            self.editors_layout.add_widget(widget)

    def get_schema(self, obj):
        for type in self.Schemas.keys():
            if isinstance(obj, type):
                return self.Schemas[type]
