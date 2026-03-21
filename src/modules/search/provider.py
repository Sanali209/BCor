from dishka import Provider, Scope, provide
from .domain.interfaces import ISearchAdapter
from .adapters.duckduckgo_adapter import DuckDuckGoAdapter
from .adapters.pexels_adapter import PexelsAdapter

class SearchProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_ddg_adapter(self) -> DuckDuckGoAdapter:
        return DuckDuckGoAdapter()

    @provide(scope=Scope.REQUEST)
    def provide_pexels_adapter(self) -> PexelsAdapter:
        # In a real app, this would come from settings
        return PexelsAdapter(api_key="fWR0eYyjy9EY2hu9b9bsADZSOQhexk0hgGlVSYnrs53Dq0AQNqNhxyML")

    @provide(scope=Scope.REQUEST)
    def provide_search_adapters(
        self, 
        ddg: DuckDuckGoAdapter, 
        pexels: PexelsAdapter
    ) -> list[ISearchAdapter]:
        return [ddg, pexels]
