import pytest
import os
import asyncio
from fs.base import FS
from src.core.system import System
from src.core.unit_of_work import AbstractUnitOfWork
from src.modules.vfs.module import VfsModule
from dishka import Provider, Scope, provide

class FakeUnitOfWork(AbstractUnitOfWork):
    def commit(self): pass
    def _commit(self): pass
    def rollback(self): pass
    def collect_events(self): return []

class MockUoWProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_uow(self) -> AbstractUnitOfWork:
        return FakeUnitOfWork()

@pytest.mark.asyncio
async def test_vfs_detection_and_injection_defaults_to_mem_in_tests():
    """Test that VFS defaults to MemoryFS when running in a test environment."""
    vfs_module = VfsModule()
    system = System(modules=[vfs_module])
    system.providers.append(MockUoWProvider())
    system._bootstrap()
    
    async with system.container() as container:
        # FS is the base class from PyFilesystem2
        vfs = await container.get(FS)
        assert isinstance(vfs, FS)
        
        # In a test environment (detected via PYTEST_CURRENT_TEST),
        # it should be an instance of MemoryFS.
        from fs.memoryfs import MemoryFS
        assert isinstance(vfs, MemoryFS)

@pytest.mark.asyncio
async def test_vfs_basic_operations():
    """Test standard PyFilesystem2 operations through the injected port."""
    vfs_module = VfsModule()
    system = System(modules=[vfs_module])
    system.providers.append(MockUoWProvider())
    system._bootstrap()
    
    async with system.container() as container:
        vfs = await container.get(FS)
        
        # Write
        vfs.writetext("test_file.txt", "Hello BCor VFS!")
        
        # Read & Exist
        assert vfs.exists("test_file.txt")
        assert vfs.readtext("test_file.txt") == "Hello BCor VFS!"
        
        # Directory operation
        vfs.makedir("sub_folder")
        assert vfs.isdir("sub_folder")

@pytest.mark.asyncio
async def test_vfs_lifecycle_closes_on_stop():
    """Test that the filesystem is properly closed when the system stops."""
    vfs_module = VfsModule()
    system = System(modules=[vfs_module])
    system.providers.append(MockUoWProvider())
    await system.start()
    
    async with system.container() as container:
        vfs = await container.get(FS)
        assert not vfs.isclosed()
        
    # Stopping the system should trigger VfsModule.on_stop hooks
    await system.stop()
    assert vfs.isclosed()
