from pydantic_settings import BaseSettings
from dishka import Provider, Scope, provide, AsyncContainer
from src.core.module import BaseModule
from src.core.messagebus import MessageBus
from src.modules.agm.mapper import AGMMapper
from src.modules.agm.messages import StoredFieldRecalculationRequested
from src.modules.agm.handlers import handle_stored_field_recalc


class AGMSettings(BaseSettings):
    """Configuration for the AGM module."""

    pass


class AGMProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_agm_mapper(
        self, container: AsyncContainer, message_bus: MessageBus
    ) -> AGMMapper:
        """
        Provides the AGMMapper, injecting the current
        AsyncContainer and MessageBus.
        """
        # Note: the AGMMapper needs the AsyncContainer to resolve Live fields.
        return AGMMapper(container=container, message_bus=message_bus)


class AGMModule(BaseModule):
    settings_class = AGMSettings

    def __init__(self):
        super().__init__()

        self.provider = AGMProvider()

        # Register command handlers (none for AGM)
        self.command_handlers = {}

        # Register event handlers for TaskIQ triggers
        self.event_handlers = {
            StoredFieldRecalculationRequested: [handle_stored_field_recalc]
        }
