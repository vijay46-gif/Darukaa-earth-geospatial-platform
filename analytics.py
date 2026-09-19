from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class OverviewMetrics(BaseModel):
    total_projects: int
    total_sites: int
    total_area_hectares: float
    total_carbon_impact_tco2e: float
    average_biodiversity_score: float
    active_projects_count: int
    pending_projects_count: int
    at_risk_sites_count: int


class TimeSeriesPoint(BaseModel):
    date: str
    value: float
    secondary_value: Optional[float] = None
    label: Optional[str] = None


class ChartDataset(BaseModel):
    label: str
    data: List[TimeSeriesPoint]
    color: Optional[str] = None


class CarbonAnalyticsResponse(BaseModel):
    total_carbon_stored: float
    annual_sequestration_rate: float
    trend_percentage: float
    monthly_historical: List[TimeSeriesPoint]
    site_distribution: List[Dict[str, Any]]


class BiodiversityAnalyticsResponse(BaseModel):
    average_score: float
    trend_percentage: float
    monthly_historical: List[TimeSeriesPoint]
    project_scores: List[Dict[str, Any]]


class SiteComparisonItem(BaseModel):
    site_id: int
    site_name: str
    project_name: str
    area: float
    carbon_value: float
    biodiversity_score: float
    status: str


class SiteAnalyticsDetail(BaseModel):
    site_id: int
    site_name: str
    project_name: str
    area: float
    status: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    historical_metrics: List[TimeSeriesPoint]
    vegetation_index: float
    annual_sequestration: float
    is_simulated: bool = False
