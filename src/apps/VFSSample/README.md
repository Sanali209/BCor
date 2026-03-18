# VFSSample App

A simple console application demonstrating the core functionality of the BCor VFS (Virtual File System) module.

## Features

- **Command-Based Interface**: Uses the `MessageBus` to dispatch commands (`WriteFileCommand`, `ReadFileCommand`, `ListDirCommand`).
- **DI-Aware Handlers**: Handlers automatically receive the `FS` dependency from the DI container.
- **Bootstrapping**: Demonstrates how to initialize a multi-module system using `app.toml`.

## How to Run

1. Ensure your `app.toml` is configured:

```toml
[vfs]
connection_string = "osfs://./storage"

[vfssample]
# No specific settings for VFSSample yet
```

2. Run the application:

```bash
py -m src.apps.VFSSample.main
```

## Architecture

The app follows the standard BCor pattern:

- `messages.py`: Defines commands and events.
- `handlers.py`: Implements domain logic (writing, reading, listing). Handlers are thin and receive dependencies via DI.
- `module.py`: Registers handlers and providers.
- `main.py`: Composition root that bootstraps the `System` and dispatches commands.

## Example Flow

The sample app performs the following:
1. Writes "Hello BCor VFS!" to `example.txt`.
2. Verifies the write by reading it back.
3. Lists the contents of the root directory.
