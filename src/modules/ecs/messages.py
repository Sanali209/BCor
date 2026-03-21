from src.core.messages import Command, Event


# --- System Events ---
# --- System Events ---
class TickEvent(Event):
    """Drives the game loop and orchestrates all systems.

    Attributes:
        delta_time: Elapsed time since the last tick in seconds.
        current_tick: Monotonically increasing tick counter.
    """

    delta_time: float
    current_tick: int


# --- Domain Events ---
class ComponentAddedEvent(Event):
    """Event emitted when a component is added to an entity.

    Attributes:
        entity_id: The identifier of the entity.
        component_type: The string name of the component type.
    """

    entity_id: str
    component_type: str


class CollisionDetectedEvent(Event):
    """Event emitted when two entities overlap in space.

    Attributes:
        entity_a: First entity in the collision.
        entity_b: Second entity in the collision.
    """

    entity_a: str
    entity_b: str


# --- Domain Commands ---
class MoveEntityCommand(Command):
    """Command to forcibly set an entity's position.

    Attributes:
        entity_id: Targeted entity.
        target_x: New horizontal coordinate.
        target_y: New vertical coordinate.
    """

    entity_id: str
    target_x: float
    target_y: float
