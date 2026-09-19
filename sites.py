import datetime
import json
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth.security import get_current_user
from app.database.session import get_db
from app.models.environmental_metric import EnvironmentalMetric
from app.models.project import Project
from app.models.site import Site
from app.models.user import User
from app.schemas.analytics import SiteAnalyticsDetail, TimeSeriesPoint
from app.schemas.site import (
    EnvironmentalMetricSummary,
    SiteCreate,
    SiteDetailResponse,
    SiteResponse,
    SiteUpdate,
)
from app.services.activity_service import log_activity
from app.services.geospatial import GeospatialService

router = APIRouter(prefix="/sites", tags=["Sites"])


def build_site_response(site: Site, db: Session) -> SiteResponse:
    project = db.query(Project).filter(Project.id == site.project_id).first()
    latest_metric = (
        db.query(EnvironmentalMetric)
        .filter(EnvironmentalMetric.site_id == site.id)
        .order_by(EnvironmentalMetric.metric_date.desc())
        .first()
    )

    return SiteResponse(
        id=site.id,
        project_id=site.project_id,
        project_name=project.name if project else "Unassigned",
        name=site.name,
        description=site.description,
        area=site.area,
        status=site.status,
        latitude=site.latitude,
        longitude=site.longitude,
        geometry=site.get_geojson(),
        created_at=site.created_at,
        updated_at=site.updated_at,
        latest_carbon=round(latest_metric.carbon_value, 2) if latest_metric else 0.0,
        latest_biodiversity=round(latest_metric.biodiversity_score, 1) if latest_metric else 0.0,
        latest_vegetation=round(latest_metric.vegetation_value, 3) if latest_metric else 0.0,
        latest_sequestration=round(latest_metric.carbon_sequestration, 2) if latest_metric else 0.0,
    )


@router.get("", response_model=List[SiteResponse])
def list_sites(
    project_id: Optional[int] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    search: Optional[str] = None,
    db: Session = Depends(get_db),
):
    query = db.query(Site)

    if project_id:
        query = query.filter(Site.project_id == project_id)

    if status_filter:
        query = query.filter(Site.status == status_filter)

    if search:
        pattern = f"%{search.strip()}%"
        query = query.filter(or_(Site.name.ilike(pattern), Site.description.ilike(pattern)))

    sites = query.order_by(Site.created_at.desc()).all()
    return [build_site_response(s, db) for s in sites]


@router.post("", response_model=SiteResponse, status_code=status.HTTP_201_CREATED)
def create_site(
    site_in: SiteCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    # Verify project exists
    project = db.query(Project).filter(Project.id == site_in.project_id).first()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Parent project with ID {site_in.project_id} not found.",
        )

    geometry_wkt = None
    geojson_str = None
    area_ha = site_in.area or 0.0
    lat = site_in.latitude
    lng = site_in.longitude

    if site_in.geometry:
        try:
            poly, calculated_ha, c_lat, c_lng = GeospatialService.validate_and_parse_geojson(
                site_in.geometry
            )
            geometry_wkt = GeospatialService.prepare_postgis_geometry(poly)
            geojson_str = json.dumps(site_in.geometry)
            area_ha = calculated_ha
            lat = c_lat
            lng = c_lng
        except ValueError as val_err:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Invalid polygon geometry: {str(val_err)}",
            )

    site = Site(
        project_id=site_in.project_id,
        name=site_in.name.strip(),
        description=site_in.description,
        area=area_ha,
        status=site_in.status,
        geometry=geometry_wkt,
        geojson_data=geojson_str,
        latitude=lat,
        longitude=lng,
    )
    db.add(site)
    db.commit()
    db.refresh(site)

    # Initialize historical baseline metrics for newly created site based on area
    base_carbon = round(area_ha * 12.5, 2)
    base_bio = 78.5
    now = datetime.datetime.utcnow()

    for i in range(6, -1, -1):
        m_date = now - datetime.timedelta(days=i * 30)
        carbon_factor = 1.0 - (i * 0.04)
        bio_factor = 1.0 - (i * 0.02)
        metric = EnvironmentalMetric(
            site_id=site.id,
            metric_date=m_date,
            carbon_value=round(base_carbon * carbon_factor, 2),
            biodiversity_score=min(100.0, round(base_bio * bio_factor, 1)),
            vegetation_value=round(0.72 + (0.02 * (6 - i)), 3),
            carbon_sequestration=round(4.8 + (0.15 * (6 - i)), 2),
        )
        db.add(metric)
    db.commit()

    log_activity(
        db=db,
        action="Site Added",
        entity_type="Site",
        entity_id=site.id,
        user_id=current_user.id,
        details=f"Site '{site.name}' ({site.area} ha) added to project '{project.name}'",
    )

    return build_site_response(site, db)


