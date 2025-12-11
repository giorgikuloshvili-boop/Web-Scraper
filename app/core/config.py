from pathlib import Path

from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent

class Settings(BaseSettings):
    HTML_STORAGE_PATH: Path = BASE_DIR / "storage" / "html"
    MARKDOWN_STORAGE_PATH: Path = BASE_DIR / "storage" / "markdown"



settings = Settings()