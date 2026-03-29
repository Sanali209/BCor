"""
Configuration Service - Single source of truth for all application configuration
Combines constants.py, model_config.py into a unified configuration manager.
"""


from loguru import logger


class ConfigurationService:
    """Centralized configuration management following single source of truth principle"""

    def __init__(self):
        # Core application settings
        logger.info("Configuration Service initialized")