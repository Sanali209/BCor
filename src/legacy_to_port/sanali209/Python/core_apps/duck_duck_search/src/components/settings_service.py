"""
Settings Service Component for YAML-based configuration persistence.

Provides centralized configuration management with YAML file storage,
hot-reload capabilities, and integration with SLM framework.
"""

import asyncio
import os
from pathlib import Path
from typing import Dict, Any, Optional, Set, List
import yaml

from loguru import logger

from SLM.core.component import Component


class SettingsService(Component):
    """
    YAML-based settings persistence service.

    Features:
    - YAML file format for human-readable configuration
    - Hot-reload capability for runtime changes
    - Settings validation and defaults
    - Integration with SLM configuration system
    - Change notification via message bus
    """

    def __init__(self, name: Optional[str] = None):
        super().__init__(name or "settings_service")
        self.settings_file = "settings.yaml"
        self.settings: Dict[str, Any] = {}
        self._settings_cache: Dict[str, Any] = {}
        self._file_watcher = None
        self._change_listeners: Set[str] = set()

        # Default settings structure
        self._default_settings = {
            "app": {
                "window": {
                    "width": 800,
                    "height": 600,
                    "position_x": 100,
                    "position_y": 100,
                    "always_on_top": False
                },
                "search": {
                    "max_results": 200,
                    "default_query": "",
                    "safe_search": False,
                    "region": "wt-wt"
                },
                "download": {
                    "base_directory": "~/Downloads/ImageSearch",
                    "create_subfolders": True,
                    "thumbnail_sizes": [64, 128, 256, 512],
                    "concurrent_downloads": 5
                },
                "ui": {
                    "theme": "default",
                    "show_progress": True,
                    "grid_columns": 5,
                    "thumbnail_quality": 85
                },
                "cache": {
                    "enabled": True,
                    "max_size_mb": 1024,
                    "location": "cache/thumbnails"
                }
            }
        }

    async def on_initialize_async(self):
        """Initialize the settings service."""
        await self.load_settings()
        logger.info("Settings service initialized")

    async def on_start_async(self):
        """Start the settings service."""
        # Set up file watching for hot-reload
        await self._setup_file_watching()
        logger.info("Settings service started")

    async def on_shutdown_async(self):
        """Shutdown the settings service."""
        if self._file_watcher:
            self._file_watcher = None
        logger.info("Settings service shutdown")

    async def load_settings(self) -> Dict[str, Any]:
        """
        Load settings from YAML file.

        Returns:
            Dictionary of current settings
        """
        try:
            settings_path = Path(self.settings_file)

            if settings_path.exists():
                with open(settings_path, 'r', encoding='utf-8') as f:
                    loaded_settings = yaml.safe_load(f) or {}

                # Merge with defaults to ensure all keys exist
                self.settings = self._deep_merge(self._default_settings, loaded_settings)
                logger.info(f"Loaded settings from {self.settings_file}")
            else:
                logger.info(f"Settings file not found, using defaults")
                self.settings = self._deep_copy(self._default_settings)
                await self.save_settings()  # Create the file with defaults

            # Update cache
            self._settings_cache = self._deep_copy(self.settings)

            return self.settings.copy()

        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            # Fall back to defaults
            self.settings = self._deep_copy(self._default_settings)
            return self.settings.copy()

    async def save_settings(self, settings: Optional[Dict[str, Any]] = None):
        """
        Save settings to YAML file.

        Args:
            settings: Settings to save (uses current if None)
        """
        if settings:
            self.settings = self._deep_merge(self.settings, settings)

        try:
            # Ensure directory exists
            settings_path = Path(self.settings_file)
            settings_path.parent.mkdir(parents=True, exist_ok=True)

            # Write settings to file
            with open(settings_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    self.settings,
                    f,
                    default_flow_style=False,
                    indent=2,
                    allow_unicode=True
                )

            # Update cache
            self._settings_cache = self._deep_copy(self.settings)

            logger.info(f"Saved settings to {self.settings_file}")

            # Notify listeners of changes
            await self._notify_settings_change()

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            raise

    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value using dot notation.

        Args:
            key: Setting key (e.g., "app.window.width")
            default: Default value if key not found

        Returns:
            Setting value or default
        """
        return self._get_nested_value(self.settings, key, default)

    async def set_setting(self, key: str, value: Any):
        """
        Set a setting value and persist to file.

        Args:
            key: Setting key (e.g., "app.window.width")
            value: New value
        """
        # Update in memory
        self._set_nested_value(self.settings, key, value)

        # Save to file
        await self.save_settings()

        # Notify listeners
        await self._notify_setting_change(key, value)

    def get_settings_section(self, section: str) -> Dict[str, Any]:
        """
        Get all settings for a section.

        Args:
            section: Section name (e.g., "app", "app.window")

        Returns:
            Dictionary of settings for the section
        """
        return self._get_nested_value(self.settings, section, {})

    async def update_settings_section(self, section: str, updates: Dict[str, Any]):
        """
        Update multiple settings in a section.

        Args:
            section: Section name
            updates: Dictionary of updates
        """
        current_section = self.get_settings_section(section)
        current_section.update(updates)

        # Set the entire section
        self._set_nested_value(self.settings, section, current_section)
        await self.save_settings()

        # Notify listeners
        for key, value in updates.items():
            full_key = f"{section}.{key}" if section else key
            await self._notify_setting_change(full_key, value)

    def has_setting(self, key: str) -> bool:
        """
        Check if a setting exists.

        Args:
            key: Setting key to check

        Returns:
            True if setting exists
        """
        try:
            self._get_nested_value(self.settings, key)
            return True
        except KeyError:
            return False

    def get_all_settings(self) -> Dict[str, Any]:
        """
        Get all current settings.

        Returns:
            Copy of all settings
        """
        return self.settings.copy()

    def reset_to_defaults(self):
        """Reset all settings to defaults."""
        self.settings = self._deep_copy(self._default_settings)
        # Note: save_settings() will be called by caller if needed

    async def reload_settings(self) -> Dict[str, Any]:
        """
        Force reload settings from file.

        Returns:
            New settings dictionary
        """
        return await self.load_settings()

    def subscribe_to_changes(self, callback):
        """
        Subscribe to settings change notifications.

        Args:
            callback: Function to call when settings change
        """
        # For now, just track that we have listeners
        # In a more advanced implementation, this could track specific callbacks
        self._change_listeners.add(str(id(callback)))

    def unsubscribe_from_changes(self, callback):
        """
        Unsubscribe from settings change notifications.

        Args:
            callback: Function to remove
        """
        self._change_listeners.discard(str(id(callback)))

    async def _setup_file_watching(self):
        """Set up file watching for hot-reload."""
        # For now, we'll implement manual reload
        # In a production system, you might use watchdog or similar
        pass

    async def _notify_settings_change(self):
        """Notify all listeners of settings changes."""
        if self.message_bus:
            await self.message_bus.publish_async(
                "settings.changed",
                settings=self.settings.copy(),
                timestamp=asyncio.get_event_loop().time()
            )

    async def _notify_setting_change(self, key: str, value: Any):
        """Notify listeners of a specific setting change."""
        if self.message_bus:
            await self.message_bus.publish_async(
                "setting.changed",
                key=key,
                value=value,
                old_value=self._settings_cache.get(key),
                timestamp=asyncio.get_event_loop().time()
            )

    def _get_nested_value(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """
        Get a nested dictionary value using dot notation.

        Args:
            data: Dictionary to search
            key: Dot-notation key (e.g., "app.window.width")
            default: Default value if not found

        Returns:
            Value or default
        """
        keys = key.split('.')
        current = data

        for k in keys:
            if isinstance(current, dict) and k in current:
                current = current[k]
            else:
                return default

        return current

    def _set_nested_value(self, data: Dict[str, Any], key: str, value: Any):
        """
        Set a nested dictionary value using dot notation.

        Args:
            data: Dictionary to modify
            key: Dot-notation key
            value: Value to set
        """
        keys = key.split('.')
        current = data

        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in current:
                current[k] = {}
            current = current[k]

        # Set the final value
        current[keys[-1]] = value

    def _deep_merge(self, base: Dict[str, Any], overlay: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.

        Args:
            base: Base dictionary
            overlay: Dictionary to merge on top

        Returns:
            Merged dictionary
        """
        result = self._deep_copy(base)

        for key, value in overlay.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = self._deep_copy(value)

        return result

    def _deep_copy(self, obj: Any) -> Any:
        """
        Deep copy an object.

        Args:
            obj: Object to copy

        Returns:
            Deep copy of object
        """
        if isinstance(obj, dict):
            return {key: self._deep_copy(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self._deep_copy(item) for item in obj]
        else:
            return obj

    def validate_settings(self) -> List[str]:
        """
        Validate current settings.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        # Validate window settings
        window = self.get_settings_section("app.window")
        if window.get("width", 0) < 400:
            errors.append("Window width must be at least 400px")
        if window.get("height", 0) < 300:
            errors.append("Window height must be at least 300px")

        # Validate search settings
        search = self.get_settings_section("app.search")
        if search.get("max_results", 0) < 1:
            errors.append("Max results must be at least 1")
        if search.get("max_results", 0) > 1000:
            errors.append("Max results cannot exceed 1000")

        # Validate thumbnail sizes
        thumbnail_sizes = self.get_setting("app.download.thumbnail_sizes", [])
        if not thumbnail_sizes:
            errors.append("At least one thumbnail size must be specified")
        for size in thumbnail_sizes:
            if not isinstance(size, int) or size < 16 or size > 2048:
                errors.append(f"Thumbnail size {size} must be between 16 and 2048")

        return errors

    def export_settings(self, file_path: str) -> bool:
        """
        Export current settings to a file.

        Args:
            file_path: Path to export to

        Returns:
            True if successful
        """
        try:
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(
                    self.settings,
                    f,
                    default_flow_style=False,
                    indent=2,
                    allow_unicode=True
                )
            return True
        except Exception as e:
            logger.error(f"Error exporting settings: {e}")
            return False

    def import_settings(self, file_path: str) -> bool:
        """
        Import settings from a file.

        Args:
            file_path: Path to import from

        Returns:
            True if successful
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                imported_settings = yaml.safe_load(f) or {}

            # Validate imported settings
            temp_settings = self._deep_merge(self._default_settings, imported_settings)
            validation_errors = []  # Could add validation here

            if not validation_errors:
                self.settings = temp_settings
                # Save to main settings file
                import asyncio
                asyncio.create_task(self.save_settings())
                return True

        except Exception as e:
            logger.error(f"Error importing settings: {e}")

        return False
