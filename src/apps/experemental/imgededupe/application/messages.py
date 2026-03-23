from dataclasses import dataclass, field
from typing import List, Optional
from src.core.messages import Command, Event

# --- Commands ---

@dataclass(frozen=True)
class StartScanCommand(Command):
    """Command to start scanning directories for images."""
    roots: List[str]
    recursive: bool = True

@dataclass(frozen=True)
class StartDeduplicationCommand(Command):
    """Command to start the deduplication process using a specific engine."""
    engine_type: str = "phash"
    threshold: float = 5.0
    include_ignored: bool = False
    roots: Optional[List[str]] = None

# --- Events ---

@dataclass(frozen=True)
class ScanStarted(Event):
    """Event emitted when a scan starts."""
    roots: List[str]

@dataclass(frozen=True)
class FileScanned(Event):
    """Event emitted when a single file has been scanned and hashed."""
    path: str
    phash: Optional[str] = None

@dataclass(frozen=True)
class ScanCompleted(Event):
    """Event emitted when the scan process is finished."""
    files_count: int

@dataclass(frozen=True)
class DeduplicationStarted(Event):
    """Event emitted when deduplication starts."""
    engine_type: str

@dataclass(frozen=True)
class DuplicatesFound(Event):
    """Event emitted when the engine finds potential duplicates."""
    relations_count: int

@dataclass(frozen=True)
class ClustersGenerated(Event):
    """Event emitted when clusters (groups of duplicates) are ready."""
    clusters_count: int
