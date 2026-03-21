from typing import Union

from kivy.core.window import Window
from kivy.properties import NumericProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.graphics import Rectangle, Color
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.uix.stacklayout import StackLayout
from kivy.uix.widget import Widget

from kivy.uix.button import Button

from SLM.appGlue.DesignPaterns.SingletonAtr import singleton


class ListViewItemWidget(BoxLayout, ButtonBehavior):

    @property
    def selected(self):
        return self._selected

    @selected.setter
    def selected(self, value):
        if self._selected == value:
            return
        self._selected = value
        if self._selected:
            self.background_color.rgb = (0, 0.3, 0)
        else:
            self.background_color.rgb = (0, 0, 0)

    def __init__(self, **kwargs):
        if "list_widget" in kwargs:
            self.list_widget: ListWidget = kwargs["list_widget"]
            del kwargs["list_widget"]
        else:
            self.list_widget: ListWidget = None
        super(ListViewItemWidget, self).__init__(**kwargs)
        self.navigationName = ""
        self.orientation = "vertical"
        self.size_hint = (None, None)
        self.width = 256
        self.height = 256
        self.on_click = []
        self._selected = False
        self.header_layout = BoxLayout(orientation="horizontal", size_hint=(1, None), height=20)
        self.sub_items_collapsed = True
        self.sub_items_indent = 1
        self.sub_items_layout = StackLayout(orientation="lr-tb")
        self.sub_items_layout.size_hint = (1, None)
        self.sub_items_layout.height = 0
        self.sub_items_layout.bind(minimum_height=self.sub_items_layout.setter('height'))
        self.bind(minimum_height=self.setter('height'))
        self.add_widget(self.header_layout)
        self.add_widget(self.sub_items_layout)
        self.sub_items = []

        with self.canvas.before:
            self.background_color = Color(0, 0, 0, 1)
            self.background_rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(pos=self.update_rect, size=self.update_rect)

    def set_sub_items(self, sub_items):
        self.sub_items = sub_items
        self.sub_items_layout.clear_widgets()
        self.populate_sub_items()

    def expand_sub_items_by_nav_path(self, nav_path_list):
        if len(nav_path_list) == 0:
            return
        current_level_nav_name = nav_path_list[0]
        for item in self.sub_items_layout.children:
            if item.navigationName == current_level_nav_name:
                item.expand_sub_items()
                item.expand_sub_items_by_nav_path(nav_path_list[1:])

    def populate_sub_items(self):
        if self.sub_items_collapsed:
            return
        # set padding left
        self.sub_items_layout.padding = [self.sub_items_indent, 0, 0, 0]
        for item in self.sub_items:
            item_template: ListViewItemBuilder = self.list_widget.Template.itemTemplateSelector.get_template(item)
            item_widget = item_template.build(self.list_widget, item)
            self.sub_items_layout.add_widget(item_widget)

    def collapse_sub_items(self):
        self.sub_items_collapsed = True
        self.sub_items_layout.clear_widgets()

    def expand_sub_items(self):
        self.sub_items_collapsed = False
        self.populate_sub_items()

    def update_rect(self, instance, value):
        self.background_rect.pos = self.pos
        self.background_rect.size = self.size

    def on_touch_down(self, touch):
        KeyboardDaemon.instance().is_key_down(305)
        if self.collide_point(*touch.pos):
            for callback in self.on_click:
                callback(self)
            self.list_widget.sel_handler.set_selection([self])
            return super(ListViewItemWidget, self).on_touch_down(touch)
        return super(ListViewItemWidget, self).on_touch_down(touch)


class ListViewGroupWidget(StackLayout):
    def __init__(self, **kwargs):
        if "name" in kwargs:
            self.name = kwargs["name"]
            del kwargs["name"]
        else:
            self.name = ""
        super(ListViewGroupWidget, self).__init__(**kwargs)
        self.header = BoxLayout(orientation="horizontal", size_hint=(1, None), height=20)
        self.add_widget(self.header)
        self.label = Label(text=self.name, size_hint=(1, None), height=20)
        self.header.add_widget(self.label)
        self.orientation = "lr-tb"
        self.size_hint = (1, None)
        self.bind(minimum_height=self.setter('height'))


class ListViewTemplate:
    def __init__(self):
        self.list_widget = None
        self.itemTemplateSelector = ItemTemplateSelector()

    def create_toolbar(self, list_widget, toolbar):
        page_label = Label(text="page " + str(list_widget.page + 1) + "/" + str(list_widget.page_count),
                           size_hint=(None, None), height=20)

        def page_label_update(list_widget, value):
            page_label.text = "page " + str(list_widget.page + 1) + "/" + str(list_widget.page_count)

        self.list_widget.bind(page=page_label_update, page_count=page_label_update)
        toolbar.add_widget(page_label)
        prev_button = Button(text="<", size_hint=(None, None), height=20)
        prev_button.bind(on_press=list_widget.prev_page)
        toolbar.add_widget(prev_button)
        next_button = Button(text=">", size_hint=(None, None), height=20)
        next_button.bind(on_press=list_widget.next_page)
        toolbar.add_widget(next_button)

    def create_items_layout(self):
        self.list_widget.items_layout = StackLayout(orientation="lr-tb")
        self.list_widget.items_layout.size_hint = (1, None)
        self.list_widget.items_layout.bind(minimum_height=self.list_widget.items_layout.setter('height'))


