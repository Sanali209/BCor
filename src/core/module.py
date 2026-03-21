from collections.abc import Callable
from typing import Any

from dishka import Provider
from pydantic_settings import BaseSettings


class BaseModule:
    """Base class for every domain module.

    A module encapsulates:
    1. Settings: Defined via `settings_class` (Pydantic).
    2. Dependency Injection: Defined via a `dishka.Provider`.
    3. Message Routing: Mapping commands and events to their respective handlers.

    Attributes:
        settings_class: Optional Pydantic BaseSettings class for the module.
        provider: Optional Dishka Provider instance for the module's dependencies.
        command_handlers: Dict mapping command types to handler functions.
        event_handlers: Dict mapping event types to lists of handler functions.
    """

    settings_class: type[BaseSettings] | None = None
    provider: Provider | None = None

    command_handlers: dict[type, Callable[..., Any]] = {}
    event_handlers: dict[type, list[Callable[..., Any]]] = {}

    def __init__(self) -> None:
        """Initializes a module instance.

        Ensures that routing maps are copied from the class level to the
        instance level to prevent cross-module pollution.
        """
        self.command_handlers = self.__class__.command_handlers.copy()
        self.event_handlers = {k: list(v) for k, v in self.__class__.event_handlers.items()}
        self.settings: BaseSettings | None = None

    def setup(self) -> None:
        """Lifecycle hook called during system bootstrap.

        Modules can override this to perform one-time initialization
        logic, such as registering custom providers or setting up
        external resources.
        """
        pass
