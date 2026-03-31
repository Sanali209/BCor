**ДИЗАЙН-ДОКУМЕНТ: Ядро и структура монорепозитория для модульного монолита**

**1. Архитектурная парадигма и стиль**
Система проектируется как **Модульный монолит (Modular Monolith)**, управляемый событиями (Event-Driven Architecture). Данный подход позволяет сохранить простоту единого развертывания и избежать сетевых издержек на начальном этапе, но при этом обеспечивает строгую логическую изоляцию бизнес-доменов (модулей).

Фундаментом системы выступает **Предметно-ориентированное проектирование (DDD)** и **Разделение ответственности команд и запросов (CQRS)**. Ядро системы отвечает за инверсию зависимостей (Dependency Inversion): бизнес-логика не зависит от низкоуровневых деталей, а опирается на абстракции.

**2. Структура монорепозитория (Repository Structure)**
Проект использует компоновку `src-layout`. Ниже представлена структура, отражающая текущее состояние кодовой базы.

```text
.
├── pyproject.toml           # Project metadata and dependencies (uv)
├── uv.lock                  # Deterministic dependency graph
├── app.toml                 # Global App Manifest (System discovery root)
├── src/                     # Source code
│   ├── core/                # Core Framework (System, MessageBus, UoW)
│   ├── modules/             # Business Modules (Bounded Contexts)
│   │   ├── agm/             # Aetheris Graph Mapper (Neo4j OGM)
│   │   ├── assets/          # Asset Explorer Core (Managed Files)
│   │   ├── vfs/             # Virtual File System (PyFilesystem2)
│   │   ├── llm/             # AI & LLM Connectivity
│   │   └── ...              # analytics, files, ecs, orders
│   ├── adapters/            # Infrastructure Adapters (TaskIQ, ORM)
│   └── entrypoints/         # Primary Entrypoints (FastAPI, Workers)
├── legacy/                  # Quarantine (Legacy/Experimental code)
│   └── sanali/              # Isolated Migration Stage
└── tests/                   # Testing Suite (TDD-driven)
```

**3. Архитектура и компоненты Ядра (The Core Framework)**
Ядро инкапсулирует сложность работы, предоставляя бизнес-модулям чистый декларативный API.

*   **Шина сообщений (Message Bus):** Built on the `bubus` library.
    *   **Commands:** Single-handler intent (routed via `register_command`).
    *   **Events:** Multi-handler announcements (routed via `register_event`).
*   **Единица работы (Unit of Work - UoW):** Context-managed transaction boundaries for cross-module consistency.
*   **Репозиторий (Repository):** Port/Adapter abstraction for persistence.
*   **Загрузчик / DI (Dependency Injection):** Powered by **Dishka**. 
    *   Modules are discovered via `app.toml` manifest using the `ModuleDiscovery` system in `src/core/system.py`.

**4. Распределенное выполнение (Async Infrastructure)**
Для тяжелых или долгих операций ядро использует внешние брокеры:
*   **Background Tasks:** `TaskIQ` integration with `NATS` for AI/IO heavy jobs.
*   **Event Traversal:** Synchronous causal tracing for event chains in the `MessageBus`.

**5. Разделение команд и запросов (CQRS Concepts)**
В ядре применяется концепция CQRS:
*   **Write Model:** State changes are captured via Aggregates and Command Handlers.
*   **Read Model:** Optimized views are provided via `AGMMapper` fluent queries or domain-specific projections.

**6. Наблюдаемость и отладка (Observability)**
*   **Tracing:** `OpenTelemetry` auto-tracing for message flow inside the bus.
*   **Logging:** Contextual logging using `loguru`.

**7. Стратегия тестирования (Test-Driven Development)**
Система следует строгому TDD. 
*   **WindowsLoopManager**: Specific lifecycle management to prevent event loop deadlocks on Windows during test teardowns.
*   **Pytest-Asyncio**: Seamless async test integration across all layers.

---
*Note: This doc is synchronized with the code as of March 2026. Code remains the primary reference point.*
