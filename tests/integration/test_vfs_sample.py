import pytest
import pytest_asyncio
from dishka import Provider, Scope, provide
from fs.base import FS
from fs.memoryfs import MemoryFS

from src.apps.VFSSample.messages import ListDirCommand, ReadFileCommand, WriteFileCommand
from src.apps.VFSSample.module import VFSSampleModule
from src.core.messagebus import MessageBus
from src.core.system import System
from src.core.unit_of_work import AbstractUnitOfWork
from src.modules.vfs.module import VfsModule


class FakeUnitOfWork(AbstractUnitOfWork):
    def commit(self):
        pass

    def _commit(self):
        pass

    def rollback(self):
        pass

    def collect_events(self):
        return []


class MockUoWProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_uow(self) -> AbstractUnitOfWork:
        return FakeUnitOfWork()


@pytest_asyncio.fixture
async def vfs_sample_system():
    modules = [VfsModule(), VFSSampleModule()]
    system = System(modules=modules)
    system.providers.append(MockUoWProvider())
    await system.start()
    yield system
    await system.stop()


@pytest.mark.asyncio
async def test_vfs_sample_app_lifecycle(vfs_sample_system):
    """Verify that the VFSSample app starts and provides VFS."""
    async with vfs_sample_system.container() as container:
        vfs = await container.get(FS)
        assert isinstance(vfs, MemoryFS)
        assert not vfs.isclosed()


@pytest.mark.asyncio
async def test_vfs_sample_write_and_read_commands(vfs_sample_system):
    """Test the full command flow: Write -> Read."""
    async with vfs_sample_system.container() as container:
        bus = await container.get(MessageBus)

        # 1. Write
        cmd_write = WriteFileCommand(path="test.txt", content="TDD Success")
        result_write = await (await bus.dispatch(cmd_write)).event_result()
        assert result_write.unwrap() == "test.txt"

        # 2. Read
        cmd_read = ReadFileCommand(path="test.txt")
        result_read = await (await bus.dispatch(cmd_read)).event_result()
        assert result_read.unwrap() == "TDD Success"


@pytest.mark.asyncio
async def test_vfs_sample_list_command(vfs_sample_system):
    """Test the ListDirCommand."""
    async with vfs_sample_system.container() as container:
        bus = await container.get(MessageBus)
        vfs = await container.get(FS)

        vfs.writetext("file1.txt", "one")
        vfs.writetext("file2.txt", "two")

        cmd_list = ListDirCommand(path="/")
        result_list = await (await bus.dispatch(cmd_list)).event_result()

        contents = result_list.unwrap()
        assert "file1.txt" in contents
        assert "file2.txt" in contents
