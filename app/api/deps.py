from fastapi import Depends, HTTPException, status
from app.models.app_user import AppUser
from app.core.security import get_current_user, oauth2_scheme

def get_current_admin(current_user: AppUser = Depends(get_current_user)):
    if current_user.role != "admin":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Sadece admin erişebilir")
    return current_user

def get_current_dealer(current_user: AppUser = Depends(get_current_user)):
    if current_user.role not in ("dealer", "admin"):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Yetkiniz yok")
    return current_user
