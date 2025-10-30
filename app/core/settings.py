from pydantic import BaseSettings, AnyUrl, EmailStr, Field

class Settings(BaseSettings):
    # ---- Brand / App ----
    BRAND_NAME: str = Field("Tümen Alüminyum", env="BRAND_NAME")

    # ---- Database ----
    database_url: AnyUrl  # ör: postgresql+psycopg2://user:pass@host:5432/dbname

    # ---- SMTP ----
    SMTP_HOST: str = "localhost"
    SMTP_PORT: int = 1025
    SMTP_USER: str = ""                 # yerelde boş kalsın → login yapılmaz
    SMTP_PASSWORD: str = ""
    SMTP_FROM: EmailStr = "no-reply@example.com"

    SMTP_USE_SSL: bool = False          # 465 ise True
    SMTP_STARTTLS: bool = False         # 587 ise True

    # ---- URLs ----
    FRONTEND_URL: AnyUrl = "http://localhost:5173"

    # ---- Auth / Security ----
    DEBUG: bool = False
    access_token_expire_minutes: int = Field(30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(30, env="REFRESH_TOKEN_EXPIRE_DAYS")
    refresh_cookie_name: str = Field("refresh_token", env="REFRESH_COOKIE_NAME")
    refresh_cookie_secure: bool = Field(False, env="REFRESH_COOKIE_SECURE")
    refresh_cookie_samesite: str = Field("lax", env="REFRESH_COOKIE_SAMESITE")  # "lax" | "strict" | "none"
    refresh_cookie_domain: str | None = Field(None, env="REFRESH_COOKIE_DOMAIN")

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
