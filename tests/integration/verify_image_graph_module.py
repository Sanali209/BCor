import sys
import asyncio
from PySide6.QtWidgets import QApplication
from src.apps.ImageGraph.module import ImageGraphModule
from src.apps.ImageGraph.gui.main_window import ImageGraphMainWindow

async def verify_module():
    print("Verifying ImageGraphModule...")
    
    # Mocking FileRepo for DI
    class MockFileRepo:
        async def get_by_id(self, file_id):
            return None

    from dishka import make_async_container, Provider, Scope, provide
    from typing import Any
    from src.apps.ImageGraph.gui.widgets.graph_widget import ImageGraphWidget

    class AppProvider(Provider):
        scope = Scope.APP
        @provide
        def get_file_repo(self) -> Any:
            return MockFileRepo()

    container = make_async_container(ImageGraphModule(), AppProvider())
    
    main_window = await container.get(ImageGraphMainWindow)
    print("Successfully instantiated ImageGraphMainWindow")
    
    widget = await container.get(ImageGraphWidget)
    print(f"Graph widget scene items: {len(widget.scene.items())}")
    
    # Test Auto Arrange
    widget.scene.auto_arrange()
    print("Auto-arrange executed successfully")

if __name__ == "__main__":
    app = QApplication(sys.argv)
    loop = asyncio.get_event_loop()
    loop.run_until_complete(verify_module())
    print("Verification complete.")
