"""UI selection management utilities.

Ported from legacy appGlue/selectionManager.py.
"""
from __future__ import annotations

from typing import Any, Callable


class SelectionItemData:
    """Container for selection data with optional type conversion."""

    def __init__(self, data: Any = None):
        self.data = data
        self.converters: dict[type, Callable[[Any], Any]] =强化

    def get_as(self, target_type: type) -> Any:
        """Get the selection data converted to the target type if a converter exists."""
        if target_type in self.converters:
            return self.converters[target_type](self.data)
        return self.data


class SelectionManager:
    """Manager for coordinating selection state across multiple UI components."""

    def __init__(self):
        self.users: list[SelectionManagerUser] = []
        self.callbacks: list[Callable[[SelectionManager], None]] = []
        self.last_selection: Any | None = None

    def on_change(self, callback: Callable[[SelectionManager], None]) -> None:
        """Register a callback for selection changes."""
        self.callbacks.append(callback)

    def register(self, user: SelectionManagerUser) -> None:
        """Register a selectable item/component."""
        self.users.append(user)
        user._manager = self

    def unregister(self, user: SelectionManagerUser) -> None:
        """Unregister a selectable item/component."""
        if user in self.users:
            self.users.remove(user)
            user._manager = None

    def fire_change(self) -> None:
        """Notify all listeners that the selection has changed."""
        for callback in self.callbacks:
            try:
                callback(self)
            except Exception:
                pass

    def get_selected_data(self) -> list[Any]:
        """Get data of all currently selected items."""
        return [u.data for u in self.users if u.is_selected]

    def clear(self) -> None:
        """Deselect all items."""
        for user in self.users:
            user.set_selected(False, notify=False)
        self.fire_change()


class SelectionManagerUser:
    """A selectable item or component that participates in selection management."""

    def __init__(self, data: Any = None):
        self.is_selected = False
        self.data = data
        self._manager: SelectionManager | None = None

    def set_selected(self, selected: bool, notify: bool = True) -> None:
        """Set the selection state of this item."""
        if self.is_selected == selected:
            return
            
        self.is_selected = selected
        if self._manager:
            if selected:
                self._manager.last_selection = self.data
            if notify:
                self._manager.fire_change()
