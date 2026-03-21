from dataclasses import dataclass, field
from enum import Enum, auto
from typing import List, Optional, Dict, Any
from datetime import datetime

class RelationSubType(Enum):
    WRONG = "wrong"
    SIMILAR = "similar"
    NOT_SIMILAR = "near_dub"
    SIMILAR_STYLE = "similar_style"
    MANUAL = "manual"
    SOME_PERSON = "some_person"
    SOME_IMAGE_SET = "some_image_set"
    OTHER = "other"
    HIDEN = "hiden"
    NONE = "none"

@dataclass(frozen=True)
class RelationRecord:
    id: str
    from_id: str
    to_id: str
    relation_type: str = "similar_search"
    sub_type: RelationSubType = RelationSubType.NONE
    distance: float = 0.0
    euclidean: float = 0.0
    manhattan: float = 0.0
    hamming: float = 0.0
    dot: float = 0.0
    emb_type: str = "unknown"
    created_at: datetime = field(default_factory=datetime.now)

@dataclass(frozen=True)
class GraphNode:
    id: str
    type: str  # "file", "tag", "pin"
    name: str
    pos_x: float = 0.0
    pos_y: float = 0.0
    data: Dict[str, Any] = field(default_factory=dict)

@dataclass(frozen=True)
class GraphEdge:
    from_node_id: str
    to_node_id: str
    relation_id: Optional[str] = None
    edge_type: str = "relation" # "relation", "tag", "manual"
    sub_type: RelationSubType = RelationSubType.NONE
