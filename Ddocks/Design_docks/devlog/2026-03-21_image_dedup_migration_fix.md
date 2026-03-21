# DevLog: 2026-03-21 - ImageDedup Migration & Stability Fixes

## 🛠️ Work Done (Phase 1)
- **Resolved ImageDedup Integration Failures**: Fixed the `AssertionError: assert 0 == 1` by aligning DI types and implementing a functional mock repository.
- **DI Alignment**: Fixed a conflict where the handler was receiving the real infrastructure UoW instead of the mock. Refactored all handlers to use `AbstractUnitOfWork` for universal compatibility.
- **Core Framework Stability**: Fixed an `AttributeError` in `System._bootstrap` by adding a no-op `setup()` method to `BaseModule`.
- **MessageBus Restoration**: Restored the canonical `MessageBus` with async support, OpenTelemetry tracing, and `tenacity` retries.
- **Repository Implementation**: Implemented `JsonProjectRepository` for `ImageDedup` and verified it via integration tests.

## 🎓 Knowledge Gained
- **Dishka DI Precedence**: Dishka prioritizes exact type matches over subclasses. When a handler asks for `AbstractUnitOfWork`, a provider explicitly returning that type will win over one returning a concrete subclass like `ImageDedupUnitOfWork`.
- **System Bootstrap Contract**: Every module in the BCor framework MUST have a `setup()` method (even if no-op) because the `System._bootstrap` iterates through all enabled modules and calls it.
- **Asynchronous Result Aggregation**: In `bubus`, asynchronous handlers must be correctly awaited to ensure that events and results are captured before the UoW is committed.

## 👤 User Decisions & Guidance
- **"Independent Verification"**: The user mandated that we do not trust existing documentation and instead verify the actual state via TDD and direct testing.
- **"TDD-Driven Development"**: All architectural changes were validated by a working integration test suite before being finalized.
- **"Legacy Isolation"**: A strict decision was made NOT to modify legacy code internals during the initial porting phase; instead, we focused on wrapping them in Clean Architecture adapters.
- **"MessageBus Debugging"**: The user correctly identified that `MessageBus` timeouts were necessary to debug silent hangs in asynchronous handlers.

---
**Status**: Phase 1 Stabilized & Verified. Ready for Phase 2.
