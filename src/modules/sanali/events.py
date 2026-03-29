from src.core.messages import Event
from typing import Any, Dict
from pydantic import Field

class LegacyMessageEvent(Event):
    """Event wrapper for legacy string-based messages"""
    message_name: str
    message_data: Dict[str, Any] = Field(default_factory=dict)
    
    @property
    def name(self):
        return self.message_name
