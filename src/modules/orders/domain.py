from enum import Enum

from src.core.domain import Aggregate
from src.modules.orders.messages import OrderCreated, OrderShipped


class OrderState(Enum):
    """Enumerate representing the possible states of an Order."""

    PENDING = "PENDING"
    SHIPPED = "SHIPPED"


class DomainError(Exception):
    """Base exception for domain logic errors in the Orders module."""

    pass


class Order(Aggregate):
    """Order Aggregate Root.

    Represents a customer order within the system. Handles the business
    logic for state transitions and emits domain events.

    Attributes:
        ref: Unique reference string for the order.
        customer_name: Name of the customer who placed the order.
        total_amount: Total monetary value of the order.
        status: Current status of the order (PENDING, SHIPPED).
    """

    def __init__(self, ref: str, customer_name: str, total_amount: float):
        """Initializes a new Order and emits an OrderCreated event.

        Args:
            ref: Unique order identifier.
            customer_name: Customer's full name.
            total_amount: Order total amount.
        """
        super().__init__()
        self.ref = ref
        self.customer_name = customer_name
        self.total_amount = total_amount
        self.status = OrderState.PENDING

        self.add_event(
            OrderCreated(
                order_id=self.ref,
                customer_name=self.customer_name,
                total_amount=self.total_amount,
            )
        )

    def ship(self) -> None:
        """Transitions the order to SHIPPED and emits an OrderShipped event.

        Raises:
            DomainError: If the order is already shipped.
        """
        if self.status == OrderState.SHIPPED:
            raise DomainError(f"Order {self.ref} is already shipped.")

        self.status = OrderState.SHIPPED
        self.add_event(OrderShipped(order_id=self.ref))
