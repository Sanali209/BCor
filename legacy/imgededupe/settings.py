from pydantic import Field
from pydantic_settings import BaseSettings

class ImgeDeduplicationSettings(BaseSettings):
    db_path: str = Field(default="imgededupe.db")
