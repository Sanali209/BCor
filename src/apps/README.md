# Applications

Application entry points for the BCor framework. Each application is a standalone executable that boots the BCor `System` with specific modules and configurations.

## Available Applications

### `hello_app`
Minimal demonstration application showcasing core BCor patterns.
- **Purpose**: Getting started, learning BCor basics
- **Modules**: None (core only)
- **Entry**: `main.py`

### `ImageAnalyze`
Image analysis application with GUI (PySide6).
- **Purpose**: Image scanning, metadata extraction, analysis
- **Modules**: VFS, Analytics, LLM
- **Features**: PIL integration, multiprocessing, GUI

### `ImageDedup`
Image deduplication tool.
- **Purpose**: Find and manage duplicate images
- **Modules**: VFS, Analytics
- **Features**: Image comparison, grouping, batch operations

### `VFSSample`
Virtual File System demonstration.
- **Purpose**: Showcase VFS module capabilities
- **Modules**: VFS
- **Features**: File operations, multiple storage backends

### `default_app`
Base application template.
- **Purpose**: Template for creating new applications
- **Modules**: Configurable
- **Features**: Minimal boilerplate

## Application Structure

Each application follows this structure:
```
app_name/
├── app.toml        # Module manifest and settings
├── main.py         # Entry point
├── settings.py     # Application-specific settings (optional)
├── handlers.py     # Application-specific handlers (optional)
├── messages.py     # Application-specific messages (optional)
└── module.py       # Application module (optional)
```

## Creating a New Application

1. Copy `default_app/` as template
2. Edit `app.toml` to enable required modules:
```toml
[modules]
enabled = ["vfs", "analytics"]

[settings]
database_url = "sqlite+aiosqlite:///./app.db"
```

3. Implement `main.py`:
```python
from src.core.system import System

async def main():
    system = System.from_manifest("app.toml")
    await system.start()

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
```

4. Run the application:
```bash
uv run python -m src.apps.your_app.main
```

## Configuration

### `app.toml` Format
```toml
[modules]
enabled = ["module1", "module2"]

[module1]
# Module-specific settings

[settings]
# Global application settings
```

### Environment Variables
Applications load environment variables via `pydantic-settings`:
- Variables are validated at startup
- Missing required variables cause immediate failure (Fail-Fast)
- Use `.env` file for local development

## Related Documentation

- [ARCHITECTURE.md](../../ARCHITECTURE.md) — System architecture
- [DEVELOPER_GUIDE.md](../../DEVELOPER_GUIDE.md) — Development guide
- [How-to: Add New Module](../../Ddocks/How-tos/Add_New_Module.md) — Module creation guide