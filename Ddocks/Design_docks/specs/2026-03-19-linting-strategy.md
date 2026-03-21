# Design: Modern Linting Strategy (Ruff + Mypy)

**Status:** Approved (Approach 1)

## Context
With the adoption of Python 3.12+ (PEP 695 generics) and `uv` for package management, we need a high-performance linting stack that reinforces the project's "Code First" and "TDD" principles without being overly bureaucratic.

## Requirements
- **All-in-one**: Ruff replaces multiple legacy tools (`flake8`, `isort`, `black`).
- **Type-Safe**: Mypy enforces strict typing for the new generics syntax.
- **No Pre-commit**: Periodic manual/CI runs instead of blocking commits.
- **Constitutional**: Explicitly documented in the project constitution.

## Architecture

### 1. Configuration (pyproject.toml)
Consolidate all linter and type-checker settings into the root `pyproject.toml`.

#### Ruff Configuration
- **Line Length**: 120 (consistency with current `.flake8`).
- **Enabled Rules**:
  - `E`, `W`: Pycodestyle (errors/warnings).
  - `F`: Pyflakes (logical errors).
  - `B`: Bugbear (common pitfalls).
  - `I`: Isort (import sorting).
  - `UP`: Pyupgrade (modern syntax).
  - `PT`: Pytest specific rules (matches our TDD focus).
  - `ANN`: Annotations (enforces the type-safe goal).

#### Mypy Configuration
- **Checkers**: Enable `strict = true` to fully utilize 3.12 generics.
- **Handling**: Ignore missing imports for third-party libraries without stubs.

### 2. File Cleanup
- **DELETE**: `.flake8` (replaced by Ruff).

### 3. Constitution Update
Add Rule #5 to `constitution.md`:
> 5. periodically run linters (Ruff and Mypy)

## Verification Plan
1.  **Ruff**: `uv run ruff check .` and `uv run ruff format .` (dry-run).
2.  **Mypy**: `uv run mypy .`.
3.  **Constitution**: Check alignment with other ADRs (0005, 0006).
