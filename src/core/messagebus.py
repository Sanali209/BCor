from typing import Any, Callable, Dict, Type, List
import logging

from src.core.messages import Message, Command, Event
from src.core.unit_of_work import AbstractUnitOfWork

logger = logging.getLogger(__name__)

class MessageBus:
    """Central dispatcher for Commands and Events."""

    def __init__(
        self,
        uow: AbstractUnitOfWork,
        event_handlers: Dict[Type[Event], List[Callable]],
        command_handlers: Dict[Type[Command], Callable]
    ):
        self.uow = uow
        self.event_handlers = event_handlers
        self.command_handlers = command_handlers
        self.queue: List[Message] = []

    async def handle(self, message: Message):
        self.queue = [message]
        while self.queue:
            msg = self.queue.pop(0)
            if isinstance(msg, Event):
                await self._handle_event(msg)
            elif isinstance(msg, Command):
                await self._handle_command(msg)
            else:
                logger.warning(f"Unknown message type {type(msg)}")

    async def _handle_event(self, event: Event):
        for handler in self.event_handlers.get(type(event), []):
            try:
                # Handlers can optionally request uow if needed via kwargs or DI
                # Here we pass it directly per architecture requirements snippet
                await handler(event, uow=self.uow)
                self.queue.extend(self.uow.collect_new_events())
            except Exception as e:
                logger.exception(f"Ошибка обработки события {event}: {e}")
                continue # Изоляция сбоев

    async def _handle_command(self, command: Command):
        try:
            handler = self.command_handlers[type(command)]
            await handler(command, uow=self.uow)
            self.queue.extend(self.uow.collect_new_events())
        except KeyError:
            logger.exception(f"Нет обработчика для команды {command}")
            raise # Проброс ошибки наверх
        except Exception as e:
            logger.exception(f"Ошибка обработки команды {command}: {e}")
            raise # Проброс ошибки наверх (Fail Fast)
