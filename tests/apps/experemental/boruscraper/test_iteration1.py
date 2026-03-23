import pytest
from pydantic_settings import BaseSettings
from dishka import make_async_container, Provider, Scope, provide
from src.core.messagebus import MessageBus

def test_imports():
    try:
        from src.apps.experemental.boruscraper.settings import BoruScraperSettings
        from src.apps.experemental.boruscraper.module import BoruScraperModule
        from src.apps.experemental.boruscraper.provider import BoruScraperProvider
        from src.apps.experemental.boruscraper.common.database import DatabaseManager
    except ImportError as e:
        pytest.fail(f"Iteration 1 files do not exist or have import errors: {e}")

@pytest.mark.asyncio
async def test_settings_can_be_instantiated():
    from src.apps.experemental.boruscraper.settings import BoruScraperSettings
    settings = BoruScraperSettings(save_path="/tmp/test", deduplication_threshold=10)
    assert isinstance(settings, BaseSettings)
    assert settings.save_path == "/tmp/test"
    assert settings.deduplication_threshold == 10

@pytest.mark.asyncio
async def test_module_has_correct_settings_class():
    from src.apps.experemental.boruscraper.module import BoruScraperModule
    from src.apps.experemental.boruscraper.settings import BoruScraperSettings
    assert BoruScraperModule.settings_class == BoruScraperSettings
    assert BoruScraperModule.name == "boruscraper"

@pytest.mark.asyncio
async def test_dishka_provider_yields_database_manager():
    from src.apps.experemental.boruscraper.settings import BoruScraperSettings
    from src.apps.experemental.boruscraper.provider import BoruScraperProvider
    from src.apps.experemental.boruscraper.common.database import DatabaseManager

    settings_dict = {"boruscraper": BoruScraperSettings(save_path="/tmp/test", deduplication_threshold=10)}
    provider = BoruScraperProvider()
    
    class SettingsProvider(Provider):
        @provide(scope=Scope.APP)
        def get_settings(self) -> dict[str, BaseSettings]:
            return settings_dict

        @provide(scope=Scope.APP)
        def get_message_bus(self) -> MessageBus:
            from unittest.mock import MagicMock
            return MagicMock(spec=MessageBus)

    container = make_async_container(SettingsProvider(), provider)
    
    db_manager = await container.get(DatabaseManager)
    assert db_manager is not None
    assert isinstance(db_manager, DatabaseManager)
    await container.close()
