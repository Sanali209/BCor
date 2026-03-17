from src.core.messages import Command, Event


class CreateOrderCommand(Command):
    order_id: str
    customer_name: str
    total_amount: float


class ShipOrderCommand(Command):
    order_id: str


class OrderCreated(Event):
    order_id: str
    customer_name: str
    total_amount: float


class OrderShipped(Event):
    order_id: str
