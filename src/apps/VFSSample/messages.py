from typing import List
from src.core.messages import Command, Event

class WriteFileCommand(Command):
    """Command to write content to a file in the VFS."""
    path: str
    content: str

class ReadFileCommand(Command):
    """Command to read content from a file in the VFS."""
    path: str

class ListDirCommand(Command):
    """Command to list contents of a directory in the VFS."""
    path: str = "/"

class FileWrittenEvent(Event):
    """Event triggered after a file is successfully written."""
    path: str
