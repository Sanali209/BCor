# SLM Core Pythonic Rewrite - Todo & Documentation

## ✅ Completed Tasks

### 1. Singleton Infrastructure
- [x] Created `singleton.py` with thread-safe metaclass pattern
- [x] Implemented `SingletonMeta` with double-check locking
- [x] Added `Singleton` base class with helper methods
- [x] Included reset capabilities for testing

### 2. Lifecycle Management
- [x] Created `lifecycle.py` with state machine
- [x] Implemented `AppState` enum (CREATED → CONFIGURED → INITIALIZED → STARTED → RUNNING → STOPPING → STOPPED → SHUTDOWN)
- [x] Built `LifecycleManager` with state transition validation
- [x] Added lifecycle hooks and state listeners
- [x] Implemented guard methods (can_start, can_stop, etc.)

### 3. Decorator Syntactic Sugar
- [x] Created `decorators.py` with comprehensive decorator suite
- [x] Implemented `@component` decorator for component registration
- [x] Added `@service` decorator for service registration
- [x] Created `@inject` and `@auto_inject` for dependency injection
- [x] Built `@subscribe` for event subscriptions
- [x] Added lifecycle hooks: `@on_app_start`, `@on_app_stop`, `@on_app_initialize`, `@on_app_shutdown`
- [x] Implemented `@on_config_change` for configuration reactivity
- [x] Added `@cached_property` decorator

### 4. Core Singletons Update
- [x] Updated `Config` to inherit from `Singleton`
- [x] Updated `MessageBus` to inherit from `Singleton`
- [x] Updated `DependencyManager` to inherit from `Singleton`
- [x] Updated `ComponentManager` to inherit from `Singleton`
- [x] Updated `PluginSystem` to inherit from `Singleton`
- [x] Added re-initialization prevention logic to all singletons

### 5. Module-level Elegant Access
- [x] Rewrote `core/__init__.py` with module-level singleton instances
- [x] Created `config`, `bus`, `dependencies`, `components`, `plugins` module-level instances
- [x] Implemented `Core` class for property-based access
- [x] Added comprehensive `__all__` exports
- [x] Included utility functions (`reset_all`, `get_version`)

### 6. Documentation & Examples
- [x] Created `elegant_usage_example.py` showcasing all patterns
- [x] Demonstrated 10 different usage patterns
- [x] Included comprehensive inline documentation

## 📋 Usage Patterns

### Pattern 1: Module-level Singleton Access
```python
from SLM.core import config, bus, dependencies, components

# Direct singleton access
config.database.host = "localhost"
bus.publish("event", data="value")
```

### Pattern 2: Core Class Access
```python
from SLM.core import Core

# Property-based access
Core.config.app.name = "MyApp"
Core.bus.publish("event")
```

### Pattern 3: Component Decorator
```python
from SLM.core import component, Component, Config

@component(name="MyService")
class MyService(Component):
    config: Config  # Auto-injected
    
    def on_start(self):
        print("Started!")
```

### Pattern 4: Service Decorator
```python
from SLM.core import service

@service(singleton=True)
class AuthService:
    def login(self, user, password):
        # Logic here
        pass
```

### Pattern 5: Dependency Injection
```python
from SLM.core import inject, auto_inject, Config, MessageBus

@inject(config=Config, bus=MessageBus)
def process(data, config, bus):
    bus.publish("processed", data=data)

@auto_inject
def auto_process(data: str, config: Config):
    # Config auto-injected based on type hint
    pass
```

### Pattern 6: Event Subscriptions
```python
from SLM.core import subscribe, on_config_change

@subscribe("app.started", "user.created")
def on_events(event_type, **data):
    print(f"Event: {event_type}")

@on_config_change("database.host")
def on_db_change(old_value, new_value):
    print(f"DB host changed: {old_value} → {new_value}")
```

### Pattern 7: Lifecycle Hooks
```python
from SLM.core import on_app_start, on_app_stop

@on_app_start
def initialize():
    print("App starting...")

@on_app_stop
def cleanup():
    print("App stopping...")
```

## 🔄 Migration Guide

### Old Pattern → New Pattern

#### Config Access
```python
# Old
dependency_manager.get_service(Config).database.host = "localhost"

# New
from SLM.core import config
config.database.host = "localhost"
# or
from SLM.core import Core
Core.config.database.host = "localhost"
```

#### Message Bus
```python
# Old
dependency_manager.get_service(MessageBus).publish("event")

# New
from SLM.core import bus
bus.publish("event")
# or
from SLM.core import Core
Core.bus.publish("event")
```

