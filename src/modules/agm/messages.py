from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, List
from src.core.messages import Event

@dataclass
class SyncFieldInfo:
    """Descriptor for a single field metadata recalculation in a batch."""
    field_name: str
    source_value: Any
    handler: str | None = None
    model: str | None = None
    priority: int = 0
    context_metadata: dict[str, Any] = field(default_factory=dict)

class StoredFieldRecalculationRequested(Event):
    """Event emitted when a source field changes, requiring a recalculation."""
    node_id: str
    field_name: str
    new_source_val: Any
    mime_type: str = ""
    handler: str | None = None
    model: str | None = None
    use_taskiq: bool = False
    priority: int = 0
    context_metadata: dict[str, Any] = {}

class NodeSyncRequested(Event):
    """Batch event for synchronizing multiple fields of a single node."""
    node_id: str
    fields: List[SyncFieldInfo]
    mime_type: str = ""
    use_taskiq: bool = False
    priority: int = 0
