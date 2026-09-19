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
from app.schemas.project import ProjectCreate, ProjectDetailResponse, ProjectResponse, ProjectUpdate
from app.schemas.site import SiteResponse
from app.services.activity_service import log_activity
from app.services.geospatial import GeospatialService

router = APIRouter(prefix="/projects", tags=["Projects"])


def build_project_response(project: Project, db: Session) -> ProjectResponse:
    sites = db.query(Site).filter(Site.project_id == project.id).all()
    sites_count = len(sites)
    total_area = sum(s.area for s in sites) if sites else 0.0

    # Calculate carbon and biodiversity from latest metrics of these sites
    total_carbon = 0.0
    biodiversity_scores = []

    for s in sites:
        latest_metric = (
            db.query(EnvironmentalMetric)
            .filter(EnvironmentalMetric.site_id == s.id)
            .order_by(EnvironmentalMetric.metric_date.desc())
            .first()
        )
        if latest_metric:
            total_carbon += latest_metric.carbon_value
            biodiversity_scores.append(latest_metric.biodiversity_score)

    avg_biodiversity = (
        (sum(biodiversity_scores) / len(biodiversity_scores)) if biodiversity_scores else 0.0
    )

    return ProjectResponse(
        id=project.id,
        name=project.name,
        description=project.description,
        project_type=project.project_type,
        start_date=project.start_date,
        end_date=project.end_date,
        status=project.status,
        created_by=project.created_by,
        created_at=project.created_at,
        updated_at=project.updated_at,
        sites_count=sites_count,
        total_area=round(total_area, 2),
        total_carbon=round(total_carbon, 2),
        avg_biodiversity=round(avg_biodiversity, 1),
        location_summary=(
            "Global / Mixed"
            if sites_count > 1
            else (sites[0].name if sites else "No sites assigned")
        ),
    )


@router.get("", response_model=List[ProjectResponse])
def list_projects(
    search: Optional[str] = None,
    project_type: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db),
):
    query = db.query(Project)

    if search:
        search_pattern = f"%{search.strip()}%"
        query = query.filter(
            or_(Project.name.ilike(search_pattern), Project.description.ilike(search_pattern))
        )

    if project_type:
        query = query.filter(Project.project_type == project_type)

    if status_filter:
        query = query.filter(Project.status == status_filter)

    projects = query.order_by(Project.created_at.desc()).all()
    return [build_project_response(p, db) for p in projects]


@router.post("", response_model=ProjectResponse, status_code=status.HTTP_201_CREATED)
def create_project(
    project_in: ProjectCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = Project(
        name=project_in.name.strip(),
        description=project_in.description,
        project_type=project_in.project_type,
        start_date=project_in.start_date,
        end_date=project_in.end_date,
        status=project_in.status,
        created_by=current_user.id,
    )
    db.add(project)
    db.commit()
    db.refresh(project)

    # Process any sites added during multi-step project creation wizard
    if project_in.sites:
        for site_data in project_in.sites:
            geometry_wkt = None
            geojson_str = None
            area_ha = site_data.area or 0.0
            lat = site_data.latitude
            lng = site_data.longitude

            if site_data.geometry:
                try:
                    poly, calculated_ha, c_lat, c_lng = (
                        GeospatialService.validate_and_parse_geojson(site_data.geometry)
                    )
                    geometry_wkt = GeospatialService.prepare_postgis_geometry(poly)
                    geojson_str = json.dumps(site_data.geometry)
                    if not area_ha:
                        area_ha = calculated_ha
                    if lat is None:
                        lat = c_lat
                    if lng is None:
                        lng = c_lng
                except Exception:
                    # Keep going or log warning
                    pass

            new_site = Site(
                project_id=project.id,
                name=site_data.name.strip(),
                description=site_data.description,
                area=area_ha,
                status=site_data.status,
                geometry=geometry_wkt,
                geojson_data=geojson_str,
                latitude=lat,
                longitude=lng,
            )
            db.add(new_site)

        db.commit()

    log_activity(
        db=db,
        action="Project Created",
        entity_type="Project",
        entity_id=project.id,
        user_id=current_user.id,
        details=f"Project '{project.name}' created with type {project.project_type} and {len(project_in.sites or [])} sites",
    )

    return build_project_response(project, db)


@router.get("/{project_id}", response_model=ProjectDetailResponse)
def get_project(project_id: int, db: Session = Depends(get_db)):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    base_resp = build_project_response(project, db)
    sites = db.query(Site).filter(Site.project_id == project.id).all()

    site_responses = []
    for s in sites:
        latest_metric = (
            db.query(EnvironmentalMetric)
            .filter(EnvironmentalMetric.site_id == s.id)
            .order_by(EnvironmentalMetric.metric_date.desc())
            .first()
        )
        site_responses.append(
            SiteResponse(
                id=s.id,
                project_id=s.project_id,
                project_name=project.name,
                name=s.name,
                description=s.description,
                area=s.area,
                status=s.status,
                latitude=s.latitude,
                longitude=s.longitude,
                geometry=s.get_geojson(),
                created_at=s.created_at,
                updated_at=s.updated_at,
                latest_carbon=latest_metric.carbon_value if latest_metric else 0.0,
                latest_biodiversity=latest_metric.biodiversity_score if latest_metric else 0.0,
                latest_vegetation=latest_metric.vegetation_value if latest_metric else 0.0,
                latest_sequestration=latest_metric.carbon_sequestration if latest_metric else 0.0,
            )
        )

    return ProjectDetailResponse(**base_resp.model_dump(), sites=site_responses)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    update_dict = project_update.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(project, key, value)

    db.commit()
    db.refresh(project)

    log_activity(
        db=db,
        action="Project Updated",
        entity_type="Project",
        entity_id=project.id,
        user_id=current_user.id,
        details=f"Project '{project.name}' details updated",
    )

    return build_project_response(project, db)


@router.delete("/{project_id}", status_code=status.HTTP_200_OK)
def delete_project(
    project_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")

    proj_name = project.name
    db.delete(project)
    db.commit()

    log_activity(
        db=db,
        action="Project Deleted",
        entity_type="Project",
        entity_id=project_id,
        user_id=current_user.id,
        details=f"Project '{proj_name}' (ID: {project_id}) was deleted",
    )

    return {"message": f"Project '{proj_name}' deleted successfully", "id": project_id}
