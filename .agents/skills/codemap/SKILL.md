---
name: codemap
description: Generates visual maps of codebases, dependencies, and structures. Use for instant project context and navigation.
---

# Codemap Skill

`codemap` is a CLI tool and VSCode extension that generates visual maps of codebases, dependencies, and structures. It is essential for AI agents to establish project context and understand architectural patterns quickly.

## Installation & Environment

### Windows (Local)
The tool is typically installed via `uv tool install codemap`. On this system, it is located at:
`C:\Users\User\.local\bin\cm.exe`

If `cm` is not in your `PATH`, you must use the absolute path or add it to your session:
```powershell
$env:PATH += ";C:\Users\User\.local\bin"
```

### macOS/Linux
```bash
uv tool install codemap
```

## Usage

Run `cm` from the project root. For large projects, focus on specific subdirectories to avoid performance issues or recursion errors.

### Basic Commands
- `cm gen .`: Generate a code representation of the current directory.
- `cm gen src`: Generate a map of the `src` directory (recommended for large projects).
- `cm gen -e .`: Generate a Mermaid entity graph of the project structure.
- `cm index`: Index the repository for RAG-based search with `cm ask`.
- `cm ask "How is X implemented?"`: Ask questions about the codebase after indexing.
- `cm conf`: Create a default `.codemap.yml` configuration.

## Troubleshooting

### `RecursionError: maximum recursion depth exceeded`
This common issue on Windows occurs when the project structure is too deep or contains cycles.
- **Solution**: Use the `--exclude` flag to skip problematic directories (e.g., `.venv`, `node_modules`, `build`).
- **Optimization**: Run `cm gen` on a specific subdirectory (e.g., `cm gen src/core`) instead of the entire project root.
- **Config**: Create or edit `.codemap.yml` to strictly define `include` and `exclude` paths.

## Best Practices for Agents
1. **Context First**: Always run `cm gen src` (or a similar relevant path) before starting any task.
2. **Subdirectory Focus**: If the project is huge, map only the components you are working on.
3. **Index for Complex Queries**: If manual navigation is slow, use `cm index` and `cm ask`.
4. **Absolute Paths**: On Windows, check `C:\Users\User\.local\bin\cm.exe` if the command is not found.
