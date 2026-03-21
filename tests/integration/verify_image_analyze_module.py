import sys
import asyncio
from PySide6.QtWidgets import QApplication
from dishka import Provider, Scope, provide
from src.apps.ImageAnalyze.module import ImageAnalyzeModule
from src.apps.ImageAnalyze.gui.main_window import ImageAnalyzeMainWindow
from src.apps.ImageAnalyze.use_cases import ScanDirectoryUseCase, GetCollectionStatsUseCase, ExecuteBatchRulesUseCase

from src.core.system import System
from src.core.unit_of_work import AbstractUnitOfWork
from unittest.mock import MagicMock

class UowProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def get_uow(self) -> AbstractUnitOfWork:
        return MagicMock(spec=AbstractUnitOfWork)

async def verify_module():
    module = ImageAnalyzeModule()
    uow_provider = UowProvider()
    system = System(modules=[module])
    # Manually add the provider since we aren't using the full bootstrap 
    # but System.start() will call bootstrap which adds module.provider and core_provider.
    # We can inject our provider into the modules list for simplicity or add to providers list.
    system.providers.append(uow_provider)
    await system.start()
    
    container = system.container
    
    async with container() as req:
        scan_uc = await req.get(ScanDirectoryUseCase)
        stats_uc = await req.get(GetCollectionStatsUseCase)
        batch_uc = await req.get(ExecuteBatchRulesUseCase)
        
        assert isinstance(scan_uc, ScanDirectoryUseCase)
        assert isinstance(stats_uc, GetCollectionStatsUseCase)
        assert isinstance(batch_uc, ExecuteBatchRulesUseCase)
        
        print("Module verification successful: All Use Cases resolved via DI.")
        
        # Verify GUI instantiation (needs QApplication)
        app = QApplication.instance() or QApplication(sys.argv)
        window = ImageAnalyzeMainWindow(scan_uc, stats_uc, batch_uc)
        assert window.windowTitle() == "BCor - Image Analysis Hub"
        print("GUI verification successful: MainWindow instantiated.")
    
    await system.stop()

if __name__ == "__main__":
    asyncio.run(verify_module())
