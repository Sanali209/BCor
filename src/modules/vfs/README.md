# VFS Module

The VFS (Virtual File System) module provides a unified abstraction for file system operations in BCor, leveraging the powerful `PyFilesystem2` library.

## Features

- **Unified API**: Interact with local files, memory, S3, FTP, etc., using the same interface.
- **Provider-based Lifecycle**: VFS instances are automatically managed and closed by the DI container.
- **Environment Aware**: Automatically overrides to `mem://` (in-memory) during tests.
- **DI Integration**: Fully integrated with Dishka for seamless injection into command handlers and services.

## Configuration

Add the following to your `app.toml`:

```toml
[vfs]
# Connection string (e.g., "osfs://./data", "mem://", "s3://bucket")
connection_string = "osfs://./storage"
```

## Usage

### In Command Handlers

Thanks to the DI-aware `MessageBus`, you can simply request `FS` in your handler signature:

```python
from fs.base import FS

async def my_handler(cmd: MyCommand, vfs: FS):
    vfs.writetext("hello.txt", "world")
```

### In Services

Inject `FS` via the constructor:

```python
class MyService:
    def __init__(self, vfs: FS):
        self.vfs = vfs
```

## Testing

When running tests, the VFS module automatically switches to `mem://` if not explicitly configured, ensuring tests are fast and isolated.
