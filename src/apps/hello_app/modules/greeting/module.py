from dishka import Provider, Scope, provide
from pydantic_settings import BaseSettings

from src.apps.hello_app.modules.greeting.domain import Greeter
from src.apps.hello_app.modules.greeting.handlers import handle_say_hello, on_hello_said
from src.apps.hello_app.modules.greeting.messages import HelloSaidEvent, SayHelloCommand
from src.core.module import BaseModule


class GreetingSettings(BaseSettings):
    default_name: str = "Anonymous"
    greeting_style: str = "normal"


class GreetingProvider(Provider):
    scope = Scope.REQUEST

    @provide
    def provide_greeter(self, settings: dict[str, BaseSettings]) -> Greeter:
        # settings dict is provided by CoreProvider (from System)
        # However, to avoid tight coupling to the global dict,
        # we can just use the module's own settings if we want.
        # But Dishka allows injecting Dict[str, BaseSettings]
        module_settings = settings.get("greeting", GreetingSettings())
        return Greeter(default_name=module_settings.default_name, style=module_settings.greeting_style)


class GreetingModule(BaseModule):
    settings_class = GreetingSettings

    def __init__(self):
        super().__init__()
        self.provider = GreetingProvider()

        self.command_handlers = {
            SayHelloCommand: handle_say_hello,
        }

        self.event_handlers = {
            HelloSaidEvent: [on_hello_said],
        }
