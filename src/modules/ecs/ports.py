import abc
from src.core.repository import AbstractRepository
from src.core.unit_of_work import AbstractUnitOfWork
from src.modules.ecs.domain import EcsWorld


class AbstractEcsRepository(AbstractRepository[EcsWorld], abc.ABC):
    """Abstract Port for persisting and retrieving ECS worlds.
    
    Hides the storage implementation (In-Memory, SQLAlchemy, Neo4j) 
    from the domain logic.
    """

    @abc.abstractmethod
    async def get_world(self, world_id: str) -> EcsWorld:
        """Fetches an ECS World Aggregate from the storage.

        Args:
            world_id: Unique identifier for the world.

        Returns:
            The loaded EcsWorld instance.
        """
        raise NotImplementedError


class EcsUnitOfWork(AbstractUnitOfWork, abc.ABC):
    """Specialized Unit of Work for ECS Module operations.
    
    Provides strongly-typed access to the ECS world repository.

    Attributes:
        worlds: The EcsWorld repository instance.
    """
    worlds: AbstractEcsRepository
