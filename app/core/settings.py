# app/core/settings.py
from pydantic import BaseSettings, AnyUrl

class Settings(BaseSettings):
    database_url: AnyUrl

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
