# app/core/settings.py
from pydantic import BaseSettings, AnyUrl, EmailStr

class Settings(BaseSettings):
    database_url: AnyUrl
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""                 # yerelde boş kalsın → login yapılmaz
    SMTP_PASSWORD: str = ""
    SMTP_FROM: EmailStr = "no-reply@example.com"

    SMTP_USE_SSL: bool = False          # 465 ise True
    SMTP_STARTTLS: bool = False         # 587 ise True

    FRONTEND_URL: AnyUrl = "http://localhost:5173"
    
    DEBUG: bool = False
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
