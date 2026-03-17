from pydantic_settings import BaseSettings
from src.core.module import BaseModule
from src.modules.orders.messages import (
    CreateOrderCommand,
    OrderCreated,
    ShipOrderCommand,
    OrderShipped,
)
from src.modules.orders.handlers import handle_create_order, handle_ship_order

import loguru


class OrdersSettings(BaseSettings):
    """Configuration for the Orders module if needed."""

    pass


class OrdersModule(BaseModule):
    settings_class = OrdersSettings

    def __init__(self):
        super().__init__()

        # Register command handlers
        self.command_handlers = {
            CreateOrderCommand: handle_create_order,
            ShipOrderCommand: handle_ship_order,
        }

        # Register event handlers
        # Currently we just log them to show they are published correctly
        self.event_handlers = {
            OrderCreated: [self.on_order_created],
            OrderShipped: [self.on_order_shipped],
        }

    async def on_order_created(self, event: OrderCreated, uow=None):
        loguru.logger.info(
            f"Integration Event Received: OrderCreated for {event.order_id} ({event.total_amount}$)"
        )

    async def on_order_shipped(self, event: OrderShipped, uow=None):
        loguru.logger.info(
            f"Integration Event Received: OrderShipped for {event.order_id}"
        )
