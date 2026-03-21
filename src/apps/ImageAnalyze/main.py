from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, cast

from loguru import logger

# Add project root to sys.path to allow direct execution
root_path = str(Path(__file__).resolve().parent.parent.parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from dishka import Provider, Scope, provide  # noqa: E402

from src.apps.ImageAnalyze.messages import LaunchLegacyGuiCommand  # noqa: E402
from src.core.messagebus import MessageBus  # noqa: E402
from src.core.system import System  # noqa: E402
from src.core.unit_of_work import AbstractUnitOfWork  # noqa: E402


class DefaultUoW(AbstractUnitOfWork):
    def _commit(self) -> None:
        pass

    def rollback(self) -> None:
        pass

    def _get_all_seen_aggregates(self) -> list[Any]:  # noqa: ANN401
        return []


class UoWProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_uow(self) -> AbstractUnitOfWork:
        return DefaultUoW()


async def run_image_analyze() -> None:
    manifest_path = Path(__file__).parent / "app.toml"
    system = System.from_manifest(manifest_path)
    system.providers.append(UoWProvider())

    logger.info("Starting Image Analyze App...")
    await system.start()

    try:
        async with system.container() as container:
            bus = await container.get(MessageBus)
            logger.info("--- Launching GUI ---")

            res = await bus.dispatch(LaunchLegacyGuiCommand())
            res = await res.event_result()

            if res.is_success():
                logger.info("GUI exited successfully.")
            else:
                logger.error(f"GUI exited with error: {res.unwrap_err()}")

    finally:
        await system.stop()


if __name__ == "__main__":
    asyncio.run(run_image_analyze())
