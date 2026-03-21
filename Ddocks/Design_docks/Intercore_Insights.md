# Intercore Framework & Speckit Workflow Insights

## 1. Unidirectional Data Flow (UDF) Architecture
Intercore prioritizes a "Single Source of Truth" via a centralized store that projects onto various UI toolkits.

### Core Implementation (`libs/base_framework/src/base_framework/gui/store.py`)
- **Immutable State**: States are `Pydantic` models with `frozen=True`.
- **Atomic Updates**: Uses `asyncio.Lock` during `dispatch` to prevent race conditions during state transitions.
- **Versioning**: Each state update increments a `version` counter and updates `last_updated` timestamp, enabling efficient synchronization with rendering layers.
- **Observer Pattern**: Simple `subscribe(callback)` registration for UI components to listen for state deltas.

## 2. Reversible Command System
Encapsulates operations into commands that can be undone/redone.

### Command Pattern (`libs/base_framework/src/base_framework/command_system/manager.py`)
- **Protocol-Based**: Commands must implement `async def execute()` and `async def undo()`.
- **Manager Logic**:
  - `run(command)`: Executes and pushes to `undo_stack`. Clears `redo_stack`.
  - `undo()`: Pops from `undo_stack`, calls `undo()`, pushes to `redo_stack`.
  - `redo()`: Pops from `redo_stack`, calls `execute()`, pushes to `undo_stack`.

## 3. Speckit: The Agentic Protocol
Intercore defines a "Speckit" workflow in `.agent/workflows/` that enforces a phased, high-rigor development cycle for AI agents.

### The Phased Workflow
1. **Phase 0: Research (`speckit.analyze.md`)**: Checks `spec.md`, `plan.md`, and `tasks.md` for consistency *before* any code is written. Mandatory "Constitution Check".
2. **Phase 1: Design (`speckit.plan.md`)**: Generates technical design artifacts:
   - `data-model.md`: Entity relationships and validation rules.
   - `contracts/`: API or interface definitions.
   - `quickstart.md`: Minimal instructions for verification.
3. **Phase 2: Planning (`speckit.tasks.md`)**: Breaks the design into granular, parallelizable tasks [P] grouped by User Story.
4. **Phase 3: Phased Implementation**:
   - **Foundational**: Core infrastructure (DB, Auth, Routing) must be 100% complete before User Stories begin.
   - **User Stories**: Implemented and tested independently.

### Key Rules for Agents
- **ADR First**: No implementation without a plan.
- **TDD Requirement**: Write failing tests before implementation.
- **Strict Traceability**: All tasks must map back to User Stories in the spec.
- **Parallelization**: Tasks marked with `[P]` are safe for concurrent execution by multiple agent threads.

## 4. Messaging & Event Bus
- **Simple Decorators**: `@subscribe(EventType)` for declarative event handling.
- **Class-Name Topics**: Uses the class name of the message object as the lookup key in the `MessageBus`.
- **Concurrent Notification**: `publish(message)` uses `asyncio.gather` for all subscribers.

---

## 5. Takeaways for BCor
1. **Adopt Speckit Phasing**: Use the "Setup -> Foundational -> User Story" progression for BCor modules.
2. **Implement Command Manager**: For complex BCor operations (like image processing or data migrations), wrap logic in `Command` objects to allow safe reversal.
3. **Formalize State**: Consider moving critical BCor module states to frozen Pydantic models with versioning for better observability.
4. **Protocol Templates**: Copy the `.specify/templates/` to BCor's `Ddocks/Reference/Blueprint/` to standardize our planning process.
