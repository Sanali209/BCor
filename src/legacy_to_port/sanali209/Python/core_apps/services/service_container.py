"""
Service Container - Single source of truth for all application services
Following module-level Singleton pattern with lazy service instantiation.
"""

from typing import Dict, Any, Optional, Callable
from loguru import logger

# Module-level singleton instance
_service_container: Optional['ServiceContainer'] = None


class ServiceContainer:
    """Central service registry implementing service locator pattern with lazy instantiation"""

    def __init__(self):
        self._services: Dict[type, Any] = {}
        self._service_factories: Dict[type, Callable[[], Any]] = {}
        self._initialize_services()

    def get_service(self, service_type: type) -> Any:
        """Get a service instance, creating it if necessary"""
        if service_type not in self._services:
            if service_type in self._service_factories:
                logger.debug(f"Creating service instance: {service_type.__name__}")
                self._services[service_type] = self._service_factories[service_type]()
            else:
                raise ValueError(f"Service not registered: {service_type.__name__}")

        return self._services[service_type]

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

        self.declaration_services()
        logger.info("Service container initialization complete")

    def get_configuration(self):
        """Convenience method for common services"""
        from .configuration_service import ConfigurationService
        return self.get_service(ConfigurationService)


def get_service_container(serviceContainer=ServiceContainer()) -> ServiceContainer:
    """Get the singleton service container instance"""
    global _service_container
    if _service_container is None:
        _service_container = serviceContainer
        _service_container._initialize_services()
    return _service_container


class BaseServiceContainer(ServiceContainer):
    """Base service container for application-specific services"""

    def declaration_services(self):
        """Declare additional services specific to the application"""
        # Import modules to get class references - do this once at startup
        from .configuration_service import ConfigurationService

        # Register core service factories
        def config_factory():
            return ConfigurationService()  # No dependencies

        # Register in dependency order
        self.register_service_factory(ConfigurationService, config_factory)


def get_config() -> Any:
    """Global function to get configuration service"""
    return get_service_container().get_configuration()