class ListViewItemBuilder:
    def build(self, list_view, data_item):
        lvitem = ListViewItemWidget(list_widget=list_view)
        lvitem.dataContext = data_item
        lvitem.navigationName = self.get_nav_name(data_item)
        self.build_control(lvitem, data_item)

        sub_items = self.get_sub_items(data_item)
        if sub_items is not None:
            lvitem.set_sub_items(sub_items)
        return lvitem

    def build_control(self, item_widget, data_item):
        item_widget.size_hint = (1, None)
        item_widget.height = 20
        button = Button(text=str(data_item), size_hint=(1, None), height=20)
        item_widget.header_layout.add_widget(button)

    def get_group_name(self, data_item, group_by) -> Union[None, list[str]]:
        return None

    def sort_by(self, data_item, sort_by):
        return data_item

    def get_sub_items(self, data_item) -> Union[None, list]:
        return None

    def get_nav_name(self, data_item):
        return ""


class ItemTemplateSelector:
    def __init__(self):
        self.template_map: dict[type] = {}
        self.get_template_del = []
        self.default_template = ListViewItemBuilder()

    def add_template(self, ittype: type, template: ListViewItemBuilder):
        self.template_map[ittype] = template

    def get_template(self, item) -> ListViewItemBuilder:
        for delgate in self.get_template_del:
            template = delgate(item)
            if template is not None:
                return template
        for type in self.template_map.keys():
            if isinstance(item, type):
                return self.template_map[type]
        return self.default_template


@singleton
class KeyboardDaemon:

    def __init__(self):
        self.key = []

    def on_key_down(self, window, key, scancode, codepoint, modifier):
        if key not in self.key:
            self.key.append(key)

        print(self.key)

    def on_key_up(self, window, key, scancode):
        if key in self.key:
            self.key.remove(key)
        print(self.key)

    def is_key_down(self, key):
        return key in self.key

    def start(self):
        Window.bind(on_key_down=self.on_key_down)
        Window.bind(on_key_up=self.on_key_up)


class SelHandler:
    def __init__(self, list_widget: 'ListWidget'):
        self.selected = []
        self.list_widget = list_widget

    def set_selection(self, selection: list[ListViewItemWidget]):
        for item in self.selected:
            item.selected = False
        self.selected = selection
        for item in self.selected:
            item.selected = True

    def set_sel_add(self, item: ListViewItemWidget):
        if item in self.selected:
            return
        self.selected.append(item)
        item.selected = True

    def set_sel_range(self, end: ListViewItemWidget):
        start = self.selected[-1]
        if start == end:
            return
        start_index = self.list_widget.items_layout.children.index(start)
        end_index = self.list_widget.items_layout.children.index(end)
        if start_index > end_index:
            start_index, end_index = end_index, start_index
        for i in range(start_index, end_index + 1):
            self.set_sel_add(self.list_widget.items_layout.children[i])

    def get_selection_data(self):
        return [item.dataContext for item in self.selected]


