from PySide6.QtCore import QObject, Signal

from src.apps.experemental.boruscraper.application.messages import (
    ScrapeLogEvent,
    ScrapeStatsEvent,
    DuplicateFoundEvent,
    CaptchaDetectedEvent,
    DebugConfirmationEvent,
    MinContentWarningEvent,
    WorkerFinishedEvent
)


class GuiEventAdapter(QObject):
    """
    Provides PySide6 Signals for the GUI to consume.
    BCor Event Handlers update this adapter.
    """
    log_signal = Signal(str, str) # (level, message)
    stats_signal = Signal(int, dict) # (project_id, stats)
    duplicate_found_signal = Signal(int, str, list) # (project_id, new_image, conflicts)
    captcha_detected_signal = Signal(int) # (project_id)
    debug_confirmation_signal = Signal(int, str) # (project_id, message)
    min_content_warning_signal = Signal(int, str, int, int) # (project_id, url, current_size, min_size)
    worker_finished_signal = Signal(int) # (project_id)

    def __init__(self):
        super().__init__()


# ---------------------------------------------------------------------------
# BCor Event Handlers
# These are registered with the MessageBus and get GuiEventAdapter injected.
# ---------------------------------------------------------------------------

async def handle_log_event(event: ScrapeLogEvent, adapter: GuiEventAdapter):
    adapter.log_signal.emit(event.level, event.message)

async def handle_stats_event(event: ScrapeStatsEvent, adapter: GuiEventAdapter):
    from loguru import logger
    logger.debug(f"Handling ScrapeStatsEvent for project {event.project_id}: {event.stats}")
    adapter.stats_signal.emit(event.project_id, event.stats)

async def handle_duplicate_found(event: DuplicateFoundEvent, adapter: GuiEventAdapter):
    # data contains 'new_image' and 'conflicts'
    adapter.duplicate_found_signal.emit(
        event.project_id, 
        event.data.get('new_image', ''), 
        event.data.get('conflicts', [])
    )

async def handle_captcha_detected(event: CaptchaDetectedEvent, adapter: GuiEventAdapter):
    adapter.captcha_detected_signal.emit(event.project_id)

async def handle_debug_confirmation(event: DebugConfirmationEvent, adapter: GuiEventAdapter):
    adapter.debug_confirmation_signal.emit(event.project_id, event.message)

async def handle_min_content_warning(event: MinContentWarningEvent, adapter: GuiEventAdapter):
    adapter.min_content_warning_signal.emit(
        event.project_id, event.url, event.current_size, event.min_size
    )

async def handle_worker_finished(event: WorkerFinishedEvent, adapter: GuiEventAdapter):
    adapter.worker_finished_signal.emit(event.project_id)
