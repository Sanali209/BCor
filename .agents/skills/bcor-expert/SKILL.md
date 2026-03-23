---
name: bcor-expert
description: Expert knowledge and professional architectural patterns for the BCor framework. Make sure to use this skill whenever the user mentions BCor modules, dependency injection (Dishka), porting legacy applications to BCor, the MessageBus (bubus), Domain-Driven Design (CQRS, Aggregates, Unit of Work), app.toml configuration, global lifecycle hooks, or debugging Pytest-Asyncio deadlocks on Windows. This is the ultimate guide to professional use of the BCor framework.
---

# BCor Expert Guide

This skill encompasses hard-earned insights and advanced professional patterns from the BCor framework codebase (`src/core`). It covers the core design philosophy (CQRS + DI), resiliency, observability, and robust refactoring strategies.

## 1. Automated Dependency Resolution in Handlers

You do **not** need to manually retrieve dependencies from the `Dishka` container inside your handlers. The `MessageBus` automatically inspects the type hints (signatures) of your Command and Event handlers and resolves dependencies via the active container.

```python
# GOOD: Automated DI
async def handle_create_user(cmd: CreateUserCommand, db: DatabaseManager, uow: AbstractUnitOfWork):
    await db.execute(...)  # db is automatically injected!

# BAD: Manual DI (Anti-pattern)
async def handle_create_user(cmd: CreateUserCommand, container: AsyncContainer):
    db = await container.get(DatabaseManager) # Do not do this
```

## 2. Resiliency, Idempotency, and Observability

BCor is built for production robustness. Operations on the `MessageBus` are inherently resilient but require strict handler design:

- **Command Handlers MUST be Idempotent:** All 1-to-1 command handlers are automatically wrapped in a `tenacity` retry policy (up to 3 attempts with exponential backoff on exceptions). If a transient failure occurs in the middle of a transaction, the handler will run again. Design handlers so repeated executions with the same command do not corrupt data.
- **Event Isolation:** 1-to-N event handlers execute independently. A failure in one event handler is caught, logged as an "Isolated failure", and does **not** crash the entire bus.
- **Observability:** Both commands and events are automatically wrapped in context-aware OpenTelemetry spans, passing along the `command.type` or `event.type`.

## 3. Module Configuration (`app.toml` & Pydantic)

Modules configure themselves via Pydantic settings. Do not parse `os.environ` manually inside a module. 

Instead, define a `settings_class` referencing `BaseSettings` within your module extending `BaseModule`. The `System` bootstrap will automatically read the corresponding TOML block in `app.toml` matching your module's normalized name, instantiate your settings class, and register it in the DI provider.

```python
class MyModuleSettings(BaseSettings):
    api_key: str
    timeout: int = 30

class MyModule(BaseModule):
    settings_class = MyModuleSettings
    # settings will automatically be available inside the Dishka system core container
```

## 4. Lifecycle Hooks vs. DI Teardowns

BCor offers two distinct ways to manage resource lifecycles:

- **Global Bootstrapping (`@on_start` / `@on_stop`):** Use the decorators from `src.core.decorators` for system-wide initialization that only needs to happen when the application boots (e.g., establishing a persistent connection pool, warming a cache, setting up a tracer).
- **Dependency Teardown (`Dishka` Generators):** Use a Dishka provider `yield` inside a generator for resources that strictly belong to a specific DI scope (like a `Scope.REQUEST` transaction or consumer).

## 5. Event Collection, Causality, and the MessageBus

The BCor `MessageBus` replaces the built-in loop prevention of `bubus` with a sophisticated causality tracing system (`max_trace_depth` typically set to 20).

**Why you must NOT return events from Command Handlers:**
Returning an event directly drops it into the basic bubus scheduler, bypassing BCor's context tracking. Instead, domain Aggregate roots should queue events internally. The `UnitOfWork` then exposes `collect_new_events()`, which the `MessageBus` calls after dispatching a message. This process automatically assigns the correct `correlation_id` and appends the `trace_stack` to the new event, preventing hidden infinite loops.

```python
# BAD
async def handle_cmd(cmd) -> MyEvent:
    return MyEvent()

# GOOD
async def handle_cmd(cmd, uow):
    aggregate.do_something_which_adds_event()
    await uow.repository.add(aggregate)
    # The UoW will emit the event securely through the bus automatically
```

