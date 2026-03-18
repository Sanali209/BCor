# Analytics Module

The `analytics` module demonstrates how BCor handles computationally expensive or long-running tasks using background workers.

## Core Concepts
- **Background Delegation**: Commands received by the `MessageBus` are analyzed, and heavy work is offloaded to `TaskIQ` workers.
- **Asynchronous Execution**: The main application remains responsive while complex reports are generated in the background.

## Components
- `GenerateReportCommand`: Primary entry point for analytics requests.
- `build_heavy_report_task`: A `broker.task` decorated function that performs the actual computation.
- `AnalyticsModule`: Orchestrates the command routing.

## Workflow
1. User sends a `GenerateReportCommand`.
2. `AnalyticsModule` receives the command and calls `.kiq()` on the task.
3. TaskIQ dispatches the job via NATS (or InMemoryBroker in tests).
4. The system immediately returns a `task_id` to the user for status tracking.
