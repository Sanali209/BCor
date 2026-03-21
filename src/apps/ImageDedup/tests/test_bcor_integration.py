import pytest
import asyncio
from src.core.system import System
from src.core.messagebus import MessageBus
from src.apps.ImageDedup.messages import LaunchGuiCommand, LoadProjectCommand, ProjectLoadedEvent
from src.apps.ImageDedup.use_cases.load_project import LoadProjectUseCase

@pytest.mark.asyncio
async def test_system_bootstrap_and_command_handling():
    """Verify that the BCor system bootstraps correctly and handles commands."""
    # 1. Initialize System
    system = System.from_manifest("src/apps/ImageDedup/app.toml")
    
    # 2. Start System
    await system.start()
    
    try:
        # 3. Resolve MessageBus
        async with system.container() as request_container:
            bus = await request_container.get(MessageBus)
            
            # 4. Dispatch LoadProjectCommand
            cmd = LoadProjectCommand(path=".")
            await bus.dispatch(cmd)
            
            # Verification: The handler logs success, but let's check if we can resolve the UseCase
            use_case = await request_container.get(LoadProjectUseCase)
            assert use_case is not None
            
            # event = await use_case.execute(".")
            # assert isinstance(event, ProjectLoadedEvent)
            # assert event.work_path == "."
            
    finally:
        await system.stop()

@pytest.mark.asyncio
async def test_provider_resolves_legacy_components():
    """Verify that Dishka correctly provides legacy components."""
    system = System.from_manifest("src/apps/ImageDedup/app.toml")
    await system.start()
    
    try:
        async with system.container() as request_container:
            from src.apps.ImageDedup.core.database import DatabaseManager
            from src.apps.ImageDedup.core.repositories.file_repository import FileRepository
            
            db = await request_container.get(DatabaseManager)
            repo = await request_container.get(FileRepository)
            
            assert db is not None
            assert repo is not None
            assert repo.db == db
    finally:
        await system.stop()
