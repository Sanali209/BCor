import json
import logging
from pathlib import Path

from core.batch_engine import (
    AreaCondition,
    ConflictStrategy,
    ConvertAction,
    DeleteAction,
    FormatCondition,
    Rule,
    ScaleAction,
    SizeCondition,
)

logger = logging.getLogger(__name__)


class PresetManager:
    def __init__(self, storage_path: str = "presets.json"):
        self.storage_path = Path(storage_path)
        self.presets: dict[str, list[Rule]] = {}
        self.load_presets()

        # Add defaults if empty
        if not self.presets:
            self.create_defaults()

    def create_defaults(self):
        """Create some useful default presets."""
        # 1. Web Compact (Convert non-WEBP to WEBP, Scale to 1920x1080)
        self.presets["Web Compact"] = [
            Rule(FormatCondition([".webp"], invert=True), ConvertAction(".webp")),
            Rule(
                AreaCondition(min_area=1920 * 1080 + 1),  # Logic: if bigger than HD
                ScaleAction(1920, 1080),
            ),
        ]

        # 2. Cleanup Tiny (Delete images < 1KB or very small dimensions)
        self.presets["Cleanup Tiny Junk"] = [
            Rule(
                SizeCondition(max_bytes=1024),  # < 1KB
                DeleteAction(),
            ),
            Rule(
                AreaCondition(max_area=64 * 64),  # < 64x64
                DeleteAction(),
            ),
        ]

        # 3. Standardize to JPG
        self.presets["Standardize to JPG"] = [
            Rule(FormatCondition([".jpg", ".jpeg"], invert=True), ConvertAction(".jpg"))
        ]

        self.save_presets()

    def save_presets(self):
        """Serialize rules to JSON."""
        data = {}
        for name, rules in self.presets.items():
            serialized_rules = []
            for rule in rules:
                # Prepare Action vars (handle Enums)
                act_vars = {k: v for k, v in vars(rule.action).items() if k != "pil_format_map"}
                if "conflict_strategy" in act_vars and isinstance(act_vars["conflict_strategy"], ConflictStrategy):
                    act_vars["conflict_strategy"] = act_vars["conflict_strategy"].value  # or .name

                serialized_rules.append(
                    {
                        "cond_type": rule.condition.__class__.__name__,
                        "cond_vars": vars(rule.condition),
                        "act_type": rule.action.__class__.__name__,
                        "act_vars": act_vars,
                    }
                )
            data[name] = serialized_rules

        try:
            with open(self.storage_path, "w") as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save presets: {e}")

    def load_presets(self):
        """Deserialize rules from JSON."""
        if not self.storage_path.exists():
            return

        try:
            with open(self.storage_path) as f:
                data = json.load(f)

            for name, rule_dicts in data.items():
                parsed_rules = []
                for rd in rule_dicts:
                    # Reconstruct Condition
                    cond_type = rd["cond_type"]
                    c_vars = rd["cond_vars"]
                    condition = None

                    if cond_type == "AreaCondition":
                        condition = AreaCondition(**c_vars)
                    elif cond_type == "SizeCondition":
                        condition = SizeCondition(**c_vars)
                    elif cond_type == "FormatCondition":
                        condition = FormatCondition(**c_vars)

                    # Reconstruct Action
                    act_type = rd["act_type"]
                    a_vars = rd["act_vars"]

                    # Fix Enum serialization (ConflictStrategy)
                    if "conflict_strategy" in a_vars:
                        try:
                            # Try to load by value (if saved as value)
                            a_vars["conflict_strategy"] = ConflictStrategy(a_vars["conflict_strategy"])
                        except:
                            # Fallback or default
                            a_vars["conflict_strategy"] = ConflictStrategy.RENAME_NEW

                    action = None
                    if act_type == "DeleteAction":
                        action = DeleteAction()
                    elif act_type == "ConvertAction":
                        target = a_vars.get("target_format")
                        qual = a_vars.get("quality", 90)
                        strat = a_vars.get("conflict_strategy", ConflictStrategy.RENAME_NEW)
                        del_orig = a_vars.get("delete_original", False)
                        action = ConvertAction(
                            target_format=target, quality=qual, conflict_strategy=strat, delete_original=del_orig
                        )
                    elif act_type == "ScaleAction":
                        action = ScaleAction(**a_vars)

                    if condition and action:
                        parsed_rules.append(Rule(condition, action))

                self.presets[name] = parsed_rules
        except Exception as e:
            logger.error(f"Failed to load presets: {e}")

    def get_preset_names(self) -> list[str]:
        return list(self.presets.keys())

    def get_rules(self, preset_name: str) -> list[Rule]:
        return self.presets.get(preset_name, [])

    def add_preset(self, name: str, rules: list[Rule]):
        self.presets[name] = rules
        self.save_presets()

    def remove_preset(self, name: str):
        if name in self.presets:
            del self.presets[name]
            self.save_presets()
