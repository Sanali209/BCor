import os
import logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Any, Optional
from PIL import Image

logger = logging.getLogger(__name__)

# Increase max image size slightly for discovery (user can configure later)
Image.MAX_IMAGE_PIXELS = 200_000_000 

def get_supported_formats() -> Dict[str, str]:
    """Dynamically discover all formats supported by the installed PIL/Pillow."""
    Image.init()
    # extension -> format name (e.g., .jpg -> JPEG)
    return {ext: fmt for ext, fmt in Image.EXTENSION.items()}

def scan_file(path: str) -> Optional[Dict[str, Any]]:
    """
    Process a single file to extract metadata.
    Designed to be run in a separate process.
    """
    try:
        p = Path(path)
        stat = p.stat()
        
        # Quick filtering by extension first to avoid opening non-images
        # This is an optimization; PIL.open would fail anyway, but this is faster.
        # However, to be truly generic, we might trust PIL.open more. 
        # For 1M files, we assume the user is scanning valid dirs.
        
        with Image.open(path) as img:
            width, height = img.size
            return {
                "path": str(p.absolute()),
                "filename": p.name,
                "extension": p.suffix.lower(),
                "size_bytes": stat.st_size,
                "width": width,
                "height": height,
                "created_at": stat.st_ctime,
                "modified_at": stat.st_mtime
            }
    except Exception as e:
        # Not an image or corrupted
        return None

def scan_directory_parallel(directory: str, max_workers: int = None) -> List[Dict[str, Any]]:
    """
    Scan a directory recursively using multiprocessing.
    Returns a list of valid image records.
    """
    directory = Path(directory)
    if not directory.exists():
        logger.error(f"Directory not found: {directory}")
        return []

    image_extensions = set(get_supported_formats().keys())
    files_to_process = []
    
    # Fast directory traversal
    # os.walk is usually fast enough, but scandir is better.
    # We collect all candidate paths first, then process them in parallel.
    logger.info("Traversing directory structure...")
    for root, dirs, files in os.walk(directory):
        for file in files:
            _, ext = os.path.splitext(file)
            if ext.lower() in image_extensions:
                files_to_process.append(os.path.join(root, file))
    
    logger.info(f"Found {len(files_to_process)} candidate files. scanning metadata...")
    
    results = []
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        # Chunking might be better for 1M files, but ProcessPoolExecutor handles queuing well.
        # taking care not to consume too much RAM with futures if 1M files.
        # For very large sets, we might yield chunks.
        
        # Batch submission for memory safety on massive sets?
        # Let's simple-batch it: process in chunks of 10000
        
        chunk_size = 5000
        for i in range(0, len(files_to_process), chunk_size):
            chunk = files_to_process[i:i + chunk_size]
            future_to_file = {executor.submit(scan_file, f): f for f in chunk}
            
            for future in as_completed(future_to_file):
                res = future.result()
                if res:
                    results.append(res)
                    
    return results

class Scanner:
    """Class wrapper for stateful scanning if needed later."""
    def __init__(self):
        self.supported_formats = get_supported_formats()

    def scan(self, path: str) -> List[Dict[str, Any]]:
        return scan_directory_parallel(path)
