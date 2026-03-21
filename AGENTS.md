# AGENTS.md - BCor Project Guidelines

Welcome to the BCor project. As an AI agent working in this codebase, you MUST adhere to the following project guidelines and utilize the provided skills effectively.

## Project Constitution
**CRITICAL**: All agents MUST read and follow the [Project Constitution](file:///d:/github/BCor/Ddocks/Design_docks/constitution.md). 
This document outlines core principles including:
- **ADR First**: Architecture decisions guide implementation.
- **TDD Requirement**: Write failing tests before code.
- **uv Management**: Use `uv` for Python packages.
- **Linting Hygiene**: Follow the project's [linting strategy](file:///d:/github/BCor/Ddocks/Design_docks/specs/2026-03-19-linting-strategy.md).

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

## Agent Skills Directory
The following skills are available in `.agents/skills/`. Trigger them when their use case applies:

### Research & Discovery
- **`find-docs`**: Retrieves authoritative technical documentation using `context7`. Use for library/framework lookups.
- **`last30days`**: Research current trends on Reddit, X, YouTube, HN, etc. Use for gathering "state of the art" info.
- **`find-skills`**: Discover and install new agent skills from the open ecosystem.

### Planning & Architecture
- **`brainstorming`**: **MANDATORY** before any creative work. Explores intent and design before implementation.
- **`writing-plans`**: **MANDATORY** after brainstorming. Generates detailed implementation plans for complex tasks.
- **`excalidraw`**: Create diagrams, flowcharts, and wireframes programmatically.

### Implementation & Quality
- **`python-best-practices`**: Guidance on PEP 8, idiomatic patterns, and production-grade Python code.
- **`python-refactor`**: Systematic refactoring of Python code for maintainability and readability.
- **`refactor`**: Surgical code refactoring for any language (extract functions, rename variables, fix smells).
- **`code-documenter`**: Format and validate technical documentation (docstrings, JSDoc, OpenAPI).

### UI/UX & Design
- **`ui-ux-pro-max`**: Design intelligence for 50+ styles, palettes, and UX guidelines. Use for all front-end work.
- **`critique`**: Evaluation of design effectiveness from a UX perspective.
- **`web-design-guidelines`**: Audit UI code for compliance with Vercel Web Interface Guidelines.

### Specialized Tasks
- **`documentation`**: Write and maintain READMEs, runbooks, and architecture documents.
- **`documentation-writer`**: Expert documentation creation following the Diátaxis framework.
- **`skill-creator`**: Create or improve agent skills using iterative evaluation loops.
- **`codemap`**: **PRIMARY TOOL FOR NAVIGATION**. Generate visual maps of the codebase and dependencies.

---

## Navigation
Always use `codemap` to establish project context before starting a task.
Example: `codemap .` or `codemap src/module_name`

---

*Note: This file is a living document. Update it as new skills are added or project principles evolve.*
