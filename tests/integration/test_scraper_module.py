import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from dishka import Provider, Scope, provide
from src.core.system import System
from src.core.messagebus import MessageBus
from src.core.unit_of_work import AbstractUnitOfWork
from src.modules.scraper.messages import ScrapePageCommand, ScrapedEvent
from src.modules.scraper.domain.interfaces import IScraperAdapter, ScraperConfig, ScraperResult, ScraperFieldConfig

class SimpleUoW(AbstractUnitOfWork):
    def _commit(self): pass
    def rollback(self): pass
    def _get_all_seen_aggregates(self): return []

@pytest.mark.asyncio
async def test_scraper_module_flow(tmp_path):
    # Setup minimal system with ScraperModule
    manifest_content = f"""
[system]
name = "TestScraper"
version = "0.1.0"
[modules]
enabled = ["scraper"]
paths = ["src.modules"]
"""
    manifest_path = tmp_path / "app.toml"
    manifest_path.write_text(manifest_content)
    
    class TestProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def provide_uow(self) -> AbstractUnitOfWork: return SimpleUoW()

    with patch("src.modules.scraper.provider.PlaywrightScraperAdapter") as mock_adapter_cls:
        # Setup mock behavior
        mock_adapter = mock_adapter_cls.return_value
        mock_adapter.scrape_page = AsyncMock(return_value=ScraperResult(
            url="http://example.com",
            fields={"title": "Example Title"},
            success=True
        ))

        system = System.from_manifest(manifest_path)
        system.providers.append(TestProvider())

        await system.start()
    
        try:
            async with system.container() as container:
                bus = await container.get(MessageBus)
                
                # Use Future to wait for the event
                future_evt = asyncio.Future()
                
                async def on_scraped(event: ScrapedEvent, **kwargs):
                    if not future_evt.done():
                        future_evt.set_result(event)
                
                bus.register_event(ScrapedEvent, on_scraped)
                
                config = ScraperConfig(
                    url="http://example.com",
                    fields=[ScraperFieldConfig(name="title", selector="h1", type="text")]
                )
                cmd = ScrapePageCommand(config=config)
                
                await bus.dispatch(cmd)
                
                evt = await asyncio.wait_for(future_evt, timeout=5.0)
                
                assert isinstance(evt, ScrapedEvent)
                assert evt.result.success
                assert evt.result.fields["title"] == "Example Title"
                
        finally:
            await system.stop()
