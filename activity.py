import datetime
from typing import Optional

from pydantic import BaseModel


class ActivityLogCreate(BaseModel):
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[str] = None


class ActivityLogResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    user_name: Optional[str] = "System"
    action: str
    entity_type: str
    entity_id: Optional[int] = None
    details: Optional[str] = None
    timestamp: datetime.datetime

    class Config:
        from_attributes = True
