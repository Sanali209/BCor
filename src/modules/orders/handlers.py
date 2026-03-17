from src.core.monads import BusinessResult, success, failure
from src.core.unit_of_work import AbstractUnitOfWork
from src.modules.orders.messages import CreateOrderCommand, ShipOrderCommand
from src.modules.orders.domain import Order, DomainError


async def handle_create_order(
    cmd: CreateOrderCommand, uow: AbstractUnitOfWork
) -> BusinessResult:
    """Creates a new Order aggregate and saves it."""
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
    """Updates an order's status to SHIPPED."""
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
