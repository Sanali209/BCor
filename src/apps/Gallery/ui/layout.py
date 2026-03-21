from nicegui import ui
from typing import Callable, Optional

def side_drawer(current_page: str):
    """Common side drawer for gallery app."""
    with ui.left_drawer(fixed=False).classes('bg-blue-50 dark:bg-slate-900 border-r border-slate-200 dark:border-slate-800').props('bordered'):
        with ui.column().classes('w-full p-4 gap-4'):
            ui.label('BCor Gallery').classes('text-2xl font-bold text-blue-600 dark:text-blue-400 mb-4')
            
            # Navigation
            with ui.list().classes('w-full'):
                items = [
                    ('Main Gallery', 'grid_view', '/gallery'),
                    ('Dashboard', 'dashboard', '/gallery/stats'),
                    ('Relations', 'reorder', '/gallery/relations'),
                    ('Bulk Management', 'settings', '/gallery/manage'),
                ]
                for label, icon, target in items:
                    with ui.item(on_click=lambda t=target: ui.navigate.to(t)).classes('rounded-lg mb-1 pointer ' + ('bg-blue-100 dark:bg-blue-900' if current_page == target else '')):
                        with ui.item_section().props('avatar'):
                            ui.icon(icon)
                        with ui.item_section():
                            ui.label(label)

            ui.separator().classes('my-4')
            
            # Search & Filters
            ui.label('SEARCH & FILTERS').classes('text-xs font-bold text-slate-400 tracking-widest px-2')
            with ui.tabs().classes('w-full') as tabs:
                text_tab = ui.tab('Text', icon='search')
                ai_tab = ui.tab('AI', icon='bolt')
            
            with ui.tab_panels(tabs, value=text_tab).classes('w-full bg-transparent'):
                with ui.tab_panel(text_tab).classes('p-0 gap-3'):
                    ui.input(label='Keywords', placeholder='Nature, Sunset...').props('outlined rounded dense')
                    ui.select(['Recently Added', 'Popular'], label='Sort').classes('w-full')
                
                with ui.tab_panel(ai_tab).classes('p-0 gap-3'):
                    ui.input(label='Vector Prompt', placeholder='Describe what you see...').props('outlined rounded dense')
                    ui.slider(min=0, max=1, step=0.01, value=0.7).props('label-always color="blue"')
                    ui.upload(label='Visual Search', on_upload=lambda e: ui.notify(f'Searching by {e.name}')).props('flat bordered').classes('w-full')

            ui.separator().classes('my-2')
            ui.label('CATEGORIES').classes('text-xs font-bold text-slate-400 tracking-widest px-2')
            with ui.scroll_area().classes('h-64 w-full'):
                ui.tree([
                    {'id': 'nature', 'label': 'Nature', 'children': [{'id': 'forest', 'label': 'Forest'}, {'id': 'ocean', 'label': 'Ocean'}]},
                    {'id': 'travel', 'label': 'Travel'},
                    {'id': 'art', 'label': 'Art'},
                ], label_key='label', on_select=lambda e: ui.notify(f'Selected {e.value}')).classes('w-full')

def page_header(title: str):
    """Common header for gallery pages."""
    with ui.header().classes('bg-white dark:bg-slate-950 text-slate-900 dark:text-white border-b border-slate-200 dark:border-slate-800 q-py-sm'):
        with ui.row().classes('w-full items-center px-4'):
            ui.button(on_click=lambda: ui.left_drawer().toggle(), icon='menu').props('flat round')
            ui.label(title).classes('text-xl font-medium ml-2')
            ui.space()
            ui.button(icon='upload', color='blue').props('round flat').tooltip('Fast Upload')
            ui.button(icon='dark_mode', on_click=ui.dark_mode().toggle).props('flat round')
