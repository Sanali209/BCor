# BCor Technical Debt Registry (TDR)

## Purpose
This registry tracks architectural and implementation technical debt across the BCor monorepo. Each entry represents a structured debt item linked to specific source code or modules.

---

## 📜 Active Debt Items

| ID | Title | Module | Priority | Status | Mitigation Plan |
|:---|:---|:---|:---:|:---:|:---|
| **TD-0002** | Missing `ImageAnalyze` components | `tests/apps` | P0 | **MITIGATED** | Legacy tests moved to `legacy/sanali`. CI/CD no longer blocked. |
| **TD-0003** | Incomplete Core Domain Models | `assets` | P0 | **OPEN** | Fully implement `DocumentAsset`, `Album`, and `SmartAlbum` in `assets/domain/models.py`. |
| **TD-0004** | Redundant Direct IO (VFS Bypass) | `assets` | P1 | **OPEN** | Refactor `AssetIngestionService` to use the injected `VFS` instance instead of `os.walk`. |
| **TD-0005** | Invalid Typing in Experimental Apps | `apps/experemental` | P1 | **OPEN** | Fix `mypy` errors in `imgededupe` or move the entire `experemental` directory to `legacy/`. |
| **TD-0001** | Missing type annotations in adapters | `adapters` | P2 | **OPEN** | Gradual typing per-file in ORM and NATS adapters. |

---

## 📊 Detailed Records

### TD-0003: Incomplete Core Domain Models
- **Description**: Several core classes required for the Asset Explorer UI (`DocumentAsset`, `Album`, `SmartAlbum`) are currently implemented as empty stubs.
- **Impact**: Blocks full implementation of the File Triage and Grouping features.
- **Evidence**: `src/modules/assets/domain/models.py:L110-150`

### TD-0004: Redundant Direct IO (VFS Bypass)
- **Description**: `AssetIngestionService` performs native OS walking instead of using the `VfsProvider`.
- **Impact**: Prevents seamless transition to cloud storage (S3/Azure) without rewriting core logic.
- **Evidence**: `src/modules/assets/domain/services.py`

---
*Date of Last Audit: 2026-03-31*
