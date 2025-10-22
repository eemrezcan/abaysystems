#app/schemas/token.py
from pydantic import BaseModel
from typing import Optional
from datetime import datetime, timedelta

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class TokenData(BaseModel):
    user_id: Optional[str] = None

# ✅ Frontend'in beklediği genişletilmiş yanıt
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    is_admin: bool
    role: str