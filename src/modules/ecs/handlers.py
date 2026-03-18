import logging
from src.core.monads import BusinessResult, success
from src.modules.ecs.messages import TickEvent, MoveEntityCommand
from src.modules.ecs.domain import PositionComponent, VelocityComponent
from src.modules.ecs.ports import EcsUnitOfWork

logger = logging.getLogger(__name__)


async def physics_system_handler(event: TickEvent, uow: EcsUnitOfWork):
    """Processes physics updates across all entities in the world.

    This 'System' implementation iterates over entities with both 
    `PositionComponent` and `VelocityComponent`, updates their 
    coordinates based on `delta_time`, and triggers collision checks.

    Args:
        event: The tick event containing timing information.
        uow: The ECS-specific Unit of Work.
    """
    with uow:
        # Load the default 'main' world.
        world = await uow.worlds.get_world("main_scene")

        # Iterate over all entities with both Position and Velocity components
        for entity_id, (pos, vel) in world.query(PositionComponent, VelocityComponent):
            # Update position based on velocity and time delta
            pos.x += vel.dx * event.delta_time
            pos.y += vel.dy * event.delta_time

            # Check collisions within the aggregate boundary
            world.check_collisions(entity_id, pos)

        uow.commit()


async def handle_move_entity_command(
    cmd: MoveEntityCommand, uow: EcsUnitOfWork
) -> BusinessResult:
    """Directly updates an entity's position.

    Used for manual overrides or teleportation logic, bypassing the 
    normal physics system.

    Args:
        cmd: The command specifying the target coordinates.
        uow: The ECS-specific Unit of Work.

    Returns:
        A BusinessResult indicating success or failure.
    
    Raises:
        ValueError: If the entity does not have a PositionComponent.
    """
    with uow:
        world = await uow.worlds.get_world("main_scene")
        pos = world.get_component(cmd.entity_id, PositionComponent)

        if not pos:
            raise ValueError(f"Entity {cmd.entity_id} missing PositionComponent")

        pos.x = cmd.target_x
        pos.y = cmd.target_y

        uow.commit()

    return success(True)
