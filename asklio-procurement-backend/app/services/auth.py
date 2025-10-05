from fastapi import HTTPException, status
from app.models.user import User

def is_manager(user: User) -> bool:
    for ur in (user.roles or []):
        role = getattr(ur, "role", None)
        if role and getattr(role, "name", None) == "Manager":
            return True
    return False

def ensure_manager(user: User) -> None:
    if not is_manager(user):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Managers only")