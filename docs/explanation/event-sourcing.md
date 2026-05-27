# Explanation: Event Bus и MessageBus

BCor использует двухуровневую систему обмена сообщениями: **bubus** (лёгкий asyncio Event Bus) и **MessageBus** (обёртка с DI, retry и трассировкой).

## Зачем два уровня?

```
┌────────────────────────────────────────────┐
│  MessageBus (src.core.messagebus)          │
│  ┌──────────────────────────────────────┐  │
│  │  Bubus EventBus (bubus.service)      │  │
│  │  - dispatch(message)                 │  │
│  │  - on(type, handler)                 │  │
│  └──────────────────────────────────────┘  │
│  - DI-инжекция параметров                   │
│  - Tenacity retry (экспоненциальный)        │
│  - OpenTelemetry spans                      │
│  - Сбор и публикация вложенных событий      │
│  - Детектор зацикливаний (trace_stack)      │
│  - Изоляция ошибок в event handlers         │
└────────────────────────────────────────────┘
```

**Bubus** — минимальный asyncio Event Bus от сторонней библиотеки. Предоставляет:
- Регистрацию хендлеров `on(type, handler)`.
- Диспетчеризацию `dispatch(message)`.
- Гарантию вызова всех подписчиков.

**MessageBus** — надстройка BCor, которая добавляет всё, что нужно production-системе.

## Паттерн Pub-Sub: Command vs Event

BCor строго разделяет два типа сообщений через наследование:

```python
class Command(Message):  # 1-to-1
    ...

class Event(Message):    # 1-to-N
    ...
```

| Характеристика | Command | Event |
|---------------|---------|-------|
| Название | Глагол в повелительном (CreateOrder) | Причастие прошедшего времени (OrderCreated) |
| Маршрутизация | Один хендлер | Много хендлеров |
| Retry | Да (exponential backoff, 3 попытки) | Нет (изоляция ошибок, не крашат bus) |
| Результат | Возвращает BusinessResult | None (fire-and-forget) |
| Семантика | "Сделай это" | "Это произошло" |

## Диспетчеризация и сбор событий

```python
async def dispatch(self, message: Message) -> Message:
    # 1. Отправить в bubus (выполнить хендлеры)
    await self.bus.dispatch(message)

    # 2. Собрать новые события из UoW
    await self._publish_collected_events(message)

    # 3. Проверить результаты (поднять ошибки команд)
    await message.event_result(raise_if_any=True, raise_if_none=False)

    return message
```

Цепочка вызовов:

```
handle_create_order() → order.add_event(OrderCreated)
                      → uow.commit()           # события пока в aggregate.events
                      → MessageBus._publish_collected_events()
                      → bus.dispatch(OrderCreated)
                      → on_order_created()
                      → on_inventory_update()
                      → bus.dispatch(StockReserved)  # если хендлер породил новые события
```

## Детектор зацикливаний (Causal Tracing)

Каждое сообщение несёт `trace_stack` — список имён типов, через которые прошёл запрос.

```python
# В _publish_collected_events:
new_trace = parent_message.trace_stack.copy()
new_trace.append(type(parent_message).__name__)

if len(new_trace) > self.max_trace_depth:  # default: 20
    raise RuntimeError(f"Infinite loop detected: {new_trace}")
```

Если глубина превышает `max_trace_depth` (по умолчанию 20), выбрасывается `RuntimeError`. Это предотвращает бесконечные циклы вида:

```
OrderCreated → on_order_created → emit OrderCreated → ...
```

## DI-инжекция в хендлеры

Хендлеры не вызываются напрямую — MessageBus анализирует сигнатуру через `inspect.signature()`:

```python
async def handle_ship_order(cmd: ShipOrderCommand, uow: AbstractUnitOfWork) -> BusinessResult:
    # cmd — первый параметр (сообщение)
    # uow — второй параметр, инжектится из bus.uow
    ...
```

Правила:
1. Первый параметр — сообщение (Command или Event).
2. Если параметр называется `uow` — подставляется `self.uow`.
3. Все остальные параметры разрешаются из Dishka-контейнера по type hint.
4. Если разрешение не удалось — логируется debug, параметр пропускается.

Поддерживаются sync и async хендлеры. Sync-функции выполняются через `asyncio.to_thread()`.

## Изоляция ошибок в Event-хендлерах

```python
# event_wrapper
try:
    await handler(event, **kwargs)
    await self._publish_collected_events(event)
except Exception as e:
    logger.exception(f"Isolated failure in {handler.__name__}: {e}")
    if isinstance(e, RuntimeError) and "Infinite loop detected" in str(e):
        raise  # loop detection — критично, перевыбрасываем
```

Ошибка в одном подписчике не блокирует остальных. Исключение логируется, но bus продолжает работу.

## Bubus-патч

BCor отключает встроенный 2-уровневый детектор циклов bubus, чтобы использовать собственный depth-based детектор:

```python
def _patch_bubus() -> None:
    if hasattr(bubus.service.EventBus, "_would_create_loop"):
        bubus.service.EventBus._would_create_loop = lambda self, event, handler: False

_patch_bubus()  # вызывается при импорте messagebus.py
```

## Сравнение с другими подходами

| Паттерн | Реализация в BCor |
|---------|-------------------|
| Mediator | MessageBus.dispatch() — центральная точка |
| Pub-Sub | register_event() / dispatch() |
| Domain Events | Aggregate.add_event() → UoW.collect_new_events() |
| Event Sourcing | Пока не реализован; события логируются, но state хранится materialized |
| Saga | Chain of events через trace_stack |

## Где используется

- **Orders**: CreateOrder → OrderCreated → интеграционные слушатели.
- **AGM**: NodeSyncRequested → handle_node_sync_requested → TaskIQ sync_node_metadata.
- **Assets**: при изменении uri/description запускается цепочка CLIP → Ollama → Thumbnail.
- **ECS**: TickEvent → handle_tick → MoveEntityCommand.
