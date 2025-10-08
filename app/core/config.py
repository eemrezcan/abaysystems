# app/core/config.py

import os
import json
from typing import List, Optional
from pydantic import BaseSettings, AnyHttpUrl

def parse_cors(value: Optional[str]) -> List[str]:
    """
    .env içindeki CORS değerini hem JSON dizi ('["https://a","https://b"]')
    hem de virgüllü/boşluklu formatlarda ('https://a, https://b' / 'https://a https://b')
    güvenle listeye çevirir.
    """
    if not value:
        return []
    # JSON dizi dene
    try:
        data = json.loads(value)
        if isinstance(data, list):
            return [str(x).strip() for x in data if str(x).strip()]
    except Exception:
        pass
    # CSV / boşluk ayırıcı fallback
    tmp = value.replace(";", ",").replace("\n", " ").strip()
    parts = []
    for chunk in tmp.split(","):
        chunk = chunk.strip()
        if chunk:
            parts.extend(chunk.split())  # boşlukla ayrılmışsa da yakalar
    return [p for p in (s.strip() for s in parts) if p]

class Settings(BaseSettings):
    # --- Auth/Token ---
    SECRET_KEY: str = os.getenv("SECRET_KEY", "CHANGE_ME_TO_A_SECURE_RANDOM_KEY")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 30
    REFRESH_COOKIE_NAME: str = "refresh_token"
    REFRESH_COOKIE_SECURE: bool = False
    REFRESH_COOKIE_SAMESITE: str = "lax"  # Aynı site: Lax iş görür
    REFRESH_COOKIE_DOMAIN: Optional[str] = None

    # --- Medya ---
    # (Varsayılanı koruyoruz)
    class Config:
        env_file = ".env"

    # --- CORS / URL ---
    FRONTEND_URL: Optional[AnyHttpUrl] = None
    BACKEND_CORS_ORIGINS_RAW: Optional[str] = None  # .env’den ham string

    @property
    def BACKEND_CORS_ORIGINS(self) -> List[str]:
        return parse_cors(self.BACKEND_CORS_ORIGINS_RAW)

settings = Settings()

MEDIA_ROOT = os.getenv("MEDIA_ROOT", "media")

