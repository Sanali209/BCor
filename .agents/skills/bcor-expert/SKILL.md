---
name: bcor-expert
description: Expert knowledge on the BCor framework, including DI (Dishka), CQRS (bubus), and the Strangler Fig pattern. MUST be triggered when porting legacy applications to BCor, writing BCor modules, handling bubus message bus threads, configuring dependency injection scopes, or debugging Pytest-Asyncio hangs and deadlocks on Windows environments.
---

# BCor Expert Guide

This skill encompasses hard-earned insights from actively porting legacy applications into the BCor framework. It covers the core design philosophy (CQRS + DI), refactoring strategies, and critical fixes for common testing deadlocks.

## 1. Porting Strategy: The Strangler Fig Pattern
When integrating legacy applications (e.g., `ImageDedup`) into BCor:
- **Do not extract all code immediately:** Keep the legacy logic in its original module folder.
- **Iterative wrapping:** Start by building the BCor infrastructure (`app.toml`, `module.py`, `messages.py`, `handlers.py`, `uow.py`) inside the legacy app's directory.
- **Bridge the Gap:** Wrap legacy services in `Dishka` providers. Migrate business logic incrementally by wrapping legacy function calls in new BCor `UseCases` and triggering them via the `MessageBus`.

## 2. Dependency Injection (Dishka) & Teardowns
BCor heavily utilizes `Dishka` for Dependency Injection. Correct lifecycle management is critical to avoid deadlocks:

- **Scopes:** Use `Scope.APP` for singletons (e.g., DB connections, repositories) and `Scope.REQUEST` for transient operations (e.g., UseCases, MessageBus).
- **Generators for Teardown:** Never just `return` a resource that requires cleanup (like a Database connection or an Event Bus). Use generators to `yield` the resource and tear it down afterward.
  ```python
  @provide(scope=Scope.APP)
  def get_db_manager(self) -> typing.Iterable[DatabaseManager]:
      db = DatabaseManager('data.db')
      yield db
      db.close() # Executes when the container closes
  ```

## 3. The `MessageBus` (`bubus` integration)
`MessageBus` orchestrates commands and events asynchronously via `bubus`.

### Preventing Background Thread Hangs
`bubus` spins up a `ThreadPoolExecutor` under the hood. To close it correctly and prevent the Python interpreter from hanging (especially during tests), the DI provider MUST safely await the asynchronous bus stop.
```python
from typing import AsyncIterable

@provide(scope=Scope.REQUEST)
async def provide_message_bus(self, uow: AbstractUnitOfWork, container: AsyncContainer) -> AsyncIterable[MessageBus]:
    bus = MessageBus(uow=uow, container=container)
    
    # ... register commands and events ...
    
    yield bus
    await bus.bus.stop() # CRITICAL: Await the coroutine to kill background threads
```

### Handler Anti-Patterns
Command Handlers execute logic, but they should **NOT return events directly**. Returning an Event instance from a `bubus` handler can cause the framework to spawn unawaited background publish tasks, leading to hanging tasks during teardown.
```python
# BAD
async def my_handler(cmd, use_case) -> MyEvent:
    return MyEvent() # Avoid this

# GOOD
async def my_handler(cmd, use_case) -> None:
    await use_case.execute() 
    # UseCase or Domain Layer should publish the event through the UoW/Bus
```

## 4. Pytest Stability on Windows (`pytest-asyncio`)
Windows testing of async code involving threading pools (`bubus`, `chromadb`, etc.) frequently results in infinite hangs during interpreter teardown (`ProactorEventLoop` closure bugs).

To guarantee robust test execution, apply these steps in `tests/conftest.py`:

1. **Switch to Selector Event Loop:**
   ```python
   import sys
   import asyncio
   if sys.platform == 'win32':
       asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
   ```
2. **Aggressive Interpreter Drop (The Ultimate Fix):**
   Even with the selector loop, lingering daemon threads from 3rd-party SDKs might block the teardown. Hook into `pytest_unconfigure` to ruthlessly drop the process once testing completes.
   ```python
   import os
   def pytest_unconfigure(config):
       print("Forcing pytest process exit to avoid teardown hang...", flush=True)
       os._exit(0)
   ```

## 5. Pydantic Compatability
BCor base Command and Event structures inherit from `Pydantic` `BaseModel`.
**WARNING:** Do not decorate classes deriving from BCor Messages with Python's `@dataclass`. This creates profound conflicts with Pydantic's internal initialization logic, leading to missing attribute `AttributeError`s at runtime.
