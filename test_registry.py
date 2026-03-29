from src.modules.assets.infrastructure.providers import AssetsInfrastructureProvider
registry = AssetsInfrastructureProvider().provide_handler_registry()
print("Registry resolving image/webp with handler_name=ContentHashHandler:")
print(registry.resolve("image/webp", handler_name="ContentHashHandler"))
