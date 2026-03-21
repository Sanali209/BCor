import os
from collections.abc import Iterable

from dishka import Provider, Scope, provide
from fs import open_fs
from fs.base import FS

from src.core.module import BaseModule
from src.modules.vfs.settings import VfsSettings


class VfsProvider(Provider):
    """Dishka Provider for the Virtual File System.

    This provider manages the lifecycle of the FS instance using a
    generator-based provider to ensure the filesystem is closed on container exit.
    """

    def __init__(self, settings: VfsSettings):
        super().__init__()
        self.settings = settings

    @provide(scope=Scope.APP)
    def provide_vfs(self) -> Iterable[FS]:
        """Provides a Singleton FS instance with automatic cleanup."""
        url = self.settings.url
        # Automatic test override or default to memory
        if os.getenv("PYTEST_CURRENT_TEST") or not url:
            url = "mem://"

        vfs = open_fs(url, create=True)
        yield vfs

        if not vfs.isclosed():
            vfs.close()


class VfsModule(BaseModule):
    """Virtual File System (VFS) Module.

    Integrates PyFilesystem2 into the BCor system, providing a unified
    abstraction for file operations across different backends.
    """

    settings_class = VfsSettings

    def __init__(self):
        super().__init__()
        self._provider: VfsProvider | None = None

    @property
    def provider(self) -> Provider:
        """Returns the VfsProvider initialized with module settings."""
        if not self._provider:
            # self.settings is injected by System during bootstrap
            self._provider = VfsProvider(self.settings)
        return self._provider
