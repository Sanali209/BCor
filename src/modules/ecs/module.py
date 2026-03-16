from src.core.module import BaseModule
from src.modules.ecs.messages import TickEvent, MoveEntityCommand
from src.modules.ecs.handlers import physics_system_handler, handle_move_entity_command

from dishka import Provider, Scope, provide
from src.modules.ecs.ports import EcsUnitOfWork

class EcsModule(BaseModule):
    """The ECS Engine Domain Module.

    Acts as a container for all game systems, routing events and configuring DI.
    """

    # Declarative routing map for systems
    command_handlers = {
        MoveEntityCommand: handle_move_entity_command
    }

    event_handlers = {
        TickEvent: [physics_system_handler]
    }
