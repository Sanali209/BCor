from dishka import Provider, Scope, provide
from pydantic_settings import BaseSettings
import os

from src.apps.experemental.boruscraper.common.database import DatabaseManager
from src.apps.experemental.boruscraper.common.deduplication import DeduplicationManager
from src.apps.experemental.boruscraper.settings import BoruScraperSettings
from src.apps.experemental.boruscraper.application.handlers import ScrapeTaskManager
from src.apps.experemental.boruscraper.infrastructure.events_adapter import GuiEventAdapter
from src.core.messagebus import MessageBus
from src.apps.experemental.boruscraper.application.template_registry import ScrapingTemplateRegistry
from src.apps.experemental.boruscraper.infrastructure.uow import SqliteUnitOfWork
from src.core.unit_of_work import AbstractUnitOfWork

class BoruScraperProvider(Provider):
    scope = Scope.APP

    @provide(scope=Scope.APP)
    def get_uow(self, db_manager: DatabaseManager) -> AbstractUnitOfWork:
        return SqliteUnitOfWork(db_manager)

    @provide
    def get_database_manager(self, settings_dict: dict[str, BaseSettings]) -> DatabaseManager:
        settings: BoruScraperSettings = settings_dict["boruscraper"]
        return DatabaseManager(db_path=settings.db_path)

    @provide
    def get_deduplication_manager(self, db_manager: DatabaseManager) -> DeduplicationManager:
        return DeduplicationManager(db_manager)

    @provide(scope=Scope.APP)
    def get_scrape_task_manager(self, bus: MessageBus, db: DatabaseManager, dedup: DeduplicationManager) -> ScrapeTaskManager:
        return ScrapeTaskManager(bus, db, dedup)

    @provide(scope=Scope.APP)
    def get_gui_event_adapter(self) -> GuiEventAdapter:
        return GuiEventAdapter()

    @provide(scope=Scope.APP)
    def get_template_registry(self) -> ScrapingTemplateRegistry:
        # Templates are located in the `scraper` package next to this file
        templates_dir = os.path.join(os.path.dirname(__file__), "scraper")
        return ScrapingTemplateRegistry(templates_dir)
