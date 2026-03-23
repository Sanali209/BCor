from typing import List, Optional
from src.core.messages import Command, Event
from pydantic import Field

# --- Commands ---

class StartScanCommand(Command):
    """Command to start scanning directories for images."""
    roots: List[str]
    recursive: bool = True

class StartDeduplicationCommand(Command):
    """Command to start the deduplication process using a specific engine."""
    engine_type: str = "phash"
    threshold: float = 5.0
    include_ignored: bool = False
    roots: Optional[List[str]] = None

# --- Events ---

class ScanStarted(Event):
    """Event emitted when a scan starts."""
    roots: List[str]

class FileScanned(Event):
    """Event emitted when a single file has been scanned and hashed."""
    path: str
    phash: Optional[str] = None

class ScanCompleted(Event):
    """Event emitted when the scan process is finished."""
    files_count: int

class DeduplicationStarted(Event):
    """Event emitted when deduplication starts."""
    engine_type: str

class DuplicatesFound(Event):
    """Event emitted when the engine finds potential duplicates."""
    relations_count: int

class ClustersGenerated(Event):
    """Event emitted when clusters (groups of duplicates) are ready."""
    clusters_count: int
