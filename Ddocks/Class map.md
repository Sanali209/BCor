# Class Map

> The source of truth is the codebase (`src/`). This file strictly maps the currently implemented architecture and classes.

## Core (`src/core/`)

### Messages (`messages.py`)
*   `Message(bubus.BaseEvent)`: Base message data structure.
*   `Command(Message)`: Intentions routed to a single handler.
*   `Event(Message)`: Facts routed to multiple subscribers.

### Lifecycle & Hooks (`decorators.py`)
*   `@on_start`: Decorator for system startup hooks.
*   `@on_stop`: Decorator for system shutdown hooks.

### Functional Core (`monads.py`)
*   `BusinessResult`: Type alias for `Result` monad (Success/Failure).
*   `success()` / `failure()`: Helpers for Railway Oriented Programming.

### Discovery & Loading (`discovery.py`)
*   `ModuleDiscovery`: Manifest-based (`app.toml`) module discovery and instantiation.

### Domain (`domain.py`)
*   `Aggregate`: Base class for entities boundary. Includes `events` list and `add_event()`.

### Message Bus (`messagebus.py`)
*   `MessageBus`: Dispatcher wrapping `bubus.EventBus`. Supports **DI-aware parameter injection** from the Dishka container.
    *   Methods: `register_command()`, `register_event()`, `dispatch()`, `_publish_collected_events()`

### Ports (`repository.py`, `unit_of_work.py`)
*   `AbstractRepository[T](abc.ABC)`: Data storage abstraction.
    *   State: `seen: set`
    *   Methods: `add()`, `get()`, `_add()`, `_get()`
*   `AbstractUnitOfWork(abc.ABC)`: Transaction boundary.
    *   Methods: `__enter__()`, `__exit__()`, `commit()`, `rollback()`, `collect_new_events()`, `_commit()`, `_get_all_seen_aggregates()`

### System Composition (`module.py`, `system.py`)
*   `BaseModule`: Declarative configuration logic.
    *   State: `settings_class`, `provider`, `command_handlers`, `event_handlers`
*   `System`: Application composition root.
    *   Methods: `from_manifest()` (Bootstrap via TOML), `start()`, `stop()`.
*   `CoreProvider(dishka.Provider)`: Provides global `MessageBus` instances and Pydantic settings.

---

## Modules (`src/modules/`)

### Entity Component System (`ecs/`)
*   **Domain**:
    *   `PositionComponent`, `VelocityComponent` (@dataclass)
    *   `EcsWorld(Aggregate)`: Game world aggregate (methods: `add_component`, `query`, `check_collisions`)
*   **Messages**:
    *   Events: `TickEvent`, `ComponentAddedEvent`, `CollisionDetectedEvent`
    *   Commands: `MoveEntityCommand`
*   **Ports**:
    *   `AbstractEcsRepository(AbstractRepository[EcsWorld])`
    *   `EcsUnitOfWork(AbstractUnitOfWork)`: Holds `worlds: AbstractEcsRepository`
*   **Handlers**: `physics_system_handler`, `handle_move_entity_command`
*   **Registration**: `EcsModule(BaseModule)`

### Orders (`orders/`)
*   **Domain**:
    *   `OrderState(Enum)`
    *   `Order(Aggregate)`: E-commerce order (methods: `create`, `ship`)
*   **Messages**:
    *   Events: `OrderCreated`, `OrderShipped`
    *   Commands: `CreateOrderCommand`, `ShipOrderCommand`
*   **Handlers**: `handle_create_order`, `handle_ship_order`
*   **Registration**: `OrdersModule(BaseModule)`

### Analytics (`analytics/`)
*   **Domain**:
    *   `AnalyticsSettings(BaseSettings)`
    *   `GenerateReportCommand(Command)`
    *   `ReportGenerationStartedEvent(Event)`
*   **Handlers / Tasks**:
    *   Background task: `build_heavy_report_task` (Taskiq)
*   **Registration**: `AnalyticsModule(BaseModule)`

*   **Registration**: `AGMModule(BaseModule)` with `AGMProvider`

### Virtual File System (`vfs/`)
*   **Infrastructure**:
    *   `VfsSettings(BaseSettings)`: Configures connection string.
    *   `VfsProvider(Provider)`: Provides `FS` (PyFilesystem2) instances with automatic lifecycle management.
*   **Registration**: `VfsModule(BaseModule)`

---

## Adapters (`src/adapters/`)
*   `taskiq_broker.py`: Configures `NatsBroker` (Taskiq) with Prometheus metrics middleware. Used for async task delegation.
*   `orm.py`: Imperative mapping registry for SQLAlchemy.
*   `repository.py`: `SqlAlchemyRepository` (generic implementation).
*   `unit_of_work.py`: `SqlAlchemyUnitOfWork` (manages DB sessions).

---

## Applications (`src/apps/`)
*   `app.toml`: Application manifest (enabled modules, settings).
*   `main.py`: Entry point using `System.from_manifest()`.
*   **Samples**:
    *   `hello_app`: Core pattern demonstration.
    *   `VFSSample`: Demonstrates VFS integration and DI-aware message bus handlers.
