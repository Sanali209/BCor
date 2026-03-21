# Common Utilities

Shared pure Python utilities used across the BCor framework. These modules have **zero dependencies** on BCor core or external frameworks.

## Modules

### `concurrency.py`
Async concurrency utilities and helpers for parallel task execution.

### `formatters.py`
Data formatting utilities for display, serialization, and output formatting.

### `hashing.py`
Cryptographic hashing functions for data integrity and caching.

### `monads.py`
Functional programming monads for error handling and composition.

### `progress.py`
Progress tracking and reporting utilities for long-running operations.

### `undo.py`
Undo/redo functionality and command pattern implementations.

## Subdirectories

### `io/`
- `pathtools.py` — File system path manipulation utilities.

### `scheduling/`
- `timers.py` — Timer and scheduling utilities.

### `ui/`
- `selection.py` — UI selection helpers.
- `theming/` — Theme management utilities.

## Usage

```python
from src.common.io.pathtools import get_files, move_file_if_exist
from src.common.monads import success, failure
from src.common.hashing import compute_hash
```

## Design Principles

1. **Pure Python** — No external dependencies
2. **Framework Agnostic** — Can be used outside BCor
3. **Type Safe** — Full type hints
4. **Well Tested** — Comprehensive unit tests