from unittest.mock import MagicMock, patch

import pytest
from returns.result import Success

from src.apps.ImageAnalyze.handlers import launch_legacy_gui_handler
from src.apps.ImageAnalyze.messages import LaunchLegacyGuiCommand


@pytest.mark.asyncio
async def test_launch_legacy_gui_handler_executes_successfully() -> None:
    # Arrange
    command = LaunchLegacyGuiCommand()
    mock_bus = MagicMock()
    mock_preset_manager = MagicMock()
    mock_theme_manager = MagicMock()

    # Act & Assert
    with (
        patch("src.apps.ImageAnalyze.handlers.QApplication") as MockQApp,
        patch("src.apps.ImageAnalyze.handlers.MainWindow") as MockMainWindow,
    ):
        # Настраиваем MockQApp.instance() чтобы он возвращал наш мок
        mock_app_instance = MockQApp.return_value
        MockQApp.instance.return_value = mock_app_instance

        # Act
        result = await launch_legacy_gui_handler(command, mock_bus, mock_preset_manager, mock_theme_manager)

        # Assert
        assert isinstance(result, Success)
        assert result.unwrap() == "GUI Exited Successfully"
        MockMainWindow.assert_called_once_with(bus=mock_bus, preset_manager=mock_preset_manager, theme_manager=mock_theme_manager)

        # Проверяем, что exec был вызван либо у инстанса, либо у нового объекта
        # В зависимости от того, как сработал QApplication.instance()
        assert mock_app_instance.exec.called
