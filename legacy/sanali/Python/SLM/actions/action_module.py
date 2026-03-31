from typing import List

from loguru import logger


class AppAction:

    def __init__(self, **args):
        if "name" in args: self.name = args.pop("name")
        if "description" in args: self.description = args.pop("description")
        self.args = args

    def run_with_delayed_args(self):
        args_dict = self.args
        args_list = []
        for key in args_dict:
            args_list.append(args_dict[key])
        self.run(*args_list, **args_dict)

    def run_on_thread_queue(self):
        pass

    def run(self, *args, **kwargs):
        pass

    def is_supported(self, context):
        return True

    def is_can_run(self, context):
        return True


class ActionManager:
    actions: List[AppAction] = []

    def register(self):
        def decorator(cls):
            self.actions.append(cls())
            return cls

        return decorator

    def get_action_by_name(self, name: str):
        for action in self.actions:
            if action.name == name:
                return action
        return None

    def run_action_by_name(self, name: str, *args, **kwargs):
        action = self.get_action_by_name(name)
        if action is None:
            return False
        return action.run(*args, **kwargs)

    def run_action(self, action: type, *args, **kwargs):
        if not issubclass(action, AppAction):
            logger.error("action is not subclass of AppAction")
        action = action()
        return action.run(*args, **kwargs)
