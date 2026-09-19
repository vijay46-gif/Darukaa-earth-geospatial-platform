import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from app.schemas.site import SiteResponse


class SiteInlineCreate(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    status: str = Field("Active", pattern="^(Active|Pending|Completed|At Risk)$")
    geometry: Optional[Dict[str, Any]] = None
    area: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class ProjectBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    project_type: str = Field(..., pattern="^(Carbon|Biodiversity|Carbon \\+ Biodiversity)$")
    start_date: Optional[datetime.datetime] = None
    end_date: Optional[datetime.datetime] = None
    status: str = Field("Active", pattern="^(Active|Pending|Completed|At Risk)$")


class ProjectCreate(ProjectBase):
    sites: Optional[List[SiteInlineCreate]] = []


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    project_type: Optional[str] = Field(
        None, pattern="^(Carbon|Biodiversity|Carbon \\+ Biodiversity)$"
    )
    start_date: Optional[datetime.datetime] = None
    end_date: Optional[datetime.datetime] = None
    status: Optional[str] = Field(None, pattern="^(Active|Pending|Completed|At Risk)$")


class ProjectResponse(ProjectBase):
    id: int
    created_by: Optional[int] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    # Aggregated KPI summaries
    sites_count: int = 0
    total_area: float = 0.0  # hectares
    total_carbon: float = 0.0  # tCO2e
    avg_biodiversity: float = 0.0  # 0 - 100
    location_summary: Optional[str] = "Global"

    class Config:
        from_attributes = True


class ProjectDetailResponse(ProjectResponse):
    sites: List[SiteResponse] = []
