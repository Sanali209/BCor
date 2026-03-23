from loguru import logger
from typing import List

class MetadataWriter:
    def __init__(self):
        pass

    def write_tags(self, file_path: str, tags: List[str]):
        """Writes XMP tags to the file using pyexiv2."""
        try:
            import pyexiv2
            with pyexiv2.Image(file_path) as img:
                img.modify_xmp({'Xmp.dc.subject': tags})
            logger.info(f"Wrote {len(tags)} tags to {file_path}")
        except ImportError:
            logger.warning("pyexiv2 not installed. Skipping metadata writing.")
        except Exception as e:
            logger.error(f"Failed to write metadata: {e}")
