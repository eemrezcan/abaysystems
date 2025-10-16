# app/schemas/project_code_rule.py
from pydantic import BaseModel, Field
from typing import Optional
from uuid import UUID
from datetime import datetime

class ProjectCodeRuleBase(BaseModel):
    prefix: str = Field(
        ...,
        min_length=2,
        max_length=32,
        regex=r"^[A-Z0-9]+$",
        description="Prefix; yalnızca A-Z ve 0-9 (global unique değil)."
    )
    separator: str = Field(
        "-",
        min_length=1,
        max_length=5,
        description="Kod ayırıcısı (örn. '-')."
    )
    # ⛔ padding kaldırıldı
    start_number: int = Field(
        1,
        ge=0,
        description="İlk verilecek sayı (alt sınır mantığı)."
    )

class ProjectCodeRuleCreate(ProjectCodeRuleBase):
    pass

class ProjectCodeRuleUpdate(BaseModel):
    prefix: Optional[str] = Field(
        None,
        min_length=2,
        max_length=32,
        regex=r"^[A-Z0-9]+$",
        description="Yeni prefix (opsiyonel)."
    )
    separator: Optional[str] = Field(
        None,
        min_length=1,
        max_length=5,
        description="Yeni ayırıcı (opsiyonel)."
    )
    # ⛔ padding kaldırıldı
    start_number: Optional[int] = Field(
        None,
        ge=0,
        description="Yeni başlangıç sayısı (opsiyonel; alt sınır)."
    )

class ProjectCodeRuleOut(ProjectCodeRuleBase):
    id: UUID = Field(...)
    owner_id: UUID = Field(...)
    current_number: int = Field(..., ge=0, description="Son verilen sayı.")
    is_active: bool = Field(..., description="Kural aktif mi?")
    created_at: datetime = Field(...)
    updated_at: datetime = Field(...)

    class Config:
        orm_mode = True

class NextProjectCodeOut(BaseModel):
    next_number: int = Field(..., ge=0, description="Bir sonraki verilecek sayı.")
    # Artık padding yok; kod basitçe prefix + separator + number
    next_code: str = Field(..., description="Örn: BALU-10")
