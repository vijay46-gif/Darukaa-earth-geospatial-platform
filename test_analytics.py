def test_overview_metrics(client):
    res = client.get("/api/analytics/overview")
    assert res.status_code == 200
    data = res.json()
    assert "total_projects" in data
    assert "total_sites" in data
    assert "total_area_hectares" in data
    assert "total_carbon_impact_tco2e" in data
    assert "average_biodiversity_score" in data


def test_carbon_analytics(client):
    res = client.get("/api/analytics/carbon?range=1y")
    assert res.status_code == 200
    data = res.json()
    assert "total_carbon_stored" in data
    assert "monthly_historical" in data
    assert "site_distribution" in data


def test_biodiversity_analytics(client):
    res = client.get("/api/analytics/biodiversity?range=1y")
    assert res.status_code == 200
    data = res.json()
    assert "average_score" in data
    assert "project_scores" in data


def test_map_sites_feature_collection(client):
    res = client.get("/api/map/sites")
    assert res.status_code == 200
    data = res.json()
    assert data["type"] == "FeatureCollection"
    assert "features" in data
