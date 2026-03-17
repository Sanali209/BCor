from enum import Enum
from src.core.domain import Aggregate
from src.modules.orders.messages import OrderCreated, OrderShipped


class OrderState(Enum):
    PENDING = "PENDING"
    SHIPPED = "SHIPPED"


class DomainError(Exception):
    pass


class Order(Aggregate):
    def __init__(self, ref: str, customer_name: str, total_amount: float):
        super().__init__()
        self.ref = ref
        self.customer_name = customer_name
        self.total_amount = total_amount
        self.status = OrderState.PENDING

        # When creating a new Order, emit the OrderCreated domain event
        self.add_event(
            OrderCreated(
                order_id=self.ref,
                customer_name=self.customer_name,
                total_amount=self.total_amount,
            )
        )

    def ship(self) -> None:
        """Transitions the order to SHIPPED and emits an event."""
        if self.status == OrderState.SHIPPED:
            raise DomainError(f"Order {self.ref} is already shipped.")

        self.status = OrderState.SHIPPED
        self.add_event(OrderShipped(order_id=self.ref))
