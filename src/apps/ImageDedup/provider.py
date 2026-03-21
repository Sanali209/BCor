"""ImageDedup Dishka provider."""
from dishka import Provider, Scope, provide

from src.apps.ImageDedup.domain.interfaces.i_image_differ import IDuplicateFinder, IImageDiffer, IThumbnailCache
from src.apps.ImageDedup.domain.interfaces.i_image_tagger import IImageTagger
from src.apps.ImageDedup.domain.interfaces.i_xmp_metadata import IXmpMetadata
from src.modules.llm.domain.interfaces.llm import ILlmAdapter
from src.apps.ImageDedup.infrastructure.uow import ImageDedupUnitOfWork
from src.core.unit_of_work import AbstractUnitOfWork


class ImageDedupProvider(Provider):
    """Provides ImageDedup adapters to the DI container."""

    @provide(scope=Scope.APP)
    def provide_image_differ(self) -> IImageDiffer:
        from src.apps.ImageDedup.adapters.cv_differ import OpenCVDiffer
        return OpenCVDiffer()

    @provide(scope=Scope.APP)
    def provide_thumbnail_cache(self) -> IThumbnailCache:
        from src.apps.ImageDedup.adapters.pil_thumbnail_cache import PILThumbnailCache
        return PILThumbnailCache()

    @provide(scope=Scope.APP)
    def provide_duplicate_finder(self) -> IDuplicateFinder:
        from src.apps.ImageDedup.adapters.annoy_finder import AnnoyDuplicateFinder
        return AnnoyDuplicateFinder()

    @provide(scope=Scope.APP)
    def provide_xmp_metadata(self) -> IXmpMetadata:
        from src.apps.ImageDedup.adapters.pyexiv2_adapter import PyExiv2MetadataAdapter
        return PyExiv2MetadataAdapter()

    @provide(scope=Scope.SESSION)
    def provide_image_tagger(self, llm: ILlmAdapter) -> IImageTagger:
        from src.apps.ImageDedup.adapters.llm_tagger_adapter import LlmImageTagger
        return LlmImageTagger(llm)

    @provide(scope=Scope.REQUEST)
    def provide_uow(self) -> AbstractUnitOfWork:
        return ImageDedupUnitOfWork()
