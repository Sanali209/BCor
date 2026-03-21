from nicegui import ui
from .layout import side_drawer, page_header

def gallery_page():
    """Main Gallery Grid View."""
    page_header('Main Gallery')
    side_drawer('/gallery')
    
    with ui.column().classes('w-full p-6 gap-6'):
        # Filter Bar
        with ui.row().classes('w-full items-center gap-4'):
             ui.input(placeholder='Search by tags...').props('outlined rounded dense clearable').classes('flex-grow')
             ui.button('Mass Update', icon='edit_calendar').props('outline color="silver"')
             ui.button('Select Mode', icon='check_box', on_click=lambda: ui.notify('Selection mode toggled')).props('fill color="green"')
             ui.button(icon='filter_list').props('flat round')

        # Gallery Grid
        with ui.grid(columns=4).classes('w-full gap-6'):
            for i in range(12):
                with ui.card().tight().classes('rounded-xl overflow-hidden hover:shadow-lg transition-shadow cursor-pointer position-relative'):
                    # Selection Checkbox (visible in select mode)
                    with ui.row().classes('absolute top-2 right-2 z-10'):
                        ui.checkbox().props('dense color="blue"')
                    
                    ui.image(f'https://picsum.photos/id/{i+10}/400/300').classes('h-48 w-full object-cover')
                    with ui.card_section().classes('p-3'):
                        with ui.row().classes('w-full justify-between items-start'):
                             ui.label(f'Image {i+1}').classes('font-medium text-sm truncate')
                             ui.icon('more_vert', color='slate-400').classes('cursor-pointer')
                        
                        ui.label('Nature > Forest').classes('text-xs text-slate-500 mt-1')
                        with ui.row().classes('w-full items-center justify-between mt-2'):
                            with ui.row().classes('gap-1'):
                                ui.badge('AI', color='blue-100', text_color='blue-700').props('rounded outline')
                                ui.badge('Nikon', color='slate-100', text_color='slate-700').props('rounded outline')
                            ui.badge('4.8', color='orange').props('outline text-color="orange"')

        # Pagination
        with ui.row().classes('w-full justify-center mt-8'):
            ui.pagination(1, 10, direction_links=True)

# Registering the route (conceptual, will be done in the app entry point)
# @ui.page('/gallery')
# def main():
#     gallery_page()
