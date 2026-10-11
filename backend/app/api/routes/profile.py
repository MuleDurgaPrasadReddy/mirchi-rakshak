from typing import Dict
from fastapi import APIRouter, Depends
from app.dependencies import get_current_user_id
from app.schemas.profile import ProfileResponse, ProfileUpdate

router = APIRouter(prefix="/profile", tags=["profile"])


@router.get("", response_model=Dict[str, str])
async def get_profile(user_id: str = Depends(get_current_user_id)):
    """
    Placeholder endpoint to get current farmer profile.
    """
    return {
        "id": user_id,
        "message": "Profile endpoint scaffolded",
    }


@router.put("", response_model=Dict[str, str])
async def update_profile(profile: ProfileUpdate, user_id: str = Depends(get_current_user_id)):
    """
    Placeholder endpoint to update farmer profile & language.
    """
    return {
        "id": user_id,
        "message": "Profile update endpoint scaffolded",
    }
