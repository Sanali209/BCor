from typing import Optional
from pydantic_settings import BaseSettings

class VfsSettings(BaseSettings):
    """Configuration for the Virtual File System module.
    
    Attributes:
        url: The FS URL (e.g., 'osfs://./data', 's3://bucket'). 
             If None, defaults to 'mem://' in tests or local temp in prod.
    """
    url: Optional[str] = None
