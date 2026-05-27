# How-to: Создать новый бизнес-модуль с CQRS

Эта инструкция описывает, как добавить новый бизнес-модуль в BCor, используя паттерны CQRS и Event-Driven архитектуру.

## 1. Определите сообщения

В файле `messages.py` опишите команды (намерения) и события (факты).

```python
# src/modules/inventory/messages.py
from src.core.messages import Command, Event

class AddStockCommand(Command):
    product_id: str
    quantity: int
    warehouse: str

class ReserveStockCommand(Command):
    product_id: str
    quantity: int

class StockAdded(Event):
    product_id: str
    quantity: int
    warehouse: str

class StockReserved(Event):
    product_id: str
    quantity: int
```

**Правила:**
- Команда именуется в повелительном наклонении (глагол + существительное) — `AddStock`, `ReserveStock`.
- Событие именуется в прошедшем времени — `StockAdded`, `StockReserved`.
- Команда всегда маршрутизируется **одному** хендлеру.
- Событие может быть обработано **многими** хендлерами.

## 2. Реализуйте доменную модель

В `domain.py` создаёте `Aggregate` — корень агрегации с бизнес-правилами.

```python
# src/modules/inventory/domain.py
from src.core.domain import Aggregate
from src.modules.inventory.messages import StockAdded, StockReserved

class InsufficientStockError(Exception):
    pass

class InventoryItem(Aggregate):
    def __init__(self, product_id: str, warehouse: str):
        super().__init__()
        self.ref = product_id
        self.warehouse = warehouse
        self.quantity = 0

    def add_stock(self, quantity: int) -> None:
        self.quantity += quantity
        self.add_event(StockAdded(
            product_id=self.ref,
            quantity=quantity,
            warehouse=self.warehouse,
        ))

    def reserve(self, quantity: int) -> None:
        if self.quantity < quantity:
            raise InsufficientStockError(
                f"Need {quantity}, have {self.quantity}"
            )
        self.quantity -= quantity
        self.add_event(StockReserved(
            product_id=self.ref,
            quantity=quantity,
        ))
```

Ключевой момент: `add_event()` добавляет событие в список `self.events`. После коммита UoW соберёт их и опубликует через MessageBus.

## 3. Напишите обработчики

В `handlers.py` — функции, принимающие (command/event, uow).

```python
# src/modules/inventory/handlers.py
from src.common.monads import BusinessResult, success, failure
from src.modules.inventory.domain import InventoryItem, InsufficientStockError
from src.modules.inventory.messages import (
    AddStockCommand, ReserveStockCommand, StockAdded,
)

async def handle_add_stock(cmd: AddStockCommand, uow) -> BusinessResult:
    with uow:
        item = uow.repo.get(cmd.product_id) or InventoryItem(
            product_id=cmd.product_id,
            warehouse=cmd.warehouse,
        )
        item.add_stock(cmd.quantity)
        uow.repo.add(item)
        uow.commit()
    return success(item.ref)

async def handle_reserve_stock(cmd: ReserveStockCommand, uow) -> BusinessResult:
    with uow:
        item = uow.repo.get(cmd.product_id)
        if not item:
            return failure(f"Product {cmd.product_id} not found")
        try:
            item.reserve(cmd.quantity)
            uow.commit()
        except InsufficientStockError as e:
            return failure(str(e))
    return success(item.ref)

async def on_stock_added(event: StockAdded, uow):
    # Интеграционный слушатель — например, обновление поискового индекса
    print(f"Stock updated: {event.product_id} += {event.quantity}")
```

Обратите внимание на:
- `uow.repo` — автоматически предоставляется `SqlAlchemyUnitOfWork` (или FakeUoW в тестах).
- `BusinessResult` — монада из `returns` (алиас в `src.common.monads`).
- Команды возвращают `success(...)` или `failure(...)`.

## 4. Соберите модуль

```python
# src/modules/inventory/module.py
from pydantic_settings import BaseSettings
from src.core.module import BaseModule
from src.modules.inventory.handlers import (
    handle_add_stock, handle_reserve_stock, on_stock_added,
)
from src.modules.inventory.messages import (
    AddStockCommand, ReserveStockCommand, StockAdded,
)

class InventorySettings(BaseSettings):
    default_warehouse: str = "main"
    max_reserve_percent: float = 0.9

class InventoryModule(BaseModule):
    settings_class = InventorySettings

    def __init__(self):
        super().__init__()
        self.command_handlers = {
            AddStockCommand: handle_add_stock,
            ReserveStockCommand: handle_reserve_stock,
        }
        self.event_handlers = {
            StockAdded: [on_stock_added],
        }
```

## 5. Подключите в манифесте

В `app.toml` вашего приложения добавьте модуль в список `enabled`:

```toml
[modules]
paths = ["src.modules"]
enabled = ["inventory"]

[inventory]
default_warehouse = "Riga"
```

## 6. Проверьте в тесте

Создайте `tests/unit/test_inventory_module.py`:

```python
import pytest
from src.modules.inventory.domain import InventoryItem

def test_inventory_item_adds_stock():
    item = InventoryItem(product_id="P001", warehouse="main")
    item.add_stock(10)
    assert item.quantity == 10
    assert len(item.events) == 1

def test_inventory_item_reserves():
    item = InventoryItem(product_id="P001", warehouse="main")
    item.add_stock(10)
    item.reserve(3)
    assert item.quantity == 7
    assert len(item.events) == 2
```

---

**Итог:** новый бизнес-модуль = messages.py + domain.py + handlers.py + module.py. Без лишнего кода: только команды, события, доменная логика и регистрация.
