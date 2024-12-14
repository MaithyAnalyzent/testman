from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List, Optional

class Settings(BaseSettings):
    BLUESKY_HANDLE: str
    BLUESKY_PASSWORD: str
    BOT_HANDLE: str
    GROQ_API_KEY: str
    BOT_DID: Optional[str] = None
    emailAuthFactor: Optional[str] = None
    active: Optional[bool] = None

    class Config:
        env_file = ".env"

def get_settings():
    return Settings()
