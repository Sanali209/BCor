# Reference: Core API

## MessageBus

**Модуль:** `src.core.messagebus`

Центральный диспетчер команд и событий. Построен поверх `bubus.EventBus` с добавлением DI, retry-политики и трассировки.

```python
class MessageBus:
    def __init__(
        self,
        uow: AbstractUnitOfWork,
        container: AsyncContainer | None = None,
        max_trace_depth: int = 20,
    )
```

### Методы

**`register_command(cmd_type: type[Command], handler: Callable)`**

Регистрирует 1-к-1 обработчик команды. Обработчик оборачивается:
- `tenacity.retry`: exponential backoff, до 3 попыток.
- OpenTelemetry span: `"Handle Command: {cmd_type.__name__}"`.
- DI-инжекция: параметры хендлера, кроме первого (сообщение), разрешаются из контейнера.

```python
bus.register_command(CreateOrderCommand, handle_create_order)
```

**`register_event(evt_type: type[Event], handler: Callable)`**

Регистрирует N-к-1 подписчика события. Обработчик оборачивается:
- OpenTelemetry span: `"Handle Event: {evt_type.__name__}"`.
- DI-инжекция: как в командах.
- Изоляция ошибок: исключения логируются, но не крашат bus.
- После выполнения вызывает `_publish_collected_events()`.

```python
bus.register_event(OrderCreated, on_order_created)
```

**`async dispatch(message: Message) -> Message`**

Главная точка входа. Принимает Command или Event, отправляет в `bubus`, собирает новые события из UoW и публикует их. Поддерживает трассировку стека вызовов через `message.trace_stack`.

### Retry-политика

```python
@retry(
    wait=wait_exponential(multiplier=0.1, min=0.1, max=1.0),
    stop=stop_after_attempt(3),
    reraise=True,
    retry=retry_if_exception_type(Exception),
)
```

3 попытки с экспоненциальной задержкой (0.1–1.0 сек).

### Патч bubus

При импорте модуля отключается встроенный 2-уровневый детектор циклов bubus — BCor использует собственный `max_trace_depth` (по умолчанию 20).

---

## AbstractUnitOfWork

**Модуль:** `src.core.unit_of_work`

Абстрактный класс для Unit of Work паттерна. Обеспечивает атомарность операций и сбор доменных событий.

```python
class AbstractUnitOfWork(abc.ABC):
    def __enter__(self) -> AbstractUnitOfWork
    def __exit__(self, exc_type, exc_val, exc_tb) -> None

    async def __aenter__(self) -> AbstractUnitOfWork
    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None

    def commit(self) -> None
    def rollback(self) -> None

    def collect_new_events(self) -> Generator[Event, None, None]
```

### Детали реализации

- `__exit__` / `__aexit__` вызывают `self.rollback()` — откат при ошибке.
- `collect_new_events()` итерирует все repositories через `dir(self)`, находит `AbstractRepository`, собирает `aggregate.events`.
- `_get_all_seen_aggregates()` — рефлексивно находит все репозитории, привязанные к UoW.

### SqlAlchemyUnitOfWork (конкретная реализация)

**Модуль:** `src.adapters.unit_of_work`

```python
class SqlAlchemyUnitOfWork(AbstractUnitOfWork):
    def __init__(self, session_factory: Callable[[], Session], model_class: type[Aggregate])
```

- `__enter__`: создаёт сессию, инициализирует `SqlAlchemyRepository`.
- `_commit`: `self.session.commit()`.
- `rollback`: `self.session.rollback()`.
- `__exit__`: закрывает сессию.

---

## System (Composition Root)

**Модуль:** `src.core.system`

Управляет lifecycle приложения: загрузка модулей, инициализация DI, запуск/остановка.

```python
class System:
    @classmethod
    def from_manifest(cls, manifest_path: str | Path) -> System
    def __init__(self, modules: list[BaseModule], config: dict | None = None)
    async def start(self) -> None
    async def stop(self) -> None
```

### from_manifest

1. Читает `app.toml` через `tomllib`.
2. Загружает модули через `ModuleDiscovery.load_from_manifest()`.
3. Создаёт `System(modules, config)`.

### start()

1. `_bootstrap()` — для каждого модуля:
   - `module.setup()` (pre-DI).
   - Собирает command_handlers / event_handlers.
   - Валидирует Pydantic-настройки.
   - Добавляет Dishka-провайдеры.
2. Создаёт `CoreProvider` с общими настройками и MessageBus.
3. Создаёт `make_async_container()` из Dishka.
4. Для каждого модуля: `module.startup()` (post-DI).
5. Запускает `@on_start` хуки.

### stop()

1. Запускает `@on_stop` хуки.
2. Закрывает Dishka-контейнер.

---

## CoreProvider

**Модуль:** `src.core.system`

Dishka Provider для системных компонентов.

```python
class CoreProvider(Provider):
    def __init__(self, event_handlers, command_handlers, settings)
    def provide_settings(self) -> dict[str, BaseSettings]
    async def provide_message_bus(self, uow, container) -> AsyncIterable[MessageBus]
```

- `provide_message_bus`: регистрирует все command_handlers и event_handlers на bus, затем yield bus. При выходе из контекста вызывает `bus.bus.stop()`.

---

## Monads (BusinessResult)

**Модуль:** `src.common.monads`

```python
from returns.result import Result

BusinessResult = Result[T, E]   # алиас

def success(value: T) -> BusinessResult[T, Any]
def failure(error: E) -> BusinessResult[Any, E]
```

Используется как возвращаемый тип хендлеров команд:

```python
async def handle_create_order(cmd, uow) -> BusinessResult:
    ...
    return success(order.ref)
    # или
    return failure("Order already exists")
```

Позволяет вызывающему коду:

```python
result = await handle_create_order(cmd, uow)
if result.is_success():
    print(result.unwrap())
else:
    print(f"Error: {result.failure()}")
```

---

## Декораторы lifecycle

**Модуль:** `src.core.decorators`

```python
@on_start
def my_startup():
    ...

@on_stop
async def my_shutdown():
    ...

clear_hooks()  # для тестов
```

Поддерживают sync и async функции.

---

## BCorTestSystem

**Модуль:** `src.core.testing`

```python
class BCorTestSystem:
    def __init__(self, manifest_path: str, drain_delay: float = 0.5)
    @asynccontextmanager
    async def run(self) -> AsyncGenerator[System, None]

async def run_test_system(manifest_path, test_func, *args, **kwargs)
```

Управляет lifecycle тестового System + дренирование event loop на Windows.

---

## WindowsLoopManager

**Модуль:** `src.core.loop_policies`

```python
class WindowsLoopManager:
    @staticmethod
    async def drain_loop(delay: float = 0.5)
```

Предотвращает зависания asyncio-цикла на Windows после остановки System.
