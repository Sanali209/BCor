from src.core.module import BaseModule
from src.apps.experemental.boruscraper.settings import BoruScraperSettings
from src.apps.experemental.boruscraper.provider import BoruScraperProvider
from src.apps.experemental.boruscraper.application.messages import (
    StartScrapeCommand, PauseScrapeCommand, ResumeScrapeCommand, 
    StopScrapeCommand, SetResolutionActionCommand,
    ScrapeLogEvent, ScrapeStatsEvent, DuplicateFoundEvent,
    CaptchaDetectedEvent, DebugConfirmationEvent, 
    MinContentWarningEvent, WorkerFinishedEvent
)
from src.apps.experemental.boruscraper.application.handlers import (
    start_scrape_handler, pause_scrape_handler, resume_scrape_handler,
    stop_scrape_handler, set_resolution_action_handler
)
from src.apps.experemental.boruscraper.infrastructure.events_adapter import (
    handle_log_event, handle_stats_event, handle_duplicate_found,
    handle_captcha_detected, handle_debug_confirmation,
    handle_min_content_warning, handle_worker_finished
)

class BoruScraperModule(BaseModule):
    name = "boruscraper"
    settings_class = BoruScraperSettings
    
    def __init__(self):
        super().__init__()
        self.provider = BoruScraperProvider()
        
        self.command_handlers = {
            StartScrapeCommand: start_scrape_handler,
            PauseScrapeCommand: pause_scrape_handler,
            ResumeScrapeCommand: resume_scrape_handler,
            StopScrapeCommand: stop_scrape_handler,
            SetResolutionActionCommand: set_resolution_action_handler,
        }
        
        self.event_handlers = {
            ScrapeLogEvent: [handle_log_event],
            ScrapeStatsEvent: [handle_stats_event],
            DuplicateFoundEvent: [handle_duplicate_found],
            CaptchaDetectedEvent: [handle_captcha_detected],
            DebugConfirmationEvent: [handle_debug_confirmation],
            MinContentWarningEvent: [handle_min_content_warning],
            WorkerFinishedEvent: [handle_worker_finished],
        }
