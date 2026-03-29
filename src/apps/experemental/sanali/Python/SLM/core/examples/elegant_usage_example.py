"""
Elegant Usage Example - SLM Framework 2.0
Demonstrates pythonic patterns, decorators, and singleton access
"""

from SLM.core import (
    config, bus, dependencies, components, plugins, Core,
    component, service, inject, auto_inject, subscribe,
    on_app_start, on_app_stop, on_config_change,
    Component, Config, MessageBus
)
from loguru import logger


# =============================================================================
# PATTERN 1: Module-level Singleton Access
# =============================================================================

def example_module_level_access():
    """Elegant module-level singleton access"""
    print("\n=== Pattern 1: Module-level Access ===")
    
    # Direct access to singletons
    config.database.host = "localhost"
    config.database.port = 5432
    
    print(f"Database host: {config.database.host}")
    print(f"Database port: {config.database.port}")
    
    # Publish events
    bus.publish("app.started", message="Application is running")
    
    # All are singletons - same instance everywhere
    config2 = Config()
    print(f"Same config instance: {config is config2}")  # True


# =============================================================================
# PATTERN 2: Core Class Access
# =============================================================================

def example_core_class_access():
    """Using the Core class for elegant property access"""
    print("\n=== Pattern 2: Core Class Access ===")
    
    # Alternative elegant access via Core
    Core.config.app.name = "MyApp"
    Core.config.app.version = "1.0.0"
    
    print(f"App name: {Core.config.app.name}")
    print(f"App version: {Core.config.app.version}")
    
    # Publish via Core
    Core.bus.publish("config.updated", section="app")


# =============================================================================
# PATTERN 3: Component Decorator
# =============================================================================

@component(name="DatabaseService")
class DatabaseService(Component):
    """Example component using decorator"""
    
    # Type hints for dependency injection
    config: Config
    message_bus: MessageBus
    
    def on_initialize(self):
        logger.info(f"Database connecting to {self.config.database.host}:{self.config.database.port}")
    
    def on_start(self):
        logger.info("Database service started")
    
    def on_stop(self):
        logger.info("Database service stopped")


@component(name="CacheService")
class CacheService(Component):
    """Another example component"""
    
    config: Config
    
    def on_initialize(self):
        logger.info("Cache service initialized")
    
    def get_cached(self, key: str) -> str:
        return f"cached_value_for_{key}"


# =============================================================================
# PATTERN 4: Service Decorator
# =============================================================================

@service(singleton=True, name="AuthService")
class AuthService:
    """Example service with dependency injection"""
    
    config: Config
    message_bus: MessageBus
    
    def __init__(self):
        self.users = {}
    
    def login(self, username: str, password: str) -> bool:
        logger.info(f"Login attempt for {username}")
        # Simulate login logic
        return True


# =============================================================================
# PATTERN 5: Inject Decorator
# =============================================================================

@inject(config=Config, bus=MessageBus)
def process_data(data: str, config, bus):
    """Function with dependency injection"""
    logger.info(f"Processing data with config: {config}")
    bus.publish("data.processed", data=data)
    return f"Processed: {data}"


@auto_inject
def auto_process(data: str, config: Config, bus: MessageBus):
    """Automatic injection based on type hints"""
    logger.info(f"Auto-injecting config and bus")
    bus.publish("auto.processed", data=data)
    return f"Auto-processed: {data}"


# =============================================================================
# PATTERN 6: Event Subscription Decorators
# =============================================================================

@subscribe("app.started", "config.updated")
def on_app_events(event_type: str, **data):
    """Subscribe to multiple events"""
    logger.info(f"Event received: {event_type} with data: {data}")


@on_config_change("database.host")
def on_database_host_changed(old_value, new_value):
    """React to specific config changes"""
    logger.info(f"Database host changed from {old_value} to {new_value}")


# =============================================================================
# PATTERN 7: Lifecycle Hooks
# =============================================================================

@on_app_start
def initialize_resources():
    """Called on app start"""
    logger.info("Initializing resources...")
    config.resources.initialized = True


@on_app_stop
def cleanup_resources():
    """Called on app stop"""
    logger.info("Cleaning up resources...")
    config.resources.initialized = False


# =============================================================================
# PATTERN 8: Manual Component Registration
# =============================================================================

def example_manual_registration():
    """Manual component registration"""
    print("\n=== Pattern 8: Manual Registration ===")
    
    # Create and register components
    db_service = DatabaseService()
    cache_service = CacheService()
    
    # Register with dependency manager
    dependencies.register_singleton(DatabaseService, db_service)
    dependencies.register_singleton(CacheService, cache_service)
    dependencies.register_singleton(Config, config)
    dependencies.register_singleton(MessageBus, bus)
    
    # Setup dependencies (inject and initialize)
    dependencies.setup_dependencies()
    
    # Register with component manager
    components.register_component("db", db_service)
    components.register_component("cache", cache_service)
    
    # Start components
    components.start_all()
    
    print(f"Component count: {components.get_component_count()}")
    print(f"Components: {components.get_component_names()}")


# =============================================================================
# PATTERN 9: Configuration Patterns
# =============================================================================

def example_config_patterns():
    """Various configuration access patterns"""
    print("\n=== Pattern 9: Configuration Patterns ===")
    
    # Nested attribute access
    config.app.database.host = "localhost"
    config.app.database.port = 5432
    config.app.features.caching = True
    
    # Dictionary-style access
    config["api"] = {"key": "secret", "timeout": 30}
    
    # Dot-separated key access
    api_key = config.get("api.key")
    print(f"API Key: {api_key}")
    
    # Update with dict
    config.update({
        "logging": {
            "level": "INFO",
            "format": "json"
        }
    })
    
    # Convert to dict
    config_dict = config.to_dict()
    print(f"Config as dict keys: {list(config_dict.keys())}")


# =============================================================================
# PATTERN 10: Message Bus Patterns
# =============================================================================

def example_message_bus_patterns():
    """Message bus usage patterns"""
    print("\n=== Pattern 10: Message Bus Patterns ===")
    
    # Simple publish
    bus.publish("user.created", user_id=123, username="john")
    
    # Subscribe manually
    def on_user_created(event_type: str, **data):
        print(f"User created: {data}")
    
    bus.subscribe("user.created", on_user_created)
    
    # Publish again
    bus.publish("user.created", user_id=456, username="jane")
    
    # Unsubscribe
    bus.unsubscribe("user.created", on_user_created)
    
    # Check subscribers
    count = bus.get_subscriber_count("user.created")
    print(f"Subscribers for 'user.created': {count}")


# =============================================================================
# Main Demonstration
# =============================================================================

def main():
    """Run all examples"""
    print("="*80)
    print("SLM Framework 2.0 - Elegant Pythonic Patterns")
    print("="*80)
    
    # Pattern examples
    example_module_level_access()
    example_core_class_access()
    example_manual_registration()
    example_config_patterns()
    example_message_bus_patterns()
    
    # Test dependency injection
    print("\n=== Dependency Injection Demo ===")
    result1 = process_data("test_data")
    print(f"Result: {result1}")
    
    result2 = auto_process("auto_data")
    print(f"Result: {result2}")
    
    # Test config change events
    print("\n=== Config Change Events ===")
    config.message_bus = bus  # Connect message bus
    config.database.host = "new_host"  # Triggers event
    
    print("\n=== Complete ===")
    print("All patterns demonstrated successfully!")


if __name__ == "__main__":
    main()
