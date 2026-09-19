import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class GeoJSONPolygon(BaseModel):
    type: str = "Polygon"
    coordinates: List[List[List[float]]]


class SiteBase(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    description: Optional[str] = None
    status: str = Field("Active", pattern="^(Active|Pending|Completed|At Risk)$")


class SiteCreate(SiteBase):
    project_id: int
    geometry: Optional[Dict[str, Any]] = None  # GeoJSON dict
    area: Optional[float] = None  # in hectares (if provided, or calculated backend)
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class SiteUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(Active|Pending|Completed|At Risk)$")
    geometry: Optional[Dict[str, Any]] = None
    area: Optional[float] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None


class EnvironmentalMetricSummary(BaseModel):
    id: int
    metric_date: datetime.datetime
    carbon_value: float
    biodiversity_score: float
    vegetation_value: float
    carbon_sequestration: float

    class Config:
        from_attributes = True


class SiteResponse(BaseModel):
    id: int
    project_id: int
    project_name: Optional[str] = None
    name: str
    description: Optional[str] = None
    area: float
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    geometry: Optional[Dict[str, Any]] = None
    created_at: datetime.datetime
    updated_at: datetime.datetime

    # Latest metric aggregates
    latest_carbon: Optional[float] = 0.0
    latest_biodiversity: Optional[float] = 0.0
    latest_vegetation: Optional[float] = 0.0
    latest_sequestration: Optional[float] = 0.0

    class Config:
        from_attributes = True


class SiteDetailResponse(SiteResponse):
    metrics: List[EnvironmentalMetricSummary] = []
