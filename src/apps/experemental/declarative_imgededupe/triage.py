"""Triage logic for imgededupe — Commands and History."""
from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any
from loguru import logger

from src.modules.assets.domain.models import Asset, SimilarTo, RelationType


class TriageCommand(ABC):
    """Base class for undoable triage actions."""
    
    @abstractmethod
    async def execute(self) -> None:
        """Execute the action."""
        pass

    @abstractmethod
    async def undo(self) -> None:
        """Undo the action."""
        pass


class DeleteAssetCommand(TriageCommand):
    """Command to delete an asset, with undo support (re-saving it to graph)."""
    
    def __init__(self, mapper: Any, asset: Asset):
        self.mapper = mapper
        self.asset = asset

    async def execute(self) -> None:
        logger.info(f"Executing delete for asset {self.asset.id}")
        await self.mapper.delete(self.asset)

    async def undo(self) -> None:
        logger.info(f"Undoing delete for asset {self.asset.id}")
        await self.mapper.save(self.asset)


class AnnotateRelationCommand(TriageCommand):
    """Command to annotate a relationship between assets."""
    
    def __init__(self, mapper: Any, asset: Asset, target_id: str, new_relation: str):
        self.mapper = mapper
        self.asset = asset
        self.target_id = target_id
        self.new_relation = new_relation
        self.old_relation: str | None = None

    async def execute(self) -> None:
        # 1. Update/Add relationship property
        found = False
        for sim in self.asset.similar:
            if sim.id == self.target_id:
                self.old_relation = sim.relation_type
                sim.relation_type = self.new_relation
                found = True
                break
        
        if not found:
            self.asset.similar.append(
                SimilarTo(id=self.target_id, relation_type=self.new_relation)
            )
            
        # 2. Persist to graph
        await self.mapper.save(self.asset)

    async def undo(self) -> None:
        if self.old_relation is not None:
            for sim in self.asset.similar:
                if sim.id == self.target_id:
                    sim.relation_type = self.old_relation
                    break
            await self.mapper.save(self.asset)


class CommandHistory:
    """Manages an undo stack of TriageCommands."""
    
    def __init__(self, max_size: int = 100):
        self._stack: list[TriageCommand] = []
        self._max_size = max_size

    def push(self, command: TriageCommand) -> None:
        """Add a command to history."""
        self._stack.append(command)
        if len(self._stack) > self._max_size:
            self._stack.pop(0)

    async def undo(self) -> None:
        """Undo the last command."""
        if not self._stack:
            logger.warning("Undo stack empty")
            return
        
        command = self._stack.pop()
        await command.undo()
