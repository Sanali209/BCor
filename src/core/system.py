from collections.abc import Callable
from pathlib import Path
from typing import Any, Iterable
import typing

from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from loguru import logger
from pydantic_settings import BaseSettings

from src.core.decorators import _run_hooks, get_start_hooks, get_stop_hooks
from src.core.messagebus import MessageBus
from src.core.module import BaseModule
from src.core.unit_of_work import AbstractUnitOfWork


class CoreProvider(Provider):
    """Dishka Provider for core system components.

    This provider manages the lifecycle and injection of global settings
    and the MessageBus, ensuring event and command handlers are correctly
    mapped from all enabled modules.
    """

    def __init__(
        self,
        event_handlers: dict[type, list[Callable[..., Any]]],
        command_handlers: dict[type, Callable[..., Any]],
        settings: dict[str, BaseSettings],
        *args: Any,  # noqa: ANN401
        **kwargs: Any,  # noqa: ANN401
    ) -> None:
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
    def provide_settings(self) -> dict[str, BaseSettings]:
        """Provides the global settings dictionary.

        Returns:
            A dictionary containing all validated module settings.
        """
        return self.settings

    @provide(scope=Scope.APP)
    async def provide_message_bus(self, uow: AbstractUnitOfWork, container: AsyncContainer) -> typing.AsyncIterable[MessageBus]:
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

        yield bus
        await bus.bus.stop()


class System:
    """System Composition Root.

    The System class manages the application's entire lifecycle using the 
    Composition Root pattern. It is responsible for orchestrating 
    discovery, bootstrapping, DI initialization, and hook execution.

    Lifecycle Diagram:
    ```mermaid
    graph TD
        A[from_manifest] --> B[_bootstrap]
        B --> C[Module.setup]
        C --> D[Collect Settings/Providers]
        D --> E[Init Dishka Container]
        E --> F[start]
        F --> G[Module.startup]
        G --> H[Run @on_start hooks]
    ```

    Rationale:
        By centralizing the wiring of all modules into a single System object, 
        we ensure that dependencies are strictly managed and the order of 
        initialization is deterministic.
    """

    @classmethod
    def from_manifest(cls, manifest_path: str | Path) -> "System":
        """Creates a System instance by discovering modules from a TOML manifest.

        Args:
            manifest_path: Path to the app.toml manifest file.

        Returns:
            An initialized System instance.
        """
        import tomllib

        from src.core.discovery import ModuleDiscovery

        path = Path(manifest_path)
        with path.open("rb") as f:
            config_data = tomllib.load(f)

        modules = ModuleDiscovery.load_from_manifest(manifest_path)
        return cls(modules=modules, config=config_data)

    def __init__(self, modules: list[BaseModule], config: dict[str, Any] | None = None) -> None:
        """Initializes the System with a list of modules and raw configuration.

        Args:
            modules: List of instantiated BaseModule subclasses.
            config: Raw configuration data from the manifest.
        """
        self.modules = modules
        self.config = config or {}
        self.container: AsyncContainer
        self.command_handlers: dict[type, Callable[..., Any]] = {}
        self.event_handlers: dict[type, list[Callable[..., Any]]] = {}
        self.providers: list[Provider] = []
        self.settings: dict[str, BaseSettings] = {}
        self._started = False
        self._initialized = False

    async def _bootstrap(self) -> None:
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
            await module.setup()
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
                self.providers.insert(0, module.provider)

        core_provider = CoreProvider(
            event_handlers=self.event_handlers,
            command_handlers=self.command_handlers,
            settings=self.settings,
            scope=Scope.APP,
        )

        self.providers.append(core_provider)
        self.container = make_async_container(*self.providers)
        
        # Inject container into modules for post-init resolution
        for module in self.modules:
            module.container = self.container
            
        self._initialized = True

    async def start(self) -> None:
        """Starts the system and triggers registered @on_start hooks.

        Ensures the system is bootstrapped before running hooks.
        """
        if self._started:
            logger.warning("System already started")
            return

        await self._bootstrap()

        logger.info("System starting...")
        
        # Give modules a chance to activate using the container
        for module in self.modules:
            await module.startup()
            
        await _run_hooks(get_start_hooks())

        self._started = True
        logger.info("System started")

    async def stop(self) -> None:
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
