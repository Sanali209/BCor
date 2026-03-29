# Monorepo Roadmap — Consolidation & Evolution (BCor)

Дата: 2026-03-29

Кратко
: Трёхспринтовая дорожная карта для аудита, консолидации конфигураций, карантина/продвижения экспериментальных модулей и погашения критического техдолга.

Sprint S1 — Audit & Stabilize (2 weeks)
- Цель: получить полную видимость репозитория, устранить блокирующие ошибки линтеров/типизации и прогнать тесты; пометить экспериментальные/legacy модули.
- Вехи:
  - Создать `monorepo-inventory.md` с owners и статусом модулей.
  - Запустить `uv ruff`, `uv mypy`, `uv pytest` из корня; зафиксировать fatal issues.
  - Пометить `src/apps/experemental/**` как QUARANTINE (добавить `QUARANTINE.md`/README флаг).
- Acceptance criteria:
  - `uv ruff .` запускается и не падает с парсинг-ошибками.
  - `uv mypy src` выполняется (или документированы причины игнорирования отдельных модулей).
  - `uv pytest tests -q` выполняется; список failing tests и blocker-failures задокументирован в `.audit/`.
  - Inventory создан, initial owners назначены.
- Owners: `arch-team` (координация), `module-owner:src/*` (назначенные per-module)
- Оценка: 2 недели

Sprint S2 — Consolidate Configs & Promote (3 weeks)
- Цель: консолидировать `pyproject.toml`/lint/mypy конфиги, создать CI prototype, продвинуть 1–2 low-risk experimental модуля.
- Вехи:
  - Единый/агрегированный `pyproject.toml` с секциями для `ruff`, `mypy`, `pytest`.
  - CI prototype (workflow) или локальная runbook для `uv ruff`, `uv mypy`, `uv pytest`.
  - Promotion PR для выбранных experimental-модулей с тестами и doc updates.
- Acceptance criteria:
  - Корневой `pyproject.toml` валидируется (см. `monorepo-audit-template.md`).
  - CI prototype выполняет ruff+mypy+pytest (локально/CI).
  - Для promo-модулей есть тесты и чеклист из ADR.
- Owners: `arch-team`, `ci-team`, `module-owner:promoted-module`
- Оценка: 3 недели

Sprint S3 — Hardening & Tech-debt (3 weeks)
- Цель: задокументировать и планировать погашение техдолга, утвердить ADR quarantine/promotion, выпустить executive summary и детальный технический отчёт.
- Вехи:
  - Сформирован `TECH_DEBT_REGISTRY.md` с P0/P1 элементами.
  - ADR `ADR-experimental-quarantine.md` утверждён (arch-team sign-off).
  - Executive summary и детальный audit report готовы и размещены в `Ddocks/Design_docks/specs/`.
- Acceptance criteria:
  - TECH_DEBT_REGISTRY содержит все P0/P1 элементы с owner и планами.
  - ADR принята — PR/approval history доступна.
  - Executive summary (1–2 стр.) и детальный отчет (evidence + artifacts) размещены.
- Owners: `arch-team`, `doc-owner`, `module-owner:*`
- Оценка: 3 недели

Prioritization & Governance
- Priorities: P0 (blockers/security/type-safety), P1 (stability/CI/config), P2 (refactor/cleanup)
- Governance: ADR-first for promotions; all promotions require arch-team + module-owner approval and passing CI.

Quick references
- Inventory path: `Ddocks/Design_docks/specs/monorepo-inventory.md`
- Backlog path: `Ddocks/Design_docks/specs/monorepo-backlog.md`
- ADR path: `Ddocks/ADR/ADR-experimental-quarantine.md`
- Audit template: `Ddocks/Design_docks/specs/monorepo-audit-template.md`

