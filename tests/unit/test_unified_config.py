from src.core.system import System
from src.core.module import BaseModule
from pydantic_settings import BaseSettings

# Mock Module for testing local path discovery
class MockLocalSettings(BaseSettings):
    setting_a: str = "default"
    setting_b: int = 0

class MockLocalModule(BaseModule):
    settings_class = MockLocalSettings

def test_discovery_with_custom_paths(tmp_path, monkeypatch):
    """Test that ModuleDiscovery can find modules in custom paths defined in TOML."""
    manifest = tmp_path / "app.toml"
    manifest.write_text("""
[modules]
paths = ["tests.unit.mock_app_modules", "src.modules"]
enabled = ["mock_local"]
""")
    
    # We need to mock the importlib behavior or create a real package structure
    # For TDD, let's create a temporary package structure
    mock_pkg = tmp_path / "tests" / "unit" / "mock_app_modules" / "mock_local"
    mock_pkg.mkdir(parents=True)
    (mock_pkg / "__init__.py").write_text("")
    (mock_pkg / "module.py").write_text("""
from pydantic_settings import BaseSettings
from src.core.module import BaseModule

class MockLocalSettings(BaseSettings):
    setting_a: str = "default"
    setting_b: int = 0

class MockLocalModule(BaseModule):
    settings_class = MockLocalSettings
""")
    
    # Add tmp_path to sys.path so importlib can find our dynamic 'tests.unit.mock_app_modules'
    monkeypatch.syspath_prepend(str(tmp_path))

    system = System.from_manifest(str(manifest))
    assert len(system.modules) == 1
    assert system.modules[0].__class__.__name__ == "MockLocalModule"

def test_system_loads_module_settings_from_toml(tmp_path, monkeypatch):
    """Test that System injects TOML configuration blocks into the Pydantic settings."""
    manifest = tmp_path / "app.toml"
    manifest.write_text("""
[modules]
paths = ["tests.unit.mock_app_modules"]
enabled = ["mock_local"]

[mocklocal]
setting_a = "from_toml"
setting_b = 42
""")
    
    mock_pkg = tmp_path / "tests" / "unit" / "mock_app_modules" / "mock_local"
    mock_pkg.mkdir(parents=True)
    (mock_pkg / "__init__.py").write_text("")
    (mock_pkg / "module.py").write_text("""
from pydantic_settings import BaseSettings
from src.core.module import BaseModule

class MockLocalSettings(BaseSettings):
    setting_a: str = "default"
    setting_b: int = 0

class MockLocalModule(BaseModule):
    settings_class = MockLocalSettings
""")
    monkeypatch.syspath_prepend(str(tmp_path))

    from dishka import Provider, Scope, provide
    from src.core.unit_of_work import AbstractUnitOfWork

    class FakeUoW(AbstractUnitOfWork):
        async def commit(self): pass
        async def rollback(self): pass

    class TestProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def provide_uow(self) -> AbstractUnitOfWork:
            return FakeUoW()

    system = System.from_manifest(str(manifest))
    system.providers.append(TestProvider())
    system._bootstrap()
    
    # The settings should have been populated from the TOML file
    assert "mocklocal" in system.settings
    loaded_settings = system.settings["mocklocal"]
    assert loaded_settings.setting_a == "from_toml"
    assert loaded_settings.setting_b == 42
