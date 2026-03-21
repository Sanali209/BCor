import asyncio
import sys
from pathlib import Path

import loguru

# Ensure the BCor root is in sys.path if running directly
# (This is just for easy manual execution)
sys.path.append(str(Path(__file__).parent.parent.parent.parent))

from src.apps.hello_app.modules.greeting.messages import SayHelloCommand
from src.apps.hello_app.settings import HelloAppSettings
from src.core.system import System


async def main():
    """Main entry point for the Hello BCor console application.

    This function demonstrates the full bootstrap lifecycle:
    1. Loading configuration from 'app.toml'.
    2. Initializing the System (IoC, Module Discovery).
    3. Customizing the DI container with app-specific providers.
    4. Running an interactive CLI loop that dispatches commands
       through the MessageBus.
    """
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
        level=app_settings.log_level,
    )

    loguru.logger.info(f"Starting {app_settings.app_name} with log level {app_settings.log_level}")

    # Initialize the IoC container
    from dishka import Provider, Scope, provide

    from src.core.unit_of_work import AbstractUnitOfWork

    class FakeUoW(AbstractUnitOfWork):
        """A simplified Unit of Work for console-based interaction."""

        def __init__(self, greeter):
            self.greeter = greeter
            self.events = []

        def _commit(self):
            pass

        def rollback(self):
            pass

        def collect_new_events(self):
            while self.events:
                yield self.events.pop(0)

    class AppProvider(Provider):
        """Dishka Provider for application-level overrides."""

        @provide(scope=Scope.REQUEST)
        def provide_uow(
            self,
            greeter: getattr(
                sys.modules[__name__],
                "Greeter",
                __import__("src.apps.hello_app.modules.greeting.domain", fromlist=["Greeter"]).Greeter,
            ),
        ) -> AbstractUnitOfWork:
            """Resolves a FakeUoW for the greeting module."""
            return FakeUoW(greeter)

    system.providers.append(AppProvider())
    system._bootstrap()

    # 3. Execution Loop
    try:
        async with system.container() as request_container:
            # We must resolve the MessageBus manually for CLI usage
            from src.core.messagebus import MessageBus

            bus = await request_container.get(MessageBus)

            print("\n" + "=" * 50)
            print(f"Welcome to {app_settings.app_name} Console Playground!")
            print("=" * 50)

            while True:
                user_input = input("Enter a name (or 'quit' to exit): ")
                if user_input.lower() in ("quit", "q", "exit"):
                    break

                # Dispatching command (this demonstrates EDA & CQRS)
                await bus.dispatch(SayHelloCommand(name=user_input))

    except KeyboardInterrupt:
        pass
    finally:
        loguru.logger.info("Shutting down application...")
        await system.container.close()


if __name__ == "__main__":
    asyncio.run(main())
