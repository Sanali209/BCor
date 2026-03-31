import abc
from typing import List, Optional, Dict
from src.apps.experemental.boruscraper.domain.models import Project, Post

class IProjectRepository(abc.ABC):
    @abc.abstractmethod
    def get(self, project_id: int) -> Optional[Project]:
        pass

    @abc.abstractmethod
    def save(self, project: Project) -> None:
        pass
        
    @abc.abstractmethod
    def create(self, name: str, settings: dict, start_urls: list) -> int:
        pass

    @abc.abstractmethod
    def get_all_projects(self) -> List[Dict]:
        pass

    @abc.abstractmethod
    def fetch_queued_projects(self) -> List[Dict]:
        pass
        
    @abc.abstractmethod
    def get_pagination_state(self, project_id: int, start_url: str) -> Optional[dict]:
        pass

    @abc.abstractmethod
    def update_pagination_state(self, project_id: int, start_url: str, last_page_url: str, direction: str = "forward") -> None:
        pass

    @abc.abstractmethod
    def delete_pagination_state(self, project_id: int, start_url: str) -> None:
        pass

class IPostRepository(abc.ABC):
    @abc.abstractmethod
    def get(self, post_id: str) -> Optional[Post]:
        pass

    @abc.abstractmethod
    def save(self, post: Post) -> None:
        pass

    @abc.abstractmethod
    def post_exists(self, project_id: int, post_id: str) -> bool:
        pass
        
    @abc.abstractmethod
    def get_existing_post_path(self, project_id: int, post_id: str) -> Optional[str]:
        pass
