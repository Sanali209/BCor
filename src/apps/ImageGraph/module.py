from typing import Any
from dishka import Provider, Scope, provide
from .infrastructure.mongo_relation_repo import MongoRelationRepo
from .use_cases import SearchRelatedImagesUseCase, UpdateRelationUseCase, CreateManualRelationUseCase
from .gui.widgets.graph_widget import ImageGraphWidget
from .gui.main_window import ImageGraphMainWindow

class ImageGraphModule(Provider):
    scope = Scope.APP

    @provide
    def get_relation_repo(self) -> MongoRelationRepo:
        return MongoRelationRepo()

    @provide
    def get_search_use_case(self, repo: MongoRelationRepo, file_repo: Any) -> SearchRelatedImagesUseCase:
        return SearchRelatedImagesUseCase(repo, file_repo)

    @provide
    def get_update_use_case(self, repo: MongoRelationRepo) -> UpdateRelationUseCase:
        return UpdateRelationUseCase(repo)

    @provide
    def get_create_manual_use_case(self, repo: MongoRelationRepo) -> CreateManualRelationUseCase:
        return CreateManualRelationUseCase(repo)

    @provide
    def get_graph_widget(self, search: SearchRelatedImagesUseCase, update: UpdateRelationUseCase) -> ImageGraphWidget:
        return ImageGraphWidget(search, update)

    @provide
    def get_main_window(self, widget: ImageGraphWidget) -> ImageGraphMainWindow:
        return ImageGraphMainWindow(widget)
