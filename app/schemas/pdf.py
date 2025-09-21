# app/schemas/pdf.py
from pydantic import BaseModel, Field, AnyHttpUrl
from typing import Optional, Union
from uuid import UUID
from datetime import datetime
from typing import Any, Dict

# -------- Titles --------
class PdfTitleTemplateBase(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    config_json: Dict[str, Any]

class PdfTitleTemplateCreate(PdfTitleTemplateBase):
    pass

class PdfTitleTemplateUpdate(BaseModel):
    key: Optional[str] = Field(None, min_length=1, max_length=100)
    config_json: Optional[Dict[str, Any]]

class PdfTitleTemplateOut(PdfTitleTemplateBase):
    id: UUID
    created_at: datetime
    updated_at: datetime
    class Config:
        orm_mode = True


# -------- Brands --------
class PdfBrandBase(BaseModel):
    key: str = Field(..., min_length=1, max_length=100)
    config_json: Dict[str, Any]

class PdfBrandCreate(PdfBrandBase):
    pass

class PdfBrandUpdate(BaseModel):
    key: Optional[str] = Field(None, min_length=1, max_length=100)
    config_json: Optional[Dict[str, Any]]

class PdfBrandOut(PdfBrandBase):
    id: UUID
    logo_url: Optional[Union[AnyHttpUrl, str]] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        orm_mode = True

# -------- Brand Logo --------
class PdfBrandLogoOut(BaseModel):
    brand_id: UUID
    logo_url: Optional[Union[AnyHttpUrl, str]] = None
