from datetime import datetime
from typing import Optional, Literal
from pydantic import BaseModel, ConfigDict

AppLanguage = Literal["en", "hi", "te"]


class ProfileBase(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    language: AppLanguage = "en"
    district: Optional[str] = None
    village: Optional[str] = None
    onboarded: bool = False


class ProfileCreate(ProfileBase):
    id: str


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None
    phone: Optional[str] = None
    avatar_url: Optional[str] = None
    language: Optional[AppLanguage] = None
    district: Optional[str] = None
    village: Optional[str] = None
    onboarded: Optional[bool] = None


class ProfileResponse(ProfileBase):
    id: str
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
