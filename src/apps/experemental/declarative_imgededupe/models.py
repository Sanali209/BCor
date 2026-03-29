from dataclasses import dataclass, field
from typing import Annotated, Any
from src.modules.agm.metadata import Unique, Indexed

@dataclass
class DedupeSession:
    """Represents a single deduplication run/session.
    
    This can be persisted in the graph to track history of scans and clusters.
    """
    id: Annotated[str, Unique()]
    root_path: str
    threshold: float = 0.95
    status: str = "pending"  # pending, scanning, clustering, finished
    count_total: int = 0
    count_duplicates: int = 0
    created_at: float = 0.0
