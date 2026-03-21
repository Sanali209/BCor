# Руководство разработчика BCor

## Начало работы

### Предварительные требования
- Python 3.12+
- Менеджер пакетов `uv`
- Docker (опционально, для баз данных)

### Установка
```bash
# Клонировать репозиторий
git clone https://github.com/Sanali209/BCor.git
cd BCor

# Создать виртуальное окружение
uv venv

# Установить зависимости
uv pip install -e ".[dev]"

# Установить pre-commit хуки (опционально)
pre-commit install
```

### Запуск приложения
```bash
# Запустить приложение по умолчанию
uv run python -m src.apps.hello_app.main

# Запустить с конкретным app.toml
uv run python -m src.apps.ImageAnalyze.main

# Запустить тесты
uv run pytest

# Запустить с покрытием
uv run pytest --cov=src --cov-report=html
```

## Структура проекта

```
BCor/
├── src/
│   ├── core/              # Основные компоненты фреймворка
│   ├── modules/           # Бизнес-модули
│   ├── apps/              # Точки входа приложений
│   ├── adapters/          # Адаптеры инфраструктуры
│   └── common/            # Общие утилиты
├── tests/
│   ├── unit/              # Модульные тесты
│   ├── integration/       # Интеграционные тесты
│   └── conftest.py        # Фикстуры тестов
├── Ddocks/                # Документация
├── pyproject.toml         # Конфигурация проекта
└── uv.lock               # Файл блокировки зависимостей
```

## Создание нового модуля

### 1. Структура модуля
Создайте структуру директорий:
```
src/modules/your_module/
├── __init__.py
├── module.py
├── messages.py
├── handlers.py
├── provider.py
├── domain/
│   ├── __init__.py
│   └── models.py
└── adapters/
    ├── __init__.py
    └── repository.py
```

### 2. Определение сообщений (`messages.py`)
```python
from src.core.messages import Command, Event

class CreateItemCommand(Command):
    name: str
    description: str

class ItemCreatedEvent(Event):
    item_id: str
    name: str
```

### 3. Создание доменной модели (`domain/models.py`)
```python
from src.core.domain import Aggregate

class Item(Aggregate):
    def __init__(self, item_id: str, name: str, description: str):
        super().__init__()
        self.item_id = item_id
        self.name = name
        self.description = description
    
    def create(self):
        self.add_event(ItemCreatedEvent(
            item_id=self.item_id,
            name=self.name
        ))
```

### 4. Реализация обработчиков (`handlers.py`)
```python
from src.core.unit_of_work import AbstractUnitOfWork
from .messages import CreateItemCommand, ItemCreatedEvent

async def handle_create_item(
    cmd: CreateItemCommand,
    uow: AbstractUnitOfWork,
    event_bus
):
    async with uow:
        item = Item(
            item_id=generate_id(),
            name=cmd.name,
            description=cmd.description
        )
        item.create()
        await uow.items.add(item)
        await uow.commit()
```

### 5. Регистрация модуля (`module.py`)
```python
from src.core.module import BaseModule
from .provider import YourProvider
from .messages import CreateItemCommand
from .handlers import handle_create_item

class YourModule(BaseModule):
    def __init__(self):
        super().__init__()
        self.provider = YourProvider()
        self.command_handlers = {
            CreateItemCommand: handle_create_item,
        }
```

### 6. Создание провайдера (`provider.py`)
```python
from dishka import Provider, Scope
from .adapters.repository import YourRepository

class YourProvider(Provider):
    def __init__(self):
        super().__init__()
        self.provide(YourRepository, scope=Scope.REQUEST)
```

## Тестирование

### Модульные тесты
```python
# tests/unit/test_your_module.py
import pytest
from src.modules.your_module.messages import CreateItemCommand
from src.modules.your_module.handlers import handle_create_item

@pytest.mark.asyncio
async def test_create_item(fake_uow, fake_event_bus):
    cmd = CreateItemCommand(name="Test", description="Test item")
    await handle_create_item(cmd, fake_uow, fake_event_bus)
    
    # Проверить, что события были опубликованы
    assert len(fake_event_bus.published_events) == 1
```

### Интеграционные тесты
```python
# tests/integration/test_your_repository.py
import pytest
from src.modules.your_module.adapters.repository import YourRepository

@pytest.mark.asyncio
async def test_repository_save(db_session):
    repo = YourRepository(db_session)
    item = Item(item_id="123", name="Test", description="Test")
    
    await repo.add(item)
    saved = await repo.get("123")
    
    assert saved.name == "Test"
```

## Конфигурация

### Манифест приложения (`app.toml`)
```toml
[modules]
enabled = ["your_module", "analytics"]

[your_module]
setting1 = "value1"
setting2 = 42

[settings]
database_url = "sqlite+aiosqlite:///./test.db"
```

