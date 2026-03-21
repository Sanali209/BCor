import sys
import asyncio
from loguru import logger
from src.core.system import System
from src.core.messagebus import MessageBus
from .messages import LaunchGuiCommand

async def async_main():
    """Bootstrap the BCor system and launch the app."""
    try:
        # 1. Initialize System from manifest
        # Note: app.toml is in the same directory as main.py
        system = System.from_manifest("src/apps/ImageDedup/app.toml")
        
        # 2. Start System (runs hooks, builds DI container)
        await system.start()
        
        # 3. Get MessageBus from container and send Launch command
        # MessageBus is REQUEST scoped, so we might need a context or just resolve from container
        # System doesn't directly expose container in a simple way for one-offs, 
        # but we can use system.container.
        async with system.container() as request_container:
            bus = await request_container.get(MessageBus)
            await bus.handle(LaunchGuiCommand())
            
        # 4. Stop System (cleanup)
        await system.stop()
        
    except Exception as e:
        logger.exception(f"System failed: {e}")
        sys.exit(1)

def main():
    # Configure logging
    logger.remove()
    logger.add(sys.stderr, format="{time} {level} {message}", level="INFO")
    
    # Run the async entry point
    asyncio.run(async_main())

if __name__ == "__main__":
    main()

