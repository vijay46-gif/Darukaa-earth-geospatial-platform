from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.session import get_db
from app.models.user import User
from app.schemas.auth import UserResponse

router = APIRouter(prefix="/settings", tags=["Settings"])


class ProfileUpdate(BaseModel):
    name: str


class AppPreferences(BaseModel):
    map_style: str = "satellite-streets-v12"
    notifications_enabled: bool = True
    units: str = "metric"


@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    current_user.name = profile_data.name.strip()
    db.commit()
    db.refresh(current_user)
    return UserResponse.model_validate(current_user)


@router.get("/preferences")
def get_preferences(current_user: User = Depends(get_current_user)):
    return {
        "map_style": "satellite-streets-v12",
        "notifications_enabled": True,
        "units": "metric",
        "theme": "dark-environmental",
    }
