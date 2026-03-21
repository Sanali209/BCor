from src.core.system import System
from src.modules.agm.module import AGMModule
from src.modules.orders.module import OrdersModule


def test_system_discovery_from_manifest(tmp_path):
    # Setup: Create a temporary app.toml
    manifest = tmp_path / "app.toml"
    manifest.write_text("""
[app]
name = "test-app"

[modules]
enabled = ["orders", "agm"]
""")

    # Use a mock directory structure if needed, but since we are in the repo,
    # it should find the actual modules.
    system = System.from_manifest(str(manifest))

    assert len(system.modules) == 2
    assert any(isinstance(m, OrdersModule) for m in system.modules)
    assert any(isinstance(m, AGMModule) for m in system.modules)


def test_system_bootstrap_with_discovery(tmp_path):
    from dishka import Provider, Scope, provide

    from src.core.unit_of_work import AbstractUnitOfWork

    class FakeUoW(AbstractUnitOfWork):
        async def commit(self):
            pass

        async def rollback(self):
            pass

    class TestProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def provide_uow(self) -> AbstractUnitOfWork:
            return FakeUoW()

    manifest = tmp_path / "app.toml"
    manifest.write_text("""
[modules]
enabled = ["orders"]
""")
    system = System.from_manifest(str(manifest))
    system.providers.append(TestProvider())
    system._bootstrap()

    assert "orders" in system.settings
    assert system.container is not None
