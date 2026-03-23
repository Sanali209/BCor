# Generic Plan: Experimental Application Porting (Legacy -> BCor)

A standardized framework for migrating legacy applications  legacy codebase into the BCor ecosystem. This plan ensures consistency across all experimental (`src/apps/experemental/`) ports.

## Phase P1: Inception (Discovery)
1. **Legacy Audit**: Identify the entry point in the legacy codebase.
2. **Dependency Mapping**: Use `grep` or `codemap` to find dependencies.
3. **Core Scoping**: Define what is "Domain" (pure logic) and what is "Infrastructure" (IO, GUI, DB).
4. **BCor Alignment**: Decided whether it should be a standalone `app` or a shared `module`.

## Phase P2: Research Spike (Validation)
1. **Identify Blockers**: Find components that rely on legacy threading or blocking IO.
2. **Prototype Bridging**: Create a minimal POC for any new integration (e.g., Async libraries, new UI frameworks).
3. **Verdict**: Decide on specific adapters (e.g., `Playwright` vs `BeautifulSoup`, `SQLite` vs `JSON`).

## Phase P3: Iterative Refactoring (Implementation)
Porting is strictly **iterative**. Every step must follow the **Analysis-Implementation-Verification** loop. Follow the "BCor Hexagonal Cycle" in 6 standard iterations:

1. **Bootstrap**: 
    - *Analysis*: Audit legacy settings and DI needs.
    - *Implementation*: Create `module.py`, `provider.py`, and `settings.py`.
2. **Domain**: 
    - *Analysis*: Identify core entities and invariants.
    - *Implementation*: Define pure entities, value objects, and domain events in `domain/`.
3. **Application**: 
    - *Analysis*: Map legacy procedures to Commands/Queries.
    - *Implementation*: Define Handlers and use `bubus.MessageBus` for orchestration.
4. **Infrastructure**: 
    - *Analysis*: Select persistence (SQLite/NoSQL) and external adapters.
    - *Implementation*: Implement `Repository` and `UnitOfWork`.
5. **Presentation**: 
    - *Analysis*: Map GUI/CLI interactions to Application Commands.
    - *Implementation*: Build the UI bridge via events/commands.
6. **Polishing**: 
    - *Analysis*: Review code smells and cross-module couplings.
    - *Implementation*: Extract common utilities, fix type hints, and ensure 100% compliance.

## Phase P4: Design Verification (Quality)
1. **TDD Coverage**: Ensure every iteration has corresponding tests in `tests/apps/experemental/{app_name}/`.
2. **Integration Proof**: Verify the application launches and performs its core function end-to-end.
3. **Documentation**: Write the `walkingthrough.md` and specific `porting_protocol.md`.

## Common Pitfalls
- **`sys.path` Issues**: Always ensure the project root is in the path when running experimental apps as standalone scripts. Use the `Path(__file__).parents` hack if necessary.
- **Dishka Scopes**: Be mindful of dependencies across scopes (e.g., `APP` vs `REQUEST`). Components depending on `MessageBus` usually need to be `REQUEST` scoped.
- **Message Inheritance**: Ensure all messages inherit from `Command` or `Event` from `src.core.messages` to remain compatible with the framework dispatchers.
- **Signal/Slot Mismatch**: Native UI signals must exactly match the number and type of arguments expected by their handlers.

---
*Template version: 1.1.0 (2026-03-23)*
