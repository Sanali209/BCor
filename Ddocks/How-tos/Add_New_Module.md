# How-to: Добавление нового бизнес-модуля

Этот гид описывает шаги по созданию и регистрации нового модуля в архитектуре BCor.

## Шаг 1: Создание структуры директорий
Создайте новую папку в `src/modules/` (например, `inventory/`):
```text
src/modules/inventory/
├── __init__.py
├── domain.py      # Агрегаты и сущности
├── messages.py    # Commands и Events (DTO)
├── handlers.py    # Логика обработки сообщений
└── module.py      # Класс регистрации модуля
```

## Шаг 2: Определение сообщений (`messages.py`)
Используйте базовые классы из `src.core.messages`:
```python
from src.core.messages import Command, Event

class AddItemCommand(Command):
    sku: str
    quantity: int

class ItemAddedEvent(Event):
    sku: str
```

## Шаг 3: Реализация домена (`domain.py`)
Наследуйтесь от `Aggregate` для автоматического сбора событий:
```python
from src.core.domain import Aggregate

class InventoryItem(Aggregate):
    def add_stock(self, quantity: int):
        # Бизнес-логика...
        self.add_event(ItemAddedEvent(sku=self.sku))
```

## Шаг 4: Написание обработчиков (`handlers.py`)
Обработчики получают сообщение и `uow`:
```python
async def handle_add_item(cmd: AddItemCommand, uow: AbstractUnitOfWork):
    async with uow:
        item = await uow.inventory.get(cmd.sku)
        item.add_stock(cmd.quantity)
        await uow.commit()
```

## Шаг 5: Регистрация модуля (`module.py`)
Создайте класс, наследуемый от `BaseModule`:
```python
from src.core.module import BaseModule

class InventoryModule(BaseModule):
    command_handlers = {
        AddItemCommand: handle_add_item,
    }
    # event_handlers, provider, settings_class...
```

## Шаг 6: Подключение в System
Добавьте ваш модуль в список инициализации в точке входа вашего приложения (или в тестах):
```python
from src.core.system import System
from src.modules.inventory.module import InventoryModule

system = System(modules=[InventoryModule(), ...])
await system._bootstrap()
```

---
> [!TIP]
> Всегда начинайте разработку нового модуля с написания падающего теста в `tests/unit/` (TDD)!
