# Reference: Module API

## BaseModule

**Модуль:** `src.core.module`

Базовый класс для всех бизнес-модулей. Инкапсулирует настройки, DI-провайдер и маршрутизацию сообщений.

```python
class BaseModule:
    settings_class: type[BaseSettings] | None = None
    provider: Provider | None = None
    command_handlers: dict[type, Callable[..., Any]] = {}
    event_handlers: dict[type, list[Callable[..., Any]]] = {}
```

### Жизненный цикл

Методы, вызываемые `System`:

1. **`async setup()`** — вызывается во время `_bootstrap()`, до инициализации DI-контейнера. Используется для предварительной настройки, проверки зависимостей.

2. **`async startup()`** — вызывается после создания DI-контейнера. В этот момент доступен `self.container`. Используется для регистрации моделей в AGMMapper, запуска TaskIQ broker и т.д.

3. **`async stop()`** — вызывается во время `System.stop()`. Для очистки ресурсов, остановки фоновых задач.

### Пример

```python
class GreetingModule(BaseModule):
    settings_class = GreetingSettings
    provider = GreetingProvider()

    def __init__(self):
        super().__init__()
        self.command_handlers = {
            SayHelloCommand: handle_say_hello,
        }
        self.event_handlers = {
            HelloSaidEvent: [on_hello_said],
        }
```

### Dishka Provider

Модуль может предоставить свой `dishka.Provider`:

```python
class GreetingProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_greeter(self, settings: dict[str, BaseSettings]) -> Greeter:
        module_settings = settings.get("greeting", GreetingSettings())
        return Greeter(default_name=module_settings.default_name, style=module_settings.greeting_style)
```

---

## Aggregate

**Модуль:** `src.core.domain`

Базовый класс для корней агрегации.

```python
class Aggregate:
    events: list[Event] = []

    def __init__(self) -> None
    def add_event(self, event: Event) -> None
```

### Правила

- Агрегат — это консистентная граница: все изменения внутри одного агрегата атомарны.
- События добавляются через `add_event()` и собираются UoW при коммите.
- Не должен знать о БД, репозиториях или фреймворках.

### Пример (Orders)

```python
class Order(Aggregate):
    def __init__(self, ref: str, customer_name: str, total_amount: float):
        super().__init__()
        self.ref = ref
        self.customer_name = customer_name
        self.total_amount = total_amount
        self.status = OrderState.PENDING
        self.add_event(OrderCreated(order_id=self.ref, ...))

    def ship(self) -> None:
        if self.status == OrderState.SHIPPED:
            raise DomainError(f"Order {self.ref} is already shipped.")
        self.status = OrderState.SHIPPED
        self.add_event(OrderShipped(order_id=self.ref))
```

---

## AbstractRepository[T]

**Модуль:** `src.core.repository`

Generic абстракция для хранения и загрузки агрегатов.

```python
class AbstractRepository(Generic[T], abc.ABC):
    seen: set[T] = set()

    def __init__(self) -> None
    def add(self, aggregate: T) -> None
    def get(self, reference: str) -> T | None

    @abc.abstractmethod
    def _add(self, aggregate: T) -> None
    @abc.abstractmethod
    def _get(self, reference: str) -> T | None
```

### Контракт

- `add(a)`: вызывает `_add(a)` и добавляет `a` в `seen`.
- `get(ref)`: вызывает `_get(ref)`, если найден — добавляет в `seen`.
- `_add()` / `_get()` — реализуются конкретным адаптером.

### Реализации

**SqlAlchemyRepository** (`src/adapters/repository.py`):

```python
class SqlAlchemyRepository(AbstractRepository[T]):
    def __init__(self, session: Session, model_class: type[T])
    def _add(self, aggregate) -> None: self.session.add(aggregate)
    def _get(self, reference) -> T | None:
        # сначала по PK, потом по ref
```

**JsonRepository** (`src/adapters/persistence/json_repository.py`):

```python
class JsonRepository(AbstractRepository[T], Generic[T]):
    def __init__(self, file_path: str | Path, model_class: type[T])
    def list(self) -> list[T]
    def remove(self, reference: str) -> bool
```

---

## Message (Command / Event)

**Модуль:** `src.core.messages`

```python
class Message(BaseEvent):
    correlation_id: str = Field(default_factory=lambda: uuid.uuid4().hex)
    trace_stack: list[str] = Field(default_factory=list)

class Command(Message): ...    # намерение изменить состояние
class Event(Message): ...     # факт, что что-то произошло
```

- `correlation_id` — идентификатор для трассировки цепочек сообщений.
- `trace_stack` — список имён типов сообщений, через которые прошёл запрос (детектор зацикливаний).
- `Command` маршрутизируется **одному** хендлеру.
- `Event` рассылается **всем** подписчикам.

---

## ModuleDiscovery

**Модуль:** `src.core.discovery`

```python
class ModuleDiscovery:
    @staticmethod
    def load_from_manifest(manifest_path: str | Path) -> list[BaseModule]
```

- Читает TOML-файл.
- Для каждого имени из `enabled` пытается импортировать `{search_path}.{name}.module`.
- Ищет в импортированном модуле любой класс — наследник `BaseModule`.
- Вызывает `cls()` и возвращает экземпляр.

---

## Сводка контрактов

| Компонент | Обязанность | Не должен |
|-----------|-------------|-----------|
| `Aggregate` | Бизнес-правила, события | Знать о БД, ORM, DI |
| `BaseModule` | Регистрация хендлеров, DI | Содержать бизнес-логику |
| `AbstractRepository` | Сохранение/загрузка агрегатов | Знать о MessageBus, UoW |
| `AbstractUnitOfWork` | Атомарность, сбор событий | Содержать бизнес-логику |
| `Command` | Намерение изменить состояние | Возвращать данные |
| `Event` | Факт, что произошло | Выполнять логику (кроме подписчиков) |
