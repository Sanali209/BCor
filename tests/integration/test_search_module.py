import asyncio
import pytest
from unittest.mock import AsyncMock, patch
from dishka import Provider, Scope, provide, make_async_container
from src.core.system import System
from src.core.messagebus import MessageBus
from src.core.unit_of_work import AbstractUnitOfWork
from src.modules.search.messages import SearchImagesCommand, SearchResultsEvent
from src.modules.search.domain.interfaces import ISearchAdapter, SearchResult

class SimpleUoW(AbstractUnitOfWork):
    def _commit(self): pass
    def rollback(self): pass
    def _get_all_seen_aggregates(self): return []

class SearchTestProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_uow(self) -> AbstractUnitOfWork:
        return SimpleUoW()

    @provide(scope=Scope.REQUEST)
    def provide_mock_adapter(self) -> ISearchAdapter:
        mock = AsyncMock(spec=ISearchAdapter)
        mock.search_images.return_value = [
            SearchResult(title="Mock Result", url="http://ext.com", image_url="http://ext.com/img.jpg", source="Mock")
        ]
        return mock

    @provide(scope=Scope.REQUEST)
    def provide_search_adapters(self, mock: ISearchAdapter) -> list[ISearchAdapter]:
        return [mock]

@pytest.mark.asyncio
async def test_search_module_flow(tmp_path):
    # Setup minimal system with SearchModule
    manifest_content = f"""
[system]
name = "TestSearch"
version = "0.1.0"
[modules]
enabled = ["search"]
paths = ["src.modules"]
"""
    manifest_path = tmp_path / "app.toml"
    manifest_path.write_text(manifest_content)
    
    class TestProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def provide_uow(self) -> AbstractUnitOfWork: return SimpleUoW()

    with patch("src.modules.search.provider.DuckDuckGoAdapter") as mock_ddg_cls, \
         patch("src.modules.search.provider.PexelsAdapter") as mock_pexels_cls:
        
        # Setup mock behavior
        mock_ddg = mock_ddg_cls.return_value
        mock_ddg.search_images = AsyncMock(return_value=[
            SearchResult(title="Mock DDG", url="http://ddg.com", image_url="http://ddg.com/i.jpg", source="DDG")
        ])
        
        mock_pexels = mock_pexels_cls.return_value
        mock_pexels.search_images = AsyncMock(return_value=[
            SearchResult(title="Mock Pexels", url="http://pexels.com", image_url="http://pexels.com/i.jpg", source="Pexels")
        ])

        system = System.from_manifest(manifest_path)
        system.providers.append(TestProvider())

        print("Starting system...")
        await system.start()
        print("System started.")
    
        try:
            print("Creating container...")
            async with system.container() as container:
                print("Getting MessageBus...")
                bus = await container.get(MessageBus)
                
                # Use Future to wait for the event
                future_evt = asyncio.Future()
                
                async def on_results(event: SearchResultsEvent, **kwargs):
                    print(f"Subscriber received results: {len(event.results)}")
                    if not future_evt.done():
                        future_evt.set_result(event)
                
                bus.register_event(SearchResultsEvent, on_results)
                
                cmd = SearchImagesCommand(query="test", limit=1)
                
                print("Dispatching command...")
                await bus.dispatch(cmd)
                
                print("Waiting for event via Future...")
                evt = await asyncio.wait_for(future_evt, timeout=5.0)
                print("Received event successfully.")
                
                assert isinstance(evt, SearchResultsEvent)
                assert len(evt.results) == 2
                assert any(r.source == "DDG" for r in evt.results)
                assert any(r.source == "Pexels" for r in evt.results)
                
        finally:
            print("Stopping system...")
            await system.stop()
            print("System stopped.")
