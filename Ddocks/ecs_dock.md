# ECS (Entity Component System) Documentation

The BCor ECS module provides a performant and decoupled way to handle complex entity logic and world state, suitable for simulations, games, or massive agentic environments.

## Architecture
Bcor's ECS is built as a standard Domain Module, using the core patterns:
- **Aggregate Root**: `EcsWorld` manages the consistency boundary for all entities and components.
- **Components**: Plain data classes (Value Objects) stored in the world.
- **Systems**: Event handlers that react to `TickEvent` or other triggers to process entities.

## Core Components
### `EcsWorld`
Manages the lifecycle of entities and their components.
- `add_component(entity_id, component)`: Attaches data to an entity.
- `query(*component_types)`: Efficiently retrieves entities having all requested components.
- `check_collisions(entity_id, pos)`: Internal domain logic for spatial consistency.

### Systems
Systems are implemented as asynchronous handlers in `handlers.py`:
- `physics_system_handler`: The primary logic driver for movement and collision detection.

## Communication
- **Commands**: `MoveEntityCommand` for external world manipulation.
- **Events**: 
    - `TickEvent`: Drives the engine loop.
    - `CollisionDetectedEvent`: Emitted by the world aggregate when invariants are violated.
    - `ComponentAddedEvent`: Emitted for audit or reactive logic.

## Integration
To enable ECS in your application, add it to `app.toml`:
```toml
[modules]
enabled = ["ecs"]
```
