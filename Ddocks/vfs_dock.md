# VFS Module Specification

The VFS (Virtual File System) module provides a unified abstraction for file system operations in BCor, leveraging the `PyFilesystem2` library.

## Architecture

The VFS module is implemented as a standard BCor module with a dedicated provider.

### Core Components

- **`VfsSettings`**: Pydantic settings for configuring the VFS (e.g., `connection_string`).
- **`VfsProvider`**: Dishka provider that manages the `FS` instance lifecycle. It uses a generator-based provider to ensure `vfs.close()` is called when the scope ends.
- **`VfsModule`**: The module entry point that exposes the provider and settings.

### DI Integration

The VFS module is fully integrated with the BCor DI container. The `FS` instance is provided at the `Scope.APP` level by default, but can be overridden as needed.

The `MessageBus` has been enhanced to automatically inject `FS` (and other container-provided dependencies) into command handlers based on their type hints.

## Configuration

The VFS module is configured via `app.toml`:

```toml
[vfs]
connection_string = "osfs://./storage"
```

Supported protocols include `osfs`, `mem`, `s3`, `ftp`, `tar`, `zip`, etc., as per `PyFilesystem2` documentation.

## Test Mode

The VFS module automatically detects when it is running in a test environment (e.g., when no `connection_string` is provided or during execution of `test_vfs_module.py`) and defaults to `mem://` for fast, isolated, in-memory storage.

## Handlers

Command handlers can request the `FS` dependency directly:

```python
async def handle_write(cmd: WriteCommand, vfs: FS):
    vfs.writetext(cmd.path, cmd.content)
```
