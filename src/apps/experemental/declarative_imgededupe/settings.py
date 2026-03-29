import json
import os
from dataclasses import dataclass, field, asdict
from typing import List, Optional

@dataclass
class DedupeUISettings:
    """Settings for the Deduplication UI session setup."""
    root_folders: List[str] = field(default_factory=list)
    engine: str = "clip"
    # Store threshold per engine
    thresholds: dict[str, float] = field(default_factory=lambda: {
        "phash": 10.0,
        "clip": 0.85,
        "blip": 0.80
    })

    @property
    def current_threshold(self) -> float:
        return self.thresholds.get(self.engine, 0.85)

class SettingsManager:
    """Handles loading and saving of DedupeUISettings to a local JSON file."""
    
    def __init__(self, filename: str = "imgededupe_settings.json"):
        # Put settings in the same directory as the app for experimental portability
        # In a real app we might use platformdirs.user_config_dir
        app_dir = os.path.dirname(os.path.abspath(__file__))
        self.filepath = os.path.join(app_dir, filename)

    def load(self) -> DedupeUISettings:
        """Loads settings from file or returns defaults if not found."""
        if not os.path.exists(self.filepath):
            return DedupeUISettings()
        
        try:
            with open(self.filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
                return DedupeUISettings(**data)
        except Exception:
            # Fallback to defaults on corruption
            return DedupeUISettings()

    def save(self, settings: DedupeUISettings):
        """Saves settings to the JSON file."""
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(asdict(settings), f, indent=4)
        except Exception as e:
            # We don't want to crash the UI on settings save failure, just log it
            print(f"Error saving settings: {e}")
