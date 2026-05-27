# Explanation: Архитектура BCor

BCor — Event-Driven Modular Monolith на Python 3.11+, реализующий принципы Чистой архитектуры (Clean Architecture), Domain-Driven Design (DDD) и CQRS.

## Слои архитектуры

```
┌──────────────────────────────────────────────────┐
│                  Entrypoints                      │
│  (CLI: main.py, PySide6 GUI, консольные утилиты) │
├──────────────────────────────────────────────────┤
│                  Application                      │
│  (Handlers, MessageBus, System, Use Cases)        │
├──────────────────────────────────────────────────┤
│                  Domain                           │
│  (Aggregate, бизнес-правила, события, порты)       │
├──────────────────────────────────────────────────┤
│               Infrastructure                      │
│  (SQLAlchemy, Neo4j AGM, TaskIQ, Playwright...)   │
└──────────────────────────────────────────────────┘
```

**Правило зависимости:** код домена НЕ импортирует код инфраструктуры. Адаптеры реализуют интерфейсы, определённые в ядре (`src/core/`) или в портах модулей.

## Как это реализовано в коде

### 1. Ядро (`src/core/`)

Ядро содержит только абстракции и механизмы:

| Файл | Назначение |
|------|-----------|
| `domain.py` | `Aggregate` — база для всех корней агрегации |
| `messages.py` | `Message` / `Command` / `Event` — базовые сообщения |
| `messagebus.py` | `MessageBus` — диспетчер с DI, retry, трассировкой |
| `unit_of_work.py` | `AbstractUnitOfWork` — UoW паттерн |
| `repository.py` | `AbstractRepository[T]` — generic репозиторий |
| `module.py` | `BaseModule` — каркас модуля |
| `system.py` | `System` — Composition Root через Dishka |
| `discovery.py` | `ModuleDiscovery` — авто-загрузка модулей из TOML |

Все эти классы НЕ импортируют SQLAlchemy, Neo4j, Redis и т.д. Они только определяют контракты.

### 2. Адаптеры (`src/adapters/`)

Здесь — конкретные реализации:

- `SqlAlchemyRepository` & `SqlAlchemyUnitOfWork` — реализация паттерна Repository/UoW через SQLAlchemy.
- `JsonRepository` — файловое хранилище для простых данных.
- `PlaywrightAdapter` / `BS4Extractor` / `ScraperEngine` — веб-скрапинг.
- `MotorMongoAdapter` — MongoDB без ORM.
- `taskiq_broker.py` / `LocalMonitorMiddleware` — TaskIQ + NATS.

### 3. Бизнес-модули (`src/modules/`)

Каждый модуль — независимая bounded context:

- **orders** — эталонный CQRS: Order Aggregate, CreateOrder/ShipOrder команды.
- **assets** — самый развитый модуль: 10+ Asset-моделей, 12 обработчиков (CLIP, BLIP, OCR, PHash, Ollama, Thumbnail...), интеграция с AGM.
- **ecs** — Entity Component System (игровой движок).
- **agm** — Graph-Object Mapper для Neo4j.
- **analytics** — TaskIQ-задачи для аналитики.
- **llm** — Gemini adapter, NLP pipeline.
- **vfs** — PyFilesystem2 интеграция.
- **files** — Pydantic модели файлов.

### 4. Точки входа (`src/apps/`)

Приложения, которые компонуют модули через `app.toml`:

- **hello_app** — демонстрационный CLI.
- **asset_explorer** — PySide6 GUI с FlowLayout, TagCloud, SearchConstructor, TaskMonitor.
- **boruscraper** — GUI-скрапинг с портированием из legacy.
- **VFSSample** — пример виртуальной файловой системы.

## DDD и CQRS на примере модуля orders

**Команда** (Command) — императив: `CreateOrderCommand(customer_name, total_amount)`.

**Хендлер** проверяет бизнес-правила, создаёт `Order Aggregate`, добавляет событие:

```python
async def handle_create_order(cmd, uow):
    with uow:
        existing = uow.repo.get(cmd.order_id)
        if existing:
            return failure("Already exists")
        order = Order(ref=cmd.order_id, customer_name=cmd.customer_name, total_amount=cmd.total_amount)
        uow.repo.add(order)
        uow.commit()              # → собирает OrderCreated события
    return success(order.ref)
```

**Unit of Work** (SqlAlchemyUnitOfWork) собирает все события из репозиториев:

```python
for aggregate in uow.seen_aggregates:
    yield aggregate.events.pop(0)
```

**MessageBus** берёт эти события и публикует:

```python
for event in uow.collect_new_events():
    await bus.dispatch(event)     # → on_order_created, on_order_shipped
```

## Почему Modular Monolith, а не микросервисы?

1. **Единый DI-контейнер**: Dishka управляет всеми зависимостями в одном процессе.
2. **Атомарные транзакции**: UoW гарантирует консистентность между модулями в одной БД.
3. **Event Bus для слабой связанности**: модули общаются через события, а не прямые вызовы.
4. **Портирование при необходимости**: `LegacyAllocatorBridge` и `BaseGuiAdapter` позволяют вырезать модуль в микросервис, не меняя код.

## Composition Root через System

`System.from_manifest("app.toml")` — это Composition Root: единственное место в приложении, где все модули собираются вместе.

```python
system = System.from_manifest("app.toml")
await system.start()

async with system.container() as container:
    bus = await container.get(MessageBus)
    await bus.dispatch(SomeCommand(...))

await system.stop()
```

**Что происходит внутри:**
1. Загружается `app.toml`.
2. `ModuleDiscovery` импортирует перечисленные модули.
3. Для каждого модуля: `module.setup()`, сбор handler'ов и провайдеров.
4. Создаётся `CoreProvider`, который регистрирует MessageBus и UoW.
5. Dishka `make_async_container()` создаёт DI.
6. `module.startup()` — финальная инициализация.

## Тестирование архитектуры

Тесты разделены по слоям:

- **Unit** (`tests/unit/`): тестируют Aggregate напрямую, без инфраструктуры.
- **Integration** (`tests/integration/`): используют `BCorTestSystem` + FakeUoW/реальные адаптеры.
- **E2E** (`tests/e2e/`): полный стек с GUI и внешними сервисами.

Это гарантирует, что доменная логика тестируется изолированно, а инфраструктурные баги отлавливаются на уровне интеграции.
