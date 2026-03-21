from src.core.module import BaseModule
from src.modules.ecs.handlers import handle_move_entity, handle_tick
from src.modules.ecs.messages import MoveEntityCommand, TickEvent


class EcsModule(BaseModule):
    """The ECS Engine Domain Module.

    Acts as a container for all game systems, routing events and configuring DI.
    """

    # Declarative routing map for systems
    command_handlers = {MoveEntityCommand: handle_move_entity}

    event_handlers = {TickEvent: [handle_tick]}
