# app/utils/ownership.py
from fastapi import HTTPException, status

def ensure_owner_or_404(obj, current_user_id, owner_field: str):
    if not obj:
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Kayıt bulunamadı")
    # varsa soft-delete’i kontrol et (Customer’da var, Project’te yok)
    if getattr(obj, "is_deleted", False):
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Kayıt bulunamadı")
    owner_id = getattr(obj, owner_field)
    if owner_id != current_user_id:
        # başka tenant’ın kaydını ifşa etmemek için 404
        raise HTTPException(status.HTTP_404_NOT_FOUND, detail="Kayıt bulunamadı")
    return obj
