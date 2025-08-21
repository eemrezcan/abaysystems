from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

import os
import sys
import re
from dotenv import load_dotenv
from sqlalchemy.engine import URL

# Proje kökünü PYTHONPATH'e ekle
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# .env dosyasını erkenden yükle
load_dotenv()

from app.core.settings import settings
from app.db.base import Base

# Modeller (autogenerate için)
from app.models.app_user import AppUser
from app.models.customer import Customer
from app.models.profile import Profile
from app.models.glass_type import GlassType
from app.models.other_material import OtherMaterial
from app.models.system import System, SystemVariant
import app.models.system_profile_template
import app.models.system_glass_template
import app.models.system_material_template
from app.models.project import Project, ProjectSystem
from app.models.order import (
    SalesOrder,
    OrderItem,
    OrderItemProfile,
    OrderItemGlass,
    OrderItemMaterial,
    OrderItemExtraMaterial,
)
import app.models.user_token   # ← eklendi


# Alembic Config nesnesi
config = context.config

# Logging yapılandırması
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Autogenerate için metadata
target_metadata = Base.metadata


def _mask_pwd(url: str) -> str:
    """Log/debug için parolayı yıldızlar."""
    try:
        return re.sub(r"(?<=//[^:]+:)[^@]+", "***", url)
    except Exception:
        return url


def get_db_url() -> str:
    """
    Önce .env'den DATABASE_URL'i al, UTF-8 olarak encode edilebiliyorsa onu kullan.
    Değilse POSTGRES_* değişkenlerinden güvenli bir URL yarat (URL.create).
    """
    # 1) .env içindeki DATABASE_URL'i dene
    env_url = os.getenv("DATABASE_URL")
    if env_url:
        try:
            env_url.encode("utf-8")  # UTF-8 kontrolü
            return env_url
        except UnicodeEncodeError:
            # Gizli/Türkçe karakter karışmış; fallback'e geç
            pass

    # 2) Fallback: POSTGRES_* değişkenlerinden güvenli URL oluştur
    user = os.getenv("POSTGRES_USER", "abaysystems_user")
    password = os.getenv("POSTGRES_PASSWORD", "")
    host = os.getenv("POSTGRES_SERVER", "127.0.0.1")
    port = int(os.getenv("POSTGRES_PORT", "5432"))
    database = os.getenv("POSTGRES_DB", "abaysystems_db")

    # URL.create özel karakterleri güvenli biçimde kaçışlar
    url_obj = URL.create(
        "postgresql+psycopg2",
        username=user,
        password=password,
        host=host,
        port=port,
        database=database,
    )
    return str(url_obj)


def run_migrations_offline() -> None:
    """'Offline' modda migration çalıştırır."""
    db_url = get_db_url()
    # print(f"[alembic] offline db_url = { _mask_pwd(db_url) }")  # gerekirse aç

    config.set_main_option("sqlalchemy.url", db_url)
    context.configure(
        url=db_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """'Online' modda migration çalıştırır."""
    db_url = get_db_url()
    # print(f"[alembic] online db_url = { _mask_pwd(db_url) }")  # gerekirse aç

    config.set_main_option("sqlalchemy.url", db_url)

    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
