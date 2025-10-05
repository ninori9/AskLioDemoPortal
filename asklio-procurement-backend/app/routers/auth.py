from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password, require_api_key
from app.db.session import get_db
from app.schemas.auth import LoginRequest, Token

from app.models.user import User  # keep this import path as in your project

router = APIRouter(prefix="/auth", tags=["auth"], dependencies=[Depends(require_api_key)])


@router.post("/login", response_model=Token)
def login(body: LoginRequest, db: Annotated[Session, Depends(get_db)]) -> Token:
    # 1) Find user
    user: User | None = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.hashedPassword):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )

    role_names: list[str] = []
    if getattr(user, "roles", None):
        for r in user.roles:
            if hasattr(r, "role") and getattr(r.role, "name", None):
                role_names.append(r.role.name)
            elif getattr(r, "name", None):
                role_names.append(r.name)

    claims = {
        "username": user.username,
        "given_name": user.firstname, 
        "family_name": user.lastname,
        "roles": role_names,
    }

    expires = settings.ACCESS_TOKEN_EXPIRE_MINUTES
    token = create_access_token(subject=str(user.id), expires_minutes=expires, claims=claims)
    return Token(access_token=token, expires_in=expires)