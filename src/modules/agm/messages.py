from typing import Any
from src.core.messages import Event


class StoredFieldRecalculationRequested(Event):
    node_id: str
    field_name: str
    new_source_val: Any
