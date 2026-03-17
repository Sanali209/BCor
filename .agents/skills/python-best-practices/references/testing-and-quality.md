# Testing and Quality

Python defers nearly all error checking to runtime. Testing, type hints, linting, and debugging are your safety net.

## Table of Contents
1. [Testing Strategy](#testing-strategy)
2. [Writing Tests](#writing-tests)
3. [Mocking](#mocking)
4. [Type Hints and Static Analysis](#type-hints-and-static-analysis)
5. [Debugging](#debugging)
6. [Profiling and Performance](#profiling-and-performance)
7. [Code Quality Tools](#code-quality-tools)
8. [Packaging and Collaboration](#packaging-and-collaboration)

---

## Testing Strategy

### Prefer integration tests

Python's dynamic nature makes integration tests the best (sometimes only) way to gain correctness confidence. Unit tests complement them for edge cases and boundary conditions.

- **Integration tests** → verify multiple components work together
- **Unit tests** → verify individual components in isolation; best for complex logic w/ many edge cases

### Test organization

```python
# test_calculator.py
import unittest

class TestCalculator(unittest.TestCase):
    def setUp(self):
        """Called before each test method."""
        self.calc = Calculator()

    def tearDown(self):
        """Called after each test method."""
        self.calc.close()

    def test_add_positive_numbers(self):
        self.assertEqual(self.calc.add(2, 3), 5)

    def test_add_negative_numbers(self):
        self.assertEqual(self.calc.add(-1, -1), -2)

    def test_divide_by_zero_raises(self):
        with self.assertRaises(ZeroDivisionError):
            self.calc.divide(1, 0)
```

### Data-driven tests with `subTest`

Reduce boilerplate for parameterized tests:

```python
def test_is_palindrome(self):
    cases = [
        ("racecar", True),
        ("hello", False),
        ("", True),
        ("a", True),
    ]
    for word, expected in cases:
        with self.subTest(word=word):
            self.assertEqual(is_palindrome(word), expected)
```

### Module-level setup

Use `setUpModule` / `tearDownModule` for expensive one-time setup (e.g., starting a test database):

```python
def setUpModule():
    global test_db
    test_db = start_test_database()

def tearDownModule():
    test_db.stop()
```

### Floating-point testing

```python
self.assertAlmostEqual(result, expected, places=5)
self.assertAlmostEqual(result, expected, delta=0.001)
```

Never use `assertEqual` for float comparisons — rounding makes exact comparisons flaky.

---

## Writing Tests

### pytest (the modern standard)

```python
# test_example.py
import pytest

def test_basic():
    assert calculate(2, 3) == 5

def test_exception():
    with pytest.raises(ValueError, match="must be positive"):
        validate(-1)

@pytest.fixture
def sample_data():
    return {"users": [{"name": "Alice"}, {"name": "Bob"}]}

def test_with_fixture(sample_data):
    assert len(sample_data["users"]) == 2

@pytest.mark.parametrize("input,expected", [
    (1, 1),
    (2, 4),
    (3, 9),
])
def test_square(input, expected):
    assert square(input) == expected
```

### What to test

- **Happy path** — normal usage produces expected output
- **Edge cases** — empty inputs, None, zero, boundary values
- **Error cases** — invalid input raises the right exception
- **State changes** — side effects (DB writes, file creation) happen correctly

---

## Mocking

### When to mock

Mock when real dependencies are impractical (network calls, databases, time-dependent behavior):

```python
from unittest.mock import Mock, patch, MagicMock

# Mock a specific function
with patch("mymodule.requests.get") as mock_get:
    mock_get.return_value.status_code = 200
    mock_get.return_value.json.return_value = {"key": "value"}
    result = mymodule.fetch_data("http://example.com")

# Verify the mock was called correctly
mock_get.assert_called_once_with("http://example.com")
```

### Encapsulate dependencies for easier mocking

```python
class DataService:
    def __init__(self, http_client=None):
        self.http = http_client or requests

    def fetch(self, url):
        return self.http.get(url).json()

# In tests
mock_client = Mock()
mock_client.get.return_value.json.return_value = {"data": "test"}
service = DataService(http_client=mock_client)
```

Constructor-based dependency injection is simpler to test than patching module-level imports.

---

## Type Hints and Static Analysis

### Basic type annotations

```python
def greet(name: str, times: int = 1) -> str:
    return (f"Hello, {name}! " * times).strip()

# Modern syntax (Python 3.10+)
def find(items: list[str], target: str) -> int | None:
    try:
        return items.index(target)
    except ValueError:
        return None

# For Python 3.9 and earlier, use typing.Optional
from typing import Optional
def find(items: list[str], target: str) -> Optional[int]:
    ...
```

### Type checkers

Use `mypy`, `pyright`, or `pytype` to catch type errors before runtime:

```bash
pip install mypy
mypy mymodule.py
```

### Best practices for type hints

- Start w/ function signatures (arguments and return types)
- Add variable annotations where types aren't obvious
- Use `typing.Protocol` for structural subtyping (duck typing w/ type safety)
- Don't over-annotate — hints should help, not create noise
- If using type hints, omit type info from docstrings (avoid redundancy)

### Gradual adoption

Adopt incrementally:
1. Public API functions
2. Complex functions where bugs are likely
3. Boundaries between modules

---

## Debugging

### `breakpoint()` and pdb

```python
def problematic_function(data):
    result = process(data)
    breakpoint()  # Drops into pdb here
    return result
```

Essential pdb commands:
| Command | Action |
|---------|--------|
| `n` | Execute next line |
| `s` | Step into function call |
| `c` | Continue execution |
| `p expr` | Print expression value |
| `pp expr` | Pretty-print expression |
| `l` | Show source around current line |
| `w` | Show call stack |
| `q` | Quit debugger |

### Debug f-strings

F-strings w/ `=` show both expression and value:

```python
x = 42
print(f"{x = }")       # Output: x = 42
print(f"{len(items) = }")  # Output: len(items) = 7
```

### Logging over print

```python
import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

def process(data):
    logger.debug("Processing %d items", len(data))
    try:
        result = transform(data)
        logger.info("Processed successfully")
        return result
    except Exception:
        logger.exception("Processing failed")
        raise
```

`logger.exception()` automatically includes the traceback.

### Memory debugging with tracemalloc

```python
import tracemalloc

tracemalloc.start()
# ... run your code ...
snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics("lineno")
for stat in top_stats[:10]:
    print(stat)
```

---

## Profiling and Performance

### Profile before optimizing

```python
import cProfile

cProfile.run("main()", sort="cumulative")

# Or more controlled
profiler = cProfile.Profile()
profiler.runcall(main)
stats = pstats.Stats(profiler)
stats.sort_stats("cumulative")
stats.print_stats(20)
```

### Microbenchmarks with timeit

```python
import timeit

# From code
time = timeit.timeit(
    "sorted(data)",
    setup="data = list(range(1000))",
    number=10000,
)

# From command line
# python -m timeit -s "data = list(range(1000))" "sorted(data)"
```

### Performance quick wins

- Use the right data structure (sets for lookups, deques for queues)
- `functools.lru_cache` / `functools.cache` for memoization
- Generator expressions over list comprehensions for large data
- `"".join(parts)` instead of string concatenation in loops
- `bisect` for searching sorted sequences
- `memoryview` and `bytearray` for zero-copy binary ops
- Profile first — the bottleneck is rarely where you think

### Data layout and caching

Contiguous data (arrays, NumPy arrays) is CPU-cache-friendly. Scattered data (linked structures, lists of arbitrary objects) causes cache misses. For numerical work, prefer `array.array` or NumPy arrays over lists of numbers.

### Startup time optimization

Slow imports dominate startup. Diagnose with:
```bash
python -X importtime script.py
```

Solutions:
- **Lazy imports** — move expensive imports inside functions that use them. `sys.modules` check overhead is negligible (~20 additions).
- **Precompiled bytecode** — ensure `.pyc` files exist (Python caches automatically; force w/ `py_compile` or `compileall`).
- Avoid importing large frameworks at module level if only used in rare code paths.

### memoryview and bytearray for zero-copy

For high-throughput binary processing (network I/O, file processing):

```python
# Zero-copy slice of binary data
data = bytearray(1024)
view = memoryview(data)
chunk = view[100:200]  # No copy — shares the same memory
```

`memoryview` can wrap `bytearray`, allowing received data to be spliced into an arbitrary buffer location without copying.

### When to go beyond Python

If Python is genuinely too slow after optimization:
1. **NumPy / SciPy** — C under the hood, for numerical/scientific work
2. **Cython** — hybrid Python/C; small type annotations → 10-100x speedups for numerical loops
3. **Numba** — JIT compiler for numerical Python; decorate w/ `@jit` for near-C speed; works well w/ NumPy arrays
4. **ctypes** — call C/Rust shared libraries directly; fast integration, no build complexity, limited to C-compatible types
5. **C extension modules** — maximum performance via Python C API; high dev cost, full protocol access
6. **PyPy** — alternative interpreter w/ JIT; drop-in replacement for many programs; 10-100x faster for long-running code
7. **Mojo** — Python superset for extreme performance; up to 35,000x faster for numerical work; under active development
8. **`concurrent.futures.ProcessPoolExecutor`** — bypass GIL for CPU parallelism

### Decimal for precision

When float rounding is unacceptable (finance, billing):

```python
from decimal import Decimal

# Always construct from strings, not floats
price = Decimal("19.99")
tax = Decimal("0.075")
total = price * (1 + tax)  # Exact arithmetic
```

Pass `str` to `Decimal()` — passing `float` defeats the purpose (already rounded).

---

## Code Quality Tools

| Tool | Purpose |
|------|---------|
| `uv` | Package/project management, virtual environments, Python versions (replaces pip, venv, pyenv, pipx) |
| `black` | Auto-formatting (PEP 8 compliant) |
| `ruff` | Fast linting (replaces flake8, isort, and more) — also by Astral |
| `mypy` / `pyright` | Static type checking |
| `pytest` | Testing framework |
| `coverage` | Test coverage measurement |
| `bandit` | Security linting |
| `pre-commit` | Run checks before every commit |

---

## Packaging and Collaboration

### Package and Environment Management — uv first

**uv is the recommended default for Python package and project management.** Rust-based all-in-one tool by Astral (creators of Ruff) that replaces pip, pip-tools, virtualenv, pyenv, and pipx — 10-100x faster.

#### Why uv over pip

| pip + venv workflow | uv equivalent |
|---------------------|---------------|
| `python -m venv .venv` | `uv venv` (or automatic) |
| `pip install requests` | `uv add requests` |
| `pip install -r requirements.txt` | `uv pip install -r requirements.txt` |
| `pip freeze > requirements.txt` | `uv pip freeze > requirements.txt` |
| `pip install --upgrade pip` | `uv self update` |
| `pyenv install 3.12` | `uv python install 3.12` |
| `pipx run ruff` | `uvx ruff` |

#### Starting a new project

```bash
# Install uv (no Python or Rust needed)
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create a new project
uv init myproject
cd myproject

# Add dependencies (auto-creates venv, writes pyproject.toml + lockfile)
uv add requests flask

# Run your code (auto-syncs environment)
uv run python main.py

# Run a tool without installing it globally
uvx ruff check .
uvx pytest
```

uv auto-creates/manages virtual environments, generates `uv.lock` for reproducible builds, and uses a global cache so packages are never downloaded twice.

#### Single-file scripts with inline dependencies

```bash
# Add dependencies as inline metadata to a script
uv add --script example.py requests
# Run with isolated environment
uv run example.py
```

#### Key uv features

- **Python version management** — install/switch versions without pyenv
- **Lockfile** — `uv.lock` ensures reproducible installs across machines and CI
- **Workspaces** — Cargo-style monorepo support for multi-package projects
- **pip compatibility** — `uv pip install`, `uv pip compile`, `uv pip sync` as drop-in replacements
- **Global cache** — disk-space efficient deduplication; clean w/ `uv cache clean`
- **Build and publish** — `uv build` and `uv publish` for PyPI distribution

#### When to use something else

| Situation | Tool |
|-----------|------|
| Default for all projects | **uv** |
| Scientific/data science w/ non-Python deps (C, Fortran, CUDA) | **conda / mamba** |
| Legacy project tightly coupled to pip's lenient resolution | **pip** (migrate to uv when possible) |
| Team deeply invested in Poetry w/ publishing workflows | **Poetry** (uv is catching up fast) |

For nearly all new projects, start w/ uv. Faster, simpler, and consolidates fragmented Python tooling into one tool.

### Freeze and reproduce (with uv)

```bash
# Modern way — lockfile is automatic
uv lock                              # Generate/update uv.lock
uv sync                              # Install from lockfile

# pip-compatible way
uv pip freeze > requirements.txt
uv pip install -r requirements.txt
```

### Module and package organization

- One module = one `.py` file
- One package = a directory w/ `__init__.py`
- Use `__all__` in `__init__.py` to define the public API
- Name internal modules w/ a leading underscore
- Use absolute imports (`from mypackage.submodule import thing`)

### Docstrings everywhere

```python
"""Module docstring — what this module provides."""

class MyClass:
    """Class docstring — what this class represents."""

    def my_method(self, arg):
        """Method docstring — what this method does.

        Args:
            arg: Description.

        Returns:
            Description of return value.

        Raises:
            ValueError: When arg is invalid.
        """
```

### Breaking circular imports

- Refactor shared dependencies into a separate module
- Use dynamic imports inside functions (not at module level)
- Restructure the dependency tree to eliminate cycles

Best solution is usually refactoring. Dynamic imports are the simplest fallback when refactoring is impractical.

### Deprecation with warnings

```python
import warnings

def old_function():
    warnings.warn(
        "old_function is deprecated, use new_function instead",
        DeprecationWarning,
        stacklevel=2,
    )
    return new_function()
```

Use `-W error` in tests to catch deprecation warnings as errors. In production, replicate warnings into `logging` so error-reporting systems capture them. Write tests for warnings to ensure they trigger correctly.

### Deployment configuration with module-scoped code

Use module-level logic to adapt to different environments:

```python
# config.py
import os
import sys

if os.environ.get("ENVIRONMENT") == "production":
    DATABASE_URL = os.environ["DATABASE_URL"]
    DEBUG = False
else:
    DATABASE_URL = "sqlite:///dev.db"
    DEBUG = True
```

For larger projects, consider dedicated config libraries (e.g., `pydantic-settings`, `dynaconf`, `python-dotenv`).

### Web Frameworks (choosing the right one)

| Framework | Best for |
|-----------|----------|
| **Flask** | Simple web apps, APIs, learning web development |
| **FastAPI** | Modern async APIs, automatic OpenAPI docs, type validation |
| **Django** | Full-featured apps w/ ORM, admin, auth, templates |
| **Bottle** | Single-file microapps |
| **Litestar** | FastAPI alternative w/ more features and better performance |

For REST APIs, FastAPI is the modern default — uses type hints for automatic validation and documentation.

### NumPy / pandas quick reference

**NumPy** — fast numerical arrays w/ C performance:
```python
import numpy as np
a = np.array([1, 2, 3, 4])
b = a * 2                    # Vectorized — no loop needed
c = np.zeros((3, 4))         # 3x4 matrix of zeros
d = a.reshape(2, 2)          # Reshape without copying
```

**pandas** — labeled data manipulation:
```python
import pandas as pd
df = pd.read_csv("data.csv")
filtered = df[df["age"] > 30]
grouped = df.groupby("city")["salary"].mean()
```

For large datasets, consider **Polars** (faster, Rust-based) or **DuckDB** (SQL on DataFrames).
