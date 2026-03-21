"""File and path management utilities.

Ported and modernized from legacy appGlue/iotools/pathtools.py.
"""
from __future__ import annotations

import fnmatch
import os
import shutil
import subprocess
from pathlib import Path
from typing import Iterable, Sequence

import psutil
from tqdm import tqdm


class PathTools:
    """Utilities for advanced path and file management."""

    DEFAULT_EXTS = ["*.jpg", "*.jpeg", "*.png", "*.gif", "*.bmp", "*.tif", "*.tiff"]

    @staticmethod
    def get_files(
        directory: str | Path,
        extensions: Sequence[str] | None = None,
        ignore_mask: str = "",
        recursive: bool = True,
        show_progress: bool = False,
    ) -> list[Path]:
        """Recursively (or not) find files with specific extensions.
        
        Args:
            directory: Root directory to scan.
            extensions: List of glob patterns (e.g. ['*.jpg']). Defaults to common images.
            ignore_mask: Filename pattern to ignore (e.g. 'Thumbs.db').
            recursive: Whether to scan subdirectories.
            show_progress: Whether to display a tqdm progress bar.
            
        Returns:
            List of Path objects matching the criteria.
        """
        root = Path(directory)
        if not root.exists() or not root.is_dir():
            return []

        if extensions is None:
            extensions = PathTools.DEFAULT_EXTS

        matches: list[Path] = []
        
        # Use os.walk for performance on large directories, then wrap in Path
        walker = os.walk(root) if recursive else [(str(root), [], os.listdir(root))]
        
        if show_progress:
            walker = tqdm(list(walker), desc=f"Scanning {root.name}")

        for current_root, _, filenames in walker:
            for filename in filenames:
                if ignore_mask and fnmatch.fnmatch(filename, ignore_mask):
                    continue
                
                # Check extensions
                for ext in extensions:
                    if fnmatch.fnmatch(filename.lower(), ext.lower()):
                        matches.append(Path(current_root) / filename)
                        break
                        
        return matches

    @staticmethod
    def get_sub_dirs(directory: str | Path) -> list[Path]:
        """List all accessible sub-directories.
        
        Args:
            directory: Directory to list.
            
        Returns:
            List of Path objects representing subdirectories.
        """
        root = Path(directory)
        if not root.exists():
            return []
            
        return [p for p in root.iterdir() if p.is_dir()]

    @staticmethod
    def find_new_name(target: str | Path) -> Path:
        """Find a non-existing filename by appending numbers if needed.
        
        Example: 'file.jpg' -> 'file2.jpg'.
        
        Args:
            target: Desired path.
            
        Returns:
            A Path object that is guaranteed not to exist on disk at the time of check.
        """
        target_path = Path(target)
        if not target_path.exists():
            return target_path

        parent = target_path.parent
        name = target_path.stem
        suffix = target_path.suffix
        
        # Remove existing numbers at the end of stem for clean incrementing
        import re
        name = re.sub(r'\d+$', '', name)
        
        counter = 2
        while True:
            new_path = parent / f"{name}{counter}{suffix}"
            if not new_path.exists():
                return new_path
            counter += 1

    @staticmethod
    def open_in_explorer(path: str | Path) -> None:
        """Open the OS file explorer and select the given path.
        
        Args:
            path: File or directory to show.
        """
        p = Path(path).resolve()
        if not p.exists():
            return

        import sys
        if sys.platform == "win32":
            # On Windows, use 'explorer /select,"path"'
            subprocess.Popen(f'explorer /select,"{p}"')
        elif sys.platform == "darwin":
            subprocess.Popen(["open", "-R", str(p)])
        else:
            # Linux: xdg-open doesn't always support selection, just open parent
            subprocess.Popen(["xdg-open", str(p.parent)])

    @staticmethod
    def get_drive_letters() -> list[str]:
        """Get list of active drive mount points (Windows-centric but works on Linux)."""
        return [p.device for p in psutil.disk_partitions() if os.access(p.device, os.R_OK)]
