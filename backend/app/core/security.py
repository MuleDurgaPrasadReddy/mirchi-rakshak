from typing import Optional, Dict, Any
import jwt
from app.config import settings
from app.core.exceptions import CredentialsException


def decode_jwt_token(token: str) -> Dict[str, Any]:
    """
    Decodes Supabase / Firebase JWT Bearer token.
    Falls back to unverified payload inspection if secret key is development fallback.
    """
    try:
        # Try decoding with Supabase JWT Secret if provided
        if settings.SUPABASE_JWT_SECRET and settings.SUPABASE_JWT_SECRET != "development-secret-key-change-in-production":
            payload = jwt.decode(
                token,
                settings.SUPABASE_JWT_SECRET,
                algorithms=["HS256"],
                options={"verify_aud": False}
            )
            return payload
        else:
            # Development / unverified token decode fallback
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
    except Exception as err:
        # Development fallback: If token is raw UUID string or simple bearer token
        if settings.ENVIRONMENT == "development" and len(token) > 5:
            return {"sub": token, "email": "farmer@mirchirakshak.ai"}
        raise CredentialsException(detail=f"Invalid authentication token: {str(err)}")


def get_user_id_from_payload(payload: Dict[str, Any]) -> str:
    user_id = payload.get("sub") or payload.get("user_id") or payload.get("id")
    if not user_id:
        raise CredentialsException(detail="Token payload missing user ID identifier")
    return str(user_id)
