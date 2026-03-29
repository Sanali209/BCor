import asyncio
import sys
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
from .ui.AppWindow import AppWindow
from src.core.messagebus import MessageBus

def main():
    if sys.platform == 'win32':
        import asyncio
        from asyncio import WindowsSelectorEventLoopPolicy
        asyncio.set_event_loop_policy(WindowsSelectorEventLoopPolicy())

    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)

    # Initialize Theming
    from src.common.ui.theming.manager import ThemeManager
    from src.common.ui.theming.provider import FileThemeProvider
    from pathlib import Path

    themes_dir = Path(__file__).parent / "themes"
    theme_provider = FileThemeProvider(themes_dir)
    theme_manager = ThemeManager(theme_provider)
    
    # Apply default theme
    app.setStyleSheet(theme_manager.get_current_qss())

    # Initialize dependencies
    # In a full BCor app, this would use a Dishka container
    from src.core.unit_of_work import AbstractUnitOfWork
    from src.modules.agm.mapper import AGMMapper
    from dishka import make_async_container, Provider, provide, Scope
    
    class MockUoW(AbstractUnitOfWork):
        def _commit(self): pass
        def rollback(self): pass
        def _get_all_seen_aggregates(self): return []

    class AppProvider(Provider):
        @provide(scope=Scope.APP)
        def get_bus(self, uow: AbstractUnitOfWork) -> MessageBus:
            return MessageBus(uow=uow)
        
        @provide(scope=Scope.APP)
        def get_uow(self) -> AbstractUnitOfWork:
            return MockUoW()

    container = make_async_container(AppProvider())
    # Note: We need to get the bus in an async manner, but gui.py main() is sync.
    # However, loop is already started. We can just run it in the loop.
    async def setup_mapper():
        bus = await container.get(MessageBus)
        return AGMMapper(container=container, message_bus=bus)

    mapper = loop.run_until_complete(setup_mapper())
    
    window = AppWindow(bus=mapper.message_bus)
    
    # 3. Application Logic Wiring
    from neo4j import AsyncGraphDatabase
    driver = AsyncGraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))

    factory = AssetFactory()
    ingestion = AssetIngestionService(mapper=mapper, factory=factory)
    service = DeduplicationService(ingestion=ingestion, mapper=mapper)
    history = CommandHistory()

    async def run_dedupe(roots: list[str], threshold: float, engine: str):
        window.show_progress(f"Scanning Folders with {engine}...")
        window.stack.setCurrentIndex(1)
        
        try:
            async with driver.session() as db_session:
                # Configure finders based on engine
                if engine == "phash":
                    # For phash we use higher threshold (Hamming distance)
                    session = await service.run_dedupe(roots[0], db_session, threshold=5)
                else:
                    session = await service.run_dedupe(roots[0], db_session, threshold)
                
                window.show_progress(f"Done. Processed {session.count_total} assets.")
                
                from src.modules.assets.domain.models import ImageAsset
                assets = await mapper.query(ImageAsset).all(db_session)
                window.explorer_view.table.model_proxy.update_items(assets)
        except Exception as e:
            window.show_progress(f"Error: {str(e)}")

    window.setup_view.start_scan.connect(
        lambda r, t, e: asyncio.create_task(run_dedupe(r, t, e))
    )

    # Pairwise Navigation
    async def open_pairwise(asset_a, asset_b_id):
        async with driver.session() as db_session:
            from src.modules.assets.domain.models import ImageAsset
            asset_b = await mapper.query(ImageAsset).filter(id=asset_b_id).one(db_session)
            if asset_b:
                window.pairwise_view.set_pair(asset_a, asset_b)
                window.stack.setCurrentIndex(2)

    window.explorer_view.compare_pair.connect(
        lambda a, b_id: asyncio.create_task(open_pairwise(a, b_id))
    )

    # Triage Actions
    async def handle_annotate(target_id, rel_type):
        asset = window.pairwise_view.asset_a
        cmd = AnnotateRelationCommand(mapper, asset, target_id, rel_type)
        await cmd.execute()
        history.push(cmd)
        window.show_progress(f"Annotated as {rel_type}")

    async def handle_delete(asset_id):
        asset = window.pairwise_view.asset_a if window.pairwise_view.asset_a.id == asset_id else window.pairwise_view.asset_b
        cmd = DeleteAssetCommand(mapper, asset)
        await cmd.execute()
        history.push(cmd)
        window.show_progress(f"Deleted {asset_id}")

    window.pairwise_view.annotated.connect(lambda t, r: asyncio.create_task(handle_annotate(t, r)))
    window.pairwise_view.deleted.connect(lambda id_: asyncio.create_task(handle_delete(id_)))
    window.undo_act.triggered.connect(lambda: asyncio.create_task(history.undo()))
    
    def on_close(event):
        loop.create_task(driver.close())
        event.accept()

    window.closeEvent = on_close
    window.show()

    with loop:
        loop.run_forever()

if __name__ == "__main__":
    main()
