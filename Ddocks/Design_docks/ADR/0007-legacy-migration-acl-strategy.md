# ADR 0007 — Legacy Migration Strategy: Anti-Corruption Layer

**Date:** 2026-03-19
**Status:** Accepted
**Deciders:** Project team

---

## Context

The `src/legacy_to_port/sanali209/` directory contains a legacy Python monorepo built around a custom framework called **SLM** (Singleton-Lifecycle-Manager). It uses:

- A global `DependencyManager` (Service Locator anti-pattern)
- A synchronous string-topic `MessageBus` (no typing, no CQRS)
- A `ComponentManager` + `PluginSystem` (manual lifecycle, no DI scoping)
- `PyQt5` (legacy UI toolkit, should be PySide6)
- God-object `App` class orchestrating all concerns
- Spaghetti imports (no clean boundaries between applications)

The current BCor architecture uses `dishka` (IoC), `bubus` (async event bus), typed Commands/Events (CQRS), `BaseModule`, `System`, and `PySide6`.

---

## Decision

Migrate legacy code using an **Anti-Corruption Layer (ACL)** strategy:

1. **Migrate by domain, not by file.** Each legacy application becomes a separate BCor module.
2. **Never import `SLM.*` from new code.** Legacy code is only touched inside `src/legacy_to_port/`.
3. **ACL adapters** bridge legacy concepts to BCor ports (interfaces) where needed.
4. **Phased migration:** Each phase delivers a tested, integrated module before the next starts.
5. **PyQt5 → PySide6** for all UI rewrites.
6. **String-topic pub/sub → typed CQRS** (Command/Event dataclasses via `bubus`).

## Migration Order

| Phase | Domain | Target |
|---|---|---|
| 0 | Preparation | ADR, dependencies, import map |
| 1 | ImageDedupApp | `src/apps/ImageDedup/` |
| 2 | appGlue utilities | `src/common/` + `src/adapters/` |
| 3 | LLM / NLP / chains | `src/modules/llm/` |
| 4 | Web / Scrapers | `src/adapters/web/` |
| 5 | Cleanup | Remove `legacy_to_port/` |

## Consequences

- **Positive:** Clean domain boundaries from day one; tests can be written before migration; no big-bang rewrite risk.
- **Negative:** Extra Adapter boilerplate during transition; some legacy packages must remain installed temporarily.
- **Neutral:** Legacy packages stay in `pyproject.toml` under `[project.optional-dependencies] legacy = [...]` until their module is ported.
