from src.core.module import BaseModule
import typing
from dishka import Provider, Scope, provide
from src.modules.sanali.services import ConfigurationService
from src.core.unit_of_work import AbstractUnitOfWork
from bubus import EventBus

class StubUnitOfWork(AbstractUnitOfWork):
    def _commit(self) -> None:
        pass
    def rollback(self) -> None:
        pass

from src.apps.experemental.sanali.Python.core_apps.services.configuration_service import ConfigurationService as LegacyConfig
from src.modules.sanali.services import ConfigurationService
from src.apps.experemental.sanali.Python.core_apps.repository.annotation_repository import AnnotationRepositoryInterface
from src.modules.sanali.repositories import AnnotationRepository
from src.modules.sanali.use_cases import ImageManagementUseCase
from src.modules.sanali.services import DuplicateService, ProjectStateService, NeiroFilterService, UserPreferenceService
from .presenters import ImageDedupPresenter

class SanaliProvider(Provider):
    scope = Scope.APP
    
    @provide
    def provide_uow(self) -> AbstractUnitOfWork:
        return StubUnitOfWork()
    
    @provide
    def provide_config(self) -> LegacyConfig:
        return ConfigurationService()

    @provide
    def provide_repo(self, config: LegacyConfig) -> AnnotationRepositoryInterface:
        return AnnotationRepository(config)

    @provide
    def provide_image_mgmt(self) -> ImageManagementUseCase:
        return ImageManagementUseCase()

    @provide
    def provide_duplicate_service(self) -> DuplicateService:
        return DuplicateService()

    @provide(scope=Scope.APP)
    def provide_project_state_service(self) -> ProjectStateService:
        return ProjectStateService()

    @provide(scope=Scope.APP)
    def provide_neiro_filter_service(self) -> NeiroFilterService:
        return NeiroFilterService()

    @provide(scope=Scope.APP)
    async def provide_user_preference_service(self) -> typing.AsyncIterable[UserPreferenceService]:
        service = UserPreferenceService()
        yield service
        service.close()

    @provide(scope=Scope.APP)
    def provide_dedup_presenter(
        self, 
        state_service: ProjectStateService, 
        dup_service: DuplicateService,
        neiro_service: NeiroFilterService,
        pref_service: UserPreferenceService
    ) -> ImageDedupPresenter:
        return ImageDedupPresenter(state_service, dup_service, neiro_service, pref_service)

    @provide
    async def provide_event_bus(self) -> typing.AsyncIterable[EventBus]:
        bus = EventBus()
        yield bus
        await bus.stop()

class SanaliModule(BaseModule):
    provider = SanaliProvider()
