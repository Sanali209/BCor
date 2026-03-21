from nicegui import ui
from .layout import side_drawer, page_header

def dashboard_page():
    """Statistics and Insights Dashboard."""
    page_header('System Statistics')
    side_drawer('/gallery/stats')
    
    with ui.column().classes('w-full p-6 gap-8'):
        # Top Stats Cards
        with ui.row().classes('w-full gap-6 justify-between'):
            # Card Component
            def stat_card(label: str, value: str, icon: str, color: str):
                with ui.card().classes('flex-grow h-32 rounded-2xl p-4 flex flex-row items-center border border-slate-200 dark:border-slate-800 shadow-sm hover:shadow-md transition-shadow'):
                    with ui.column().classes('flex-grow'):
                        ui.label(label).classes('text-slate-500 text-xs font-bold tracking-widest uppercase mb-1')
                        ui.label(value).classes('text-3xl font-bold text-slate-900 dark:text-white')
                    ui.icon(icon, size='3rem').classes(f'text-{color}-500 opacity-20')

            stat_card('TOTAL IMAGES', '1,248', 'photo_library', 'blue')
            stat_card('CATEGORIES', '24', 'category', 'green')
            stat_card('RELATIONS', '864', 'reorder', 'purple')
            stat_card('VECTOR EMBEDDINGS', '1,248', 'bolt', 'orange')

        # Charts Section
        with ui.row().classes('w-full gap-8 mt-4'):
            # Distribution by Category
            with ui.card().classes('flex-grow p-6 rounded-3xl min-w-[400px] border border-slate-200 dark:border-slate-800 shadow-sm'):
                ui.label('Images by Category').classes('text-lg font-bold mb-4')
                ui.chart({
                    'chart': {'type': 'column', 'backgroundColor': 'transparent'},
                    'title': {'text': ''},
                    'xAxis': {'categories': ['Nature', 'Art', 'Travel', 'Architecture', 'Other']},
                    'yAxis': {'title': {'text': 'Count'}},
                    'series': [{'name': 'Images', 'data': [450, 320, 210, 150, 118], 'color': '#3b82f6'}]
                }).classes('w-full h-80')

            # Recent Activity / Stats list
            with ui.card().classes('w-1/3 p-6 rounded-3xl min-w-[300px] border border-slate-200 dark:border-slate-800 shadow-sm'):
                ui.label('Recent Metadata Changes').classes('text-lg font-bold mb-4')
                with ui.list().classes('w-full'):
                    for i in range(5):
                        with ui.item().classes('q-py-md border-b border-slate-100 last:border-0'):
                            with ui.item_section().props('avatar'):
                                ui.avatar('person', color='blue-100', text_color='blue')
                            with ui.item_section():
                                ui.label(f'User updated Image {i+1}').classes('text-sm font-medium')
                                ui.label('2 minutes ago').classes('text-xs text-slate-400')
                            with ui.item_section().props('side'):
                                ui.badge('Edit', color='blue-100', text_color='blue').props('flat')

        # Cleanup Log or something similar (Placeholder)
        with ui.card().classes('w-full p-6 rounded-3xl bg-slate-50 dark:bg-slate-900 border border-slate-200 dark:border-slate-800 shadow-sm'):
             ui.label('Recent AI Processing Logs').classes('text-lg font-bold mb-4')
             ui.log().classes('w-full h-32 font-mono text-xs').push('AI Tagger: Processed ID-120\nChroma: Index updated for ID-120\nRelation: Linked ID-120 to Nature')
