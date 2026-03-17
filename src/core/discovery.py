import tomllib
import importlib
from pathlib import Path
from typing import List
from src.core.module import BaseModule

class ModuleDiscovery:
    """Helper to discover and instantiate modules from a manifest file."""

    @staticmethod
    def load_from_manifest(manifest_path: str | Path) -> List[BaseModule]:
        path = Path(manifest_path)
        if not path.exists():
            raise FileNotFoundError(f"Manifest not found: {manifest_path}")

        with path.open("rb") as f:
            data = tomllib.load(f)

        modules_config = data.get("modules", {})
        enabled_modules = modules_config.get("enabled", [])
        search_paths = modules_config.get("paths", ["src.modules"])
        instances = []

        for module_name in enabled_modules:
            instances.append(ModuleDiscovery._import_module(module_name, search_paths))

        return instances

    @staticmethod
    def _import_module(name: str, search_paths: List[str]) -> BaseModule:
        """Find and instantiate any BaseModule subclass in the target module across given paths."""
        for base_path in search_paths:
            module_path = f"{base_path}.{name}.module"
            try:
                mod = importlib.import_module(module_path)
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if (
                        isinstance(attr, type)
                        and issubclass(attr, BaseModule)
                        and attr is not BaseModule
                    ):
                        return attr()
            except ImportError:
                continue # Try the next path

        raise ImportError(
            f"Could not load module '{name}' from any of the provided paths: {search_paths}."
        )
