# Hello BCor Application

The `hello_app` is a reference implementation demonstrating how to bootstrap and run a console-based application using the BCor framework.

## Overview
This application showcases:
- **Manifest-based Configuration**: Uses `app.toml` to define module paths and enabled modules.
- **System Bootstrapping**: Initializes the core `System` object, which handles dependency injection and message routing.
- **Custom IoC Overrides**: Demonstrates how to inject "fake" or specialized implementations (like `FakeUoW`) for specific application contexts (e.g., CLI).
- **Interactive Command Dispatch**: Uses the `MessageBus` to process user input as structured `Commands`.

## Configuration (`app.toml`)
```toml
[app]
app_name = "Hello BCor"
log_level = "DEBUG"

[modules]
paths = ["src.apps.hello_app.modules", "src.modules"]
enabled = ["greeting"]
```

## How to Run
From the project root:
```bash
python -m src.apps.hello_app.main
```
