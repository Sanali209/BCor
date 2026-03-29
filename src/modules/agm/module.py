from dishka import AsyncContainer, Provider, Scope, provide
from pydantic_settings import BaseSettings

from src.core.messagebus import MessageBus
from src.core.module import BaseModule
from src.modules.agm.handlers import handle_stored_field_recalc, handle_node_sync_requested
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.messages import StoredFieldRecalculationRequested, NodeSyncRequested


class AGMSettings(BaseSettings):
    """Configuration settings for the Agentic Grid Management (AGM) module."""

    pass


class AGMProvider(Provider):
    """Dishka Provider for AGM-specific dependencies.

    Provides the AGMMapper, ensuring it has access to the application
    container for live field resolution.
    """

    scope = Scope.REQUEST

    @provide
    def provide_agm_mapper(self, container: AsyncContainer, message_bus: MessageBus) -> AGMMapper:
        """Provides a request-scoped AGMMapper instance.

        Args:
            container: The active AsyncContainer for dependency resolution.
            message_bus: The system MessageBus for dispatching side effects.

        Returns:
            A configured AGMMapper instance.
        """
        return AGMMapper(container=container, message_bus=message_bus)


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
