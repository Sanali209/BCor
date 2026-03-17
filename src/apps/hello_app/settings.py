from pydantic_settings import BaseSettings

class HelloAppSettings(BaseSettings):
    """Global settings for the Hello App (e.g., logging)."""
    app_name: str = "DefaultApp"
    log_level: str = "INFO"
