"""Generic undo/redo system.

Ported from legacy appGlue/undo_sustem.py.
"""
from __future__ import annotations

from typing import Callable


class UndoItem:
    """A single undoable action."""

    def __init__(self, undo_op: Callable[[], None], redo_op: Callable[[], None]):
        self.undo_op = undo_op
        self.redo_op = redo_op

    def undo(self) -> None:
        """Perform the undo operation."""
        self.undo_op()

    def redo(self) -> None:
        """Perform the redo operation."""
        self.redo_op()


class UndoSystem:
    """Manager for undo/redo stacks."""

    def __init__(self, max_depth: int = 100):
        self.undo_stack: list[UndoItem] = []
        self.redo_stack: list[UndoItem] = []
        self.max_depth = max_depth

    def add(self, undo_op: Callable[[], None], redo_op: Callable[[], None]) -> None:
        """Add a new undoable action to the stack.
        
        Clears the redo stack.
        """
        item = UndoItem(undo_op, redo_op)
        self.undo_stack.append(item)
        self.redo_stack.clear()
        
        # Limit depth
        if len(self.undo_stack) > self.max_depth:
            self.undo_stack.pop(0)

    def undo(self) -> bool:
        """Perform undo if possible. Returns True if successful."""
        if not self.undo_stack:
            return False
            
        item = self.undo_stack.pop()
        try:
            item.undo()
            self.redo_stack.append(item)
            return True
        except Exception:
            # Re-push on failure to keep stack consistent? 
            # Legacy didn't, we probably shouldn't either unless complex.
            return False

    def redo(self) -> bool:
        """Perform redo if possible. Returns True if successful."""
        if not self.redo_stack:
            return False
            
        item = self.redo_stack.pop()
        try:
            item.redo()
            self.undo_stack.append(item)
            return True
        except Exception:
            return False

    def clear(self) -> None:
        """Clear both stacks."""
        self.undo_stack.clear()
        self.redo_stack.clear()

    @property
    def can_undo(self) -> bool:
        """Whether there are items to undo."""
        return bool(self.undo_stack)

    @property
    def can_redo(self) -> bool:
        """Whether there are items to redo."""
        return bool(self.redo_stack)
