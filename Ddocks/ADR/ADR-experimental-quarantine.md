# ADR 0008: Experimental Quarantine & Promotion Policy

Status: Proposed

Date: 2026-03-29

Context
- Репозиторий содержит `src/apps/experemental/**` и другие legacy/porting артефакты. Без политики продвижения risk of accidental propagation of experimental code into core.

Decision
- Вводится политика "Quarantine & Promotion" для экспериментальных модулей:
  1. Определение: EXPERIMENTAL — код, который не имеет достаточного тестового покрытия, не использован в production, или помечен как legacy/porting.
  2. Quarantine requirements:
     - Папка помечается как `EXPERIMENTAL` в её `README.md` или содержит `QUARANTINE.md` с полями: owner, rationale, test-plan, promote-checklist.
     - CI для quarantine запускает только static checks и smoke-tests; promotion требует full CI.
     - PRы, затрагивающие quarantine-код, помечаются `requires: arch-team` и проходят дополнительный review.
  3. Promotion rules:
     - Promotion checklist (must be satisfied):
       - Unit tests covering critical paths (automated). Minimum: tests for business-critical functions.
       - Type-check (mypy) clean or documented exceptions.
       - Lint (ruff) clean or documented exceptions.
       - Documentation updated (`README.md`, `Ddocks/` entries).
       - Performance and integration smoke tests (if applicable).
     - Approvals required: arch-team + module-owner + 1 peer reviewer.
  4. Rollback policy: при regressions module может быть демотирован в quarantine по решению arch-team с созданием remediation ticket.

Consequences
- Плюсы:
  - Чёткие границы между экспериментальным и production-кодом.
  - Снижение риска регрессий и непредвиденных зависимостей.
- Минусы:
  - Дополнительная процедура для promotion увеличит время принятия изменений.

Reviewers & Approvers
- arch-team (required)
- module-owner (required for each module)

Implementation notes
- Add `QUARANTINE.md` template to `Ddocks/Design_docks/specs/` and require it for each experimental module.
- Integrate promotion checklist into PR template (optional).

