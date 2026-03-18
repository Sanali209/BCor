from pydantic_settings import BaseSettings

class HelloAppSettings(BaseSettings):
    """Global configuration settings for the 'Hello BCor' application.

    Attributes:
        app_name: The display name of the application.
        log_level: Desired logging verbosity (e.g., 'DEBUG', 'INFO').
    """
    app_name: str = "DefaultApp"
    log_level: str = "INFO"
