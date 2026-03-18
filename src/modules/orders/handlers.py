from src.core.monads import BusinessResult, success, failure
from src.core.unit_of_work import AbstractUnitOfWork
from src.modules.orders.messages import CreateOrderCommand, ShipOrderCommand
from src.modules.orders.domain import Order, DomainError


async def handle_create_order(
    cmd: CreateOrderCommand, uow: AbstractUnitOfWork
) -> BusinessResult:
    """Handles the creation of a new order.

    This handler manages the atomicity of order creation, ensuring that
    duplicate IDs are rejected and the initial state is persisted.

    Args:
        cmd: The command containing order details.
        uow: The active Unit of Work for database interaction.

    Returns:
        A BusinessResult containing the order reference on success, 
        or a failure message if a conflict occurs.
    """
    with uow:
        # Check if already exists? (Simulated constraint)
        existing = uow.repo.get(cmd.order_id)
        if existing:
            return failure(f"Order with id {cmd.order_id} already exists.")

        order = Order(
            ref=cmd.order_id,
            customer_name=cmd.customer_name,
            total_amount=cmd.total_amount,
        )
        uow.repo.add(order)
        uow.commit()

    return success(order.ref)


async def handle_ship_order(
    cmd: ShipOrderCommand, uow: AbstractUnitOfWork
) -> BusinessResult:
    """Handles order shipping transitions.

    Retrieves the order, transitions its state via domain methods, 
    and commits the changes.

    Args:
        cmd: The command containing the order ID to ship.
        uow: The active Unit of Work for database interaction.

    Returns:
        A BusinessResult containing the order reference on success,
        or a failure message if the order is not found or invalid.
    """
    with uow:
        order = uow.repo.get(cmd.order_id)
        if not order:
            return failure(f"Order with id {cmd.order_id} not found.")

        try:
            order.ship()
            uow.commit()  # UnitOfWork will collect OrderShipped event
        except DomainError as e:
            return failure(str(e))

    return success(order.ref)
