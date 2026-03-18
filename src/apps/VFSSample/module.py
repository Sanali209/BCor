from src.core.module import BaseModule
from src.apps.VFSSample.messages import WriteFileCommand, ReadFileCommand, ListDirCommand
from src.apps.VFSSample.handlers import handle_write_file, handle_read_file, handle_list_dir

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
