import abc
from src.core.repository import AbstractRepository
from src.core.unit_of_work import AbstractUnitOfWork
from src.modules.ecs.domain import EcsWorld


class AbstractEcsRepository(AbstractRepository[EcsWorld], abc.ABC):
    """Abstract Port hiding details of storing the ECS World."""

    @abc.abstractmethod
    def get_world(self, world_id: str) -> EcsWorld:
        """Fetch the ECS World Aggregate."""
        raise NotImplementedError


class EcsUnitOfWork(AbstractUnitOfWork, abc.ABC):
    """Unit of Work specifically typed for ECS Module operations."""

    worlds: AbstractEcsRepository
