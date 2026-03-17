import sys
import asyncio
from pathlib import Path
import loguru

# Ensure the BCor root is in sys.path if running directly
# (This is just for easy manual execution)
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.core.system import System
from src.apps.hello_app.settings import HelloAppSettings
from src.apps.hello_app.modules.greeting.messages import SayHelloCommand

async def main():
    # 1. Bootstrapping
    manifest_path = Path(__file__).parent / "app.toml"
    system = System.from_manifest(str(manifest_path))
    
    # 2. Extract App Settings and configure Observability
    # The TOML '[app]' block is matched to HelloAppSettings
    raw_app_config = system.config.get("app", {})
    app_settings = HelloAppSettings(**raw_app_config)

    loguru.logger.remove()
    loguru.logger.add(
        sys.stderr, 
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan> - <level>{message}</level>", 
        level=app_settings.log_level
    )
    
    loguru.logger.info(f"Starting {app_settings.app_name} with log level {app_settings.log_level}")

    # Initialize the IoC container
    # For a real app, you might want to inject a real UnitOfWork
    # But since Greeting doesn't use DB, we can just use a fake one.
    from dishka import Provider, Scope, provide
    from src.core.unit_of_work import AbstractUnitOfWork
    class FakeUoW(AbstractUnitOfWork):
        def __init__(self, greeter):
            self.greeter = greeter
            self.events = []
        def _commit(self): pass
        def rollback(self): pass
        def collect_new_events(self):
            while self.events:
                yield self.events.pop(0)

    class AppProvider(Provider):
        @provide(scope=Scope.REQUEST)
        def provide_uow(self, greeter: getattr(sys.modules[__name__], 'Greeter', __import__('src.apps.hello_app.modules.greeting.domain', fromlist=['Greeter']).Greeter)) -> AbstractUnitOfWork:
            return FakeUoW(greeter)
            
    system.providers.append(AppProvider())
    system._bootstrap()

    # 3. Execution Loop
    try:
        async with system.container() as request_container:
            # We must resolve the MessageBus manually for CLI usage
            # Typically a FastAPI route gets it injected automatically
            from src.core.messagebus import MessageBus
            bus = await request_container.get(MessageBus)

            print("\n" + "="*50)
            print(f"Welcome to {app_settings.app_name} Console Playground!")
            print("="*50)
            
            while True:
                user_input = input("Enter a name (or 'quit' to exit): ")
                if user_input.lower() in ("quit", "q", "exit"):
                    break
                
                # Dispatching command (this demonstrates EDA & CQRS)
                # The command handler logic is completed, and it returns events,
                # which the MessageBus then routes to the event handlers (on_hello_said).
                await bus.dispatch(SayHelloCommand(name=user_input))

    except KeyboardInterrupt:
        pass
    finally:
        loguru.logger.info("Shutting down application...")
        await system.container.close()

if __name__ == "__main__":
    asyncio.run(main())
