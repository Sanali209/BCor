# AGENTS.md - BCor Project Guidelines

Welcome to the BCor project. As an AI agent working in this codebase, you MUST adhere to the following project guidelines and utilize the provided skills effectively.

## Project Constitution
**CRITICAL**: All agents MUST read and follow the [Project Constitution](Ddocks/Design_docks/constitution.md). 
This document outlines core principles including:
- **ADR First**: Architecture decisions guide implementation.
- **TDD Requirement**: Write failing tests before code.
- **uv Management**: Use `uv` for Python packages.
- **Linting Hygiene**: Follow the project's [linting strategy](Ddocks/Design_docks/specs/2026-03-19-linting-strategy.md).

---

## Developer Commands

### Run Tests
```bash
# All unit tests (TDD)
PYTHONPATH=. uv run pytest tests/unit/

# Single test file
PYTHONPATH=. uv run pytest tests/unit/path/to/test_file.py::test_function

# Specific package/module
PYTHONPATH=. uv run pytest tests/unit/ -k "pattern"
```

### Lint & Typecheck
```bash
uv run ruff check .      # Lint
uv run ruff format .   # Format
uv run mypy .          # Typecheck
```

**Order matters:** lint -> typecheck -> test

---

## MCP Servers & Use Cases
Use these MCP servers to extend your capabilities:

| Server | Use Case |
| :--- | :--- |
| **`context7`** | Retrieve up-to-date documentation and code examples for any library/framework. Use this instead of relying on training data for external APIs. |
| **`memory`** | Maintain a persistent knowledge graph of entities, relations, and observations. Use for tracking project-wide concepts and architectural patterns. |
| **`sequential-thinking`** | Dynamic problem-solving via structured, reflective thoughts. Use for complex architectural planning or debugging tasks that require backtracking. |
| **`whimsical-desktop`** | Collaborative visual design and documentation. Use for creating flowcharts, mindmaps, wireframes, and documentation in the Whimsical app. |

---

## Framework-Specific Notes

### BCor Framework
Load the `bcor-expert` skill for:
- Automated DI in handlers (don't manually get from container)
- Idempotent command handler design with retry policies
- Module configuration via `app.toml` + Pydantic settings
- Windows event loop policies (already in conftest)

### Windows Testing
Tests include Windows-specific event loop fixtures in `tests/conftest.py`. These prevent hangs but add ~100ms delay per test.

### App Structure
- Entry points: `src/apps/<app_name>/main.py`
- Modules: defined in respective app folders
- Legacy code: `legacy/` directory

---

*Note: This file is a living document. Update it as new skills are added or project principles evolve.*
