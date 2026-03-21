from __future__ import annotations

import logging
import os
from typing import Any, cast

from PySide6.QtCore import QCoreApplication, Qt
from PySide6.QtWidgets import QApplication

from src.apps.ImageAnalyze.core.preset_manager import PresetManager
from src.apps.ImageAnalyze.domain.interfaces.image_repository import IImageRepository
from src.apps.ImageAnalyze.gui.main_window import MainWindow
from src.apps.ImageAnalyze.messages import (
    ApplyBatchRulesCommand,
    GetAnalyticsQuery,
    GetImageMetadataQuery,
    LaunchLegacyGuiCommand,
    ScanDirectoryCommand,
)
from src.apps.ImageAnalyze.use_cases import ExecuteBatchRulesUseCase, GetCollectionStatsUseCase, ScanDirectoryUseCase
from src.common.monads import BusinessResult, failure, success
from src.common.ui.theming.manager import ThemeManager
from src.common.ui.theming.provider import Theme
from src.core.messagebus import MessageBus

logger = logging.getLogger(__name__)


async def launch_legacy_gui_handler(
    command: LaunchLegacyGuiCommand, bus: MessageBus, preset_manager: PresetManager, theme_manager: ThemeManager
) -> BusinessResult[str, str]:
    """Точка входа для запуска GUI. Передает MessageBus в MainWindow."""
    try:
        logger.info("Launching Legacy PySide6 GUI from Handler Function")

        # Set environment variable for Chromium BEFORE creating QApplication
        os.environ["QTWEBENGINE_CHROMIUM_FLAGS"] = (
            "--disable-gpu --disable-gpu-compositing --disable-gpu-rasterization "
            "--ignore-gpu-blocklist --disable-direct-composition --log-level=3"
        )
        os.environ["QT_LOGGING_RULES"] = (
            "qt.webenginecontext.debug=false;*.debug=false;qt.webenginecontext.warning=false"
        )

        app = cast(QApplication, QApplication.instance() or QApplication([]))
        app.setStyle("Fusion")

        # Apply initial skin
        initial_qss = theme_manager.get_current_qss()
        theme = theme_manager.get_current_theme()
        if initial_qss and theme:
            bg_color = theme.colors.get("bg", "#1a1a2e")
            app.setStyleSheet(f"QMainWindow {{ background-color: {bg_color}; }}")
        theme_manager.theme_changed.connect(lambda qss: app.setStyleSheet(qss))
        # Resolve use cases from the container (which is attached to the bus)
        if bus.container is None:
            return failure("DI Container not found on MessageBus")

        scan_uc = await bus.container.get(ScanDirectoryUseCase)
        stats_uc = await bus.container.get(GetCollectionStatsUseCase)
        batch_uc = await bus.container.get(ExecuteBatchRulesUseCase)

        window = MainWindow(
            scan_use_case=scan_uc,
            stats_use_case=stats_uc,
            batch_use_case=batch_uc
        )
        window.show()

        app.exec()
        return success("GUI Exited Successfully")
    except Exception as e:
        logger.error(f"Failed to launch GUI: {e}")
        return failure(str(e))


async def handle_scan_directory(
    command: ScanDirectoryCommand, scan_use_case: ScanDirectoryUseCase, repository: IImageRepository
) -> BusinessResult[int, str]:
    """Обработчик команды сканирования. Использует доменный юзкейс и репозиторий."""
    try:
        count = await scan_use_case.execute(command.path)
        # scan_use_case already saves to repository in its execute method
        return success(count)
    except Exception as e:
        logger.error(f"Scan failed: {e}")
        return failure(str(e))


async def handle_apply_batch(
    command: ApplyBatchRulesCommand, batch_use_case: ExecuteBatchRulesUseCase, repository: IImageRepository
) -> BusinessResult[Any, str]:
    """Обработчик команды пакетной обработки. Рекордит результаты экономии места."""
    try:
        results = await batch_use_case.execute(command.rules, command.dry_run)
        for res in results:
            if res.success:
                repository.record_saving(res.action_taken, res.saved_bytes, res.original_path)
        return success(results)
    except Exception as e:
        logger.error(f"Batch processing failed: {e}")
        return failure(str(e))


async def handle_get_images(command: GetImageMetadataQuery, repository: IImageRepository) -> BusinessResult[Any, str]:
    """Обработчик запроса на получение всех изображений."""
    try:
        images = repository.get_all()
        return success(images)
    except Exception as e:
        return failure(str(e))


async def handle_get_analytics(command: GetAnalyticsQuery, repository: IImageRepository) -> BusinessResult[Any, str]:
    """Обработчик запроса на получение аналитики."""
    try:
        stats = repository.get_stats()
        ext_stats = repository.get_extension_stats()
        chart_data = repository.get_chart_data()
        savings = {
            "total_saved_bytes": repository.get_stats().get("total_saved_bytes", 0),  # Simplified for now
            "history": repository.get_savings_history(),
        }

        return success({"summary": stats, "extensions": ext_stats, "charts": chart_data, "savings": savings})
    except Exception as e:
        logger.error(f"Analytics fail: {e}")
        return failure(str(e))
