from src.core.messages import Command, Event


class CreateOrderCommand(Command):
    """Command to create a new order in the system."""

    order_id: str
    customer_name: str
    total_amount: float


class ShipOrderCommand(Command):
    """Command to trigger the shipping process for an existing order."""

    order_id: str


class OrderCreated(Event):
    """Event emitted when a new order has been successfully created."""

    order_id: str
    customer_name: str
    total_amount: float


class OrderShipped(Event):
    """Event emitted when an order's status has transitioned to SHIPPED."""

    order_id: str
