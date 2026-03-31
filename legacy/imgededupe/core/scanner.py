import os
from typing import List, Optional
from loguru import logger
from .database import DatabaseManager
from .deduper import Deduper

class Scanner:
    """
    BCor-style Scanner service.
    Handles file system traversal and indexing delegating to engine.
    """
    def __init__(self, db_manager: DatabaseManager, deduper: Deduper):
        self.db_manager = db_manager
        self.deduper = deduper

    def scan(self, roots: List[str], recursive: bool = True) -> int:
        """
        Traverse directories and index files.
        Returns the number of files processed.
        """
        logger.info(f"Scanner: Starting scan in {roots}")
        files = []
        for root in roots:
            if not os.path.exists(root):
                continue
            if recursive:
                for dirpath, _, filenames in os.walk(root):
                    for f in filenames:
                        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                            files.append(os.path.abspath(os.path.join(dirpath, f)))
            else:
                for f in os.listdir(root):
                    if f.lower().endswith(('.png', '.jpg', '.jpeg', '.bmp', '.gif', '.webp')):
                        files.append(os.path.abspath(os.path.join(root, f)))
        
        logger.info(f"Scanner: Found {len(files)} files. Starting indexing...")
        
        # Initialize engine if needed
        self.deduper.engine.initialize()
        
        # Index files
        self.deduper.engine.index_files(files)
        
        return len(files)

# Keep ScanWorker for legacy compatibility if needed by the UI
from PySide6.QtCore import QThread, Signal

class ScanWorker(QThread):
    progress = Signal(int, int)
    file_processed = Signal(str)
    finished_scan = Signal()
    error_occurred = Signal(str)
    scan_results_ready = Signal(list)

    def __init__(self, roots, db_path, engine_type='phash', threshold=5):
        super().__init__()
        self.roots = roots
        self.db_path = db_path
        self.engine_type = engine_type
        self.threshold = threshold
        self.stop_requested = False

    def run(self):
        try:
            db_manager = DatabaseManager(self.db_path)
            from .repositories.file_repository import FileRepository
            file_repo = FileRepository(db_manager)
            from .repositories.cluster_repository import ClusterRepository
            cluster_repo = ClusterRepository(db_manager)
            
            deduper = Deduper(db_manager, file_repo)
            deduper.set_engine(self.engine_type)
            
            scanner = Scanner(db_manager, deduper)
            count = scanner.scan(self.roots)
            
            results = deduper.find_duplicates(threshold=self.threshold, roots=self.roots)
            self.scan_results_ready.emit(results)
        except Exception as e:
            logger.error(f"ScanWorker error: {e}")
            self.error_occurred.emit(str(e))
        finally:
            self.finished_scan.emit()

    def stop(self):
        self.stop_requested = True
        self.wait()
