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

## MCP Servers & Use Cases
Use these MCP servers to extend your capabilities:

| Server | Use Case |
| :--- | :--- |
| **`context7`** | Retrieve up-to-date documentation and code examples for any library/framework. Use this instead of relying on training data for external APIs. |
| **`memory`** | Maintain a persistent knowledge graph of entities, relations, and observations. Use for tracking project-wide concepts and architectural patterns. |
| **`sequential-thinking`** | Dynamic problem-solving via structured, reflective thoughts. Use for complex architectural planning or debugging tasks that require backtracking. |
| **`whimsical-desktop`** | Collaborative visual design and documentation. Use for creating flowcharts, mindmaps, wireframes, and documentation in the Whimsical app. |



---

*Note: This file is a living document. Update it as new skills are added or project principles evolve.*
