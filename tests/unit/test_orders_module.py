import pytest
from pydantic import ValidationError
from returns.result import Success, Failure
import asyncio
from tests.conftest import FakeUnitOfWork
from src.core.system import System
from src.core.messagebus import MessageBus
from src.core.unit_of_work import AbstractUnitOfWork
from dishka import Provider, Scope, provide
from src.modules.orders.module import OrdersModule
from src.modules.orders.messages import (
    CreateOrderCommand,
    OrderCreated,
    ShipOrderCommand,
    OrderShipped,
)
from src.modules.orders.domain import OrderState
from src.modules.orders.handlers import handle_create_order, handle_ship_order


def test_create_order_command_validation():
    with pytest.raises(ValidationError):
        # Missing total_amount
        CreateOrderCommand(order_id="123", customer_name="Test")

    with pytest.raises(ValidationError):
        # Invalid type for order_id
        CreateOrderCommand(order_id=123, customer_name="Test", total_amount=100.0)

    # Valid command
    cmd = CreateOrderCommand(order_id="123", customer_name="Test", total_amount=100.0)
    assert cmd.order_id == "123"
    assert cmd.customer_name == "Test"
    assert cmd.total_amount == 100.0


def test_events_creation():
    evt = OrderCreated(order_id="123", customer_name="Test", total_amount=100.0)
    assert evt.order_id == "123"


@pytest.mark.asyncio
async def test_order_creation_handler():
    uow = FakeUnitOfWork()
    cmd = CreateOrderCommand(
        order_id="ord-1", customer_name="Alice", total_amount=250.50
    )

    result = await handle_create_order(cmd, uow)
    assert isinstance(result, Success)
    assert result.unwrap() == "ord-1"

    # Assert Order was saved in UoW
    order = uow.repo.get("ord-1")
    assert order is not None
    assert order.customer_name == "Alice"
    assert order.status == OrderState.PENDING

    # Assert events were collected
    events = list(order.events)
    assert len(events) == 1
    assert isinstance(events[0], OrderCreated)


@pytest.mark.asyncio
async def test_order_shipping_handler():
    uow = FakeUnitOfWork()
    # Setup existing order
    cmd_create = CreateOrderCommand(
        order_id="ord-2", customer_name="Bob", total_amount=10.0
    )
    await handle_create_order(cmd_create, uow)

    # Clear initial events
    order = uow.repo.get("ord-2")
    order.events.clear()

    # Ship
    cmd_ship = ShipOrderCommand(order_id="ord-2")
    result = await handle_ship_order(cmd_ship, uow)

    assert isinstance(result, Success)
    assert order.status == OrderState.SHIPPED

    events = list(order.events)
    assert len(events) == 1
    assert isinstance(events[0], OrderShipped)


@pytest.mark.asyncio
async def test_order_cannot_be_shipped_twice():
    uow = FakeUnitOfWork()
    cmd_create = CreateOrderCommand(
        order_id="ord-3", customer_name="Charlie", total_amount=5.0
    )
    await handle_create_order(cmd_create, uow)

    cmd_ship = ShipOrderCommand(order_id="ord-3")
    await handle_ship_order(cmd_ship, uow)

    # Second ship attempt
    result = await handle_ship_order(cmd_ship, uow)
    assert isinstance(result, Failure)
    assert "already shipped" in str(result.failure())


class MockUoWProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_uow(self) -> AbstractUnitOfWork:
        return FakeUnitOfWork()


@pytest.fixture
def system():
    orders_module = OrdersModule()
    sys = System(modules=[orders_module])
    sys.providers.append(MockUoWProvider())
    sys._bootstrap()
    return sys


@pytest.mark.asyncio
async def test_orders_module_integration(system):
    """Test full dispatch through MessageBus and Composition Root."""
    async with system.container() as request_container:
        bus = await request_container.get(MessageBus)
        uow = await request_container.get(AbstractUnitOfWork)

        cmd = CreateOrderCommand(
            order_id="sys-ord-1", customer_name="Eve", total_amount=99.99
        )
        await bus.dispatch(cmd)

        await asyncio.sleep(0.01)
        bus.bus._is_running = False

        # Assert database state
        order = uow.repo.get("sys-ord-1")
        assert order is not None
        assert order.status == OrderState.PENDING
