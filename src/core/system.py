from typing import List, Dict, Type, Callable
from dishka import Provider, make_async_container, Scope, provide
from pydantic_settings import BaseSettings

from src.core.module import BaseModule
from src.core.messagebus import MessageBus
from src.core.unit_of_work import AbstractUnitOfWork


class CoreProvider(Provider):
    def __init__(self, event_handlers, command_handlers, settings, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        self.settings = settings

    @provide(scope=Scope.APP)
    def provide_settings(self) -> Dict[str, BaseSettings]:
        return self.settings

    @provide(scope=Scope.REQUEST)
    def provide_message_bus(self, uow: AbstractUnitOfWork) -> MessageBus:
        # Create the MessageBus instance injected with the current UoW
        bus = MessageBus(uow=uow)

        # Register declarative routing maps from modules dynamically onto the new bus instance
        for cmd_type, handler in self.command_handlers.items():
            bus.register_command(cmd_type, handler)

        for evt_type, handlers in self.event_handlers.items():
            for handler in handlers:
                bus.register_event(evt_type, handler)

        return bus


class System:
    """System Base Class (Composition Root).

    Responsible for:
    1. Collecting routing maps from modules
    2. Merging declarative settings into a composite tree
    3. Merging Dishka providers
    4. Initializing the IoC container
    """

    @classmethod
    def from_manifest(cls, manifest_path: str):
        """Create a System instance by discovering modules from a TOML manifest."""
        from src.core.discovery import ModuleDiscovery
        import tomllib
        from pathlib import Path

        path = Path(manifest_path)
        with path.open("rb") as f:
            config_data = tomllib.load(f)

        modules = ModuleDiscovery.load_from_manifest(manifest_path)
        return cls(modules=modules, config=config_data)

    def __init__(self, modules: List[BaseModule], config: dict = None):
        self.modules = modules
        self.config = config or {}
        self.command_handlers: Dict[Type, Callable] = {}
        self.event_handlers: Dict[Type, List[Callable]] = {}
        self.providers: List[Provider] = []
        self.settings: Dict[str, BaseSettings] = {}

    def _bootstrap(self):
        # 1. Collect Event Bus routing maps and settings from all modules
        for module in self.modules:
            self.command_handlers.update(module.command_handlers)
            for event_type, handlers in module.event_handlers.items():
                self.event_handlers.setdefault(event_type, []).extend(handlers)

            # Collect and Validate declarative settings (Fail-Fast Boundary)
            if module.settings_class:
                module_name = module.__class__.__name__.lower().replace("module", "")
                
                # Extract settings from TOML config if available
                module_config_kwargs = self.config.get(module_name, {})

                # Instantiate settings class (reads from kwargs, then env vars via pydantic-settings)
                validated_settings = module.settings_class(**module_config_kwargs)

                # Inject validated settings back into the module
                module.settings = validated_settings

                # Register globally under a module-specific key
                module_name = module.__class__.__name__.lower().replace("module", "")
                self.settings[module_name] = validated_settings

            # Collect dependency providers
            if module.provider:
                self.providers.append(module.provider)

        # 2. Register the Core Provider (MessageBus, Settings)
        core_provider = CoreProvider(
            event_handlers=self.event_handlers,
            command_handlers=self.command_handlers,
            settings=self.settings,
            scope=Scope.APP,
        )

        self.providers.append(core_provider)

        # 3. Initialize Dishka DI container
        self.container = make_async_container(*self.providers)
