# Design Patterns

## Table of Contents
1. [When to Use Design Patterns](#when-to-use-design-patterns)
2. [Behavioral Patterns](#behavioral-patterns)
3. [Creational Patterns](#creational-patterns)
4. [Structural Patterns](#structural-patterns)
5. [Choosing Between Patterns](#choosing-between-patterns)

---

## When to Use Design Patterns

Patterns build on design principles (Single Responsibility, Loose Coupling, Encapsulate What Varies, Open-Closed). Apply when you recognize a specific architectural problem — don't force patterns where simpler solutions work.

- **Algorithms that vary** → Template Method or Strategy
- **Object creation that varies** → Factory Method or Abstract Factory
- **Incompatible interfaces** → Adapter or Façade
- **Iterating over collections** → Iterator
- **Operations across a collection** → Visitor
- **Notifying dependents of changes** → Observer
- **State-dependent behavior** → State
- **Single instances** → Singleton (use cautiously)
- **Tree structures** → Composite
- **Dynamic responsibilities** → Decorator

---

## Behavioral Patterns

### Template Method

**Problem:** Multiple classes share algorithm structure but differ in specific steps.

**Solution:** Define the algorithm skeleton in a base class, deferring steps to subclasses.

```python
from abc import ABC, abstractmethod

class DataProcessor(ABC):
    def process(self, source):
        """Template method — defines the algorithm."""
        data = self.read(source)
        data = self.transform(data)
        self.output(data)

    @abstractmethod
    def read(self, source): ...

    @abstractmethod
    def transform(self, data): ...

    def output(self, data):
        """Default implementation — can be overridden."""
        print(data)

class CsvProcessor(DataProcessor):
    def read(self, source):
        return parse_csv(source)

    def transform(self, data):
        return clean_data(data)
```

### Strategy

**Problem:** Need to switch algorithms at runtime.

**Solution:** Encapsulate each algorithm in its own class/function; make them interchangeable.

```python
from typing import Callable

class Sorter:
    def __init__(self, strategy: Callable):
        self.strategy = strategy

    def sort(self, data):
        return self.strategy(data)

# In Python, strategies are often just functions
sorter = Sorter(strategy=sorted)
sorter = Sorter(strategy=lambda data: sorted(data, reverse=True))
```

**Template Method vs. Strategy:**
- Template Method uses inheritance — variant steps live in subclasses.
- Strategy uses composition — algorithm injected as object/function.
- Prefer Strategy when algorithms change at runtime or to avoid deep inheritance.

### Observer

**Problem:** A publisher must notify many subscribers of state changes w/o tight coupling.

**Solution:** Maintain a subscriber list; notify on changes.

```python
class EventEmitter:
    def __init__(self):
        self._listeners = {}

    def on(self, event, callback):
        self._listeners.setdefault(event, []).append(callback)

    def emit(self, event, *args, **kwargs):
        for callback in self._listeners.get(event, []):
            callback(*args, **kwargs)

# Usage
emitter = EventEmitter()
emitter.on("data", lambda d: print(f"Got: {d}"))
emitter.emit("data", "hello")
```

### State

**Problem:** Object behavior changes based on internal state → complex conditionals.

**Solution:** Encapsulate each state as a separate class w/ its own behavior.

```python
from abc import ABC, abstractmethod

class State(ABC):
    @abstractmethod
    def handle(self, context): ...

class IdleState(State):
    def handle(self, context):
        print("Starting...")
        context.state = ProcessingState()

class ProcessingState(State):
    def handle(self, context):
        print("Processing complete.")
        context.state = IdleState()

class Machine:
    def __init__(self):
        self.state = IdleState()

    def handle(self):
        self.state.handle(self)
```

### Iterator

**Problem:** Traverse different data structures w/ a uniform interface.

**Solution:** Implement `__iter__` and `__next__` (or use generator functions).

Python's iterator protocol is deeply integrated — `for` loops, unpacking, and comprehensions all use it. A generator function is usually simpler than a full iterator class.

### Visitor

**Problem:** Apply different operations across objects without modifying their classes.

**Solution:** Define the operation externally; each object "accepts" the visitor.

In Python, `functools.singledispatch` provides a lightweight visitor:

```python
from functools import singledispatch

@singledispatch
def serialize(obj):
    raise TypeError(f"Cannot serialize {type(obj)}")

@serialize.register
def _(obj: str):
    return f'"{obj}"'

@serialize.register
def _(obj: int):
    return str(obj)

@serialize.register
def _(obj: list):
    return "[" + ", ".join(serialize(item) for item in obj) + "]"
```

---

## Creational Patterns

### Factory Method

**Problem:** A class needs to create objects but shouldn't know the exact type in advance.

**Solution:** Define a method/classmethod that creates and returns the appropriate object.

```python
class Notification:
    def send(self, message): ...

class EmailNotification(Notification):
    def send(self, message):
        send_email(message)

class SMSNotification(Notification):
    def send(self, message):
        send_sms(message)

def create_notification(channel: str) -> Notification:
    """Factory function."""
    match channel:
        case "email": return EmailNotification()
        case "sms":   return SMSNotification()
        case _:       raise ValueError(f"Unknown channel: {channel}")
```

In Python, factory functions are often more natural than factory classes.

### Abstract Factory

**Problem:** Create families of related objects that must be used together.

**Solution:** Define an interface for creating each kind of object, w/ concrete factories per family. Use when multiple related products (e.g., UI widgets for different platforms) must be created consistently.

### Singleton

**Problem:** A class should have only one instance.

**Solution:** Use a module-level instance (simplest). Singletons introduce global state — dependency injection is usually better:

```python
# Module-level instance — simplest singleton approach
# config.py
_config = None

def get_config():
    global _config
    if _config is None:
        _config = Config()
    return _config
```

Use sparingly — singletons make testing harder and hide dependencies. Prefer passing instances via constructor injection.

---

## Structural Patterns

### Adapter

**Problem:** Need to use a class w/ an incompatible interface.

**Solution:** Wrap the incompatible class, translating its interface.

```python
class LegacyPrinter:
    def print_old_way(self, text):
        print(f"[LEGACY] {text}")

class PrinterAdapter:
    def __init__(self, legacy: LegacyPrinter):
        self._legacy = legacy

    def print(self, text):
        self._legacy.print_old_way(text)
```

### Façade

**Problem:** A subsystem has many classes and a complex interface.

**Solution:** Provide a simplified interface wrapping the subsystem.

```python
class VideoConverter:
    """Façade that simplifies the complex video processing subsystem."""
    def convert(self, filename, format):
        source = VideoFile(filename)
        codec = CodecFactory.extract(source)
        if format == "mp4":
            result = MPEG4Compressor().compress(codec)
        else:
            result = OGGCompressor().compress(codec)
        return result
```

### Composite

**Problem:** Treat individual objects and compositions uniformly.

**Solution:** Define a common interface for both leaves and containers.

```python
from abc import ABC, abstractmethod

class FileSystemItem(ABC):
    @abstractmethod
    def size(self) -> int: ...

class File(FileSystemItem):
    def __init__(self, name, size):
        self.name = name
        self._size = size

    def size(self):
        return self._size

class Directory(FileSystemItem):
    def __init__(self, name):
        self.name = name
        self.children = []

    def add(self, item: FileSystemItem):
        self.children.append(item)

    def size(self):
        return sum(child.size() for child in self.children)
```

### Decorator (the pattern, not Python's `@decorator` syntax)

**Problem:** Add responsibilities to objects dynamically, without subclassing.

**Solution:** Wrap objects in decorator objects that add behavior before/after delegating.

Python's `@decorator` syntax is related but distinct: the design pattern wraps instances; Python decorators wrap functions/classes at definition time.

---

## Choosing Between Patterns

| If you need to... | Consider... |
|-------------------|-------------|
| Vary steps in an algorithm | Template Method (inheritance) or Strategy (composition) |
| Create objects w/o specifying exact class | Factory Method |
| Create families of related objects | Abstract Factory |
| Notify multiple objects of changes | Observer |
| Vary behavior based on object state | State |
| Traverse collections uniformly | Iterator (Python's built-in protocol) |
| Apply different operations to a collection | Visitor or `singledispatch` |
| Integrate incompatible interfaces | Adapter |
| Simplify a complex subsystem | Façade |
| Treat individuals and groups uniformly | Composite |
| Add behavior dynamically | Decorator pattern |
| Ensure only one instance | Singleton (prefer DI instead) |

### Python-specific notes

Many classic OOP patterns are simpler in Python due to first-class functions, duck typing, and built-in protocols. Before reaching for a full implementation:

- **Strategy** → Often just a function parameter
- **Iterator** → Generator function or `__iter__`/`__next__`
- **Visitor** → `functools.singledispatch`
- **Observer** → Simple callback lists or `signal` pattern
- **Singleton** → Module-level instance or `functools.cache`
- **Factory** → Factory function (no need for factory classes)
- **Command** → Closures or `functools.partial`
