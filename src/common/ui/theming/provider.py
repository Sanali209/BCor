import abc
import re
import tomllib
from dataclasses import dataclass
from pathlib import Path


@dataclass
class Theme:
    """Theme entity containing palette and metadata."""

    id: str
    name: str
    colors: dict[str, str]
    description: str = ""
    icons_dir: Path | None = None
    fonts_dir: Path | None = None


class QSSProcessor:
    """QSS Preprocessor with support for variables and color functions."""

    def __init__(self) -> None:
        self.func_re = re.compile(r"(lighten|darken|alpha)\(([^,]+),\s*([^)]+)\)")

    def process(self, template: str, colors: dict[str, str]) -> str:
        resolved_colors = self._resolve_variables(colors)
        rendered = template
        # Sort keys by length descending to avoid partial matches (e.g., @bg matching in @bg-main)
        sorted_keys = sorted(resolved_colors.keys(), key=len, reverse=True)
        for key in sorted_keys:
            rendered = rendered.replace(f"@{key}", resolved_colors[key])
        return self._process_functions(rendered)

    def _resolve_variables(self, colors: dict[str, str]) -> dict[str, str]:
        resolved = colors.copy()
        for _ in range(5):
            changed = False
            for k, v in resolved.items():
                if isinstance(v, str) and v.startswith("@"):
                    target_key = v[1:]
                    if target_key in resolved and not str(resolved[target_key]).startswith("@"):
                        resolved[k] = resolved[target_key]
                        changed = True
            if not changed:
                break
        return resolved

    def _process_functions(self, text: str) -> str:
        def replacer(match: re.Match[str]) -> str:
            func = match.group(1)
            color_str = match.group(2).strip()
            param_str = match.group(3).strip()
            r, g, b = self._parse_color(color_str)

            if func == "lighten":
                factor = float(param_str.strip("%")) / 100.0
                return f"#{min(255, int(round(r + 255 * factor))):02x}{min(255, int(round(g + 255 * factor))):02x}{min(255, int(round(b + 255 * factor))):02x}"
            elif func == "darken":
                factor = float(param_str.strip("%")) / 100.0
                return f"#{max(0, int(round(r - 255 * factor))):02x}{max(0, int(round(g - 255 * factor))):02x}{max(0, int(round(b - 255 * factor))):02x}"
            elif func == "alpha":
                a = int(round(float(param_str) * 255))
                return f"rgba({r}, {g}, {b}, {a})"
            return match.group(0)

        return self.func_re.sub(replacer, text)

    def _parse_color(self, color_str: str) -> tuple[int, int, int]:
        if color_str.startswith("#"):
            c = color_str.lstrip("#")
            return tuple(int(c[i : i + 2], 16) for i in (0, 2, 4))
        return (0, 0, 0)


class DynamicIconProvider:
    """Handles SVG template colorization."""

    def colorize_svg(self, svg_content: str, colors: dict[str, str], color_role: str = "primary") -> str:
        result = svg_content
        # Sort keys by length descending to avoid partial matches
        sorted_keys = sorted(colors.keys(), key=len, reverse=True)
        for key in sorted_keys:
            value = colors[key]
            if isinstance(value, str):
                result = result.replace(f"@{key}", value)
        if color_role in colors:
            result = result.replace("currentColor", colors[color_role])
        return result


class IThemeProvider(abc.ABC):
    @abc.abstractmethod
    def list_themes(self) -> list[str]:
        pass

    @abc.abstractmethod
    def get_theme(self, theme_id: str) -> Theme | None:
        pass

    @abc.abstractmethod
    def get_base_qss(self) -> str:
        pass

    @abc.abstractmethod
    def get_icon_template(self, theme: Theme, icon_name: str) -> str | None:
        pass


class FileThemeProvider(IThemeProvider):
    def __init__(self, themes_dir: Path):
        self.themes_dir = themes_dir
        self.themes_dir.mkdir(parents=True, exist_ok=True)

    def list_themes(self) -> list[str]:
        return [f.stem for f in self.themes_dir.glob("*.toml")]

    def get_theme(self, theme_id: str) -> Theme | None:
        path = self.themes_dir / f"{theme_id}.toml"
        if not path.exists():
            return None
        with open(path, "rb") as f:
            data = tomllib.load(f)
        return Theme(
            id=theme_id,
            name=data.get("name", theme_id),
            colors=data.get("colors", {}),
            icons_dir=self.themes_dir / "icons",
            fonts_dir=self.themes_dir / "fonts",
        )

    def get_base_qss(self) -> str:
        path = self.themes_dir / "base_style.qss"
        return path.read_text(encoding="utf-8") if path.exists() else ""

    def get_icon_template(self, theme: Theme, icon_name: str) -> str | None:
        if not theme.icons_dir:
            return None
        path = theme.icons_dir / f"{icon_name}.svg"
        return path.read_text(encoding="utf-8") if path.exists() else None
