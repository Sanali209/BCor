from typing import Dict, Type, List, Callable
from pydantic import Field
from pydantic_settings import BaseSettings
from src.core.module import BaseModule
from src.core.messagebus import Message
from .application.messages import (
    StartDeduplicationCommand, StartScanCommand,
    ScanStarted, ScanCompleted, DeduplicationStarted, DuplicatesFound, ClustersGenerated
)
from .infrastructure.providers import ImgeDeduplicationProvider
from .ui.adapter import GuiEventAdapter

from .settings import ImgeDeduplicationSettings

class ImgeDeduplicationModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.name = "imgededupe"
        self.provider = ImgeDeduplicationProvider()
        self.settings_class = ImgeDeduplicationSettings

    def setup(self) -> None:
        from src.apps.experemental.imgededupe.application.handlers import (
            handle_start_deduplication,
            handle_start_scan,
            handle_scan_started_ui,
            handle_scan_completed_ui,
            handle_dedupe_started_ui,
            handle_duplicates_found_ui,
            handle_clusters_generated_ui,
            handle_trigger_dedupe_on_scan_completed
        )
        # Commands
        self.command_handlers[StartDeduplicationCommand] = handle_start_deduplication
        self.command_handlers[StartScanCommand] = handle_start_scan
        
        # Events (Bridge to GUI and Domain Logic)
        self.event_handlers[ScanStarted] = [handle_scan_started_ui]
        self.event_handlers[ScanCompleted] = [
            handle_scan_completed_ui,
            handle_trigger_dedupe_on_scan_completed
        ]
        self.event_handlers[DeduplicationStarted] = [handle_dedupe_started_ui]
        self.event_handlers[DuplicatesFound] = [handle_duplicates_found_ui]
        self.event_handlers[ClustersGenerated] = [handle_clusters_generated_ui]
