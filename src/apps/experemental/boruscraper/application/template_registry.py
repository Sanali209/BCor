import os
import json
from pathlib import Path
from typing import Dict, Any, List
from src.apps.experemental.boruscraper.common.schemas import ScraperSettings

class ScrapingTemplateRegistry:
    def __init__(self, templates_dir: str):
        self.templates_dir = Path(templates_dir)
        self._templates: Dict[str, ScraperSettings] = {}
        self._load_templates()

    def _load_templates(self):
        """Scan the templates directory and load all JSON configuration files."""
        if not self.templates_dir.exists():
            return
        
        for file_path in self.templates_dir.glob("*.json"):
            # Exclude known non-template JSONs if any (like config.json perhaps?)
            if file_path.name == "config.json":
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    template_name = file_path.stem
                    self._templates[template_name] = ScraperSettings.from_dict(data)
            except Exception as e:
                import logging
                logging.getLogger(__name__).error(f"Failed to load template {file_path.name}: {e}")

    def get_template(self, name: str) -> ScraperSettings:
        return self._templates.get(name)

    def get_all_template_names(self) -> List[str]:
        return list(self._templates.keys())
    
    def get_raw_template_data(self, name: str) -> Dict[str, Any]:
        """Returns the raw dictionary data for serialization to the database."""
        file_path = self.templates_dir / f"{name}.json"
        if not file_path.exists():
            return {}
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
