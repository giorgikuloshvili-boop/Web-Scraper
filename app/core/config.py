from pathlib import Path
from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict

# BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    BASE_DIR: Path = Path(__file__).resolve().parent.parent.parent
    APP_NAME: str = "FastAPI Web Scraper"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    API_V1_STR: str = "/api/v1"

    SCRAPE_SCHEDULE_TIME: str = "12:00"
    TIMEZONE: str = "UTC+4"

    TARGET_URL: str = "https://www.example.com/"
    MAX_CRAWL_DEPTH: int = 3
    REQUEST_TIMEOUT: int = 30
    MAX_CONCURRENT_REQUESTS: int = 5
    RETRY_ATTEMPTS: int = 3

    HTML_STORAGE_PATH: Path = BASE_DIR / "storage" / "html"
    MARKDOWN_STORAGE_PATH: Path = BASE_DIR / "storage" / "markdown"

    LOG_LEVEL: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    LOG_FILE: Path = BASE_DIR / "logs" / "scraper.log"

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )

    def create_dirs(self) -> None:
        """Ensure necessary directories exist on startup."""
        self.HTML_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        self.MARKDOWN_STORAGE_PATH.mkdir(parents=True, exist_ok=True)
        self.LOG_FILE.parent.mkdir(parents=True, exist_ok=True)


# Singleton instance
settings = Settings()

# Auto-create directories when this module is imported/initialized
settings.create_dirs()