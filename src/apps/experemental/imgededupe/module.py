from typing import Dict, Type, List, Callable
from src.core.module import BaseModule
from src.core.messagebus import Message
from .application.messages import StartDeduplicationCommand, StartScanCommand
from .infrastructure.providers import ImgeDeduplicationProvider

class ImgeDeduplicationModule(BaseModule):
    """
    BCor Module for Image Deduplication.
    """
    def __init__(self):
        super().__init__()
        self.name = "imgededupe"
        self.provider = ImgeDeduplicationProvider()

    @property
    def handlers(self) -> Dict[Type[Message], List[Callable]]:
        from src.apps.experemental.imgededupe.application.handlers import (
            handle_start_deduplication,
            handle_start_scan
        )
        return {
            StartDeduplicationCommand: [handle_start_deduplication],
            StartScanCommand: [handle_start_scan],
        }