## 6. Porting Strategy: The Strangler Fig Pattern

When porting legacy applications into BCor:
- **Do not extract all code immediately:** Keep the legacy logic in its original folder.
- **Iterative wrapping:** Start by building the BCor infrastructure (`app.toml`, `module.py`, `messages.py`, `handlers.py`, `provider.py`) inside the legacy app's directory.
- **Bridge the Gap:** Wrap legacy services in `Dishka` providers. Migrate business logic incrementally by wrapping legacy function calls in new BCor `UseCases` and triggering them via the `MessageBus`.

## 7. Pytest Stability on Windows (`pytest-asyncio`)

Windows testing of async code involving threading pools often results in infinite hangs during interpreter teardown (`ProactorEventLoop` closure bugs). Always apply these steps in `tests/conftest.py`:

1. **Switch to Selector Event Loop:**
   ```python
   import sys
   import asyncio
   if sys.platform == 'win32':
       asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
   ```
2. **Aggressive Interpreter Drop:** Hook into `pytest_unconfigure` to drop the process once testing completes avoiding daemon thread blocks.
   ```python
   import os
   def pytest_unconfigure(config):
       os._exit(0)
   ```

## 9. Repository Implementation: Fulfilling Interfaces

When porting or implementing new SQLite repositories, you **MUST** ensure that every abstract method from the corresponding domain interface (e.g., `IProjectRepository`, `IPostRepository`) is explicitly implemented. BCor uses `abc.ABC` which raises `TypeError` at **instantiation time** (usually within the `UnitOfWork`) if implementations are missing.

**Common Required Methods for Repositories:**
- **Standard**: `get(id)`, `save(aggregate)`, `create(aggregate)`, `delete(id)`.
- **Project Specific**: `get_all_projects()`, `fetch_queued_projects()`, `move_project_to_end_of_queue(id)`.
- **Pagination**: `get_pagination_state(project_id, start_url)`, `update_pagination_state(...)`, `delete_pagination_state(...)`.

## 10. GUI Integration (PySide6 + BCor Async)

To bridge the BCor asynchronous event bus with a synchronous PySide6 (Qt) UI, use the **`GuiEventAdapter`** pattern. This preserves thread safety and allows the UI to react to domain events in real-time.

1. **The Adapter**: Create a `QObject` with `Signal` attributes for each event type (e.g., `log_signal`, `stats_signal`).
2. **The Bridging Handler**: Implement a standard BCor event handler that simply `.emit()`s the signal on the adapter.
3. **The Integration**: Register the adapter in the DI container (Dishka) and ensure it's provided where handlers are registered.

```python
# infrastructure/events_adapter.py
class GuiEventAdapter(QObject):
    log_signal = Signal(str, str)
    stats_signal = Signal(int, dict)

async def handle_log_event(event: ScrapeLogEvent, adapter: GuiEventAdapter):
    adapter.log_signal.emit(event.level, event.message)
```

## 11. Event Handler Signatures & DI Hygiene

When registering event handlers (especially simple functions), ensure their signatures match the dependencies provided by the `MessageBus` at the target `Scope` (usually `Scope.REQUEST`).

- **Avoid `**kwargs` unless necessary**: Be explicit about dependencies to benefit from static analysis.
- **DI Mismatch**: If you see `TypeError: handle_event() got an unexpected keyword argument 'uow'`, it means the bus is trying to inject a `UnitOfWork` but your function signature didn't include it. Either add it or check if the registration logic correctly filters injections.
- **Async Execution**: All handlers MUST be `async def`.

## 12. Windows-Specific GUI Event Loops

When running PySide6 + BCor on Windows, use **`qasync`** for the event loop. To avoid hangs during teardown, ensure the correct event loop policy is set before starting the application:

```python
import asyncio
from qasync import QEventLoop
from PySide6.QtWidgets import QApplication

def main():
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    # ... start system ...
```

## 13. Pydantic Compatibility

BCor Base `Command` and `Event` structures inherit from Pydantic `BaseModel`.
**WARNING:** Do not decorate classes deriving from BCor Messages with Python's `@dataclass`. This conflates Pydantic initialization logic with standard dataclasses, leading to missing attribute `AttributeError`s at runtime.
