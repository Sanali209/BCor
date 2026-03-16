from typing import Dict, List, Type, Callable, Optional
from dishka import Provider
from pydantic_settings import BaseSettings

class BaseModule:
    """Base class for every domain module.

    Encapsulates:
    1. Settings
    2. Dependency Injection Provider (Dishka)
    3. Routing maps for the Event Bus
    """
    settings_class: Optional[Type[BaseSettings]] = None
    provider: Optional[Provider] = None

    # Declarative routing maps
    command_handlers: Dict[Type, Callable] = {}
    event_handlers: Dict[Type, List[Callable]] = {}

    def __init__(self):
        # We ensure they are copied to avoid shared class-level mutation issues
        self.command_handlers = self.__class__.command_handlers.copy()
        self.event_handlers = {k: list(v) for k, v in self.__class__.event_handlers.items()}
