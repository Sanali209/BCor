from src.core.messages import Event, Command

# --- System Events ---
class TickEvent(Event):
    """Tick event that drives the game loop and all systems."""
    delta_time: float
    current_tick: int

# --- Domain Events ---
class ComponentAddedEvent(Event):
    entity_id: str
    component_type: str

class CollisionDetectedEvent(Event):
    entity_a: str
    entity_b: str

# --- Domain Commands ---
class MoveEntityCommand(Command):
    entity_id: str
    target_x: float
    target_y: float
