from diskcache import Cache
from loguru import logger
from src.common.paths import PathNormalizer

class ImageManagementUseCase:
    """UseCase for managing image project state and imagesets"""
    
    def __init__(self, cache_path: str = r"D:\data\ImSortPrCache"):
        self.cache = Cache(cache_path)
        logger.info(f"ImageManagementUseCase initialized with cache at {cache_path}")

    @PathNormalizer.normalize_args('path')
    def mark_directory_as_imageset(self, path: str):
        """Mark a directory as a recognized imageset"""
        imagesets = self.cache.get('imagesets', default=[])
        if path not in imagesets:
            imagesets.append(path)
            self.cache['imagesets'] = imagesets
            logger.info(f"Directory marked as imageset: {path}")

    def get_imagesets(self) -> list[str]:
        """Retrieve all directories marked as imagesets"""
        return self.cache.get('imagesets', default=[])
