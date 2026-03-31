"""
Service Container - Single source of truth for all application services
Following module-level Singleton pattern with lazy service instantiation.
"""

import asyncio
import os
from typing import Dict, Any, Optional, Callable, Type, TypeVar, List
from loguru import logger

# Define a TypeVar for generic service resolution
T = TypeVar('T')

# Module-level singleton instance
_service_container: Optional['ServiceContainer'] = None


class ServiceContainer:
    """Central service registry implementing service locator pattern with lazy instantiation"""

    def __init__(self):
        self._services: Dict[type, Any] = {}
        self._service_factories: Dict[type, Callable[[], Any]] = {}
        self._bcor_cache: Dict[type, Any] = {}
        self.bcor_system: Optional[Any] = None
        self._initialize_services()

    async def prepare_bcor_bridge(self, extra_services: List[Type] = None):
        """
        Async method to pre-resolve BCor services into the sync cache.
        Call this during app startup or test setup while a loop is running.
        """
        if not self.bcor_system:
            return
            
        services_to_resolve = []
        try:
            from bubus import EventBus
            services_to_resolve.append(EventBus)
        except ImportError:
            pass
            
        if extra_services:
            services_to_resolve.extend(extra_services)
            
        for stype in services_to_resolve:
            try:
                instance = await self.bcor_system.container.get(stype)
                self._bcor_cache[stype] = instance
                logger.debug(f"Bridge pre-resolved BCor service: {stype.__name__}")
            except Exception as e:
                logger.warning(f"Bridge failed to pre-resolve {stype.__name__}: {e}")

    def get_service(self, service_type: Type[T]) -> T:
        """Resolve service from legacy registry or BCor DI container."""
        # 1. Try legacy registry
        if service_type in self._services:
            return self._services[service_type]

        # 2. Try service factories
        if service_type in self._service_factories:
            logger.debug(f"Creating legacy service instance: {service_type.__name__}")
            instance = self._service_factories[service_type]()
            self._services[service_type] = instance
            return instance

        # 3. Try BCor bridge
        if self.bcor_system:
            if service_type in self._bcor_cache:
                return self._bcor_cache[service_type]

            try:
                # Try sync resolution only if no loop is running
                try:
                    asyncio.get_running_loop()
                    # Loop is running. If not in cache, we CANNOT resolve synchronously here.
                    logger.error(
                        f"CRITICAL: Attempted to resolve {service_type.__name__} from BCor "
                        "synchronously while an asyncio loop is running. "
                        "You MUST await prepare_bcor_bridge() first!"
                    )
                    raise RuntimeError(f"Service {service_type.__name__} not pre-resolved for sync access.")
                except RuntimeError as re:
                    # If this is our own RuntimeError from above, re-raise it
                    if "not pre-resolved" in str(re):
                        raise
                        
                    # No loop running, can use asyncio.run
                    logger.debug(f"Resolving {service_type.__name__} from BCor using asyncio.run()")
                    instance = asyncio.run(self.bcor_system.container.get(service_type))
                    self._bcor_cache[service_type] = instance
                    return instance
            except Exception as e:
                logger.warning(f"Failed to resolve {service_type.__name__} from BCor: {e}")
                raise ValueError(f"Service not registered or resolution failed: {service_type.__name__}")

        raise ValueError(f"Service not registered: {service_type.__name__}")

    def register_service_factory(self, service_type: type, factory: Callable[[], Any]):
        """Register a factory function for lazy service instantiation"""
        self._service_factories[service_type] = factory
        logger.debug(f"Registered service factory: {service_type.__name__}")

    def register_service(self, service_type: type, service_instance: Any):
        """Register a pre-instantiated service"""
        self._services[service_type] = service_instance
        logger.debug(f"Registered service instance: {service_type.__name__}")

    def declaration_services(self):
        """
        Method to be overridden by subclasses to declare additional services
        """
        pass

    def _initialize_services(self):
        """Initialize core services - called during singleton creation"""
        logger.info("Initializing service container...")
        
        # Initialize BCor System if app.toml exists
        try:
            from src.core.system import System
            # Try to find app.toml relative to this file
            current_dir = os.path.dirname(os.path.abspath(__file__))
            manifest_path = os.path.abspath(os.path.join(current_dir, "..", "..", "..", "app.toml"))
            
            if not os.path.exists(manifest_path):
                 # Fallback path for different execution contexts
                 manifest_path = os.path.abspath("src/apps/experemental/sanali/app.toml")

            if os.path.exists(manifest_path):
                if not self.bcor_system:
                    self.bcor_system = System.from_manifest(manifest_path)
                    self.bcor_system._bootstrap()
                    logger.info(f"BCor System initialized and bootstrapped from {manifest_path}")
                else:
                    logger.info("Using pre-injected BCor System")
            else:
                logger.warning(f"Manifest not found at {manifest_path}. BCor System skip.")
        except Exception as e:
            logger.warning(f"Could not initialize BCor System: {e}")

        self.declaration_services()
        logger.info("Service container initialization complete")

    def clear(self):
        """Reset the container state, clearing cached services and system bridge."""
        self._services.clear()
        self._bcor_cache.clear()
        self.bcor_system = None
        logger.debug("ServiceContainer cleared")

    def get_configuration(self):
        """Convenience method for common services"""
        from .configuration_service import ConfigurationService
        return self.get_service(ConfigurationService)


def get_service_container(serviceContainer=None) -> ServiceContainer:
    """Get the singleton service container instance"""
    global _service_container
    if _service_container is None:
        if serviceContainer is None:
            _service_container = ServiceContainer()
        else:
            _service_container = serviceContainer
    return _service_container


class BaseServiceContainer(ServiceContainer):
    """Base service container for application-specific services"""

    def declaration_services(self):
        """Declare additional services specific to the application"""
        from src.modules.sanali.services import (
            ConfigurationService as BCorConfig, 
            DuplicateService, 
            ProjectStateService,
            NeiroFilterService,
            UserPreferenceService
        )
        from src.modules.sanali.presenters import ImageDedupPresenter
        
        allowed_bcor_services = {
            BCorConfig, DuplicateService, ProjectStateService, 
            ImageDedupPresenter, NeiroFilterService, UserPreferenceService
        }
        
        from .configuration_service import ConfigurationService

        # Register core service factories
        def config_factory():
            return ConfigurationService()

        self.register_service_factory(ConfigurationService, config_factory)


def get_config() -> Any:
    """Global function to get configuration service"""
    return get_service_container().get_configuration()
