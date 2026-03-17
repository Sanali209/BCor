# Classes and Design

## Table of Contents
1. [Core Design Principles](#core-design-principles)
2. [Dataclasses](#dataclasses)
3. [Properties and Attributes](#properties-and-attributes)
4. [Inheritance](#inheritance)
5. [Composition and Mix-ins](#composition-and-mix-ins)
6. [Protocols and Duck Typing](#protocols-and-duck-typing)
7. [Metaclass Features](#metaclass-features)
8. [When to Use Classes vs Other Approaches](#when-to-use-classes-vs-other-approaches)

---

## Core Design Principles

### Single Responsibility Principle

A class should have one responsibility. If you can't describe it in one sentence without "and", split it.

```python
# Too many responsibilities
class Automobile:
    def accelerate(self): ...
    def wash_car(self): ...
    def change_oil(self): ...
    def vacuum_interior(self): ...

# Better — separate concerns
class Engine:
    def start(self): ...
    def accelerate(self): ...

class MaintenanceService:
    def change_oil(self, car): ...
    def rotate_tires(self, car): ...
```

### Principle of Least Knowledge (Loose Coupling)

Classes should know as little as possible about each other's internals. Minimize dependencies by:
- Making instance variables private (prefix w/ `_`)
- Exposing only necessary public methods and properties
- Using delegation — let a specialized class handle its own logic

### Encapsulate What Varies

Separate code that changes from code that stays stable. Put the varying part in its own class or function → only the encapsulated part needs updating when requirements change.

### Open-Closed Principle

Classes should be open for extension but closed for modification. Add new behavior via subclasses, composition, or configuration without changing existing code.

### Don't Surprise Your Users (Principle of Least Astonishment)

- Methods should do what their names suggest
- Avoid hidden side effects
- Properties should be fast — no I/O, no expensive computation; use methods for heavy work
- Be consistent w/ Python conventions (e.g., `__len__` returns int, `__bool__` returns bool)

---

## Dataclasses

Preferred way to create lightweight structured classes:

```python
from dataclasses import dataclass, field

@dataclass
class Point:
    x: float
    y: float
    label: str = ""

@dataclass
class Config:
    host: str
    port: int = 8080
    tags: list[str] = field(default_factory=list)
```

### What you get automatically

- `__init__` w/ all fields as parameters
- `__repr__` showing all field values
- `__eq__` comparing all fields
- Type annotations for documentation and static analysis

### Immutable dataclasses

```python
@dataclass(frozen=True)
class Coordinate:
    latitude: float
    longitude: float
```

`frozen=True` makes instances hashable (usable as dict keys / set members) and prevents accidental mutation. Prefer frozen dataclasses for value objects.

### When to use dataclasses vs other options

| Need | Use |
|------|-----|
| Simple data container w/ named fields | `@dataclass` |
| Immutable value object | `@dataclass(frozen=True)` |
| Custom validation in __init__ | `@dataclass` w/ `__post_init__` |
| Legacy code or very simple case | `NamedTuple` |
| Complex behavior, methods, state machines | Regular class |
| Grouping a few items temporarily | Tuple or dict |

---

## Properties and Attributes

### Start with simple public attributes

Don't write Java-style getters/setters. Start w/ plain attributes; use `@property` only when adding behavior:

```python
# Start simple
class Circle:
    def __init__(self, radius):
        self.radius = radius

# Later, add validation without changing the interface
class Circle:
    def __init__(self, radius):
        self.radius = radius  # Uses the setter

    @property
    def radius(self):
        return self._radius

    @radius.setter
    def radius(self, value):
        if value < 0:
            raise ValueError("Radius cannot be negative")
        self._radius = value
```

### Computed properties

```python
@property
def area(self):
    return math.pi * self._radius ** 2
```

Properties should be fast. If expensive, use a method w/ a verb name like `calculate_area()` to signal work.

### Descriptors for reusable property logic

When you need the same validation on multiple attributes, use a descriptor:

```python
class Positive:
    def __set_name__(self, owner, name):
        self.name = name
        self.private_name = f"_{name}"

    def __get__(self, obj, objtype=None):
        return getattr(obj, self.private_name)

    def __set__(self, obj, value):
        if value < 0:
            raise ValueError(f"{self.name} must be positive")
        setattr(obj, self.private_name, value)

class Rectangle:
    width = Positive()
    height = Positive()

    def __init__(self, width, height):
        self.width = width
        self.height = height
```

---

## Inheritance

### Use `super()` to initialize parent classes

Always call `super().__init__()` — it correctly handles Python's MRO, including diamond inheritance:

```python
class Animal:
    def __init__(self, name):
        self.name = name

class Pet(Animal):
    def __init__(self, name, owner):
        super().__init__(name)
        self.owner = owner
```

### The Liskov Substitution Principle

A subclass must be usable wherever its parent is expected without breaking the program:
- Don't weaken preconditions (don't reject inputs the parent accepts)
- Don't strengthen postconditions in surprising ways
- Don't remove or break methods the parent defines

### Prefer public attributes over private ones

- `_single_underscore` → protected (convention: "don't touch from outside")
- `__double_underscore` (name mangling) → use **only** to avoid naming conflicts w/ subclasses you don't control
- Don't use private attributes to "protect" code — plan for extension; document protected fields to guide subclasses

### Overriding vs overloading

- **Override**: Subclass redefines a parent method w/ the same signature
- **Overload**: Multiple methods w/ same name but different parameter types (Python doesn't natively support this; `functools.singledispatch` and `multimethod` package provide it)

---

## Composition and Mix-ins

### Prefer composition over inheritance

Inheritance creates tight coupling. Composition is more flexible:

```python
# Inheritance — tight coupling
class DatabaseLogger(Database, Logger):
    ...

# Composition — loose coupling
class Service:
    def __init__(self, db: Database, logger: Logger):
        self.db = db
        self.logger = logger
```

### Mix-in classes

Mix-ins add reusable functionality without being standalone classes:

```python
class SerializableMixin:
    def to_dict(self):
        return {k: v for k, v in self.__dict__.items()
                if not k.startswith("_")}

class TimestampMixin:
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.created_at = datetime.now()

class User(TimestampMixin, SerializableMixin):
    def __init__(self, name, email):
        super().__init__()
        self.name = name
        self.email = email
```

Mix-in rules:
- Avoid instance attributes in mix-ins when possible; always call `super().__init__()` if used
- Mix-ins should add specific, focused behavior
- They compose well — unlike metaclasses, multiple class decorators and mix-ins combine without conflicts

---

## Protocols and Duck Typing

### Duck typing

Python favors duck typing: if an object has the right methods, it works regardless of class hierarchy:

```python
# This works with any object that has a .read() method
def process(source):
    data = source.read()
    ...
```

### Structural typing with `typing.Protocol`

Use `Protocol` to formalize duck typing w/ static type checking:

```python
from typing import Protocol

class Readable(Protocol):
    def read(self) -> str: ...

class Closeable(Protocol):
    def close(self) -> None: ...

class ReadableAndCloseable(Readable, Closeable, Protocol):
    ...

def process(source: Readable) -> str:
    """Accepts any object with a .read() method — no inheritance required."""
    return source.read()
```

Protocols are checked structurally (not nominally) — any class w/ a matching `read() -> str` satisfies `Readable` without inheriting from it.

### Accept functions for simple interfaces

If an interface is just one method, accept a callable instead of requiring a class:

```python
# Simple — just pass a function
def sort_with_key(items, key_func):
    return sorted(items, key=key_func)

# Only use a class when you need to maintain state
class RunningAverage:
    def __init__(self):
        self.total = 0
        self.count = 0

    def __call__(self, value):
        self.total += value
        self.count += 1
        return self.total / self.count
```

### Custom containers

Inherit from `collections.abc` classes (`Mapping`, `Sequence`, `MutableMapping`, etc.) to ensure custom containers implement all required methods:

```python
from collections.abc import Sequence

class CardDeck(Sequence):
    def __init__(self, cards):
        self._cards = list(cards)

    def __getitem__(self, index):
        return self._cards[index]

    def __len__(self):
        return len(self._cards)
    # Sequence provides __contains__, __iter__, __reversed__, index, count
```

---

## Metaclass Features

Powerful but use sparingly. Prefer simpler alternatives when possible.

### `__init_subclass__` (preferred over metaclasses)

Validate or register subclasses at definition time:

```python
class Plugin:
    _registry = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        Plugin._registry[cls.__name__] = cls
```

### `__set_name__` for descriptors

Automatically captures the attribute name when a descriptor is assigned to a class.

### Class decorators (preferred over metaclasses for extensions)

```python
def add_logging(cls):
    for name, method in vars(cls).items():
        if callable(method) and not name.startswith("_"):
            setattr(cls, name, log_calls(method))
    return cls
```

Class decorators compose easily; metaclasses don't.

### `__getattr__` and `__getattribute__`

- `__getattr__` — called only when normal lookup fails; good for lazy loading
- `__getattribute__` — called on every attribute access; use sparingly; call `super().__getattribute__()` to avoid infinite recursion

---

## When to Use Classes vs Other Approaches

| Situation | Approach |
|-----------|----------|
| Simple data container | `@dataclass` or `NamedTuple` |
| Single behavior / stateless | Plain function |
| Stateful behavior | Class w/ methods |
| Callable w/ state | Class w/ `__call__` |
| Multiple implementations of same interface | ABC + subclasses |
| Adding behavior to existing classes | Class decorator or mix-in |
| Simple polymorphism based on type | `functools.singledispatch` |
| Configuration or settings | `@dataclass(frozen=True)` |

Don't reach for classes when a function, dict, or dataclass will do. Classes shine when you need to bundle **state and behavior** together.

---

## Programming by Contract

Design by Contract uses preconditions, postconditions, and invariants to define a method's obligations and guarantees.

### Preconditions

What must be true **before** calling a method (caller's responsibility):

```python
def withdraw(self, amount):
    """Withdraw from account.

    Precondition: amount > 0 and amount <= self.balance
    """
    if amount <= 0 or amount > self.balance:
        raise ValueError(f"Invalid withdrawal: {amount}")
    self.balance -= amount
```

### Postconditions

What must be true **after** a method returns (method's guarantee):

```python
def deposit(self, amount):
    old_balance = self.balance
    self.balance += amount
    assert self.balance == old_balance + amount  # Postcondition
```

### Class invariants

Properties that must remain true for all instances at all times (e.g., a circular buffer's count is always between 0 and capacity). Verify invariants after any state-modifying operation during development.

### Subclass contracts (Liskov Substitution)

When overriding methods in subclasses:
- A subclass **must not strengthen preconditions** (must accept everything the parent accepts)
- A subclass **must not weaken postconditions** (must guarantee at least what the parent guarantees)

---

## Iterative Design Process

Well-designed code rarely emerges in one pass:

1. **Start w/ cohesive classes** — each w/ a single clear responsibility
2. **Encapsulate what varies** — when changes leak between classes, isolate varying parts into their own class
3. **Delegate** — move functionality to the class where it naturally belongs
4. **Test** — verify correctness after each change
5. **Backtrack** when needed — recognizing a bad design decision and reverting is maturity, not failure

Don't aim for perfection in the first iteration. First version should work and be tested. Subsequent iterations improve design. An MVP w/ clean design beats a feature-complete mess.

### Code to the Interface

Program against abstractions (base classes, protocols), not concrete implementations → makes code flexible enough to swap implementations without changing callers:

```python
# Depend on the interface, not the implementation
def process_data(source: DataSource):  # Abstract
    data = source.read()
    return transform(data)
```

Use factory functions to create the right concrete implementation at runtime.
