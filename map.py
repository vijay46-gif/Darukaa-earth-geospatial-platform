from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.database.session import get_db
from app.models.environmental_metric import EnvironmentalMetric
from app.models.project import Project
from app.models.site import Site

router = APIRouter(prefix="/map", tags=["Geospatial Map"])


@router.get("/sites")
def get_map_sites(
    project_id: Optional[int] = None,
    project_type: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    """
    Returns a GeoJSON FeatureCollection of site polygon boundaries
    with rich metadata properties for Mapbox GL JS layers.
    """
    query = db.query(Site).join(Project, Site.project_id == Project.id)

    if project_id:
        query = query.filter(Site.project_id == project_id)
    if project_type:
        query = query.filter(Project.project_type == project_type)
    if status_filter:
        query = query.filter(Site.status == status_filter)
    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(or_(Site.name.ilike(pattern), Project.name.ilike(pattern)))

    sites = query.all()
    features = []

    for site in sites:
        geom = site.get_geojson()
        if not geom:
            continue

        project = site.project
        latest_metric = (
            db.query(EnvironmentalMetric)
            .filter(EnvironmentalMetric.site_id == site.id)
            .order_by(EnvironmentalMetric.metric_date.desc())
            .first()
        )

        features.append(
            {
                "type": "Feature",
                "id": site.id,
                "geometry": geom,
                "properties": {
                    "site_id": site.id,
                    "site_name": site.name,
                    "project_id": project.id if project else None,
                    "project_name": project.name if project else "Unassigned",
                    "project_type": project.project_type if project else "General",
                    "status": site.status,
                    "area": site.area,
                    "latitude": site.latitude,
                    "longitude": site.longitude,
                    "carbon_impact": round(latest_metric.carbon_value, 1) if latest_metric else 0.0,
                    "biodiversity_score": (
                        round(latest_metric.biodiversity_score, 1) if latest_metric else 0.0
                    ),
                    "vegetation_value": (
                        round(latest_metric.vegetation_value, 2) if latest_metric else 0.0
                    ),
                    "carbon_sequestration": (
                        round(latest_metric.carbon_sequestration, 2) if latest_metric else 0.0
                    ),
                    "created_date": site.created_at.strftime("%Y-%m-%d"),
                },
            }
        )

    return {"type": "FeatureCollection", "features": features}