@router.get("/{site_id}", response_model=SiteDetailResponse)
def get_site(site_id: int, db: Session = Depends(get_db)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    base_resp = build_site_response(site, db)
    metrics = (
        db.query(EnvironmentalMetric)
        .filter(EnvironmentalMetric.site_id == site.id)
        .order_by(EnvironmentalMetric.metric_date.asc())
        .all()
    )

    return SiteDetailResponse(
        **base_resp.model_dump(),
        metrics=[EnvironmentalMetricSummary.model_validate(m) for m in metrics],
    )


@router.put("/{site_id}", response_model=SiteResponse)
def update_site(
    site_id: int,
    site_update: SiteUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    update_dict = site_update.model_dump(exclude_unset=True)

    if "geometry" in update_dict and update_dict["geometry"]:
        try:
            poly, calculated_ha, c_lat, c_lng = GeospatialService.validate_and_parse_geojson(
                update_dict["geometry"]
            )
            site.geometry = GeospatialService.prepare_postgis_geometry(poly)
            site.geojson_data = json.dumps(update_dict["geometry"])
            site.area = calculated_ha
            site.latitude = c_lat
            site.longitude = c_lng
        except ValueError as val_err:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(val_err)
            )
        del update_dict["geometry"]

    for key, val in update_dict.items():
        if val is not None:
            setattr(site, key, val)

    db.commit()
    db.refresh(site)

    log_activity(
        db=db,
        action="Site Updated",
        entity_type="Site",
        entity_id=site.id,
        user_id=current_user.id,
        details=f"Site '{site.name}' attributes updated",
    )

    return build_site_response(site, db)


@router.delete("/{site_id}", status_code=status.HTTP_200_OK)
def delete_site(
    site_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    name = site.name
    db.delete(site)
    db.commit()

    log_activity(
        db=db,
        action="Site Deleted",
        entity_type="Site",
        entity_id=site_id,
        user_id=current_user.id,
        details=f"Site '{name}' (ID: {site_id}) was deleted",
    )

    return {"message": f"Site '{name}' deleted successfully", "id": site_id}


@router.get("/{site_id}/analytics", response_model=SiteAnalyticsDetail)
def get_site_analytics(site_id: int, db: Session = Depends(get_db)):
    site = db.query(Site).filter(Site.id == site_id).first()
    if not site:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Site not found")

    project = db.query(Project).filter(Project.id == site.project_id).first()
    metrics = (
        db.query(EnvironmentalMetric)
        .filter(EnvironmentalMetric.site_id == site.id)
        .order_by(EnvironmentalMetric.metric_date.asc())
        .all()
    )

    pts = [
        TimeSeriesPoint(
            date=m.metric_date.strftime("%b %Y"),
            value=m.carbon_value,
            secondary_value=m.biodiversity_score,
            label=f"{m.metric_date.strftime('%B %Y')}: {m.carbon_value:,.0f} tCO2e",
        )
        for m in metrics
    ]

    latest = metrics[-1] if metrics else None
    veg_index = latest.vegetation_value if latest else 0.75
    annual_seq = latest.carbon_sequestration if latest else 5.2

    return SiteAnalyticsDetail(
        site_id=site.id,
        site_name=site.name,
        project_name=project.name if project else "Unassigned",
        area=site.area,
        status=site.status,
        latitude=site.latitude,
        longitude=site.longitude,
        historical_metrics=pts,
        vegetation_index=veg_index,
        annual_sequestration=annual_seq,
        is_simulated=True,
    )
