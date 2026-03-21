# Foundation Template: File-by-File Insights

This document breaks down the most valuable "agentic" and "architectural" insights from the `foundation_template` repository for future reference within the `BCor` project.

## 1. Workflow & Protocols (`_blueprint/`)

These files define the methodology for a design-first, agentic workflow.

| File Path | Key Insight / Value |
| :--- | :--- |
| `Filling_Plan.md` | **The P0-P6 Master Pipeline**: A clear sequence from raw intent → goals → features → research → use cases → tasks → sprint execution. Useful for structuring complex multi-agent features. |
| `protocols/meta/Metadata_Schema.md` | **Strict Traceability Contract**: Defines mandatory YAML fields (e.g., `parent_feat`) that connect every task back to a business goal. This allows automated "impact analysis". |
| `protocols/meta/Validation_Rules.md` | **Development Gates**: Defines "Hard Blocks" (e.g., G1: Task cannot exist if parent UseCase is not APPROVED). Ensures design before implementation. |
| `protocols/knowledge/H1_Pattern_Recognition.md` | **Automated Learning**: A protocol for agents to extract "Lessons Learned" whenever a fix moves from `NEEDS_FIX` to `APPROVED`. |
| `protocols/reverse/RE0_Codebase_Scanner.md` | **Agent Onboarding**: A systematic logic for an agent to "scan" an unfamiliar codebase and identify the tech stack and architecture. |

## 2. Enforcement & Automation (`_blueprint_server/`)

The implementation of the workflow enforcement.

| File Path | Key Insight / Value |
| :--- | :--- |
| `validate_traceability.py` | **Automated Graph Validator**: The Python logic that checks the `parent_*` links in YAML front-matter. |
| `artifact_index.py` | **RAG-Ready Metadata Index**: Logic that scans all markdown files, extracts YAML, and builds a queryable in-memory index. |

## 3. Architecture Wisdom (`.agents/skills/clean-architecture/`)

Clean Code principles adapted for agentic development.

| File Path | Key Insight / Value |
| :--- | :--- |
| `references/comp-screaming-architecture.md` | **Domain First**: Proposes organizing files by business domain (e.g., `ordering/`) rather than technical layer (`controllers/`). |
| `references/usecase-orchestrates-not-implements.md` | **Thin UseCases**: Rule that UseCase classes should only orchestrate, never implement business logic. |
| `references/frame-di-container-edge.md` | **Pure Core**: The Dependency Injection container should live at the very edge of the application. |
| `references/test-tests-are-architecture.md` | **TDD as Specs**: Highlighting that tests are the true architectural documentation. |

## 4. Infrastructure & Implementation (`src/`)

Core engine and utility patterns.

| File Path | Key Insight / Value |
| :--- | :--- |
| `foundation/core/bus.py` | **Lightweight Async Bus**: Simple `asyncio.create_task` based message bus for decoupled communication. |
| `foundation/di/container.py` | **Simplified DI Wrapper**: Uses `punq` for lightweight dependency injection. |
| `foundation/core/vfs.py` | **Virtual File System**: Layer for auditing file operations by agents. |

---

### Implementation Recommendations for BCor
1. **Traceability Lite**: Use `parent_goal` and `parent_feat` YAML fields for automated roadmap tracking.
2. **Automated Roadmapping**: Generate `Roadmap.md` automatically from individual feature/goal files.
3. **Research Spikes**: Formalize new module integrations using the `RS-` protocol.
