from nicegui import ui
from .ui.gallery import gallery_page
from .ui.dashboard import dashboard_page
from .ui.relations import relations_page

# Routes
@ui.page('/gallery')
def main_gallery():
    gallery_page()

@ui.page('/gallery/stats')
def stats():
    dashboard_page()

@ui.page('/gallery/relations')
def relations():
    relations_page()

@ui.page('/gallery/manage')
def bulk():
    ui.label('Bulk Management Coming Soon').classes('text-2xl p-8')

# Entry point for the NiceGUI app
def run_app():
    ui.run(title='BCor Gallery', port=8080)

if __name__ in {"__main__", "builtins"}:
    run_app()
