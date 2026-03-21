from __future__ import annotations

"""Инструменты для работы с многопоточностью и интеграции asyncio с GUI-фреймворками."""

import asyncio
import logging
from typing import Any, Callable

from PySide6.QtCore import QThread, Signal

logger = logging.getLogger(__name__)


class AsyncWorker(QThread):
    """Базовый поток для запуска асинхронных задач в Qt.

    Создает собственный event loop в потоке, чтобы избежать конфликтов с главным циклом.
    """

    finished = Signal(object)

    def __init__(self, coro_func: Callable[..., Any], *args: Any, **kwargs: Any) -> None:
        super().__init__()
        self.coro_func = coro_func
        self.args = args
        self.kwargs = kwargs

    def run(self) -> None:
        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            result = loop.run_until_complete(self.coro_func(*self.args, **self.kwargs))
            loop.close()
            self.finished.emit(result)
        except Exception as e:
            logger.error(f"Async worker failed: {e}")
            self.finished.emit(None)
