# Pythonic Idioms

## Table of Contents
1. [Style and Formatting](#style-and-formatting)
2. [Variables and Assignment](#variables-and-assignment)
3. [String Handling](#string-handling)
4. [Truthiness and Conditionals](#truthiness-and-conditionals)
5. [Unpacking and Iteration](#unpacking-and-iteration)
6. [Comprehensions](#comprehensions)
7. [The Walrus Operator](#the-walrus-operator)
8. [Match Statements](#match-statements)
9. [Import Conventions](#import-conventions)
10. [Regular Expressions](#regular-expressions)
11. [Common Anti-Patterns](#common-anti-patterns)

---

## Style and Formatting

### PEP 8 essentials
- **4 spaces** per indent (never tabs)
- Max **79 characters** per line
- **Two blank lines** between top-level definitions; **one** between methods
- Dict colons: no space before, one space after
- **One space** around `=` in assignments; no space in keyword args/defaults
- Type annotations: no space before colon, space before the type

### Naming conventions

| Element | Style | Example |
|---------|-------|---------|
| Functions, variables, attributes | `lowercase_underscore` | `get_user_name` |
| Protected instance attributes | `_leading_underscore` | `_internal_cache` |
| Private instance attributes | `__double_leading` | `__secret_key` |
| Classes and exceptions | `CapitalizedWord` | `HttpClient` |
| Module-level constants | `ALL_CAPS` | `MAX_RETRIES` |
| Instance method first param | `self` | — |
| Class method first param | `cls` | — |

### Automation

Use `black` for formatting and `ruff` (or `pylint`) for linting.

---

## Variables and Assignment

### Multiple-assignment unpacking over indexing

```python
# Prefer this
name, age, city = person_tuple

# Over this
name = person_tuple[0]
age = person_tuple[1]
city = person_tuple[2]
```

Works w/ any iterable; can be nested.

### Catch-all unpacking w/ starred expressions

`*` captures remaining items — clearer and safer than slicing:

```python
first, *middle, last = scores
oldest, second_oldest, *rest = sorted(people, key=lambda p: p.age)
```

The starred variable always becomes a list (possibly empty).

### Swap without temporaries

```python
a, b = b, a
```

### Avoid mutable default values

Mutable defaults (list, dict) are created once at definition time and shared across calls:

```python
# WRONG — the same list is reused across calls
def add_item(item, items=[]):
    items.append(item)
    return items

# CORRECT
def add_item(item, items=None):
    if items is None:
        items = []
    items.append(item)
    return items
```

---

## String Handling

### Prefer f-strings

```python
name = "Alice"
age = 30
print(f"{name} is {age} years old")
print(f"Debug: {name!r}")  # Uses repr()
print(f"Pi is approximately {3.14159:.2f}")
```

Avoid `%`-style formatting (error-prone w/ tuples) and `str.format()` (verbose).

### Use explicit concatenation in lists

Adjacent string literals silently merge → can mask bugs (e.g. missing comma):

```python
# Dangerous — missing comma silently concatenates
names = [
    "Alice"
    "Bob",    # This becomes "AliceBob" — a silent bug
    "Charlie",
]

# Safe — explicit concatenation
long_string = (
    "This is a very long string that "
    + "spans multiple lines"
)
```

### `repr` vs. `str`

- `str()` / `__str__` → human-readable output
- `repr()` / `__repr__` → unambiguous developer representation (ideally `eval()`-able)
- In f-strings: `{x}` uses `str`, `{x!r}` uses `repr`

Always define `__repr__`. Define `__str__` only when you need a separate human-facing form.

---

## Truthiness and Conditionals

### Falsy values

`False`, `None`, `0`, `0.0`, `""`, `b""`, `[]`, `()`, `{}`, `set()`, `frozenset()`, and any object whose `__bool__` returns `False` or `__len__` returns `0`.

### Test emptiness idiomatically

```python
# Prefer
if not items:
    ...
if items:
    ...

# Avoid
if len(items) == 0:
    ...
```

### Use inline negation

```python
# Prefer
if a is not b:
    ...

# Avoid
if not a is b:
    ...
```

### Conditional expressions (ternary)

Use for simple inline logic only:

```python
status = "active" if user.is_active else "inactive"
```

Don't nest ternaries — extract a helper function instead.

---

## Unpacking and Iteration

### Prefer `enumerate` over `range(len(...))`

```python
# Prefer
for i, item in enumerate(items):
    print(f"{i}: {item}")

# With a starting index
for i, item in enumerate(items, start=1):
    ...
```

### Use `zip` for parallel iteration

```python
for name, score in zip(names, scores):
    print(f"{name}: {score}")
```

`zip` stops at the shortest iterable. Use `zip(a, b, strict=True)` (3.10+) to raise `ValueError` on length mismatch. For padding → `itertools.zip_longest`.

### Never modify containers while iterating

```python
# WRONG
for item in items:
    if should_remove(item):
        items.remove(item)

# CORRECT — iterate over a copy
for item in items[:]:
    if should_remove(item):
        items.remove(item)

# CORRECT — build a new list
items = [item for item in items if not should_remove(item)]
```

### Don't use loop variables after the loop

The loop variable leaks into enclosing scope but won't exist if the loop never executed. Relying on it is fragile.

### Avoid `else` blocks after loops

`else` after `for`/`while` runs when the loop completes without `break`. Unintuitive — use a flag or helper function instead.

### Use `any()` and `all()` for short-circuit logic

```python
has_negative = any(x < 0 for x in numbers)
all_positive = all(x > 0 for x in numbers)
```

Pass generator expressions (not list comprehensions) to preserve short-circuiting.

---

## Comprehensions

### Prefer comprehensions over `map`/`filter`

```python
# Clear
squares = [x**2 for x in range(10)]
evens = [x for x in numbers if x % 2 == 0]

# Less clear
squares = list(map(lambda x: x**2, range(10)))
```

### Limit to two control subexpressions

More than two `for`/`if` clauses → unreadable. Extract a helper or use nested loops.

### Use generator expressions for large data

Generators produce values lazily, avoiding full materialization:

```python
total = sum(x**2 for x in range(1_000_000))
```

Generators can be chained:
```python
roots = (x**0.5 for x in values)
rounded = (round(r, 2) for r in roots)
```

### Dict and set comprehensions

```python
name_to_age = {name: age for name, age in pairs}
unique_lengths = {len(word) for word in words}
```

---

## The Walrus Operator

`:=` assigns and evaluates in one expression, reducing repetition:

```python
# Without walrus
match = pattern.search(text)
if match:
    process(match)

# With walrus
if match := pattern.search(text):
    process(match)
```

Useful in comprehension conditions:
```python
results = [y for x in data if (y := expensive(x)) > threshold]
```

Variables assigned by `:=` inside comprehensions **leak** into enclosing scope (unlike loop variables, which don't).

---

## Match Statements

Use `match`/`case` for destructuring complex/heterogeneous data. Avoid for simple value comparisons where `if/elif` is clearer.

```python
match command:
    case ["quit"]:
        exit()
    case ["go", direction]:
        move(direction)
    case ["pick", "up", item]:
        pick_up(item)
    case _:
        print("Unknown command")
```

Key gotchas:
- Bare names in `case` are **capture patterns**, not value comparisons. Use dotted names (`Status.ACTIVE`) or guards (`case x if x == expected`) for value matching.
- Pattern matching works w/ built-in types, dataclasses, and custom classes, each w/ unique semantics.

### Match w/ dataclasses

```python
from dataclasses import dataclass

@dataclass
class Click:
    x: int
    y: int

@dataclass
class KeyPress:
    key: str

def handle(event):
    match event:
        case Click(x=x, y=y) if x > 100:
            handle_right_area(x, y)
        case Click(x=x, y=y):
            handle_left_area(x, y)
        case KeyPress(key="q"):
            quit()
        case KeyPress(key=k):
            handle_key(k)
```

---

## Import Conventions
- All imports at the **top of the file**
- Use **absolute imports**: `from mypackage import mymodule`
- Order: stdlib → third-party → your own, separated by blank lines
- Avoid `from module import *` — pollutes namespace, hides origins
- For expensive imports that slow startup, consider dynamic imports inside functions

---

## Regular Expressions

Key `re` module functions:

```python
import re

# match — checks only at the beginning of the string
m = re.match(r'pattern', text)

# search — finds first match anywhere in the string
m = re.search(r'pattern', text)

# findall — returns all non-overlapping matches as a list
matches = re.findall(r'pattern', text)

# sub — replace matches
result = re.sub(r'pattern', 'replacement', text)

# split — split at matches
parts = re.split(r'pattern', text)
```

### Practical patterns

```python
# Named groups for extraction
m = re.search(r'(?P<year>\d{4})-(?P<month>\d{2})-(?P<day>\d{2})', text)
if m:
    year = m.group('year')

# Compile patterns you reuse for performance
EMAIL_RE = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
matches = EMAIL_RE.findall(document)
```

Always use raw strings (`r'...'`) for patterns to avoid backslash conflicts.

### Common specifiers

| Pattern | Matches |
|---------|---------|
| `\d` | Digit (0-9) |
| `\w` | Word character (letter, digit, underscore) |
| `\s` | Whitespace |
| `.` | Any character except newline |
| `*` | Zero or more |
| `+` | One or more |
| `?` | Zero or one |
| `{n,m}` | Between n and m repetitions |
| `[abc]` | Character class |
| `^` / `$` | Start / end of string |

---

## Common Anti-Patterns

| Anti-pattern | Better approach |
|--------------|----------------|
| Complex one-liner expressions | Extract into a helper function |
| Checking `type(x) == SomeType` | Use `isinstance(x, SomeType)` |
| Bare `except:` | Catch specific exceptions |
| `if len(seq) == 0` | `if not seq` |
| Using `range(len(items))` to iterate | `enumerate(items)` |
| Returning `None` to signal errors | Raise an exception |
| Mutable default arguments | Use `None` and initialize inside the function |
| String accumulation in a loop w/ `+=` | Use `"".join(parts)` |
| Deep nesting of dicts/lists/tuples | Use dataclasses or named tuples |
| Global variables for shared state | Pass state explicitly or use classes |
