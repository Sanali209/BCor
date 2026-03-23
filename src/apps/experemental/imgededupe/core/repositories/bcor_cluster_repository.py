from typing import Optional, List
from src.core.repository import AbstractRepository
from src.apps.experemental.imgededupe.core.database import DatabaseManager
from src.apps.experemental.imgededupe.core.models import Cluster

class BcorClusterRepository(AbstractRepository[Cluster]):
    """
    BCor-native Repository for Cluster entities.
    """
    def __init__(self, db_manager: DatabaseManager):
        super().__init__()
        self.db = db_manager

    def _add(self, cluster_aggregate: Cluster) -> None:
        """Saves a cluster aggregate."""
        if cluster_aggregate.id:
            self.db.update_cluster(
                cluster_id=cluster_aggregate.id,
                name=cluster_aggregate.name,
                target_folder=cluster_aggregate.target_folder
            )
        else:
            cluster_id = self.db.create_cluster(
                name=cluster_aggregate.name,
                target_folder=cluster_aggregate.target_folder
            )
            cluster_aggregate.id = cluster_id

    def _get(self, cluster_id: str) -> Optional[Cluster]:
        """Retrieves a cluster by ID."""
        try:
            cid = int(cluster_id)
        except (ValueError, TypeError):
            return None
            
        row = self.db.get_cluster_by_id(cid)
        if not row:
            return None
            
        return Cluster(
            id=row['id'],
            name=row['name'],
            target_folder=row['target_folder']
        )
