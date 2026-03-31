# DEPRECATED: This module has been modernized and moved to BCor Common.
# Please use 'src.common.media.metadata_service' for Media Metadata handling.
# The new implementation is async-native and VFS-aware.

from src.common.media.metadata_service import MetadataService

class MDManager:
    """Backward compatibility wrapper for legacy MDManager."""
    def __init__(self, path: str):
        self.service = MetadataService()
        self.path = path
        self.metadata = {}

    async def Read(self):
        # Note: legacy was sync, new is async. 
        # Legacy apps calling this will need to be awaited or run in loop.
        import asyncio
        from fs.osfs import OSFS
        root = os.path.dirname(self.path) or "."
        filename = os.path.basename(self.path)
        with OSFS(root) as fs:
            self.metadata = await self.service.read_metadata(fs, filename)
        return self.metadata

    async def Save(self):
        from fs.osfs import OSFS
        root = os.path.dirname(self.path) or "."
        filename = os.path.basename(self.path)
        with OSFS(root) as fs:
            return await self.service.write_metadata(fs, filename, self.metadata)
