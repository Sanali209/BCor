import asyncio
import platform
from loguru import logger

class WindowsLoopManager:
    """Manages asyncio loop policies and drainage for Windows stability.
    
    This manager provides utilities to ensure that the asyncio event loop
    behaves correctly on Windows, particularly when integrated with GUI
    frameworks like PySide6 via qasync.
    """
    
    @staticmethod
    def setup_loop():
        """Set up the appropriate event loop policy for Windows.
        
        On Windows, this applies the `WindowsSelectorEventLoopPolicy` which is
        often more stable when working with certain network and GUI operations
        compared to the default ProactorEventLoop in newer Python versions.
        """
        if platform.system() == "Windows":
            # Using SelectorEventLoop for better stability with some GUI tools
            # though Proactor is default in 3.8+.
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            logger.debug("Applied WindowsSelectorEventLoopPolicy")

    @staticmethod
    async def drain_loop(delay: float = 0.5):
        """Allow pending tasks to settle before shutdown.
        
        Args:
            delay: Time in seconds to wait for tasks to settle.
        """
        logger.debug(f"Draining event loop for {delay}s...")
        try:
            # Use wait_for to ensure we don't hang forever if something is stuck
            await asyncio.wait_for(asyncio.sleep(delay), timeout=delay + 0.1)
        except Exception as e:
            logger.debug(f"Loop drainage finished (note: {e})")
