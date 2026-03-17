import pytest
import asyncio

from dishka import Provider, Scope, provide

from src.core.system import System
from src.core.messagebus import MessageBus
from src.core.unit_of_work import AbstractUnitOfWork

from src.modules.ecs.module import EcsModule
from src.modules.ecs.messages import (
    TickEvent,
    MoveEntityCommand,
    CollisionDetectedEvent,
)
from src.modules.ecs.domain import EcsWorld, PositionComponent, VelocityComponent
from src.modules.ecs.ports import AbstractEcsRepository, EcsUnitOfWork


class FakeEcsRepository(AbstractEcsRepository):
    def __init__(self):
        super().__init__()
        self._worlds = {}

    def _add(self, aggregate: EcsWorld) -> None:
        self._worlds[aggregate.world_id] = aggregate

    def _get(self, reference: str) -> EcsWorld:
        return self._worlds.get(reference)

    async def get_world(self, world_id: str) -> EcsWorld:
        world = self.get(world_id)
        if not world:
            world = EcsWorld(world_id=world_id)
            self.add(world)
        return world


class FakeEcsUnitOfWork(EcsUnitOfWork):
    def __init__(self):
        self.worlds = FakeEcsRepository()
        self.committed = False
        self.rolled_back = False

    def __enter__(self):
        self.committed = False
        self.rolled_back = False
        return super().__enter__()

    def _commit(self):
        self.committed = True

    def rollback(self):
        self.rolled_back = True


class MockUoWProvider(Provider):
    @provide(scope=Scope.REQUEST)
    def provide_uow(self) -> AbstractUnitOfWork:
        # Dishka will automatically type-match AbstractUnitOfWork / EcsUnitOfWork
        return FakeEcsUnitOfWork()


@pytest.fixture
def system():
    ecs_mod = EcsModule()
    sys = System(modules=[ecs_mod])
    sys.providers.append(MockUoWProvider())
    sys._bootstrap()
    return sys


@pytest.fixture(autouse=True)
def cleanup_bubus():
    yield
    import bubus

    for bus in bubus.EventBus.all_instances:
        bus._is_running = False


@pytest.mark.asyncio
async def test_game_loop_tick_updates_positions_and_checks_collisions(system):
    collision_handled = False

    async def collision_handler(evt: CollisionDetectedEvent, uow: FakeEcsUnitOfWork):
        nonlocal collision_handled
        collision_handled = True

    async with system.container() as request_container:
        bus = await request_container.get(MessageBus)
        uow = bus.uow

        bus.register_event(CollisionDetectedEvent, collision_handler)

        with uow:
            world = await uow.worlds.get_world("main_scene")

            world.add_component("player_1", PositionComponent(x=0.0, y=0.0))
            world.add_component("player_1", VelocityComponent(dx=10.0, dy=0.0))
            world.add_component("enemy_1", PositionComponent(x=10.0, y=0.0))

            uow.commit()

        list(uow.collect_new_events())

        tick_evt = TickEvent(delta_time=1.0, current_tick=1)
        await bus.dispatch(tick_evt)

        await asyncio.sleep(0.01)
        bus.bus._is_running = False

        with uow:
            world = await uow.worlds.get_world("main_scene")
            p1_pos = world.get_component("player_1", PositionComponent)
            assert p1_pos.x == 10.0
            assert collision_handled is True


@pytest.mark.asyncio
async def test_move_entity_command_fail_fast(system):
    async with system.container() as request_container:
        bus = await request_container.get(MessageBus)
        uow = bus.uow

        with uow:
            world = await uow.worlds.get_world("main_scene")
            world.add_component("ghost", VelocityComponent(dx=0, dy=0))
            uow.commit()

        list(uow.collect_new_events())

        try:
            results = await bus.dispatch(
                MoveEntityCommand(entity_id="ghost", target_x=100.0, target_y=100.0)
            )
            # bubus dispatch returns the Event itself which has `.event_results`
            has_error = False
            for r in results.event_results.values():
                if "missing PositionComponent" in str(r.error):
                    has_error = True
            assert has_error is True
        finally:
            bus.bus._is_running = False
