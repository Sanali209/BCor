import loguru
from pydantic_settings import BaseSettings

from src.core.module import BaseModule
from src.modules.orders.handlers import handle_create_order, handle_ship_order
from src.modules.orders.messages import (
    CreateOrderCommand,
    OrderCreated,
    OrderShipped,
    ShipOrderCommand,
)


class OrdersSettings(BaseSettings):
    """Configuration settings for the Orders module.

    Can be populated from environment variables or TOML config.
    """

    pass


class OrdersModule(BaseModule):
    """Domain module for handling customer orders.

    Registers command and event handlers related to order lifecycle
    management, including creation and shipping.
    """

    settings_class = OrdersSettings

    def __init__(self):
        """Initializes the Orders module and registers routing maps."""
        super().__init__()

        # Register command handlers
        self.command_handlers = {
            CreateOrderCommand: handle_create_order,
            ShipOrderCommand: handle_ship_order,
        }

        # Register event handlers
        self.event_handlers = {
            OrderCreated: [self.on_order_created],
            OrderShipped: [self.on_order_shipped],
        }

    async def on_order_created(self, event: OrderCreated, uow=None):
        """Subscriber for OrderCreated events.

        Currently logs the event for audit/demonstration purposes.
        """
        loguru.logger.info(f"Integration Event Received: OrderCreated for {event.order_id} ({event.total_amount}$)")

    async def on_order_shipped(self, event: OrderShipped, uow=None):
        """Subscriber for OrderShipped events.

        Currently logs the event for audit/demonstration purposes.
        """
        loguru.logger.info(f"Integration Event Received: OrderShipped for {event.order_id}")
