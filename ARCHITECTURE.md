# BCor Architecture Documentation

## Overview
BCor is an **Event-Driven Modular Monolith** built on Clean Architecture principles, DDD (Domain-Driven Design), and CQRS (Command Query Responsibility Segregation). The system is designed for scalability, maintainability, and testability.

## Core Architectural Principles

### 1. Clean Architecture Layers
```
┌─────────────────────────────────────┐
│           Presentation Layer        │  ← Entry Points (FastAPI, CLI, GUI)
├─────────────────────────────────────┤
│           Application Layer         │  ← Commands, Events, Handlers
├─────────────────────────────────────┤
│             Domain Layer            │  ← Aggregates, Entities, Value Objects
├─────────────────────────────────────┤
│          Infrastructure Layer       │  ← Adapters, Repositories, External Services
└─────────────────────────────────────┘
```

### 2. Dependency Rule
- Inner layers **never** depend on outer layers
- Domain layer has **zero** external dependencies
- Infrastructure implements domain interfaces (ports)

### 3. Event-Driven Communication
- Modules communicate **only** through events via `bubus.EventBus`
- No direct method calls between modules
- Loose coupling enables independent module evolution

## Core Components

### Message Bus (`src/core/messagebus.py`)
- Wraps `bubus.EventBus`
- Routes Commands to single handlers
- Broadcasts Events to multiple subscribers
- Automatic DI injection via `dishka`
- OpenTelemetry tracing integration

### Unit of Work (`src/core/unit_of_work.py`)
- Transaction boundary abstraction
- Manages repository instances
- Collects domain events from aggregates
- Automatic rollback on exceptions

### Repository Pattern (`src/core/repository.py`)
- Generic `AbstractRepository[T]` base class
- Tracks loaded aggregates in `seen` set
- Implemented by concrete adapters (SQLAlchemy, JSON, etc.)

### System Composition (`src/core/system.py`)
- Bootstrap via `System.from_manifest()`
- Loads `app.toml` configurations
- Initializes DI container with `dishka`
- Registers all module handlers

## Module Structure

Each module follows a consistent structure:
```
src/modules/<module>/
├── __init__.py
├── module.py          # Module registration
├── messages.py        # Commands and Events
├── handlers.py        # Business logic
├── provider.py        # DI providers
├── domain/            # Domain model
└── adapters/          # Infrastructure implementations
```

### Module Types
- **Core Modules**: `ecs`, `agm`, `analytics`, `orders`, `vfs`, `llm`, `files`
- **Applications**: `default_app`, `VFSSample`, `hello_app`
- **Common Libraries**: `src/common/` (pure Python utilities)

## Event Flow Example

```
1. FastAPI receives POST /orders
2. Creates CreateOrderCommand
3. MessageBus routes to handle_create_order
4. Handler uses OrderRepository (via DI)
5. Order aggregate generates OrderCreated event
6. UnitOfWork collects event
7. MessageBus publishes OrderCreated
8. Analytics module subscribes and logs
```

## Configuration

### Application Manifest (`app.toml`)
```toml
[modules]
enabled = ["ecs", "analytics", "orders"]

[settings]
# Module-specific settings
```

### Environment Variables
- Loaded via `pydantic-settings`
- Fail-fast on missing required vars
- Validated at startup

## Observability

### Logging
- `loguru` replaces standard `logging`
- Structured JSON output
- Context-aware with trace IDs

### Tracing
- OpenTelemetry integration
- Spans for every command/event
- Distributed tracing support

### Metrics
- Prometheus metrics in TaskIQ workers
- Port 9000 for metrics endpoint

## Testing Strategy

### Test Pyramid
```
       E2E Tests (Few)
          ↑
   Integration Tests (Some)
          ↑
    Unit Tests (Many)
```

### Test Doubles
- `FakeRepository`: In-memory implementation
- `FakeUnitOfWork`: No-op transactions
- Located in `tests/conftest.py`

### TDD Workflow
1. Write failing test (Red)
2. Implement minimum code (Green)
3. Refactor for clarity (Refactor)

## Technology Stack

| Component | Technology |
|-----------|------------|
| Package Management | `uv` |
| Event Bus | `bubus` |
| DI Container | `dishka` |
| Settings | `pydantic-settings` |
| Background Tasks | `TaskIQ` + `NATS` |
| Error Handling | `returns` (Result Monad) |
| Logging | `loguru` |
| Tracing | `OpenTelemetry` |
| Metrics | `Prometheus` |
| Testing | `pytest`, `pytest-asyncio` |

## Migration from Legacy

### Strangler Fig Pattern
1. Wrap legacy app in BCor module
2. Gradually extract business logic
3. Replace UI calls with commands
4. Remove legacy code when isolated

### Anti-Corruption Layer
- ACL adapters bridge legacy concepts
- Never import legacy code from new modules
- Domain-first migration approach

## Best Practices

### Module Development
1. Start with `messages.py` (define commands/events)
2. Create domain model in `domain/`
3. Implement handlers with business logic
4. Register in `module.py`
5. Write tests first (TDD)

### Error Handling
- Use `BusinessResult` monad for business errors
- Exceptions for infrastructure failures
- Fail-fast for configuration errors
- Fail-safe for event handlers

### Performance
- Async/await throughout
- Background tasks for heavy operations
- CQRS read models for queries
- Connection pooling for databases

## Related Documentation

- [README.md](README.md) — Project overview
- [DEVELOPER_GUIDE.md](DEVELOPER_GUIDE.md) — Development guide
- [Ddocks/](Ddocks/) — Conceptual documentation
- [src/core/](src/core/) — Core implementation
- [src/modules/](src/modules/) — Business modules
- [src/apps/](src/apps/README.md) — Application entry points
- [src/common/](src/common/README.md) — Shared utilities
