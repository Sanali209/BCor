from __future__ import annotations

import logging
from typing import Any

from src.apps.ImageAnalyze.domain.entities.batch_processing import (
    AreaCondition,
    ConflictStrategy,
    ConvertAction,
    DeleteAction,
    Condition,
    FormatCondition,
    Rule,
    ScaleAction,
    SizeCondition,
    Action,
)

logger = logging.getLogger(__name__)


class PresetManager:
    """Управляет пресетами правил пакетной обработки, загружаемыми из конфигурации."""

    def __init__(self, config_presets: dict[str, Any] | None = None) -> None:
        self.presets: dict[str, list[Rule]] = {}
        if config_presets:
            self._load_from_config(config_presets)

    def _load_from_config(self, config_presets: dict[str, Any]) -> None:
        """Парсит пресеты из TOML структуры в доменные правила."""
        for name, data in config_presets.items():
            rules = []
            for rd in data.get("rules", []):
                try:
                    # Condition
                    cond_type = rd.get("cond_type")
                    c_vars = rd.get("cond_vars", {})
                    condition: Condition | None = None
                    if cond_type == "AreaCondition":
                        condition = AreaCondition(**c_vars)
                    elif cond_type == "SizeCondition":
                        condition = SizeCondition(**c_vars)
                    elif cond_type == "FormatCondition":
                        condition = FormatCondition(**c_vars)

                    # Action
                    act_type = rd.get("act_type")
                    a_vars = rd.get("act_vars", {})
                    action: Action | None = None
                    if act_type == "DeleteAction":
                        action = DeleteAction()
                    elif act_type == "ConvertAction":
                        # Map string conflict strategy to Enum if present
                        if "conflict_strategy" in a_vars:
                            try:
                                a_vars["conflict_strategy"] = ConflictStrategy[a_vars["conflict_strategy"].upper()]
                            except (KeyError, AttributeError):
                                a_vars["conflict_strategy"] = ConflictStrategy.RENAME_NEW
                        action = ConvertAction(**a_vars)
                    elif act_type == "ScaleAction":
                        action = ScaleAction(**a_vars)

                    if condition and action:
                        rules.append(Rule(condition, action, name=f"{name} Rule"))
                except Exception as e:
                    logger.error(f"Failed to parse rule in preset {name}: {e}")

            self.presets[name] = rules

    def get_preset_names(self) -> list[str]:
        return list(self.presets.keys())

    def get_rules(self, preset_name: str) -> list[Rule]:
        return self.presets.get(preset_name, [])
