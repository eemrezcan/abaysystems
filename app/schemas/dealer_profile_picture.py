# app/schemas/dealer_profile_picture.py
from pydantic import BaseModel, AnyHttpUrl
from uuid import UUID
from datetime import datetime
from typing import Union

class DealerProfilePictureOut(BaseModel):
    id: UUID
    user_id: UUID
    image_url: Union[AnyHttpUrl, str]
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
