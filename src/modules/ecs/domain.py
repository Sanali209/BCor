from collections import defaultdict
from collections.abc import Iterator
from dataclasses import dataclass
from typing import Any

from src.core.domain import Aggregate
from src.modules.ecs.messages import CollisionDetectedEvent, ComponentAddedEvent


# --- Basic ECS Components (Data-only structs) ---
@dataclass
class PositionComponent:
    """ECS Component storing 2D spatial coordinates.

    Attributes:
        x: Horizontal position in world units.
        y: Vertical position in world units.
    """

    x: float
    y: float


@dataclass
class VelocityComponent:
    """ECS Component storing 2D movement vectors.

    Attributes:
        dx: Horizontal velocity (units per second).
        dy: Vertical velocity (units per second).
    """

    dx: float
    dy: float


# --- ECS World Aggregate ---
class EcsWorld(Aggregate):
    """The Root Aggregate acting as the ECS consistency boundary.

    The EcsWorld manages entities and their associated components,
    providing efficient query mechanisms for systems and ensuring
    domain invariants (like collision rules) are maintained.

    Attributes:
        world_id: Unique identifier for the game world/scene.
    """

    def __init__(self, world_id: str):
        """Initializes a new ECS World.

        Args:
            world_id: Unique identifier for this scene.
        """
        super().__init__()
        self.world_id = world_id

        # Component Type -> {Entity ID -> Component Instance}
        self._components: dict[type, dict[str, Any]] = defaultdict(dict)

    def add_component(self, entity_id: str, component: Any) -> None:
        """Adds a component to a specific entity and emits an event.

        Args:
            entity_id: The ID of the target entity.
            component: The component instance to attach.
        """
        comp_type = type(component)
        self._components[comp_type][entity_id] = component
        self.add_event(ComponentAddedEvent(entity_id=entity_id, component_type=comp_type.__name__))

    def get_component(self, entity_id: str, comp_type: type) -> Any:
        """Retrieves a specific component for an entity.

        Args:
            entity_id: The ID of the entity.
            comp_type: The type of component to fetch.

        Returns:
            The component instance if found, otherwise None.
        """
        return self._components[comp_type].get(entity_id)

    def query(self, *component_types: type) -> Iterator[tuple[str, list[Any]]]:
        """Performs a fast join query across multiple component types.

        Retrieves all entities that possess AT LEAST all of the specified
        component types.

        Args:
            *component_types: One or more component types to filter by.

        Yields:
            Tuples of (entity_id, [component_instances]).
        """
        if not component_types:
            return

        # Start with entities that have the first component
        base_entities = set(self._components[component_types[0]].keys())

        # Intersect with entities having the rest of the components
        for comp_type in component_types[1:]:
            base_entities.intersection_update(self._components[comp_type].keys())

        # Yield entity_id and the requested components
        for entity_id in base_entities:
            yield (
                entity_id,
                [self._components[comp_type][entity_id] for comp_type in component_types],
            )

    def check_collisions(self, entity_id: str, pos: PositionComponent) -> None:
        """Internal domain logic to detect spatial overlaps.

        Executes a spatial query within the world boundary and emits
        CollisionDetectedEvent if entities overlap.

        Args:
            entity_id: The entity performing the check.
            pos: The current position used for collision testing.
        """
        for other_id, comps in self.query(PositionComponent):
            if other_id == entity_id:
                continue
            other_pos: PositionComponent = comps[0]
            if abs(other_pos.x - pos.x) < 0.1 and abs(other_pos.y - pos.y) < 0.1:
                self.add_event(CollisionDetectedEvent(entity_a=entity_id, entity_b=other_id))
