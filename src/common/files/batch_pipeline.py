"""Async Batch File Operations Pipeline for BCor Common.

This module provides a robust, VFS-aware pipeline pattern for executing 
ordered sequences of operations (Actions) on collections of files.

Rationale:
    Most VFS providers (PyFilesystem2) are synchronous. For BCor's 
    async-native core, we offload all file IO to thread pools to prevent 
    blocking the main event loop. This ensures UI/Bus responsiveness during 
    massive batch operations.

Example:
    >>> fs = OSFS("./my_data")
    >>> pipeline = BatchPipeline(fs)
    >>> pipeline.add_action(FilterByExtension([".jpg", ".png"]))
    >>> pipeline.add_action(DeleteAction())
    >>> pipeline.add_item("image1.jpg")
    >>> await pipeline.run(desc="Cleaning images")
"""
from __future__ import annotations
import asyncio
import os
import fnmatch
from typing import List, Dict, Any, Optional, Protocol, Union
from loguru import logger
from fs.base import FS
from tqdm.asyncio import tqdm

class BatchItem:
    """Represents a single file or entity in a batch operation."""
    def __init__(self, path: str, metadata: Optional[Dict[str, Any]] = None):
        self.path = path
        self.metadata = metadata or {}
        self.aborted = False

class BatchAction(Protocol):
    """Protocol for a single action in the batch pipeline."""
    async def run(self, item: BatchItem, fs: FS) -> bool:
        """Executes the action on an item.
        
        Returns:
            True if the pipeline should continue, False to abort processing for this item.
        """
        ...

class BatchPipeline:
    """Orchestrates an asynchronous sequence of actions over a set of items."""
    
    def __init__(self, fs: FS):
        self.fs = fs
        self.actions: List[BatchAction] = []
        self.items: List[BatchItem] = []

    def add_action(self, action: BatchAction) -> BatchPipeline:
        """Adds an action to the pipeline."""
        self.actions.append(action)
        return self

    def add_item(self, path: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Adds an item to the processing queue."""
        self.items.append(BatchItem(path, metadata))

    async def run(self, desc: str = "Processing Batch") -> None:
        """Executes the pipeline over all items with async progress tracking."""
        if not self.actions:
            logger.warning("BatchPipeline: No actions registered.")
            return

        async for item in tqdm(self.items, desc=desc):
            for action in self.actions:
                try:
                    should_continue = await action.run(item, self.fs)
                    if not should_continue:
                        item.aborted = True
                        break
                except Exception as e:
                    logger.error(f"Error in Batch Action {action.__class__.__name__} on {item.path}: {e}")
                    item.aborted = True
                    break

# --- Common Actions ---

class DeleteAction:
    """Action to delete a file via VFS."""
    async def run(self, item: BatchItem, fs: FS) -> bool:
        if fs.exists(item.path):
            await asyncio.to_thread(fs.remove, item.path)
            logger.debug(f"Deleted: {item.path}")
        return False  # No further actions possible on a deleted file

class RenameAction:
    """Action to rename a file (e.g. to lowercase extension)."""
    def __init__(self, new_path_fn: callable):
        self.new_path_fn = new_path_fn

    async def run(self, item: BatchItem, fs: FS) -> bool:
        new_path = self.new_path_fn(item.path)
        if new_path != item.path:
            await asyncio.to_thread(fs.move, item.path, new_path)
            item.path = new_path
            logger.debug(f"Renamed: {item.path}")
        return True

class FilterByExtension:
    """Action to skip remaining pipeline if extension doesn't match."""
    def __init__(self, exts: List[str]):
        self.exts = [e.lower() for e in exts]

    async def run(self, item: BatchItem, fs: FS) -> bool:
        ext = os.path.splitext(item.path)[1].lower()
        return ext in self.exts or "*" in self.exts

class FilterByMask:
    """Action to skip remaining pipeline if filename doesn't match a mask."""
    def __init__(self, mask: str):
        self.mask = mask

    async def run(self, item: BatchItem, fs: FS) -> bool:
        return fnmatch.fnmatch(os.path.basename(item.path), self.mask)
