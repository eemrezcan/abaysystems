# app/schemas/user.py

from pydantic import BaseModel
from uuid import UUID
from datetime import datetime

class UserOut(BaseModel):
    id: UUID
    username: str
    role: str
    created_at: datetime

    class Config:
        orm_mode = True
