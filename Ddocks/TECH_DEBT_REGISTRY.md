# TECH_DEBT_REGISTRY

Date: 2026-03-29

Purpose
- Реестр технического долга для BCor. Каждая запись — структурированный элемент, который связывается с issue/PR.

Schema (YAML-like)
- id: TD-XXXX
- title: Short title
- description: Long description
- module: path or pattern (e.g., src/adapters)
- owner: role or username (e.g., module-owner:src/adapters)
- priority: P0 / P1 / P2
- impact: High / Medium / Low
- effort_estimate: hours / story points
- detection_date: YYYY-MM-DD
- status: Open / In Progress / Mitigated / Won't Fix
- mitigation_plan: short plan / link to PR / issue
- blocking: list of related tickets
- evidence: path to audit artifacts

Example entry
```
- id: TD-0001
- title: Missing type annotations in src/adapters
- description: Adapters lack type annotations which breaks strict mypy and makes refactors risky.
- module: src/adapters
- owner: module-owner:src/adapters
- priority: P0
- impact: High
- effort_estimate: 40h
- detection_date: 2026-03-29
- status: Open
- mitigation_plan: Add gradual typing per-file; enforce mypy on adapters after coverage.
- blocking: []
- evidence: .audit/mypy-adapters.txt
```

Example entry (discovered during audit)
```
- id: TD-0002
- title: Tests reference missing or moved module `src.apps.ImageAnalyze`
- description: Several tests import `src.apps.ImageAnalyze` but the package path is not present. Causes ImportError and blocks test runs.
- module: tests/apps/ImageAnalyze
- owner: module-owner:src/apps/experemental
- priority: P0
- impact: High
- effort_estimate: 8h
- detection_date: 2026-03-29
- status: Open
- mitigation_plan: Either restore `src/apps/ImageAnalyze` (if intended), update tests to point to new path, or quarantine/skip legacy tests and add bridging adapters.
- blocking: []
- evidence: .audit/20260329-045240/pytest-results.xml
```

Usage
- Add new TD entries as they are discovered during audit or development.
- Link entries to issues (e.g., GitHub issue IDs) and PRs.
- Quarterly review by `arch-team` to reprioritize and plan remediation sprints.

