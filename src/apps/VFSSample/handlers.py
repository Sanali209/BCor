from fs.base import FS
from loguru import logger

from src.apps.VFSSample.messages import ListDirCommand, ReadFileCommand, WriteFileCommand
from src.common.monads import BusinessResult, failure, success


async def handle_write_file(cmd: WriteFileCommand, vfs: FS) -> BusinessResult:
    """Writes content to a VFS file and returns success."""
    try:
        vfs.writetext(cmd.path, cmd.content)
        logger.info(f"VFS: Written to {cmd.path}")
        return success(cmd.path)
    except Exception as e:
        logger.error(f"VFS Write Error: {e}")
        return failure(str(e))


async def handle_read_file(cmd: ReadFileCommand, vfs: FS) -> BusinessResult:
    """Reads content from a VFS file."""
    try:
        if not vfs.exists(cmd.path):
            return failure(f"File {cmd.path} does not exist")
        content = vfs.readtext(cmd.path)
        return success(content)
    except Exception as e:
        return failure(str(e))


async def handle_list_dir(cmd: ListDirCommand, vfs: FS) -> BusinessResult:
    """Lists contents of a VFS directory."""
    try:
        if not vfs.isdir(cmd.path):
            return failure(f"Path {cmd.path} is not a directory")
        contents = vfs.listdir(cmd.path)
        return success(contents)
    except Exception as e:
        return failure(str(e))
