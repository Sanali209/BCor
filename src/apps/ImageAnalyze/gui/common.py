import logging

from src.common.concurrency import AsyncWorker
from src.core.messagebus import MessageBus
from src.core.messages import Command

logger = logging.getLogger(__name__)


class AsyncCommandWorker(AsyncWorker):
    """Специализированный воркер для диспетчеризации команд через MessageBus."""

    def __init__(self, bus: MessageBus, command: Command):
        # Передаем метод bus.dispatch как корутину для выполнения
        super().__init__(bus.dispatch, command)
        self.command = command

    def run(self) -> None:
        # Переопределяем run, чтобы возвращать саму команду (в ней результаты)
        super().run()
        # В AsyncWorker.run результат emit-ится как результат coro_func.
        # Для MessageBus.dispatch это просто None (результаты пишутся в cmd.results).
        # Но мы хотим emit-ить саму команду в сигнале finished.
        # Так как super().run() уже сделал emit(None) (или результата coro),
        # мы можем либо изменить базовый класс, либо просто переопределить здесь.
        pass

    # На самом деле, лучше изменить AsyncWorker, чтобы он принимал callback для результата,
    # или просто здесь сделать как было, но используя общую логику loop.
