# BCor Porting Kit

A set of framework-level utilities designed to streamline the porting of legacy applications to the BCor framework, with a specific focus on **Windows stability**, **async safety**, and **cross-platform resource management**.

---

## Components

| Module | Class / Function | Purpose |
|--------|-----------------|---------|
| `porting.py` | `WindowsLoopManager` | Correct asyncio policy + loop drainage on Windows |
| `porting.py` | `PathNormalizer` | OS-agnostic path normalization for functions and methods |
| `porting.py` | `AsyncPoolExecutor` | Run CPU-bound tasks in processes without blocking the loop |
| `porting.py` | `async_delay` | Async-friendly `time.sleep` replacement |
| `async_utils.py` | `TaskThrottler` | Semaphore-based concurrency limiter for async tasks |
| `ui_bridge.py` | `BaseGuiAdapter` | Qt `QObject` base class bridging BCor events to Qt signals |
| `repository_utils.py` | `SqliteRepositoryBase` | Safe SQLite base class with `row_to_dict` / `get_field` helpers |
| `testing_utils.py` | `BCorTestSystem` | Async context manager for test system lifecycle + loop drainage |
| `testing_utils.py` | `run_test_system` | Helper to run a test function inside `BCorTestSystem` |

---

## Quick Start Recipes

### 1. Windows-Stable Entry Point (qasync + PySide6)

```python
# main.py
import asyncio
from PySide6.QtWidgets import QApplication
from qasync import QEventLoop
from src.porting.porting import WindowsLoopManager

def main():
    WindowsLoopManager.setup_loop()          # Apply WindowsSelectorEventLoopPolicy
    app = QApplication(sys.argv)
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    try:
        loop.run_until_complete(amain(app))
    finally:
        WindowsLoopManager.drain_loop(0.2)   # Drain pending tasks before exit
```

**Why**: Python 3.8+ defaults to `ProactorEventLoop` on Windows which can conflict with
`qasync` and Playwright. `SelectorEventLoop` avoids these conflicts.

---

### 2. Throttling Concurrent Tasks (scrapers / API clients)

**Pattern A — Context Manager** (used in `ScrapeProjectUseCase`):
```python
from src.porting.async_utils import TaskThrottler

class MyUseCase:
    def __init__(self):
        self.throttler = TaskThrottler(concurrency_limit=5)

    async def _process_item(self, url: str) -> bool:
        async with self.throttler:   # Blocks when 5 tasks are already running
            result = await fetch(url)
            return result
```

**Pattern B — Decorator** (for standalone functions):
```python
throttler = TaskThrottler(concurrency_limit=3)

@throttler.throttle
async def scrape_page(url: str):
    # Only 3 instances run at the same time
    ...
```

---

### 3. Path Normalization for Downloaders / File I/O

**Pattern A — Named arguments** (for specific path params):
```python
from src.porting.porting import PathNormalizer

class MyEngine:
    @PathNormalizer.normalize_args('root_paths')
    def search(self, root_paths: list[str]):
        for path in root_paths:
            ...  # All paths are absolute + case-normalized
```

**Pattern B — All arguments** (for download / save methods):
```python
class AsyncResourceDownloader:
    @PathNormalizer.normalize_args     # Normalizes all str / list[str] args
    async def download(self, url: str, save_path: str) -> None:
        ...
```

---

### 4. Qt UI Adapter (BCor events → Qt signals)

```python
# infrastructure/events_adapter.py
from PySide6.QtCore import Signal
from src.porting.ui_bridge import BaseGuiAdapter

class GuiEventAdapter(BaseGuiAdapter):
    # Add app-specific signals
    log_received = Signal(str, str)          # (level, message)
    duplicate_found = Signal(dict)           # conflict data

    # Connect BCor events to signals via handlers registered on the bus
    def on_log_event(self, level: str, msg: str):
        self.log_received.emit(level, msg)
```

Inherited signals from `BaseGuiAdapter`: `started(str)`, `progress(int, str)`,
`completed(str, dict)`, `error(str)`.

---

### 5. SQLite Repository (safe `sqlite3.Row` access)

```python
# common/database.py
import sqlite3
from src.porting.repository_utils import SqliteRepositoryBase

class DatabaseManager(SqliteRepositoryBase):
    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row   # Required for row_to_dict to work
        return conn

    def get_all_items(self) -> list[dict]:
        conn = self._get_connection()
        rows = conn.execute("SELECT * FROM items").fetchall()
        conn.close()
        return [self.row_to_dict(row) for row in rows]   # Safe, never raises
```

`row_to_dict` converts `sqlite3.Row` → `dict` and handles `None` rows gracefully.
`get_field(row, "field", default)` provides a safe `.get()` equivalent.

---

### 6. Stable Test System (Windows + asyncio safety)

```python
# tests/test_my_app.py
import pytest
from src.porting.testing_utils import BCorTestSystem

@pytest.mark.asyncio
async def test_my_feature(tmp_path):
    async with BCorTestSystem("src/myapp/app.toml").run() as system:
        container = system.container
        svc = await container.get(MyService)
        result = await svc.do_something()
        assert result is not None
    # Loop is drained on exit — no Windows hangs
```

**Key rule**: Always call `.run()` on `BCorTestSystem` to get the async context manager.

---

## Porting Checklist

Use this checklist when porting a legacy application:

- [ ] **Entry point**: Add `WindowsLoopManager.setup_loop()` before Qt init
- [ ] **Shutdown**: Add `drain_loop(0.2)` in the `finally` block
- [ ] **UI Adapter**: Inherit `GuiEventAdapter` from `BaseGuiAdapter` (remove duplicate `__init__`)
- [ ] **Database**: Inherit `DatabaseManager` from `SqliteRepositoryBase`, set `row_factory = sqlite3.Row`, use `row_to_dict`
- [ ] **File I/O**: Decorate download/save methods with `@PathNormalizer.normalize_args`
- [ ] **Concurrency**: Add `TaskThrottler` to use cases that spawn concurrent async tasks
- [ ] **Tests**: Use `BCorTestSystem` in E2E tests, `@playwright_required` guard for browser tests

---

## Real-World Examples

| Application | Component Used | File |
|-------------|---------------|------|
| `boruscraper` | `WindowsLoopManager` | `boruscraper/main.py` |
| `boruscraper` | `BaseGuiAdapter` | `boruscraper/infrastructure/events_adapter.py` |
| `boruscraper` | `SqliteRepositoryBase` | `boruscraper/common/database.py` |
| `boruscraper` | `PathNormalizer` | `boruscraper/common/downloader.py` |
| `boruscraper` | `TaskThrottler` | `boruscraper/application/use_cases.py` |
| `boruscraper` | `BCorTestSystem` | `boruscraper/tests/test_boruscraper_e2e.py` |
| `imgededupe` | `AsyncPoolExecutor` | `imgededupe/core/engines/phash.py` |
| `imgededupe` | `SqliteRepositoryBase` | `imgededupe/infrastructure/repository.py` |
