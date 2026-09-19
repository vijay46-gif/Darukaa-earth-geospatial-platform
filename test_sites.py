def test_site_creation_and_geospatial_area(client, auth_headers):
    # First create parent project
    p_res = client.post(
        "/api/projects",
        headers=auth_headers,
        json={
            "name": "Borneo Peatland Protection",
            "description": "Tropical peat swamp forest preservation.",
            "project_type": "Carbon + Biodiversity",
            "status": "Active",
        },
    )
    proj_id = p_res.json()["id"]

    # Valid polygon
    valid_polygon = {
        "type": "Polygon",
        "coordinates": [
            [[113.85, -2.15], [114.05, -2.18], [114.02, -2.35], [113.82, -2.32], [113.85, -2.15]]
        ],
    }

    site_res = client.post(
        "/api/sites",
        headers=auth_headers,
        json={
            "project_id": proj_id,
            "name": "Sebangau Peat Swamp Sector",
            "description": "Deep peat dome preserving high below-ground carbon.",
            "status": "Active",
            "geometry": valid_polygon,
        },
    )
    assert site_res.status_code == 201
    site_data = site_res.json()
    assert site_data["name"] == "Sebangau Peat Swamp Sector"
    assert site_data["area"] > 0.0  # Calculated geodesic area in hectares!
    assert site_data["latitude"] is not None
    assert site_data["longitude"] is not None
    assert site_data["geometry"] is not None
    site_id = site_data["id"]

    # Retrieve site details
    get_res = client.get(f"/api/sites/{site_id}")
    assert get_res.status_code == 200
    detail = get_res.json()
    assert len(detail["metrics"]) > 0  # Historical metric baseline generated!

    # Site analytics
    analytics_res = client.get(f"/api/sites/{site_id}/analytics")
    assert analytics_res.status_code == 200
    assert "historical_metrics" in analytics_res.json()


def test_site_creation_with_invalid_polygon_fails(client, auth_headers):
    # Invalid polygon (less than 4 vertices)
    invalid_polygon = {
        "type": "Polygon",
        "coordinates": [[[113.85, -2.15], [114.05, -2.18], [113.85, -2.15]]],
    }

    res = client.post(
        "/api/sites",
        headers=auth_headers,
        json={
            "project_id": 1,
            "name": "Invalid Site",
            "status": "Active",
            "geometry": invalid_polygon,
        },
    )
    assert res.status_code in [404, 422]  # Either project not found or unprocessable polygon
