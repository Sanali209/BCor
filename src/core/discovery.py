import importlib
import tomllib
from pathlib import Path

from src.core.module import BaseModule


class ModuleDiscovery:
    """Helper to discover and instantiate modules from a manifest file.

    This class provides static methods to scan a manifest (TOML) for enabled
    modules and dynamically import and instantiate them if they subclass
    BaseModule.
    """

    @staticmethod
    def load_from_manifest(manifest_path: str | Path) -> list[BaseModule]:
        """Loads enabled modules defined in a manifest file.

        Args:
            manifest_path: Path to the TOML manifest file.

        Returns:
            A list of instantiated BaseModule subclasses.

        Raises:
            FileNotFoundError: If the manifest file does not exist.
        """
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
    def _import_module(name: str, search_paths: list[str]) -> BaseModule:
        """Finds and instantiates any BaseModule subclass in the target module.

        Searches across the provided paths for a `module.py` file containing
        a subclass of BaseModule.

        Args:
            name: The name of the module to import (folder name).
            search_paths: A list of base packages to search within.

        Returns:
            An instance of the discovered BaseModule subclass.

        Raises:
            ImportError: If no BaseModule subclass is found in the search paths.
        """
        for base_path in search_paths:
            module_path = f"{base_path}.{name}.module"
            try:
                mod = importlib.import_module(module_path)
                for attr_name in dir(mod):
                    attr = getattr(mod, attr_name)
                    if isinstance(attr, type) and issubclass(attr, BaseModule) and attr is not BaseModule:
                        return attr()
            except ImportError as e:
                # If the error is about the module_path itself, we continue searching
                # If it's a sub-import failing, we should raise it to reveal the real issue
                if e.name and e.name in module_path:
                    continue
                # If e.name is None (e.g. from a compiled extension), we check the message
                if not e.name and module_path in str(e):
                    continue
                raise

        raise ImportError(f"Could not load module '{name}' from any of the provided paths: {search_paths}.")
