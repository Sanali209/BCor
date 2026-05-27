# How-to: Писать тесты в BCor

BCor использует три уровня тестов: unit, integration, e2e. Тесты лежат в `tests/unit/`, `tests/integration/`, `tests/e2e/`.

## 1. Ссылка на базовые фикстуры

Файл `tests/conftest.py` содержит глобальные фикстуры. Всегда используйте `pytest` с `PYTHONPATH=.`:

```bash
PYTHONPATH=. uv run pytest tests/unit/
```

## 2. Unit-тесты: доменная логика без инфраструктуры

Тестируйте `Aggregate` напрямую — это чистый Python, без БД, без UoW.

```python
# tests/unit/test_orders_module.py
from src.modules.orders.domain import Order, DomainError

def test_create_order():
    order = Order(ref="ORD-001", customer_name="Alice", total_amount=100.0)
    assert order.ref == "ORD-001"
    assert order.status.value == "PENDING"
    assert len(order.events) == 1  # OrderCreated

def test_ship_order():
    order = Order(ref="ORD-001", customer_name="Alice", total_amount=100.0)
    order.ship()
    assert order.status.value == "SHIPPED"
    assert len(order.events) == 2  # OrderCreated + OrderShipped

def test_cannot_ship_twice():
    order = Order(ref="ORD-001", customer_name="Alice", total_amount=100.0)
    order.ship()
    with pytest.raises(DomainError, match="already shipped"):
        order.ship()
```

## 3. Unit-тесты с FakeUoW

Хендлеры используют UoW. Подставьте `FakeUnitOfWork` с `FakeRepository`:

```python
# tests/unit/test_orders_handlers.py
import pytest
from src.core.unit_of_work import AbstractUnitOfWork
from src.core.repository import AbstractRepository
from src.modules.orders.domain import Order
from src.modules.orders.messages import CreateOrderCommand, ShipOrderCommand
from src.modules.orders.handlers import handle_create_order, handle_ship_order

class FakeRepository(AbstractRepository[Order]):
    def __init__(self):
        super().__init__()
        self._store: dict[str, Order] = {}

    def _add(self, aggregate: Order) -> None:
        self._store[aggregate.ref] = aggregate

    def _get(self, reference: str) -> Order | None:
        return self._store.get(reference)

class FakeUnitOfWork(AbstractUnitOfWork):
    def __init__(self):
        self.repo = FakeRepository()
        self.committed = False

    def _commit(self):
        self.committed = True

    def rollback(self):
        pass

@pytest.mark.asyncio
async def test_create_order_handler():
    uow = FakeUnitOfWork()
    result = await handle_create_order(
        CreateOrderCommand(order_id="ORD-001", customer_name="Bob", total_amount=50.0),
        uow
    )
    assert result.is_success()
    assert uow.committed
    assert uow.repo.get("ORD-001") is not None

@pytest.mark.asyncio
async def test_ship_order_handler():
    uow = FakeUnitOfWork()
    await handle_create_order(CreateOrderCommand(order_id="ORD-001", customer_name="Bob", total_amount=50.0), uow)
    result = await handle_ship_order(ShipOrderCommand(order_id="ORD-001"), uow)
    assert result.is_success()
    assert uow.repo.get("ORD-001").status.value == "SHIPPED"
```

**Правила:**
- FakeUoW наследует `AbstractUnitOfWork` и заменяет `_commit()` / `rollback()`.
- FakeRepository наследует `AbstractRepository[T]` и хранит данные в dict.
- Все хендлеры асинхронные → маркируем тест `@pytest.mark.asyncio`.

## 4. Integration-тесты с BCorTestSystem

Для тестирования полного цикла (загрузка модулей, MessageBus, DI) используйте `BCorTestSystem`:

```python
# tests/integration/test_my_module.py
import pytest
from src.core.testing import BCorTestSystem

@pytest.mark.asyncio
async def test_full_flow():
    manifest = "src/apps/hello_app/app.toml"
    async with BCorTestSystem(manifest).run() as system:
        async with system.container() as container:
            from src.core.messagebus import MessageBus
            bus = await container.get(MessageBus)
            from src.apps.hello_app.modules.greeting.messages import SayHelloCommand

            result = await bus.dispatch(SayHelloCommand(name="Integration"))
            assert result is not None
```

`BCorTestSystem`:
- Загружает манифест через `System.from_manifest()`.
- Вызывает `system.start()` и `system.stop()`.
- Дренирует event loop на Windows (предотвращает зависания).
- Отменяет незавершённые таски.

## 5. E2E-тесты

E2E тесты в `tests/e2e/` проверяют GUI и интеграцию реальных сервисов:

```python
# tests/e2e/test_ui_flow.py
# Предполагают запущенный Neo4j, NATS, TaskIQ worker
```

Запускаются опционально: `pytest tests/e2e/ -v`.

## 6. Тестирование AGM-моделей

Для моделей, использующих AGM-аннотации (@Stored, @Rel, @Live), тестируйте чистую загрузку через mapper:

```python
# tests/unit/test_agm_mapper.py
import pytest
from src.modules.agm.metadata import Stored, Live, Rel

def test_stored_metadata():
    stored = Stored(source_field="uri", handler="CLIP", use_taskiq=True)
    assert stored.handler == "CLIP"
    assert stored.effective_source_fields() == ["uri"]

def test_stored_requires_source():
    with pytest.raises(ValueError):
        Stored()  # no source_field or source_fields
```

## 7. Полезные фикстуры из conftest.py

```python
# pytest автоматически подхватывает из tests/conftest.py
# Windows loop manager, TaskIQ InMemoryBroker и т.д.
```

---

**Итог:** 
- Unit: тестируйте Aggregate напрямую.
- Unit с обработчиками: FakeUoW + FakeRepository.
- Integration: `BCorTestSystem`.
- E2E: полный стек с реальными сервисами.
