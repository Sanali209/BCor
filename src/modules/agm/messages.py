from typing import Any

from src.core.messages import Event


class StoredFieldRecalculationRequested(Event):
    """Event emitted when a source field changes, requiring a recalculation.

    Attributes:
        node_id: The unique identifier of the graph node.
        field_name: The name of the stored field to recalculate.
        new_source_val: The updated value of the source field.
    """

    node_id: str
    field_name: str
    new_source_val: Any
