from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import Literal


class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./corner_explorer.db"
    SECRET_KEY: str = "corner-explorer-secret-key-2024"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    STORAGE_TYPE: Literal["local", "s3", "oss"] = "local"
    STORAGE_LOCAL_PATH: str = "uploads"
    STORAGE_BASE_URL: str = "http://localhost:8000/uploads"

    S3_ACCESS_KEY: str = ""
    S3_SECRET_KEY: str = ""
    S3_REGION: str = ""
    S3_BUCKET: str = ""
    S3_ENDPOINT: str = ""

    OSS_ACCESS_KEY: str = ""
    OSS_SECRET_KEY: str = ""
    OSS_REGION: str = ""
    OSS_BUCKET: str = ""
    OSS_ENDPOINT: str = ""

    IMAGE_MAX_SIZE: int = 10 * 1024 * 1024
    IMAGE_ALLOWED_TYPES: list = ["image/jpeg", "image/png", "image/gif", "image/webp", "image/bmp"]
    IMAGE_QUALITY: int = 80
    IMAGE_THUMBNAIL_SIZES: dict = {
        "small": (200, 200),
        "medium": (600, 600),
        "large": (1200, 1200)
    }

    IMAGE_REQUIRE_AUTH: bool = False

    class Config:
        env_file = ".env"


@lru_cache()
def get_settings():
    return Settings()
