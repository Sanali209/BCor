# BCor Developer Guide

## Getting Started

### Prerequisites
- Python 3.12+
- `uv` package manager
- Docker (optional, for databases)

### Installation
```bash
# Clone repository
git clone https://github.com/Sanali209/BCor.git
cd BCor

# Create virtual environment
uv venv

# Install dependencies
uv pip install -e ".[dev]"

# Install pre-commit hooks (optional)
pre-commit install
```

### Running the Application
```bash
# Run default application
uv run python -m src.apps.hello_app.main

# Run with specific app.toml
uv run python -m src.apps.ImageAnalyze.main

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=src --cov-report=html
```

## Project Structure

```
BCor/
├── src/
│   ├── core/              # Core framework components
│   ├── modules/           # Business modules
│   ├── apps/              # Application entry points
│   ├── adapters/          # Infrastructure adapters
│   └── common/            # Shared utilities
├── tests/
│   ├── unit/              # Unit tests
│   ├── integration/       # Integration tests
│   └── conftest.py        # Test fixtures
├── Ddocks/                # Documentation
├── pyproject.toml         # Project configuration
└── uv.lock               # Dependency lock file
```

## Creating a New Module

### 1. Module Structure
Create directory structure:
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

### 2. Define Messages (`messages.py`)
```python
from src.core.messages import Command, Event

class CreateItemCommand(Command):
    name: str
    description: str

class ItemCreatedEvent(Event):
    item_id: str
    name: str
```

### 3. Create Domain Model (`domain/models.py`)
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

### 4. Implement Handlers (`handlers.py`)
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

### 5. Register Module (`module.py`)
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

### 6. Create Provider (`provider.py`)
```python
from dishka import Provider, Scope
from .adapters.repository import YourRepository

class YourProvider(Provider):
    def __init__(self):
        super().__init__()
        self.provide(YourRepository, scope=Scope.REQUEST)
```

## Testing

### Unit Tests
```python
# tests/unit/test_your_module.py
import pytest
from src.modules.your_module.messages import CreateItemCommand
from src.modules.your_module.handlers import handle_create_item

@pytest.mark.asyncio
async def test_create_item(fake_uow, fake_event_bus):
    cmd = CreateItemCommand(name="Test", description="Test item")
    await handle_create_item(cmd, fake_uow, fake_event_bus)
    
    # Assert events were published
    assert len(fake_event_bus.published_events) == 1
```

### Integration Tests
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

## Configuration

### Application Manifest (`app.toml`)
```toml
[modules]
enabled = ["your_module", "analytics"]

[your_module]
setting1 = "value1"
setting2 = 42

[settings]
database_url = "sqlite+aiosqlite:///./test.db"
```

### Environment Variables
Create `.env` file:
```env
DATABASE_URL=sqlite+aiosqlite:///./app.db
LOG_LEVEL=INFO
NATS_URL=nats://localhost:4222
```

## Common Patterns

### Using UnitOfWork
```python
async with uow:
    # Get repository
    repo = uow.items
    
    # Load aggregate
    item = await repo.get(item_id)
    
    # Modify aggregate
    item.update_name("New Name")
    
    # Commit changes (events auto-published)
    await uow.commit()
```

### Publishing Events
```python
# From handler
await event_bus.publish(ItemCreatedEvent(item_id="123"))

# From aggregate (via UnitOfWork)
self.add_event(ItemCreatedEvent(item_id="123"))
```

### Background Tasks
```python
from src.adapters.taskiq_broker import broker

@broker.task
async def heavy_computation(data: dict):
    # Long-running task
    result = await process_data(data)
    return result

# Call from handler
await heavy_computation.kiq(data)
```

## Debugging

### Enable Debug Logging
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### View Event Flow
```python
# Add to messagebus.py for debugging
logger.debug(f"Dispatching: {message.__class__.__name__}")
```

### Database Queries
```python
# Enable SQL echo
engine = create_engine(url, echo=True)
```

## Best Practices

### Code Style
- Follow PEP 8
- Use type hints everywhere
- Keep functions small (< 20 lines)
- Write docstrings for public APIs

### Testing
- Write tests first (TDD)
- Use fixtures for common setup
- Mock external dependencies
- Test edge cases and errors

### Performance
- Use async/await for I/O
- Batch database operations
- Cache frequently accessed data
- Profile with `cProfile`

### Security
- Validate all inputs
- Use parameterized queries
- Implement proper authentication
- Log security events

## Troubleshooting

### Common Issues

**Import Errors**
```bash
# Ensure src is in Python path
export PYTHONPATH="${PYTHONPATH}:./src"
```

**Database Connection**
```bash
# Check database is running
docker ps | grep postgres

# Verify connection string
echo $DATABASE_URL
```

**Event Not Handling**
```python
# Check handler registration
print(bus._command_handlers)
print(bus._event_handlers)
```

## Contributing

1. Fork the repository
2. Create feature branch
3. Write tests first
4. Implement feature
5. Run linters: `uv run ruff check .`
6. Run tests: `uv run pytest`
7. Submit pull request

## Resources

### Core Documentation
- [README.md](README.md) — Project overview and technology stack
- [ARCHITECTURE.md](ARCHITECTURE.md) — Complete architecture documentation

### Conceptual Documentation (Ddocks/)
- [Roadmap](Ddocks/Roadmap.md) — Development status and TDD plan
- [Concept Document](Ddocks/Conceptdock.md) — Architectural vision
- [Design Document](Ddocks/Dizdok.md) — Core design and repository structure
- [Specification](Ddocks/Specification.md) — Detailed core specification
- [Technical Task](Ddocks/Tech%20tasck.md) — Development technical task

### Module Documentation
- [Orders Module](Ddocks/orders_dock.md) — Reference business module
- [AGM Module](Ddocks/agm_dock.md) — Graph mapper details
- [ECS Module](Ddocks/ecs_dock.md) — Entity Component System
- [VFS Module](Ddocks/vfs_dock.md) — Virtual File System
- [Analytics Module](src/modules/analytics/README.md) — Analytics and background tasks
- [LLM Module](src/modules/llm/README.md) — LLM and NLP processing
- [Search Module](src/modules/search/README.md) — Web and image search

### Guides
- [How-to: Add New Module](Ddocks/How-tos/Add_New_Module.md) — Module creation guide
- [First Steps](firststeps.md) — Getting started with BCor

### Code Documentation
- [src/core/](src/core/) — Core framework implementation
- [src/modules/](src/modules/) — Business modules
- [src/apps/](src/apps/README.md) — Application entry points
- [src/common/](src/common/README.md) — Shared utilities
