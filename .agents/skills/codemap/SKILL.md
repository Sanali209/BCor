---
name: codemap
description: Generates visual maps of codebases, dependencies, and structures. Use for instant project context and navigation.
---


Codemap is a CLI tool and VSCode extension that generates visual maps of codebases, dependencies, and structures, designed to empower AI agents with instant project context. It's particularly useful in agentic workflows like yours with antigravity agents, RAG systems, and clean architecture projects.
Installation

Install the CLI via uv (Python tool manager) on macOS/Linux (use WSL on Windows):

text
curl -LsSf https://astral.sh/uv/install.sh | sh
uv tool install codemap

For VSCode extension, search "llm-codemap" in the marketplace from mk668a
fix if not worck

# Codemap Skill

`codemap` is a CLI tool that provides structural insights into your codebase. It's designed to help AI agents (like Antigravity) understand complex projects quickly.

## Usage

Run `codemap` from the project root.

### Basic commands

- `cm gen .`: Generate a code representation/map of the current directory.
- `cm gen -e .`: Generate a Mermaid entity graph of the project structure.
- `cm index`: Index the repository for RAG-based search with `cm ask`.
- `cm ask "How is X implemented?"`: Ask questions about the codebase.
- `cm help`: See all available options.

## When to use

- Before starting a new task to get an overview of the relevant modules.
- When you need to understand how different components interact.
- To identify which files are affected by a change.
- When documentation is sparse or outdated.

## Output

The output is formatted as Markdown or JSON, which is ideal for inclusion in agent prompts or for further analysis.
