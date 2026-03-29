# Monorepo Audit Template (BCor)

Date: 2026-03-29

Purpose
- Шаблон и runbook для проведения аудита монорепозитория BCor: команды для PowerShell, чек-лист evidence, и инструкции по проверке `pyproject.toml` и CI readiness.

Scope
- Paths: `src/`, `tests/`, `src/apps/`, `src/modules/`, `src/adapters/`, `pyproject.toml`, `uv.lock`, `Ddocks/`.

Tools & Methods
- `uv` (package manager / runner)
- `ruff` (linting), `mypy` (typing), `pytest` (tests)
- `pip` (local checks), python scripts (inventory)

Evidence checklist
1. Module manifest (README present)
2. Unit test run logs (`.audit/pytest-results.xml`)
3. Lint report (`.audit/ruff-report.json`)
4. Typing report (`.audit/mypy.txt`)
5. Coverage report (`.audit/coverage.xml`)
6. Dependency snapshot (`uv.lock`) and `pip check` (`.audit/pip-check.txt`)
7. QUARANTINE.md or README flags for experimental modules
8. Inventory file `Ddocks/Design_docks/specs/monorepo-inventory.md`

PowerShell Commands (run from repo root)

Install / sync environment
```powershell
uv venv ; uv sync ; uv run python -m pip install -U pip setuptools wheel
```

Lint (ruff)
```powershell
uv ruff . --fix
uv ruff check . --format=json > .audit/ruff-report.json
```

Type-check (mypy)
```powershell
uv mypy src --config-file pyproject.toml --show-error-codes > .audit/mypy.txt
```

Tests + Coverage
```powershell
# Ensure Python can import the top-level `src` package
# In PowerShell set PYTHONPATH to the repo root so `import src...` works
$env:PYTHONPATH = "$PWD"
uv run python -m pytest tests -q --maxfail=1 --junitxml=.audit/pytest-results.xml
# Coverage run (use coverage module to avoid pytest plugin issues)
uv run python -m pip install -U coverage pytest-cov
uv run python -m coverage run -m pytest tests -q
uv run python -m coverage xml -o .audit/coverage.xml
```

Validate pyproject.toml (basic)
```powershell
uv python - <<'PY'
import tomllib
with open('pyproject.toml','rb') as f:
    toml = tomllib.load(f)
print('pyproject keys:', list(toml.keys()))
PY
```

Dependency check
```powershell
uv python -m pip check > .audit/pip-check.txt
```

Inventory scanner (suggestion)
- Create a small python script `tools/generate_inventory.py` to scan `src/` for top-level packages, check for README, tests, and QUARANTINE.md and emit `monorepo-inventory.md`.

pyproject.toml consolidation checklist
1. Ensure `[tool.ruff]`, `[tool.mypy]`, and `[tool.pytest.ini_options]` exist at root (or documented overrides).
2. Run `uv ruff .` and ensure no parsing errors.
3. Run `uv mypy src` and ensure config is applicable.
4. Verify `uv.lock` matches declared dependencies.

Artifacts storage
- Save all outputs to `.audit/<timestamp>/` and copy key artifacts to `Ddocks/Design_docks/specs/audit-artifacts/<timestamp>/` for provenance.

Reporting
- Executive summary (1–2 pages): high-level findings, critical blockers, P0 items.
- Detailed report: full evidence, logs, per-module findings, TECH_DEBT_REGISTRY entries.

