from pydantic_settings import BaseSettings
from pathlib import Path


class Settings(BaseSettings):
    database_url: str = "sqlite+aiosqlite:///./data/tunechain.db"
    download_dir: Path = Path("./downloads")
    max_concurrent_downloads: int = 3
    host: str = "0.0.0.0"
    port: int = 8000

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


settings = Settings()
settings.download_dir.mkdir(parents=True, exist_ok=True)
