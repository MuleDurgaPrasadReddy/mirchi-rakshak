from typing import Generator, Optional
from fastapi import Depends, Header, HTTPException, status
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.core.security import decode_jwt_token, get_user_id_from_payload
from app.config import settings


def get_current_user_id(authorization: Optional[str] = Header(None)) -> str:
    """
    FastAPI dependency that extracts and validates the user_id from Bearer header.
    In development mode without authorization header, defaults to a test user ID.
    """
    if not authorization:
        if settings.ENVIRONMENT == "development":
            return "00000000-0000-0000-0000-000000000001"
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header missing",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header format. Expected 'Bearer <token>'",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = parts[1]
    payload = decode_jwt_token(token)
    return get_user_id_from_payload(payload)
