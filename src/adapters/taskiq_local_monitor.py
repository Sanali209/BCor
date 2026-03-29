import json
from datetime import datetime
from taskiq.abc.middleware import TaskiqMiddleware
from taskiq.message import TaskiqMessage
from taskiq.result import TaskiqResult
from typing import Any

class LocalMonitorMiddleware(TaskiqMiddleware):
    """Middleware that prints task events to stdout for GUI tracking."""
    
    def _emit(self, event_type: str, data: dict):
        payload = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            **data
        }
        # Special prefix for the companion app to pick up
        print(f"[BCOR_TASK] {json.dumps(payload)}", flush=True)

    async def post_send(self, message: TaskiqMessage) -> None:
        self._emit("queued", {
            "task_id": message.task_id,
            "task_name": message.task_name,
            "labels": message.labels
        })

    async def pre_execute(self, message: TaskiqMessage) -> TaskiqMessage:
        self._emit("started", {
            "task_id": message.task_id,
            "task_name": message.task_name
        })
        return message

    async def post_execute(self, message: TaskiqMessage, result: TaskiqResult[Any]) -> None:
        status = "success" if result.error is None else "failed"
        self._emit("executed", {
            "task_id": message.task_id,
            "status": status,
            "execution_time": result.execution_time,
            "error": str(result.error) if result.error else None
        })
