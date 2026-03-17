# Error Handling

Python detects nearly all errors at runtime — robust error handling is essential.

## Table of Contents
1. [Exception Fundamentals](#exception-fundamentals)
2. [try/except/else/finally](#tryexceptelsefinally)
3. [Custom Exceptions](#custom-exceptions)
4. [Context Managers](#context-managers)
5. [Assertions](#assertions)
6. [Exception Chaining](#exception-chaining)
7. [Common Pitfalls](#common-pitfalls)

---

## Exception Fundamentals

### Raise exceptions instead of returning None

Never return `None` to signal an error — it's ambiguous. Raise a specific exception:

```python
# Bad
def find_item(items, target):
    for item in items:
        if item.name == target:
            return item
    return None  # Is this "not found" or an error?

# Good
def find_item(items, target):
    for item in items:
        if item.name == target:
            return item
    raise LookupError(f"Item '{target}' not found")
```

### Exception hierarchy

```
BaseException
├── SystemExit
├── KeyboardInterrupt
├── GeneratorExit
└── Exception
    ├── ValueError
    ├── TypeError
    ├── KeyError
    ├── AttributeError
    ├── IOError / OSError
    ├── RuntimeError
    └── ... (your custom exceptions)
```

- Catch `Exception` → handles app errors while letting `SystemExit`, `KeyboardInterrupt`, etc. propagate.
- Catch `BaseException` also catches system-exit signals — only do this w/ a specific reason, and re-raise appropriately.

---

## try/except/else/finally

### Use all four blocks

```python
try:
    result = operation()        # Only the risky operation
except SpecificError as e:
    handle_error(e)             # Handle the specific failure
else:
    process(result)             # Runs only if no exception was raised
finally:
    cleanup()                   # Always runs — for releasing resources
```

### Keep try blocks short

Too much code in `try` can catch unintended exceptions:

```python
# Bad — too much in the try block
try:
    value = data[key]           # KeyError expected
    result = transform(value)   # Might raise other exceptions
    save(result)                # Might raise other exceptions
except KeyError:
    handle_missing()

# Good — only the risky operation
try:
    value = data[key]
except KeyError:
    handle_missing()
else:
    result = transform(value)
    save(result)
```

### Catch specific exceptions

```python
# Bad — catches everything, hides bugs
try:
    do_something()
except:
    pass

# Bad — too broad
try:
    do_something()
except Exception:
    log("something went wrong")

# Good — specific
try:
    do_something()
except (ConnectionError, TimeoutError) as e:
    retry_or_fail(e)
```

---

## Custom Exceptions

### Define a root exception per module/package

Lets consumers catch all errors from your API in one place:

```python
class MyLibraryError(Exception):
    """Base exception for mylib."""

class ConnectionFailed(MyLibraryError):
    """Raised when the connection cannot be established."""

class InvalidInput(MyLibraryError):
    """Raised when input validation fails."""
```

Users can catch specific errors or the root:
```python
try:
    mylib.connect()
except mylib.ConnectionFailed:
    ...  # Handle specifically
except mylib.MyLibraryError:
    ...  # Handle any mylib error
```

### Intermediate root exceptions

Use intermediate categories for future expansion without breaking callers:

```python
class MyLibraryError(Exception): ...
class NetworkError(MyLibraryError): ...
class AuthError(NetworkError): ...
class TimeoutError(NetworkError): ...
```

---

## Context Managers

### `with` for resource management

`with` guarantees cleanup even when exceptions occur:

```python
with open("data.txt") as f:
    data = f.read()
# File is closed here, guaranteed
```

### Writing context managers w/ `contextlib`

```python
from contextlib import contextmanager

@contextmanager
def temporary_directory():
    path = create_temp_dir()
    try:
        yield path
    finally:
        remove_dir(path)

with temporary_directory() as tmpdir:
    process_files(tmpdir)
```

The `yield` value becomes the `as` variable. The `finally` block runs on exit.

### Class-based context managers

```python
class DatabaseConnection:
    def __enter__(self):
        self.conn = connect_to_db()
        return self.conn

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        return False  # Don't suppress exceptions
```

---

## Assertions

### Use `assert` for programmer assumptions, not user input

```python
# Good — internal invariant
def process_items(items):
    assert len(items) > 0, "process_items requires non-empty input"
    ...

# Bad — user input should raise a proper exception
def set_age(age):
    assert age > 0  # Don't do this — assertions can be disabled
    ...

# Good — user input validation
def set_age(age):
    if age <= 0:
        raise ValueError("Age must be positive")
    ...
```

- Assertions can be disabled w/ `python -O` → never use them for input validation or security checks.
- Failed assertions are `AssertionError` — should not be caught by callers.
- Assertions help narrow bug causes even when they don't fire.

### `raise` vs `assert`

- `raise` — expected error conditions (part of function interface, documented).
- `assert` — programmer assumptions (implementation detail, not part of API).

---

## Exception Chaining

### Implicit chaining (`__context__`)

When an exception is raised inside an `except` block, Python auto-saves the original:

```python
try:
    risky_operation()
except ConnectionError:
    raise RuntimeError("Operation failed")
# Python prints both tracebacks automatically
```

### Explicit chaining (`from`)

Use `from` to indicate causation:

```python
try:
    data = load_config(path)
except FileNotFoundError as e:
    raise ConfigError(f"Config file missing: {path}") from e
```

### Suppressing implicit chaining

Use `from None` when the original exception isn't relevant to the caller:

```python
try:
    value = cache[key]
except KeyError:
    raise LookupError(f"Unknown key: {key}") from None
```

---

## Common Pitfalls

### Exception variables disappear after `except` blocks

```python
try:
    risky()
except ValueError as e:
    saved_error = e  # Save it if you need it later
# e is no longer accessible here
```

### Don't use `except Exception` carelessly

Catches unintended things, e.g. `StopIteration` (breaks generators), `AssertionError` (hides bugs), and library custom exceptions.

### Never set `__debug__` to False

`__debug__` controls whether `assert` executes. Use `python -O` instead to disable assertions.

### Avoid `exec` and `eval`

These execute arbitrary code strings → security risks. Only use for developer tools (REPLs, debuggers), never w/ user input.

### Use `traceback` for enhanced error reporting

```python
import traceback

try:
    do_something()
except Exception:
    error_details = traceback.format_exc()
    log(error_details)
```

In concurrent programs, exception tracebacks may not print normally. `traceback` gives programmatic access to format and process stack frames.
