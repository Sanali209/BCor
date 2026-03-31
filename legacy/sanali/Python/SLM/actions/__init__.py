"""
This module is used to manage all the actions that are available in the SLM.

contains:
    class ActionManager
    class AppAction
    singleton instance of ActionManager as action_manager variable
"""

from SLM.actions.action_module import ActionManager
from SLM.actions.action_module import AppAction


action_manager = ActionManager()

