from src.apps.ImageAnalyze.core.image_scanner import scan_directory_parallel, scan_file
from src.apps.ImageAnalyze.domain.entities.image_metadata import ImageMetadata
from src.apps.ImageAnalyze.domain.interfaces.i_image_scanner import IImageScanner


class PILScanner(IImageScanner):
    """Адаптер для сканирования изображений с помощью Pillow и Multiprocessing.
    Использует существующую логику из core/image_scanner.py.
    """

    def scan_file(self, path: str) -> ImageMetadata | None:
        res = scan_file(path)
        if not res:
            return None

        return ImageMetadata(
            path=res["path"],
            filename=res["filename"],
            extension=res["extension"],
            size_bytes=res["size_bytes"],
            width=res["width"],
            height=res["height"],
            created_at=res.get("created_at"),
            modified_at=res.get("modified_at"),
        )

    def scan_directory(self, directory: str) -> list[ImageMetadata]:
        raw_results = scan_directory_parallel(directory)
        metadata_list = []
        for res in raw_results:
            metadata_list.append(
                ImageMetadata(
                    path=res["path"],
                    filename=res["filename"],
                    extension=res["extension"],
                    size_bytes=res["size_bytes"],
                    width=res["width"],
                    height=res["height"],
                    created_at=res.get("created_at"),
                    modified_at=res.get("modified_at"),
                )
            )
        return metadata_list
