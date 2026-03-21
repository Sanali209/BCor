import sys
import os
import pytest
from unittest.mock import AsyncMock, MagicMock

# Add legacy path to sys.path
legacy_parent_path = os.path.abspath(os.path.join(os.getcwd(), "src", "legacy_to_port", "sanali209", "Python"))
if legacy_parent_path not in sys.path:
    sys.path.append(legacy_parent_path)

from SLM.actions.action_module import ActionManager, AppAction
from SLM.actions import action_manager

class MockLegacyAction(AppAction):
    def run(self, *args, **kwargs):
        return "legacy_result"

@pytest.fixture
def clean_action_manager():
    """Clears ActionManager actions before/after test."""
    original_actions = action_manager.actions[:]
    action_manager.actions = []
    yield action_manager
    action_manager.actions = original_actions

def test_legacy_action_manager_basic(clean_action_manager):
    """Verifies that legacy ActionManager works as expected."""
    action = MockLegacyAction(name="test_action")
    action_manager.actions.append(action)
    
    result = action_manager.run_action_by_name("test_action")
    assert result == "legacy_result"

# TDD: We want a bridge that can map legacy action calls to BCor commands.

@pytest.mark.asyncio
async def test_action_bridge_dispatch(clean_action_manager):
    """
    Verifies that a bridge action can dispatch a BCor command.
    """
    from src.core.bridge import LegacyActionBridge
    from src.core.messages import Command
    from dataclasses import dataclass

    class TestCommand(Command):
        value: str

    mock_bus = AsyncMock()
    bridge = LegacyActionBridge(message_bus=mock_bus)
    
    # Register a bridge action
    bridge.register_action(
        name="new_action",
        command_cls=TestCommand,
        mapping=lambda *args, **kwargs: {"value": args[0]}
    )
    
    # Run via legacy manager
    action_manager.run_action_by_name("new_action", "hello")
    
    # Verify bus was called
    mock_bus.dispatch.assert_called_once()
    args, kwargs = mock_bus.dispatch.call_args
    cmd = args[0]
    assert isinstance(cmd, TestCommand)
    assert cmd.value == "hello"
