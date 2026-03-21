from __future__ import annotations

import logging

from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtGui import QColor, QIcon, QPainter, QPixmap
from PySide6.QtSvg import QSvgRenderer
from PySide6.QtWidgets import QGraphicsDropShadowEffect, QWidget

from .provider import DynamicIconProvider, IThemeProvider, QSSProcessor

logger = logging.getLogger(__name__)


class ThemeManager(QObject):
    """Universal Theme Manager for PySide6 applications.

    Handles theme switching, QSS rendering with variables/functions,
    dynamic icon colorization, and style hooks.
    """

    theme_changed = Signal(str)  # Emits QSS when theme changes

    def __init__(self, provider: IThemeProvider, initial_theme_id: str = "default") -> None:
        super().__init__()
        self.provider = provider
        self.current_theme_id = initial_theme_id
        self.qss_processor = QSSProcessor()
        self.icon_provider = DynamicIconProvider()
        self._cached_qss = ""
        self._icon_cache = {}

    def get_current_theme(self) -> Theme | None:
        """Returns the current theme entity."""
        return self.provider.get_theme(self.current_theme_id)

    def get_current_qss(self) -> str:
        """Returns the rendered QSS for the current theme."""
        if self._cached_qss:
            return self._cached_qss

        theme = self.provider.get_theme(self.current_theme_id)
        template = self.provider.get_base_qss()

        if not theme or not template:
            return ""

        self._cached_qss = self.qss_processor.process(template, theme.colors)
        return self._cached_qss

    def apply_theme(self, theme_id: str) -> None:
        """Changes the current theme and notifies subscribers."""
        if theme_id == self.current_theme_id and self._cached_qss:
            return

        self.current_theme_id = theme_id
        self._cached_qss = ""
        self._icon_cache = {}
        qss = self.get_current_qss()
        self.theme_changed.emit(qss)
        logger.info(f"Theme changed to: {theme_id}")

    def get_icon(self, name: str, color_role: str = "primary", size: int = 24) -> QIcon:
        """Returns a theme-colored QIcon generated from an SVG template."""
        cache_key = f"{name}_{color_role}_{size}"
        if cache_key in self._icon_cache:
            return self._icon_cache[cache_key]

        theme = self.provider.get_theme(self.current_theme_id)
        if not theme:
            return QIcon()

        svg_template = self.provider.get_icon_template(theme, name)
        if not svg_template:
            return QIcon()

        colorized_svg = self.icon_provider.colorize_svg(svg_template, theme.colors, color_role)

        renderer = QSvgRenderer(colorized_svg.encode("utf-8"))
        if not renderer.isValid():
            logger.error(f"QSvgRenderer is INVALID for icon {name}. Content: {colorized_svg[:100]}")
            return QIcon()

        pixmap = QPixmap(size, size)
        pixmap.fill(Qt.GlobalColor.transparent)

        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        icon = QIcon(pixmap)
        self._icon_cache[cache_key] = icon
        return icon

    def get_color(self, color_key: str, default: str = "#000000") -> str:
        """Returns a specific theme color, processing functions if present."""
        theme = self.provider.get_theme(self.current_theme_id)
        if not theme:
            return default
        color_val = theme.colors.get(color_key, default)
        if "(" in color_val:
            return self.qss_processor.process(f"color: {color_val}", theme.colors).replace("color: ", "").strip(";")
        return color_val

    def get_all_colors(self) -> dict[str, str]:
        """Returns the full palette of the current theme, processed."""
        theme = self.provider.get_theme(self.current_theme_id)
        if not theme:
            return {}
        # Resolve all colors through process logic
        return {k: self.get_color(k) for k in theme.colors}

    def apply_hook(self, widget: QWidget, hook_name: str) -> None:
        """Applies advanced visual effects (hooks) to a widget."""
        theme = self.provider.get_theme(self.current_theme_id)
        if not theme:
            return

        if hook_name == "glass":
            shadow = QGraphicsDropShadowEffect(widget)
            shadow.setBlurRadius(20)
            shadow.setColor(QColor(0, 0, 0, 80))
            shadow.setOffset(0, 0)
            widget.setGraphicsEffect(shadow)
            widget.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
            logger.debug(f"Applied glass hook to {widget.objectName()}")
