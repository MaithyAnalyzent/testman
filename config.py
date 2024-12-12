from pydantic_settings import BaseSettings
from functools import lru_cache
from typing import List

class Settings(BaseSettings):
    BLUESKY_HANDLE: str
    BLUESKY_PASSWORD: str
    BOT_HANDLE: str
    GROQ_API_KEY: str
    BOT_DID: str | None = None
    twitter_api_key: str
    twitter_api_secret: str
    twitter_access_token: str
    twitter_access_token_secret: str
    twitter_bearer_token: str
    

    class Config:
        env_file = ".env"

def get_settings():
    return Settings()