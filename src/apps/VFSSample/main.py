import sys
import os
import asyncio
from pathlib import Path
from loguru import logger

# Add project root to sys.path to allow direct execution
root_path = str(Path(__file__).resolve().parent.parent.parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from src.core.system import System
from src.core.messagebus import MessageBus
from src.apps.VFSSample.module import VFSSampleModule
from src.modules.vfs.module import VfsModule
from src.core.unit_of_work import AbstractUnitOfWork
from src.apps.VFSSample.messages import WriteFileCommand, ReadFileCommand, ListDirCommand
from dishka import Provider, Scope, provide

class DefaultUoW(AbstractUnitOfWork):
    """Minimal UoW implementation for samples/simple apps."""
    def _commit(self): pass
    def rollback(self): pass
    def _get_all_seen_aggregates(self): return []

class UoWProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_uow(self) -> AbstractUnitOfWork:
        return DefaultUoW()

async def run_vfs_sample():
    """Bootstraps and runs the VFSSample console application."""
    
    # 1. Initialize System with required modules
    # In a real app, this would be loaded from app.toml
    vfs_module = VfsModule()
    sample_module = VFSSampleModule()
    
    manifest_path = Path(__file__).parent / "app.toml"
    system = System.from_manifest(manifest_path)
    system.providers.append(UoWProvider())
    
    logger.info("Starting VFSSample App...")
    await system.start()
    
    try:
        async with system.container() as container:
            bus = await container.get(MessageBus)
            
            logger.info("--- BCor VFS Sample Console ---")
            
            # 1. Write a file
            logger.info("> Writing 'hello_vfs.txt'...")
            res_write = await (await bus.dispatch(WriteFileCommand(path="hello_vfs.txt", content="Hello from BCor VFS!"))).event_result()
            logger.info(f"  Result: {res_write.unwrap()}")
            
            # 2. List directory
            logger.info("> Listing root directory:")
            res_list = await (await bus.dispatch(ListDirCommand(path="/"))).event_result()
            logger.info(f"  Contents: {res_list.unwrap()}")
            
            # 3. Read file
            logger.info("> Reading 'hello_vfs.txt'...")
            res_read = await (await bus.dispatch(ReadFileCommand(path="hello_vfs.txt"))).event_result()
            logger.info(f"  Content: '{res_read.unwrap()}'")
            
            logger.info("--- Sample Completed Successfully ---")
            
    finally:
        await system.stop()

if __name__ == "__main__":
    asyncio.run(run_vfs_sample())
