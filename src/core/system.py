from typing import List, Dict, Type, Callable, Union
from pathlib import Path
from dishka import Provider, make_async_container, Scope, provide, AsyncContainer
from pydantic_settings import BaseSettings
from loguru import logger

from src.core.module import BaseModule
from src.core.messagebus import MessageBus
from src.core.unit_of_work import AbstractUnitOfWork
from src.core.decorators import get_start_hooks, get_stop_hooks, _run_hooks


class CoreProvider(Provider):
    """Dishka Provider for core system components.
    
    This provider manages the lifecycle and injection of global settings
    and the MessageBus, ensuring event and command handlers are correctly
    mapped from all enabled modules.
    """

    def __init__(self, event_handlers: Dict[Type, List[Callable]], 
                 command_handlers: Dict[Type, Callable], 
                 settings: Dict[str, BaseSettings], *args, **kwargs):
        """Initializes the CoreProvider with handlers and settings.

        Args:
            event_handlers: Map of event types to their subscriber lists.
            command_handlers: Map of command types to their single handlers.
            settings: Dictionary of validated module settings.
        """
        super().__init__(*args, **kwargs)
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        self.settings = settings

    @provide(scope=Scope.APP)
    def provide_settings(self) -> Dict[str, BaseSettings]:
        """Provides the global settings dictionary.

        Returns:
            A dictionary containing all validated module settings.
        """
        return self.settings

    @provide(scope=Scope.REQUEST)
    def provide_message_bus(self, uow: AbstractUnitOfWork, container: AsyncContainer) -> MessageBus:
        """Provides a request-scoped MessageBus instance with DI container access.

        The MessageBus is injected with the current Unit of Work and
        the DI container, allowing automated dependency resolution for 
        command and event handlers.

        Args:
            uow: The active Unit of Work for the request.
            container: The active DI container for the request.

        Returns:
            A configured MessageBus instance.
        """
        bus = MessageBus(uow=uow, container=container)

        for cmd_type, handler in self.command_handlers.items():
            bus.register_command(cmd_type, handler)

        for evt_type, handlers in self.event_handlers.items():
            for handler in handlers:
                bus.register_event(evt_type, handler)

        return bus


class System:
    """System Composition Root.

    The System class is responsible for the overall lifecycle of the application:
    1. Module Discovery: Finding modules via manifest files.
    2. Bootstrapping: Collecting handlers, settings, and providers from modules.
    3. DI Initialization: Setting up the Dishka container.
    4. Lifecycle Management: Running start/stop hooks.
    """

    @classmethod
    def from_manifest(cls, manifest_path: str | Path) -> "System":
        """Creates a System instance by discovering modules from a TOML manifest.

        Args:
            manifest_path: Path to the app.toml manifest file.

        Returns:
            An initialized System instance.
        """
        from src.core.discovery import ModuleDiscovery
        import tomllib

        path = Path(manifest_path)
        with path.open("rb") as f:
            config_data = tomllib.load(f)

        modules = ModuleDiscovery.load_from_manifest(manifest_path)
        return cls(modules=modules, config=config_data)

    def __init__(self, modules: List[BaseModule], config: dict = None):
        """Initializes the System with a list of modules and raw configuration.

        Args:
            modules: List of instantiated BaseModule subclasses.
            config: Raw configuration data from the manifest.
        """
        self.modules = modules
        self.config = config or {}
        self.command_handlers: Dict[Type, Callable] = {}
        self.event_handlers: Dict[Type, List[Callable]] = {}
        self.providers: List[Provider] = []
        self.settings: Dict[str, BaseSettings] = {}
        self._started = False
        self._initialized = False

    def _bootstrap(self):
        """Bootstraps the system by merging module configurations and providers.

        This method:
        - Collects event and command handlers from all modules.
        - Validates and instantiates module-specific Pydantic settings.
        - Accumulates Dishka providers.
        - Initializes the asynchronous DI container.
        """
        if self._initialized:
            return
        
        for module in self.modules:
            self.command_handlers.update(module.command_handlers)
            for event_type, handlers in module.event_handlers.items():
                self.event_handlers.setdefault(event_type, []).extend(handlers)

            if module.settings_class:
                module_name = module.__class__.__name__.lower().replace("module", "")
                module_config_kwargs = self.config.get(module_name, {})
                validated_settings = module.settings_class(**module_config_kwargs)
                module.settings = validated_settings
                self.settings[module_name] = validated_settings

            if module.provider:
                self.providers.append(module.provider)

        core_provider = CoreProvider(
            event_handlers=self.event_handlers,
            command_handlers=self.command_handlers,
            settings=self.settings,
            scope=Scope.APP,
        )

        self.providers.append(core_provider)
        self.container = make_async_container(*self.providers)
        self._initialized = True

    async def start(self):
        """Starts the system and triggers registered @on_start hooks.

        Ensures the system is bootstrapped before running hooks.
        """
        if self._started:
            logger.warning("System already started")
            return

        self._bootstrap()
        
        logger.info("System starting...")
        await _run_hooks(get_start_hooks())
        
        self._started = True
        logger.info("System started")

    async def stop(self):
        """Stops the system and triggers registered @on_stop hooks.

        Closes the DI container and marks the system as stopped.
        """
        if not self._started:
            logger.warning("System not started")
            return

        logger.info("System stopping...")
        await _run_hooks(get_stop_hooks())
        await self.container.close()
        
        self._started = False
        logger.info("System stopped")
