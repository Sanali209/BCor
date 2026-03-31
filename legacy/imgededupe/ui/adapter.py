from PySide6.QtCore import Signal
from src.porting.ui_bridge import BaseGuiAdapter
from src.apps.experemental.imgededupe.application.messages import (
    ScanStarted, ScanCompleted, DeduplicationStarted, DuplicatesFound, ClustersGenerated
)

class GuiEventAdapter(BaseGuiAdapter):
    """
    Adapter that bridges BCor async events to PySide6 signals.
    """
    # Signals for UI
    scan_started = Signal(list) # roots
    scan_completed = Signal(int) # files_count
    dedupe_started = Signal(str) # engine_type
    duplicates_found = Signal(int) # relations_count
    clusters_generated = Signal(int) # clusters_count
    
    def on_scan_started(self, event: ScanStarted) -> None:
        """Handler for ScanStarted event."""
        self.scan_started.emit(event.roots)

    def on_scan_completed(self, event: ScanCompleted) -> None:
        """Handler for ScanCompleted event."""
        self.scan_completed.emit(event.files_count)

    def on_dedupe_started(self, event: DeduplicationStarted) -> None:
        """Handler for DeduplicationStarted event."""
        self.dedupe_started.emit(event.engine_type)

    def on_duplicates_found(self, event: DuplicatesFound) -> None:
        """Handler for DuplicatesFound event."""
        self.duplicates_found.emit(event.relations_count)

    def on_clusters_generated(self, event: ClustersGenerated) -> None:
        """Handler for ClustersGenerated event."""
        self.clusters_generated.emit(event.clusters_count)
