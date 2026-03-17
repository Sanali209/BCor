# Data Structures

## Table of Contents
1. [Quick Selection Guide](#quick-selection-guide)
2. [Lists](#lists)
3. [Tuples](#tuples)
4. [Dictionaries](#dictionaries)
5. [Sets](#sets)
6. [Specialized Collections](#specialized-collections)
7. [Sorting and Searching](#sorting-and-searching)
8. [Bytes and Bytearray](#bytes-and-bytearray)

---

## Quick Selection Guide

| Need | Use | Why |
|------|-----|-----|
| Ordered, mutable sequence | `list` | Fast append, index access |
| Immutable record / fixed fields | `tuple` or `NamedTuple` | Hashable, lightweight |
| Structured data w/ named fields | `dataclass` | Clear, type-hinted, customizable |
| Key-value mapping | `dict` | O(1) lookup, insertion-ordered (3.7+) |
| Membership testing | `set` | O(1) `in` checks |
| FIFO queue | `collections.deque` | O(1) append and popleft |
| Priority queue | `heapq` | O(log n) push/pop |
| Counting items | `collections.Counter` | Built-in tallying |
| Default values for missing keys | `collections.defaultdict` | Cleaner than `setdefault` |
| Precise decimals | `decimal.Decimal` | No floating-point rounding |

---

## Lists

Key operations and costs:

| Operation | Time | Notes |
|-----------|------|-------|
| `append(x)` | O(1) amortized | Add to end |
| `insert(i, x)` | O(n) | Shifts elements |
| `pop()` | O(1) | Remove from end |
| `pop(0)` | O(n) | Use `deque` for queues |
| `x in list` | O(n) | Use `set` for frequent lookups |
| `list[i]` | O(1) | Direct index access |
| `sort()` | O(n log n) | In-place; `sorted()` for new list |

### Slicing
- Omit obvious defaults: `a[:5]` not `a[0:5]`, `a[3:]` not `a[3:len(a)]`
- Slicing forgives out-of-bounds indices
- Assigning to a slice replaces that range (lengths can differ)
- Avoid combining stride and slice in one expression — split into two steps

### Copying
- `a[:]` or `list(a)` or `a.copy()` → **shallow copy** (new list, same element refs)
- `copy.deepcopy(a)` → copies everything recursively; use when elements are mutable

### List vs. tuple

Use **tuples** when:
- Data is a fixed record (coordinates, RGB, person fields)
- You need the value as a dict key or set member (tuples are hashable if contents are)
- You want to signal immutability

Use **lists** when:
- The collection changes (appending, removing, sorting)
- Items are homogeneous and of variable length

---

## Tuples

Immutable sequences. Single-element tuples need a trailing comma:

```python
single = ("hello",)    # Tuple
not_a_tuple = ("hello") # Just a string in parentheses
```

### Named tuples

```python
from collections import namedtuple
Point = namedtuple("Point", ["x", "y"])
p = Point(3, 4)
print(p.x, p.y)
```

Or use `typing.NamedTuple` for type-hinted versions:

```python
from typing import NamedTuple

class Point(NamedTuple):
    x: float
    y: float
```

For most structured data, **prefer `dataclasses`** — more flexible, support defaults, methods, and immutability via `frozen=True`.

---

## Dictionaries

Since Python 3.7, dicts maintain **insertion order**. `collections.OrderedDict` remains useful for order-aware equality or `move_to_end()`.

### Handling missing keys

```python
# Prefer get() for simple defaults
value = d.get(key, default_value)

# For accumulation patterns, use defaultdict
from collections import defaultdict
groups = defaultdict(list)
for item in items:
    groups[item.category].append(item)

# For expensive defaults that depend on the key, use __missing__
class KeyDependentDefault(dict):
    def __missing__(self, key):
        value = expensive_computation(key)
        self[key] = value
        return value
```

Avoid `setdefault` when the default is expensive to create — it's always constructed even when not needed.

### Merging dicts

```python
# Python 3.9+
merged = dict_a | dict_b           # New dict
dict_a |= dict_b                   # In-place update

# Earlier versions
merged = {**dict_a, **dict_b}
```

### Dict comprehensions

```python
flipped = {v: k for k, v in original.items()}
filtered = {k: v for k, v in data.items() if v > threshold}
```

### Avoid deeply nested dicts

When bookkeeping gets complicated, move to **dataclasses** or proper classes. Deeply nested dicts are hard to read, lack type safety, and are error-prone.

---

## Sets

O(1) membership testing and automatic deduplication.

```python
# Set operations
union = a | b
intersection = a & b
difference = a - b
symmetric_diff = a ^ b
is_subset = a <= b
```

Use `frozenset` for an immutable, hashable set (e.g., as a dict key).

---

## Specialized Collections

### `collections.Counter`

```python
from collections import Counter
word_counts = Counter(words)
top_three = word_counts.most_common(3)
```

### `collections.deque`

Double-ended queue w/ O(1) operations on both ends:

```python
from collections import deque
q = deque(maxlen=100)  # Optional bounded size
q.append(x)      # Add to right
q.appendleft(x)  # Add to left
q.pop()           # Remove from right
q.popleft()       # Remove from left
```

Use `deque` instead of `list` for producer-consumer queues. `list.pop(0)` is O(n); `deque.popleft()` is O(1).

### `heapq` for priority queues

```python
import heapq

heap = []
heapq.heappush(heap, (priority, item))
priority, item = heapq.heappop(heap)  # Pops lowest priority
```

Items must be naturally sortable (define `__lt__` for custom classes), or wrap in tuples where the first element is the priority.

### `itertools` highlights
- `chain(*iterables)` — flatten multiple iterables into one
- `islice(iterable, stop)` — slice an iterator without materializing
- `groupby(iterable, key)` — group consecutive items (data must be pre-sorted by key)
- `product`, `permutations`, `combinations` — combinatoric iterators
- `accumulate(iterable)` — running totals

---

## Sorting and Searching

### The `key` parameter

Both `sort()` (in-place) and `sorted()` (returns new list) accept a `key` function:

```python
# Sort by multiple criteria using tuples
students.sort(key=lambda s: (s.grade, s.name))

# Reverse individual criteria with negation (numeric) or multiple passes
students.sort(key=lambda s: s.name)           # Secondary sort first
students.sort(key=lambda s: s.grade, reverse=True)  # Primary sort last
```

### `sort()` vs `sorted()`
- `sort()` modifies in place, returns `None`. Max performance, minimal memory.
- `sorted()` works on any iterable, returns new list, never mutates input.

### Binary search w/ `bisect`

For sorted sequences, `bisect` is orders of magnitude faster than linear scan:

```python
import bisect
index = bisect.bisect_left(sorted_list, target)
```

---

## Bytes and Bytearray
- `bytes` — immutable sequence of ints 0–255. Created w/ `b"..."` literals.
- `bytearray` — mutable version of `bytes`.
- Use `str.encode()` and `bytes.decode()` for conversion (always specify encoding explicitly).
- For zero-copy operations on large binary data, use `memoryview`.

### Encoding best practice

Always be explicit about encoding. Default to UTF-8:

```python
text = "hello"
data = text.encode("utf-8")
back = data.decode("utf-8")
```

Helper for accepting both `str` and `bytes`:

```python
def to_str(value):
    if isinstance(value, bytes):
        return value.decode("utf-8")
    return value
```

---

## Dates and Times

### Use `datetime`, not `time`, for anything involving time zones

```python
from datetime import datetime, timedelta, date
from zoneinfo import ZoneInfo

# Current time in UTC
now_utc = datetime.now(ZoneInfo("UTC"))

# Convert to local
now_amsterdam = now_utc.astimezone(ZoneInfo("Europe/Amsterdam"))

# Arithmetic
tomorrow = date.today() + timedelta(days=1)
```

### Key rules
- **Always store and compute in UTC.** Convert to local only at display layer.
- Use `zoneinfo` (3.9+) for timezone handling — avoid `time` module for conversions.
- `strftime` → format dates to strings; `strptime` → parse strings to dates.
- For complex date work, consider `pendulum` or `arrow`.

### Formatting/parsing

```python
# Format
now.strftime("%Y-%m-%d %H:%M:%S")  # "2025-03-02 14:30:00"

# Parse
dt = datetime.strptime("2025-03-02", "%Y-%m-%d")
```

---

## File Handling

### Reading and writing

```python
# Text files — always use 'with' for automatic cleanup
with open("data.txt", "r", encoding="utf-8") as f:
    content = f.read()       # Whole file as string
    # or: lines = f.readlines()
    # or: for line in f:     # Iterator — memory efficient

with open("output.txt", "w", encoding="utf-8") as f:
    f.write("hello\n")

# Binary files
with open("image.png", "rb") as f:
    data = f.read()
```

### Pathlib (preferred over os.path)

```python
from pathlib import Path

p = Path("data") / "subdir" / "file.txt"
p.exists()
p.is_file()
p.is_dir()
p.suffix          # ".txt"
p.stem            # "file"
p.parent          # Path("data/subdir")
p.read_text()     # Read entire file
p.write_text("content")
p.mkdir(parents=True, exist_ok=True)

# Globbing
for py_file in Path(".").rglob("*.py"):
    print(py_file)
```

Prefer `pathlib.Path` over `os.path` for all new code — more readable and object-oriented.

---

## Serialization Formats

### JSON

```python
import json

# Serialize
json_str = json.dumps(data, indent=2, default=str)  # default=str handles datetimes etc.

# Deserialize
data = json.loads(json_str)

# File I/O
with open("data.json", "w") as f:
    json.dump(data, f, indent=2)

with open("data.json") as f:
    data = json.load(f)
```

For custom objects, provide a `default` function or implement a custom encoder.

### CSV

```python
import csv

# Reading
with open("data.csv") as f:
    reader = csv.DictReader(f)  # Rows as dicts with header keys
    for row in reader:
        print(row["name"], row["age"])

# Writing
with open("output.csv", "w", newline="") as f:
    writer = csv.DictWriter(f, fieldnames=["name", "age"])
    writer.writeheader()
    writer.writerow({"name": "Alice", "age": 30})
```

### TOML (Python 3.11+)

```python
import tomllib  # Read-only, built-in since 3.11

with open("config.toml", "rb") as f:
    config = tomllib.load(f)
```

### YAML

Use `yaml.safe_load()` — **never** `yaml.load()` w/ untrusted data (security risk):

```python
import yaml

with open("config.yaml") as f:
    config = yaml.safe_load(f)
```

### pickle

Only use between trusted programs — pickle can execute arbitrary code during deserialization. Use `copyreg` for backward-compatible serialization when class definitions change.

---

## Databases (Quick Reference)

### SQLite (built-in, zero config)

```python
import sqlite3

conn = sqlite3.connect("app.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (id INTEGER PRIMARY KEY, name TEXT)")
cursor.execute("INSERT INTO users (name) VALUES (?)", ("Alice",))
conn.commit()

rows = cursor.execute("SELECT * FROM users").fetchall()
conn.close()
```

Always use parameterized queries (`?` placeholders) — never string formatting for SQL.

### SQLAlchemy (for production)

Three layers: Engine (raw SQL), Expression Language (Pythonic SQL), and ORM (full object mapping). Start w/ the ORM for most projects.

### Redis

In-memory data structure server for caching, queues, pub/sub. Supports strings, lists, hashes, sets, and sorted sets. Python client: `redis-py`.
