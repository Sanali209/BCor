import loguru
from src.apps.hello_app.modules.greeting.messages import SayHelloCommand, HelloSaidEvent

async def handle_say_hello(cmd: SayHelloCommand, uow):
    """Command Handler for SayHelloCommand."""
    message = uow.greeter.generate_greeting(cmd.name)
    
    # We use the MessageBus (uow.bus if present, or we can just return events)
    # Since BCor typical handlers return lists of events to be published,
    # or attach them to aggregate roots. For our simple console app:
    uow.events.append(HelloSaidEvent(message=message))
    return message

async def on_hello_said(event: HelloSaidEvent, uow):
    """Event Handler (Observability Test)."""
    loguru.logger.info(f"Observability Test | Event Received: {event.message}")
    # Print it to the console for the user to see easily
    print(f"\n>> App Output: {event.message}\n")
