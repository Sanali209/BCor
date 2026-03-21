import asyncio
import os
import sys
from pathlib import Path

# Add project root to sys.path
root_path = str(Path(__file__).resolve().parent.parent.parent.parent)
if root_path not in sys.path:
    sys.path.insert(0, root_path)

from dishka import Provider, Scope, provide  # noqa: E402
from loguru import logger  # noqa: E402

from src.apps.ImageDedup.domain.project import ImageDedupProject  # noqa: E402
from src.apps.ImageDedup.messages import LaunchImageDedupCommand  # noqa: E402
from src.core.domain import Aggregate  # noqa: E402
from src.core.messagebus import MessageBus  # noqa: E402
from src.core.system import System  # noqa: E402
from src.core.unit_of_work import AbstractUnitOfWork  # noqa: E402


class DefaultUoW(AbstractUnitOfWork):
    def __init__(self) -> None:
        super().__init__()
        self.projects = FakeProjectRepo()

    def _commit(self) -> None: pass
    def rollback(self) -> None: pass
    def _get_all_seen_aggregates(self) -> list[Aggregate]: return []

class FakeProjectRepo:
    async def get(self, id: str) -> ImageDedupProject:
        return ImageDedupProject(project_id=id, work_path=os.getcwd())
    async def save(self, project: ImageDedupProject) -> None: pass

class UoWProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_uow(self) -> AbstractUnitOfWork:
        return DefaultUoW()

async def run_image_dedup() -> None:
    manifest_path = Path(__file__).parent / "app.toml"
    system = System.from_manifest(manifest_path)
    system.providers.append(UoWProvider())

    logger.info("Starting Image Dedup App...")
    await system.start()

    try:
        async with system.container() as container:
            bus = await container.get(MessageBus)
            logger.info("--- Launching GUI ---")

            # Launch with a default project ID
            await bus.dispatch(LaunchImageDedupCommand(project_id="default-project"))
            # Note: GUI blocks here until closed

    finally:
        await system.stop()

if __name__ == "__main__":
    asyncio.run(run_image_dedup())
