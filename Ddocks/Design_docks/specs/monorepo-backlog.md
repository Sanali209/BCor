# Monorepo Backlog — Prioritized Tasks (P0 / P1 / P2)

Дата: 2026-03-29

Инструкция: каждая запись — тикет. Для каждого тикета указаны: Title, Priority, Description, Files to change, Estimated Effort, Risk, Acceptance Criteria.

P0 — Critical

- Title: P0-001: Fix fatal ruff/mypy configuration errors
  - Priority: P0
  - Description: Исправить ошибки конфигурации и простые кодовые нарушения, из-за которых `uv ruff` или `uv mypy` не запускаются из корня.
  - Files to change: `pyproject.toml`, `src/**`, `tests/**`
  - Estimated Effort: 8–16h
  - Risk: Medium
  - Acceptance Criteria: `uv ruff .` и `uv mypy src` запускаются; конфигурационные ошибки устранены.

- Title: P0-002: Create monorepo inventory and assign owners
  - Priority: P0
  - Description: Собрать список модулей (src/apps, src/modules, src/adapters, src/common), назначить owners и отметить experimental/legacy.
  - Files to change: `Ddocks/Design_docks/specs/monorepo-inventory.md`, `src/**/README.md` (optional)
  - Estimated Effort: 12h
  - Risk: Low
  - Acceptance Criteria: Inventory с owners создан и утверждён.

- Title: P0-003: Quarantine experimental modules
  - Priority: P0
  - Description: Пометить `src/apps/experemental/**` как QUARANTINE: добавить `QUARANTINE.md`, тест-scaffold и checklist для продвижения.
  - Files to change: `src/apps/experemental/**/QUARANTINE.md`, `src/apps/**/README.md`
  - Estimated Effort: 8h
  - Risk: Low
  - Acceptance Criteria: Каждая экспериментальная папка содержит `QUARANTINE.md` с owner и criteria to promote.

- Title: P0-004: Fix failing tests referencing missing modules (e.g., ImageAnalyze)
  - Priority: P0
  - Description: Тесты сейчас падают с ImportError (например, `src.apps.ImageAnalyze` не найден). Нужно либо вернуть/переместить реализацию, либо обновить тесты/fixtures, либо поставить skip для legacy тестов, либо добавить compatibility bridge.
  - Files to change: `tests/**`, `src/**` (possible locations: `src/apps/*`), `Ddocks/Design_docks/specs/monorepo-inventory.md`
  - Estimated Effort: 4–16h (depends on root cause)
  - Risk: Medium
  - Acceptance Criteria: `uv run pytest tests -q` проходит без ImportError; failing tests документированы or fixed.

P1 — Important

- Title: P1-010: Consolidate `pyproject.toml` (root aggregator)
  - Priority: P1
  - Description: Сконсолидировать настройки ruff/mypy/pytest в корневом `pyproject.toml` или создать root aggregator с per-module overrides.
  - Files to change: `pyproject.toml`, docs `Ddocks/Design_docks/specs/pyproject-consolidation.md`
  - Estimated Effort: 2–3d
  - Risk: High
  - Acceptance Criteria: Корневой `pyproject.toml` валидируется и покрывает lint/mypy/pytest политики.

- Title: P1-011: Add CI prototype (ruff + mypy + pytest)
  - Priority: P1
  - Description: Создать workflow (или runbook) для CI, запускающего ruff, mypy и pytest.
  - Files to change: `.github/workflows/ci.yml` (or docs)
  - Estimated Effort: 1–2d
  - Risk: Medium
  - Acceptance Criteria: Workflow запускается и возвращает results; local prototype проверен.

P2 — Backlog / Nice-to-have

- Title: P2-020: Refactor generic adapters and repositories
  - Priority: P2
  - Description: Улучшить generic repository/adapter паттерны в `src/adapters` и `src/modules/*/adapters`.
  - Files to change: `src/adapters/*`, `src/modules/*/adapters/*`
  - Estimated Effort: 1–2 weeks
  - Risk: High
  - Acceptance Criteria: Модульные тесты покрывают refactor; интеграционный smoke-test проходит.

- Title: P2-021: Improve test fixtures and fake UoW
  - Priority: P2
  - Description: Расширить `tests/conftest.py` надежными фикстурами для интеграционных тестов.
  - Files to change: `tests/conftest.py`, `tests/**`
  - Estimated Effort: 2–3d
  - Risk: Medium
  - Acceptance Criteria: Новые фикстуры доступны и используются в интеграционных тестах.

How to use this backlog
- Mark tickets with issue tracker IDs and link PRs.
- Re-evaluate priorities after S1 audit.

