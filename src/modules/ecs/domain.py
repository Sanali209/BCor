from typing import Any, Iterator, List, Tuple, Dict, Type
from collections import defaultdict
from dataclasses import dataclass

from src.core.domain import Aggregate
from src.modules.ecs.messages import ComponentAddedEvent, CollisionDetectedEvent

# --- Basic ECS Components (Data-only structs) ---
@dataclass
class PositionComponent:
    x: float
    y: float

@dataclass
class VelocityComponent:
    dx: float
    dy: float

# --- ECS World Aggregate ---
class EcsWorld(Aggregate):
    """The Root Aggregate acting as the ECS consistency boundary."""

    def __init__(self, world_id: str):
        super().__init__()
        self.world_id = world_id

        # Component Type -> {Entity ID -> Component Instance}
        self._components: Dict[Type, Dict[str, Any]] = defaultdict(dict)

    def add_component(self, entity_id: str, component: Any) -> None:
        """Add a component to an entity."""
        comp_type = type(component)
        self._components[comp_type][entity_id] = component
        self.add_event(ComponentAddedEvent(
            entity_id=entity_id,
            component_type=comp_type.__name__
        ))

    def get_component(self, entity_id: str, comp_type: Type) -> Any:
        """Retrieve a specific component for an entity."""
        return self._components[comp_type].get(entity_id)

    def query(self, *component_types: Type) -> Iterator[Tuple[str, List[Any]]]:
        """Fast retrieval of entities containing ALL specified component types."""
        if not component_types:
            return

        # Start with entities that have the first component
        base_entities = set(self._components[component_types[0]].keys())

        # Intersect with entities having the rest of the components
        for comp_type in component_types[1:]:
            base_entities.intersection_update(self._components[comp_type].keys())

        # Yield entity_id and the requested components
        for entity_id in base_entities:
            yield entity_id, [self._components[comp_type][entity_id] for comp_type in component_types]

    def check_collisions(self, entity_id: str, pos: PositionComponent) -> None:
        """Domain logic to check collisions internally within the aggregate boundary."""
        # Simple dummy logic for demonstration:
        # If another entity has the exact same position, fire a collision event.
        for other_id, comps in self.query(PositionComponent):
            if other_id == entity_id:
                continue
            other_pos: PositionComponent = comps[0]
            if abs(other_pos.x - pos.x) < 0.1 and abs(other_pos.y - pos.y) < 0.1:
                self.add_event(CollisionDetectedEvent(entity_a=entity_id, entity_b=other_id))
