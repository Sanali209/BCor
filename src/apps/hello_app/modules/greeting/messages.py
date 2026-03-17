from src.core.messages import Command, Event

class SayHelloCommand(Command):
    name: str

class HelloSaidEvent(Event):
    message: str
