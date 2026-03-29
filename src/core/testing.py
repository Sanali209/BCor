import asyncio
from typing import AsyncGenerator, Optional, Any
from contextlib import asynccontextmanager
from loguru import logger
from src.core.system import System
from src.core.loop_policies import WindowsLoopManager

class BCorTestSystem:
    """Context manager to safely manage System lifecycle and loop drainage in tests.
    
    This utility ensures that the BCor System is properly started before a test
    runs and stopped afterward, including the critical step of draining the
    asyncio event loop to prevent hangs or resource leaks on Windows.
    """
    
    def __init__(self, manifest_path: str, drain_delay: float = 0.5):
        """Initialize the test system context.
        
        Args:
            manifest_path: Path to the app.toml manifest file.
            drain_delay: Seconds to wait for loop drainage during teardown.
        """
        self.manifest_path = manifest_path
        self.drain_delay = drain_delay
        self.system: Optional[System] = None

    @asynccontextmanager
    async def run(self) -> AsyncGenerator[System, None]:
        """Start the system, yield it, and then stop it with drainage.
        
        Yields:
            The started System instance.
        """
        self.system = System.from_manifest(self.manifest_path)
        logger.debug(f"Starting Test System from {self.manifest_path}")
        await self.system.start()
        
        # Inject into ServiceContainer bridge if available (optional)
        try:
            from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
            container = get_service_container()
            container.bcor_system = self.system
            logger.debug("Injected test system into ServiceContainer bridge")
        except (ImportError, Exception):
            # This is optional and only for Sanali porting compatibility
            pass
        
        try:
            yield self.system
        finally:
            logger.debug("Stopping Test System...")
            try:
                # Clear ServiceContainer bridge FIRST while loop is still alive
                from src.apps.experemental.sanali.Python.core_apps.services.service_container import get_service_container
                container = get_service_container()
                container.clear()
                logger.debug("ServiceContainer cleared during teardown")
                
                # Clear legacy MessageSystem subscribers
                from src.apps.experemental.sanali.Python.SLM.appGlue.DesignPaterns.MessageSystem import MessageSystem
                MessageSystem.subscribers.clear()
                logger.debug("MessageSystem subscribers cleared during teardown")
            except (ImportError, Exception):
                pass

            if self.system:
                await self.system.stop()
            
            # Force cancel all pending tasks except the current one
            tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
            if tasks:
                logger.debug(f"Cancelling {len(tasks)} pending tasks...")
                for task in tasks:
                    if not task.done():
                        task.cancel()
                
                # Wait for cancellations with a timeout
                try:
                    await asyncio.wait(tasks, timeout=0.2)
                except Exception as e:
                    logger.debug(f"Error during task cancellation wait: {e}")

            await WindowsLoopManager.drain_loop(self.drain_delay)
            logger.debug("Test System stopped and loop drained.")

async def run_test_system(manifest_path: str, test_func: Any, *args: Any, **kwargs: Any):
    """Helper to run a test function within a BCorTestSystem context.
    
    Args:
        manifest_path: Path to the app.toml manifest.
        test_func: The async test function to execute.
        *args: Positional arguments for test_func.
        **kwargs: Keyword arguments for test_func.
    """
    async with BCorTestSystem(manifest_path).run() as system:
        await test_func(system, *args, **kwargs)
