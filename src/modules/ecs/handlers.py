from src.common.monads import BusinessResult, success
from src.modules.ecs.domain import PositionComponent, VelocityComponent
from src.modules.ecs.messages import MoveEntityCommand, TickEvent
from src.modules.ecs.ports import EcsUnitOfWork


async def handle_tick(event: TickEvent, uow: EcsUnitOfWork) -> None:
    """Handles the game tick, updating all entities."""
    with uow:
        world = await uow.worlds.get_world("main_scene")
        # Move system: iterate all entities with both Position + Velocity
        for entity_id, components in world.query(PositionComponent, VelocityComponent):
            pos: PositionComponent = components[0]
            vel: VelocityComponent = components[1]
            pos.x += vel.dx
            pos.y += vel.dy
            world.check_collisions(entity_id, pos)
        uow.commit()


async def handle_move_entity(cmd: MoveEntityCommand, uow: EcsUnitOfWork) -> BusinessResult:
    """Handles an explicit move command for an entity."""
    with uow:
        world = await uow.worlds.get_world("main_scene")
        pos = world.get_component(cmd.entity_id, PositionComponent)
        if not pos:
            raise ValueError(f"Entity {cmd.entity_id} missing PositionComponent")

        pos.x = cmd.target_x
        pos.y = cmd.target_y
        uow.commit()
        return success(True)
