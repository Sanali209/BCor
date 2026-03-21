from dishka import Provider, Scope, provide
from .domain.interfaces import IScraperAdapter
from .adapters.playwright_adapter import PlaywrightScraperAdapter

class ScraperProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_scraper_adapter(self) -> IScraperAdapter:
        return PlaywrightScraperAdapter()