#### Component Registration
```python
# Old
class MyComponent(Component):
    pass

app.register_component(MyComponent())

# New
from SLM.core import component

@component(name="MyComponent")
class MyComponent(Component):
    pass
# Auto-registered!
```

## 🚀 Next Steps

### Phase 1: App Rewrite (Priority)
- [ ] Rewrite `app.py` to integrate `LifecycleManager`
- [ ] Add context manager support (`with App.context()`)
- [ ] Implement builder pattern (`App.builder()`)
- [ ] Add lifecycle hooks execution
- [ ] Connect decorator registries to app initialization

### Phase 2: Enhanced Features
- [ ] Add async support (optional)
- [ ] Implement hot reload capability
- [ ] Add configuration file loaders (JSON, YAML, TOML)
- [ ] Create CLI tool for app management
- [ ] Add health check system

### Phase 3: Testing & Documentation
- [ ] Create unit tests for all singletons
- [ ] Test lifecycle state transitions
- [ ] Test decorator functionality
- [ ] Write comprehensive API documentation
- [ ] Create migration guide for existing projects
- [ ] Add performance benchmarks

### Phase 4: Advanced Patterns
- [ ] Plugin auto-discovery
- [ ] Service auto-discovery
- [ ] Configuration validation with schemas
- [ ] Distributed configuration support
- [ ] Metrics and monitoring integration

## 🏗️ Architecture Benefits

### ✅ Pythonic Patterns
- **Metaclass singletons** - Thread-safe, proper Python pattern
- **Decorators** - Syntactic sugar for common tasks
- **Module-level access** - Clean, simple imports
- **Type hints** - Full IDE support and auto-injection

### ✅ Elegant API
- **No verbose calls** - `config.value` vs `manager.get_service(Config).value`
- **Property access** - `Core.config` vs `dependency_manager.get_service(Config)`
- **Auto-registration** - Decorators handle registration automatically
- **Event-driven** - Reactive configuration and messaging

### ✅ Developer Experience
- **IDE friendly** - Full autocomplete and type checking
- **Minimal boilerplate** - Decorators reduce code
- **Clear patterns** - Consistent access methods
- **Easy testing** - `reset_all()` for test isolation

## 📝 Notes

### Current Version: 2.0.0
- Complete rewrite with pythonic patterns
- Backward compatible with 1.x (during migration)
- All core managers are now singletons
- Decorator-based registration system
- Elegant module-level access

### Breaking Changes
- Core managers no longer need manual instantiation
- Configuration access is simplified
- Dependency injection now uses type hints
- Event subscriptions can use decorators

### Performance Considerations
- Singletons are lazy-initialized (created on first access)
- Thread-safe with minimal locking overhead
- Decorator registration happens at import time
- No performance penalty for elegant access patterns

## 🔧 Development Commands

### Run Examples
```bash
python -m SLM.core.examples.elegant_usage_example
```

### Test Singletons
```python
from SLM.core import config, Config, reset_all

# Test singleton behavior
c1 = config
c2 = Config()
assert c1 is c2  # Same instance

# Reset for testing
reset_all()
c3 = Config()
assert c1 is not c3  # New instance after reset
```

### Debug Mode
```python
from SLM.core import config
from loguru import logger

# Enable debug logging
logger.add("debug.log", level="DEBUG")

config.database.host = "localhost"  # Will log config changes
```

## 📚 Key Files

### Core Infrastructure
- `singleton.py` - Singleton metaclass and base class
- `lifecycle.py` - State machine and lifecycle management
- `decorators.py` - Decorator syntactic sugar
- `__init__.py` - Module-level access and exports

### Core Managers (Singletons)
- `config.py` - Configuration singleton
- `message_bus.py` - Event bus singleton
- `dependency.py` - Dependency injection singleton
- `component.py` - Component management singleton
- `plugin_system.py` - Plugin system singleton

### Examples
- `examples/elegant_usage_example.py` - Comprehensive patterns demo
- `examples/backend_example.py` - Backend/driver system example
- Other existing examples...

## ⚠️ Known Issues

### Type Checking
- Some Pylance warnings for dynamic attributes (decorators)
- Property access type inference limitations
- These don't affect runtime functionality

### Resolution
- Use `# type: ignore` comments where needed
- Type stubs could be added in future
- Dynamic attribute access is intentional design

---

**Status**: Core rewrite complete ✅  
**Next Priority**: App.py integration with lifecycle manager  
**Version**: 2.0.0  
**Date**: 2025-01-11
