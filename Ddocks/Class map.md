# Class Map

> The source of truth is the codebase (`src/`). This file strictly maps the currently implemented architecture and classes.

## Core (`src/core/`)

### Messages (`messages.py`)
*   `Message(bubus.BaseEvent)`: Base message data structure.
*   `Command(Message)`: Intentions routed to a single handler.
*   `Event(Message)`: Facts routed to multiple subscribers.

### Domain (`domain.py`)
*   `Aggregate`: Base class for entities boundary. Includes `events` list and `add_event()`.

### Message Bus (`messagebus.py`)
*   `MessageBus`: Dispatcher wrapping `bubus.EventBus`.
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
    *   Methods: `_bootstrap()` (Initializes Dishka DI container, modules, and settings).
*   `CoreProvider(dishka.Provider)`: Provides global `MessageBus` instances.

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

### Aetheris Graph Mapper (`agm/`)
*   **Metadata (`metadata.py`)**: `Stored`, `Live`, `Rel`
*   **Messages**: `StoredFieldRecalculationRequested(Event)`
*   **Mapper (`mapper.py`)**:
    *   `AGMMapper`: Handles `load()` (live resolution, Retort mapping) and `save()` (generates Cypher `MERGE`, dispatches events).
*   **Fluent Queries (`fluent.py`)**:
    *   `QueryBuilder[T]`: Generates smart Cypher projections and executes vector searches.
*   **Models**: `AetherisBaseNode`, `TargetNode`
*   **Handlers / Tasks**: `handle_stored_field_recalc` -> `compute_stored_field` (Taskiq)
*   **Registration**: `AGMModule(BaseModule)` with `AGMProvider`

---

## Adapters (`src/adapters/`)
*   `taskiq_broker.py`: Configures `NatsBroker` (Taskiq) with Prometheus metrics middleware. Used for async task delegation.
