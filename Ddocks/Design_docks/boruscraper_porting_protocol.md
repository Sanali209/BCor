# Porting Protocol: Boruscraper (Legacy to BCor)

This document outlines the systematic porting of the Boruscraper application into the BCor framework following Domain-Driven Design (DDD) and the Strangler Fig pattern.

## P1: Inception
- **Legacy Source**: `applications/scraper/` (monolithic script).
- **Target**: `src/apps/experemental/boruscraper/`.
- **Core Requirements**:
    - Migration from thread-based to async-first architecture.
    - Integration with `Dishka` (DI) and `Bubus` (MessageBus).
    - Decoupling of domain logic from GUI and Playwright.

## P2: Research Spike
- **Async GUI Integration**: Validated `qasync` as the bridge between PySide6 and `asyncio` loop.
- **Browser Automation**: Confirmed `async_playwright` as the replacement for legacy scraping logic.
- **Concurrency**: Tested the "Command Handler" pattern to ensure GUI remains responsive during long-running scrapes.

## P3: Iterative Porting (Execution)

### Iteration 1: Bootstrap & Settings
- **Analysis**: Determined that `boruscraper` requires persistent settings for save paths and deduplication thresholds. Identified Dishka as the primary IoC container.
- **Execution**: Defined `BoruScraperSettings` and created `BoruScraperModule`.

### Iteration 2: Domain & CQRS Handlers
- **Analysis**: Identified `Project` as the aggregate root. Determined that starting a scrape is a `Command` that generates progress `Events`.
- **Execution**: Created domain models and implemented `StartScrapeCommand` handler.

### Iteration 3: Infrastructure (UoW & Repo)
- **Analysis**: Legacy app used raw SQLite calls. Decided to implement the Repository pattern to isolate domain logic from SQL details.
- **Execution**: Implemented `SqliteRepository` and `SqliteUnitOfWork`.

### Iteration 4: Core Logic (Async Scraper)
- **Analysis**: Legacy scraper was synchronous and used `requests`. Decided to migrate to `async_playwright` for better concurrency and JS support.
- **Execution**: Ported logic to `ScrapeProjectUseCase` and integrated `AsyncResourceDownloader`.

### Iteration 5: UI Refactoring
- **Analysis**: The GUI (PySide6) needs to receive updates without blocking. Decided to use an `EventsAdapter` to push background events to the main thread.
- **Execution**: Refactored `MainWindow` and implemented `EventsAdapter`.

### Iteration 6: Common Code Extraction
- **Analysis**: Identified `DatabaseManager` and `DeduplicationManager` as reusable utilities that should reside in a `common/` package for the experimental app.
- **Execution**: Extracted common utilities and standardized all internal imports.

## P4: Verification
- **Automated Tests**:
    - `test_iteration1.py`: Bootstrap and Provider verification.
    - `test_iteration2.py`: Handler and Command orchestration.
- **Quality Checks**:
    - Ruff: 100% compliant.
    - Mypy: 100% compliant (checked via dev process).
- **Manual Proof**: Launching `main.py` confirms end-to-end functionality.
- **Critical Fixes**:
    - **Path Resolution**: Added direct root injection to `sys.path`.
    - **Dishka Configuration**: Aligned `ScrapeTaskManager` scope with `MessageBus` (Scope.REQUEST) and registered the missing `AbstractUnitOfWork`.
    - **Bubus Compatibility**: Ensured all `Command` and `Event` models inherit from BCor core base classes.
    - **Signal/Slot Sync**: Corrected PySide6 signal signatures to match their associated slots.

---
*Protocol finalized: 2026-03-23*
