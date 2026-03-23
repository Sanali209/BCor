from pydantic_settings import BaseSettings

class BoruScraperSettings(BaseSettings):
    save_path: str = "downloads"
    deduplication_threshold: int = 10
    db_path: str = "data.db"
