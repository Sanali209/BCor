# Functions and Generators

Clean, composable functions — closures, decorators, generators, and comprehensions.

## Table of Contents
1. [Function Design Principles](#function-design-principles)
2. [Arguments and Parameters](#arguments-and-parameters)
3. [Return Values](#return-values)
4. [Closures and Scope](#closures-and-scope)
5. [Decorators](#decorators)
6. [Generators](#generators)
7. [Lambda and Partial](#lambda-and-partial)

---

## Function Design Principles

### Extract helpers instead of complex expressions

When an expression is hard to read, extract it into a named function — readability outweighs brevity:

```python
# Hard to read
red = int(my_values.get("red", [""])[0] or 0)

# Clear
def get_first_int(values, key, default=0):
    found = values.get(key, [""])
    if found[0]:
        return int(found[0])
    return default

red = get_first_int(my_values, "red")
```

### Functions are first-class

Functions can be stored in variables, passed as arguments, returned from other functions, and stored in data structures → enables callbacks, strategy selection, and higher-order functions.

### Docstrings

Write docstrings for every public function:

```python
def connect(host: str, port: int, timeout: float = 30.0) -> Connection:
    """Open a connection to the specified host.

    Args:
        host: The server hostname or IP address.
        port: The server port number.
        timeout: Connection timeout in seconds.

    Returns:
        An active Connection instance.

    Raises:
        ConnectionError: If the server is unreachable.
    """
```

If you use type annotations, omit types from docstrings — duplicating them is redundant.

---

## Arguments and Parameters

### Positional vs keyword arguments
- **Positional** — order matters, quick for simple calls.
- **Keyword** — self-documenting, order-independent, good for optional behavior.
- Always pass optional arguments by keyword, not position.

### Keyword-only and positional-only arguments

```python
def safe_division(
    numerator,       # Positional-only (before /)
    denominator,     # Positional-only
    /,
    *,               # Everything after * is keyword-only
    ignore_overflow=False,
    ignore_zero_division=False,
):
    ...
```

- **Positional-only** (before `/`): Reduces coupling — callers can't depend on parameter names.
- **Keyword-only** (after `*`): Enforces clarity — callers must name the argument.

### Variable positional arguments (`*args`)

```python
def log(message, *values):
    if values:
        print(f"{message}: {', '.join(str(v) for v in values)}")
    else:
        print(message)
```

**Caution:** Adding positional arguments before `*args` in a later refactor silently changes what each caller passes.

### Variable keyword arguments (`**kwargs`)

```python
def make_config(required_param, **kwargs):
    config = {"required": required_param}
    config.update(kwargs)
    return config
```

### Arguments are passed by reference

Python passes object references → functions can mutate mutable arguments (lists, dicts, objects). Make this clear in naming/docs, or create defensive copies:

```python
def process_items(items):
    items = list(items)  # Defensive copy
    # ... safe to modify items ...
```

### Dynamic defaults w/ None

Default argument values are evaluated **once** at definition time. Use `None` as sentinel for dynamic defaults (see also `pythonic-idioms.md` > Avoid mutable default values):

```python
def append_to(item, target=None):
    if target is None:
        target = []
    target.append(item)
    return target

# Same pattern for timestamps
def log_event(message, when=None):
    """Log with a timestamp. Defaults to current time."""
    if when is None:
        when = datetime.now()
    print(f"{when}: {message}")
```

---

## Return Values

### Raise exceptions instead of returning None

Returning `None` to signal errors is dangerous — `None`, `0`, and `""` are all falsey, so callers can confuse a valid result w/ an error. See `error-handling.md` > Exception Fundamentals. Use type annotations to make return types explicit:

```python
def divide(a: float, b: float) -> float:
    if b == 0:
        raise ValueError("Cannot divide by zero")
    return a / b
```

### Return dedicated result objects instead of large tuples

Unpacking 4+ variables is error-prone. Return a dataclass or named tuple:

```python
# Fragile — easy to swap values
name, age, city, score = get_user_info(user_id)

# Better
@dataclass
class UserInfo:
    name: str
    age: int
    city: str
    score: float

info = get_user_info(user_id)
print(info.name, info.score)
```

---

## Closures and Scope

### How closures work

Inner functions can reference variables from their enclosing scope:

```python
def make_counter(start=0):
    count = start
    def increment():
        nonlocal count
        count += 1
        return count
    return increment
```

Closures can **read** enclosing variables but **cannot reassign** them by default. Use `nonlocal` for reassignment. For module-level variables use `global` (but prefer avoiding global state).

### Scope resolution order: LEGB

Python resolves names in this order:
1. **L**ocal — current function
2. **E**nclosing — enclosing functions (closures)
3. **G**lobal — module level
4. **B**uilt-in — Python's built-in names

---

## Decorators

### Writing decorators correctly

Always use `functools.wraps` to preserve the wrapped function's metadata:

```python
import functools

def log_calls(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        print(f"Calling {func.__name__}")
        result = func(*args, **kwargs)
        print(f"{func.__name__} returned {result}")
        return result
    return wrapper

@log_calls
def add(a, b):
    return a + b
```

Without `@functools.wraps`, the decorated function loses `__name__`, `__doc__`, etc., breaking introspection and debugging.

### Common built-in decorators
- `@property` — read-only attribute accessor.
- `@staticmethod` — no `self` or `cls`.
- `@classmethod` — receives `cls` as first argument.
- `@functools.lru_cache` — memoize results.
- `@functools.singledispatch` — overloading by argument type.
- `@dataclasses.dataclass` — auto-generate `__init__`, `__repr__`, `__eq__`, etc.

---

## Generators

### Generator functions w/ `yield`

Generators produce values lazily — ideal for large or infinite sequences:

```python
def read_large_file(path):
    with open(path) as f:
        for line in f:
            yield line.strip()
```

Memory usage is proportional to one item, not the entire dataset.

### Generator expressions

Lazy equivalent of list comprehensions:

```python
total = sum(x**2 for x in range(1_000_000))  # No list in memory
```

### Composing generators w/ `yield from`

```python
def flatten(nested):
    for sublist in nested:
        yield from sublist
```

`yield from` eliminates boilerplate of manually iterating and yielding.

### Avoid `send()` and `throw()`

`send` injects values into generators; `throw` injects exceptions. Both harm readability. Prefer passing an input iterator as argument instead of `send`. For state transitions, use a class instead of `throw`.

### Resource management in generators

Generators allocating resources (files, connections) might not run `finally` blocks if not fully consumed. Pass resources **into** generators rather than having them allocate:

```python
# Prefer this pattern
def process_lines(file_handle):
    for line in file_handle:
        yield transform(line)

with open("data.txt") as f:
    for result in process_lines(f):
        use(result)
```

---

## Lambda and Partial

### Lambda for simple, one-off callables

```python
names.sort(key=lambda name: name.split()[-1])
```

Keep lambdas to a single expression. If logic is complex, use a named function.

### `functools.partial` for pinning arguments

```python
from functools import partial

# Pin the base argument
log2 = partial(math.log, base=2)
result = log2(8)  # 3.0

# Useful for callbacks
button.on_click(partial(handle_click, button_id=42))
```

Prefer `partial` over `lambda` when simply pinning argument values. Use `lambda` when you need to reorder arguments.

---

## Recursion

### When to use recursion

Natural for recursive structures: trees, nested data, divide-and-conquer, backtracking. For simple iteration, prefer `for`/`while` loops.

```python
def flatten(nested):
    """Recursively flatten nested lists."""
    result = []
    for item in nested:
        if isinstance(item, list):
            result.extend(flatten(item))
        else:
            result.append(item)
    return result
```

### Memoization to avoid exponential blowup

Naive recursion can be catastrophically slow (e.g., Fibonacci). Use `functools.cache`:

```python
from functools import cache

@cache
def fib(n):
    if n < 2:
        return n
    return fib(n - 1) + fib(n - 2)
```

### Backtracking pattern

For constraint satisfaction (N-queens, Sudoku, permutations):

```python
def solve(state):
    if is_complete(state):
        return state
    for choice in get_candidates(state):
        state.apply(choice)
        if is_valid(state):
            result = solve(state)
            if result is not None:
                return result
        state.undo(choice)  # Backtrack
    return None
```

### Python recursion limits

Default limit ~1000. For deep recursion, either increase w/ `sys.setrecursionlimit()` (use cautiously) or convert to iterative approach w/ an explicit stack.
