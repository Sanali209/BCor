from src.apps.VFSSample.handlers import handle_list_dir, handle_read_file, handle_write_file
from src.apps.VFSSample.messages import ListDirCommand, ReadFileCommand, WriteFileCommand
from src.core.module import BaseModule


class VFSSampleModule(BaseModule):
    """Module for the VFSSample application.

    Registers handlers for basic VFS operations.
    """

    def __init__(self):
        super().__init__()
        # Register command handlers
        self.command_handlers = {
            WriteFileCommand: handle_write_file,
            ReadFileCommand: handle_read_file,
            ListDirCommand: handle_list_dir,
        }