### Переменные окружения
Создайте файл `.env`:
```env
DATABASE_URL=sqlite+aiosqlite:///./app.db
LOG_LEVEL=INFO
NATS_URL=nats://localhost:4222
```

## Общие паттерны

### Использование UnitOfWork
```python
async with uow:
    # Получить репозиторий
    repo = uow.items
    
    # Загрузить агрегат
    item = await repo.get(item_id)
    
    # Изменить агрегат
    item.update_name("New Name")
    
    # Зафиксировать изменения (события автоматически публикуются)
    await uow.commit()
```

### Публикация событий
```python
# Из обработчика
await event_bus.publish(ItemCreatedEvent(item_id="123"))

# Из агрегата (через UnitOfWork)
self.add_event(ItemCreatedEvent(item_id="123"))
```

### Фоновые задачи
```python
from src.adapters.taskiq_broker import broker

@broker.task
async def heavy_computation(data: dict):
    # Долгая задача
    result = await process_data(data)
    return result

# Вызов из обработчика
await heavy_computation.kiq(data)
```

## Отладка

### Включение отладочного логирования
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Просмотр потока событий
```python
# Добавить в messagebus.py для отладки
logger.debug(f"Dispatching: {message.__class__.__name__}")
```

### Запросы к базе данных
```python
# Включить SQL echo
engine = create_engine(url, echo=True)
```

## Лучшие практики

### Стиль кода
- Следуйте PEP 8
- Используйте аннотации типов повсюду
- Держите функции маленькими (< 20 строк)
- Пишите docstrings для публичных API

### Тестирование
- Пишите тесты первыми (TDD)
- Используйте фикстуры для общей настройки
- Мокируйте внешние зависимости
- Тестируйте граничные случаи и ошибки

### Производительность
- Используйте async/await для I/O
- Пакетные операции с базой данных
- Кэшируйте часто запрашиваемые данные
- Профилируйте с `cProfile`

### Безопасность
- Валидируйте все входные данные
- Используйте параметризованные запросы
- Реализуйте proper аутентификацию
- Логируйте события безопасности

## Устранение неполадок

### Распространенные проблемы

**Ошибки импорта**
```bash
# Убедитесь, что src в Python path
export PYTHONPATH="${PYTHONPATH}:./src"
```

**Подключение к базе данных**
```bash
# Проверить, что база данных запущена
docker ps | grep postgres

# Проверить строку подключения
echo $DATABASE_URL
```

**Событие не обрабатывается**
```python
# Проверить регистрацию обработчика
print(bus._command_handlers)
print(bus._event_handlers)
```

## Участие в разработке

1. Форкнуть репозиторий
2. Создать ветку функциональности
3. Написать тесты первыми
4. Реализовать функциональность
5. Запустить линтеры: `uv run ruff check .`
6. Запустить тесты: `uv run pytest`
7. Отправить pull request

## Ресурсы

### Основная документация
- [README.md](README.md) — Обзор проекта и стек технологий
- [ARCHITECTURE.md](ARCHITECTURE.md) — Полная документация архитектуры
- [ARCHITECTURE_ru.md](ARCHITECTURE_ru.md) — Документация архитектуры на русском

### Концептуальная документация (Ddocks/)
- [Roadmap](Ddocks/Roadmap.md) — Статус разработки и план TDD
- [Concept Document](Ddocks/Conceptdock.md) — Архитектурное видение
- [Design Document](Ddocks/Dizdok.md) — Дизайн ядра и структура монорепозитория
- [Specification](Ddocks/Specification.md) — Детальная спецификация ядра
- [Technical Task](Ddocks/Tech%20tasck.md) — Техническое задание на разработку

### Документация модулей
- [Orders Module](Ddocks/orders_dock.md) — Эталонный бизнес-модуль
- [AGM Module](Ddocks/agm_dock.md) — Детали графового маппера
- [ECS Module](Ddocks/ecs_dock.md) — Entity Component System
- [VFS Module](Ddocks/vfs_dock.md) — Virtual File System
- [Analytics Module](src/modules/analytics/README.md) — Аналитика и фоновые задачи
- [LLM Module](src/modules/llm/README.md) — LLM и NLP обработка
- [Search Module](src/modules/search/README.md) — Веб и поиск изображений

### Руководства
- [How-to: Add New Module](Ddocks/How-tos/Add_New_Module.md) — Руководство по созданию модулей
- [First Steps](firststeps.md) — Начало работы с BCor

### Документация кода
- [src/core/](src/core/) — Реализация фреймворка
- [src/modules/](src/modules/) — Бизнес-модули
- [src/apps/](src/apps/README.md) — Точки входа приложений
- [src/common/](src/common/README.md) — Общие утилиты