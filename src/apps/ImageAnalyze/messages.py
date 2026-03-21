from src.apps.ImageAnalyze.domain.entities.batch_processing import Rule
from src.apps.ImageAnalyze.domain.entities.image_metadata import ImageMetadata
from src.core.messages import Command


class LaunchLegacyGuiCommand(Command):
    """Команда запуска старого интерфейса."""

    pass


class ScanDirectoryCommand(Command):
    """Команда сканирования директории."""

    path: str


class ApplyBatchRulesCommand(Command):
    """Команда выполнения пакетной обработки."""

    images: list[ImageMetadata]
    rules: list[Rule]
    dry_run: bool = False


class GetImageMetadataQuery(Command):
    """Запрос на получение всех метаданных из БД."""

    pass


class GetAnalyticsQuery(Command):
    """Запрос на получение полной аналитики для дашборда."""

    pass
