from src.core.messages import Command, Event

class StartScrapeCommand(Command):
    project_id: int
    debug_mode: bool = False

class PauseScrapeCommand(Command):
    project_id: int

class ResumeScrapeCommand(Command):
    project_id: int

class StopScrapeCommand(Command):
    project_id: int

class SetResolutionActionCommand(Command):
    project_id: int
    action: str

# ---------------------------------------------------------------------------
# EVENTS
# ---------------------------------------------------------------------------
from typing import Any, Dict

class ScrapeLogEvent(Event):
    project_id: int
    message: str
    level: str = "INFO"

class ScrapeStatsEvent(Event):
    project_id: int
    stats: Dict[str, Any]

class DuplicateFoundEvent(Event):
    project_id: int
    data: Dict[str, Any]  # Contains 'new_image' and 'conflicts'

class CaptchaDetectedEvent(Event):
    project_id: int
    url: str

class DebugConfirmationEvent(Event):
    project_id: int
    message: str

class MinContentWarningEvent(Event):
    project_id: int
    url: str
    current_size: int
    min_size: int
    message: str = ""

class WorkerFinishedEvent(Event):
    project_id: int
    status: str
