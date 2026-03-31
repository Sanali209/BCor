from loguru import logger
from dishka import AsyncContainer, Provider, Scope, provide
from pydantic_settings import BaseSettings

from src.core.messagebus import MessageBus
from src.core.module import BaseModule
from src.modules.agm.handlers import handle_stored_field_recalc, handle_node_sync_requested
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.schema import AGMSchemaManager
from src.modules.agm.messages import StoredFieldRecalculationRequested, NodeSyncRequested
from neo4j import AsyncDriver


class AGMSettings(BaseSettings):
    """Configuration settings for the Agentic Grid Management (AGM) module."""

    pass


class AGMProvider(Provider):
    """Dishka Provider for AGM-specific dependencies.

    Provides the AGMMapper and AGMSchemaManager, ensuring automated
    schema synchronization and live field resolution.
    """

    @provide(scope=Scope.APP)
    def provide_schema_manager(self, driver: AsyncDriver) -> AGMSchemaManager:
        """Provides a singleton AGMSchemaManager for Neo4j index management."""
        return AGMSchemaManager(driver=driver)

    @provide(scope=Scope.APP)
    def provide_agm_mapper(
        self, 
        container: AsyncContainer, 
        message_bus: MessageBus,
        schema_manager: AGMSchemaManager
    ) -> AGMMapper:
        """Provides a singleton AGMMapper instance.

        Args:
            container: The active AsyncContainer for dependency resolution.
            message_bus: The system MessageBus for dispatching side effects.
            schema_manager: Manager for automated index/constraint creation.

        Returns:
            A configured AGMMapper instance.
        """
        return AGMMapper(
            container=container, 
            message_bus=message_bus, 
            schema_manager=schema_manager
        )


class AGMModule(BaseModule):
    """Module for Agentic Grid Management (AGM).

    AGM provides a Graph-Object Mapping (GOM) layer for Neo4j,
    supporting polymorphic loading, live hydration of fields via DI,
    and background recalculation of stored fields via TaskIQ.
    """

    settings_class = AGMSettings

    def __init__(self):
        """Initializes the AGM module and registers its provider and handlers."""
        super().__init__()

        self.provider = AGMProvider()

        # Register event handlers for TaskIQ triggers
        self.event_handlers = {
            StoredFieldRecalculationRequested: [handle_stored_field_recalc],
            NodeSyncRequested: [handle_node_sync_requested]
        }

    async def startup(self) -> None:
        """Starts the TaskIQ broker in the current process."""
        try:
            from src.adapters.taskiq_broker import broker
            await broker.startup()
            logger.info("AGMModule: TaskIQ broker started.")
        except Exception as e:
            logger.error(f"AGMModule: Failed to start TaskIQ broker: {e}")

    async def stop(self) -> None:
        """Shuts down the TaskIQ broker."""
        try:
            from src.adapters.taskiq_broker import broker
            await broker.shutdown()
            logger.info("AGMModule: TaskIQ broker stopped.")
        except Exception as e:
            logger.error(f"AGMModule: Failed to stop TaskIQ broker: {e}")
