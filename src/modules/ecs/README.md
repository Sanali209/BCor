# ECS (Entity Component System) Module

The `ecs` module implements a high-performance, decouple architecture for managing game world state and logic. It adapts traditional ECS patterns into the BCor framework's Clean Architecture.

## Core Concepts
- **Entity**: A simple unique identifier string.
- **Component**: Pure data-holding dataclasses (e.g., `PositionComponent`, `VelocityComponent`).
- **System**: Event handlers (`physics_system_handler`) that operate on entities possessing specific component combinations.
- **World Aggregate**: `EcsWorld` acts as the orchestrator and consistency boundary, managing component storage and queries.

## Key Features
- **Efficient Querying**: The `world.query()` method allows systems to quickly retrieve entity subsets based on component types.
- **Tick-Driven Logic**: Systems are triggered by `TickEvent`, ensuring deterministic updates.
- **Domain-Event Integration**: Collision detection and component changes emit standard BCor Events.

## Communication
- `TickEvent`: Drives the physics and logic systems.
- `MoveEntityCommand`: Manual override for entity positioning.
- `CollisionDetectedEvent`: Result of spatial analysis within the world aggregate.

## Orchestration
The `EcsModule` class maps the incoming events and commands to their respective systems, keeping the domain logic separated from infrastructure concerns.