class ListWidget(StackLayout):
    page = NumericProperty(0)
    page_count = NumericProperty(0)

    def __init__(self, **kwargs):
        if "Template" in kwargs:
            self.Template = kwargs["Template"]
            self.Template.list_widget = self
            del kwargs["Template"]
        else:
            self.Template = ListViewTemplate()
            self.Template.list_widget = self
        super(ListWidget, self).__init__(**kwargs)
        self.size_hint = (1, 1)
        self.orientation = "lr-tb"
        self.scroll_layout = ScrollView(size_hint=(1, 0.9))
        self.toolbar = StackLayout(orientation="lr-tb")
        self.toolbar.size_hint = (1, 0.1)
        self.add_widget(self.toolbar)
        self.add_widget(self.scroll_layout)

        self.data_list = []
        self.visible_items = []

        self.filter = None
        self.sort_by = None
        self.group_by = None
        self.groups = {}

        self.items_per_page = 100
        self.visible_item_start = 0
        self.visible_item_end = self.items_per_page

        self.items_layout = None

        self.sel_handler = SelHandler(self)

        self.Refresh()

    def expand_by_nav_path(self, nav_path: str):
        # items separate by \
        nav_path_list = nav_path.split("\\")
        current_level_nav_name = nav_path_list[0]
        # iterate trouth child vidjet
        for child in self.items_layout.children:
            if child.navigationName == current_level_nav_name:
                child.expand_sub_items()
                child.expand_sub_items_by_nav_path(nav_path_list[1:])

    def Clear_layout(self):
        if self.items_layout is not None:
            self.items_layout.clear_widgets()
            self.scroll_layout.remove_widget(self.items_layout)
        self.Template.create_items_layout()
        self.scroll_layout.add_widget(self.items_layout)
        self.groups.clear()

    def CalculatePage(self):
        self.page_count = len(self.visible_items) // self.items_per_page
        if len(self.visible_items) % self.items_per_page > 0:
            self.page_count += 1
        self.visible_item_start = self.page * self.items_per_page
        self.visible_item_end = self.visible_item_start + self.items_per_page

    def next_page(self, instance):
        if self.page < self.page_count - 1:
            self.page += 1
            self.Refresh()

    def prev_page(self, instance):
        if self.page > 0:
            self.page -= 1
            self.Refresh()

    def populate_list(self):
        for item in self.visible_items[self.visible_item_start:self.visible_item_end]:
            self.add_data_item_internal(item)

    def Refresh(self):
        self.Clear_layout()
        self.Filter_all()
        self.Sort()
        self.CalculatePage()
        self.toolbar.clear_widgets()
        self.populate_list()
        self.Template.create_toolbar(self, self.toolbar)

    def SwitchTemplate(self, template: ListViewTemplate):
        self.Template = template
        template.list_widget = self

        self.Refresh()

    def add_control(self, widget):
        if not isinstance(widget, Widget):
            raise Exception("widget must be instance of Widget")
        self.items_layout.add_widget(widget)

    def create_item(self, item):
        item_template: ListViewItemBuilder = self.Template.itemTemplateSelector.get_template(item)
        item_widget = item_template.build(self, item)
        return item_widget

    def get_or_create_group(self, groupname):
        if groupname in self.groups:
            return self.groups[groupname]
        else:
            group_widjet = ListViewGroupWidget(name=groupname)
            self.groups[groupname] = group_widjet
            self.add_control(group_widjet)
            return group_widjet

    def get_group(self, data_item):
        item_template: ListViewItemBuilder = self.Template.itemTemplateSelector.get_template(data_item)
        group_names = item_template.get_group_name(data_item, self.group_by)
        if group_names is None:
            item = self.create_item(data_item)
            self.add_control(item)
        else:
            for groupname in group_names:
                group_widget = self.get_or_create_group(groupname)
                item = self.create_item(data_item)
                group_widget.add_widget(item)

    def add_data_item_internal(self, data_item):
        self.get_group(data_item)

    def filter_data_item(self, data_item):
        if self.filter is None:
            self.visible_items.append(data_item)
            return True

    def Filter_all(self):
        self.visible_items.clear()
        for item in self.data_list:
            self.filter_data_item(item)

    def sort_by_func(self, data_item):
        template = self.Template.itemTemplateSelector.get_template(data_item)
        return template.sort_by(data_item, self.sort_by)

    def Sort(self):
        if self.sort_by is not None:
            self.visible_items.sort(key=self.sort_by_func)

    def add_data_item(self, data_item):
        self.data_list.append(data_item)
        statisfaed = self.filter_data_item(data_item)
        if statisfaed:
            self.Refresh()

    def set_items(self, items):
        self.data_list = items
        self.Refresh()


class BindListToListWidget:
    def __init__(self, list_widget: ListWidget, bind_list):
        self.list_widget = list_widget
        self.bind_list = bind_list
        self.selection = []
        self.selection_changed = None

    def Refresh(self):
        self.list_widget.Refresh()
        self.populate_list()

    def populate_list(self):
        for item in self.bind_list.objList:
            self.list_widget.add_data_item(item)

    def fire_selection_changed(self):
        if self.selection_changed is not None:
            self.selection_changed(self.selection)


if __name__ == "__main__":
    from kivy.app import App


    class TestListViewTemplate(ListViewTemplate):
        def __init__(self):
            super().__init__()
            self.itemTemplateSelector.default_template = TestItemTemplate()


    class TestItemTemplate(ListViewItemBuilder):

        def build_control(self, item_widget, data_item):
            if isinstance(data_item, str):
                item_widget.size_hint = (1, None)
                item_widget.sub_items_indent = 1
                item_widget.height = 20
                button = Label(text=str(data_item), size_hint=(1, None), height=20)
                item_widget.header_layout.add_widget(button)
                return
            item_widget.sub_items_collapsed = False
            item_widget.size_hint = (None, None)
            item_widget.width = 256
            item_widget.height = 20
            button = Button(text=data_item["name"], size_hint=(1, None), height=20)
            item_widget.header_layout.add_widget(button)

        def get_group_name(self, data_item, group_by) -> list[str]:
            if "group" == group_by:
                return [data_item["group"]]

        def get_sub_items(self, data_item) -> Union[None, list]:
            if isinstance(data_item, str):
                return None
            subs = data_item["subitems"]
            return subs


    class MyApp(App):
        def build(self):
            itemlist = []
            for i in range(100):
                item = {"name": "test" + str(i),
                        "group": str(i % 3),
                        "subitems": ["subitem" + str(i) + str(j) for j in range(10)]}
                itemlist.append(item)

            lv = ListWidget()
            lv.items_per_page = 10
            # lv.group_by = "group"
            lv.SwitchTemplate(TestListViewTemplate())
            lv.set_items(itemlist)
            return lv


    MyApp().run()
