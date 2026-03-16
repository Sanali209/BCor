import logging
from src.core.monads import BusinessResult, success
from src.modules.ecs.messages import TickEvent, MoveEntityCommand
from src.modules.ecs.domain import PositionComponent, VelocityComponent
from src.modules.ecs.ports import EcsUnitOfWork

logger = logging.getLogger(__name__)

async def physics_system_handler(event: TickEvent, uow: EcsUnitOfWork):
    """The 'System' in ECS: Updates Positions based on Velocities."""
    with uow:
        # Load the default 'main' world.
        # In a real engine, the world ID might come from the event context or settings.
        world = await uow.worlds.get_world("main_scene")

        # Iterate over all entities with both Position and Velocity components
        for entity_id, (pos, vel) in world.query(PositionComponent, VelocityComponent):
            # Mutate the value object for speed (or replace it functionally)
            pos.x += vel.dx * event.delta_time
            pos.y += vel.dy * event.delta_time

            # Check collisions within the aggregate boundary
            world.check_collisions(entity_id, pos)

        uow.commit() # Flushes changes and collects new domain events (CollisionDetected)

async def handle_move_entity_command(cmd: MoveEntityCommand, uow: EcsUnitOfWork) -> BusinessResult:
    """A direct command to forcibly move an entity."""
    with uow:
        world = await uow.worlds.get_world("main_scene")
        pos = world.get_component(cmd.entity_id, PositionComponent)

        if not pos:
            raise ValueError(f"Entity {cmd.entity_id} missing PositionComponent")

        pos.x = cmd.target_x
        pos.y = cmd.target_y

        uow.commit()

    return success(True)
