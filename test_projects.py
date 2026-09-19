def test_create_and_list_projects(client, auth_headers):
    # Create project
    create_res = client.post(
        "/api/projects",
        headers=auth_headers,
        json={
            "name": "Iberian Lynx Forest Corridor",
            "description": "Mediterranean oak forest habitat restoration in southern Spain.",
            "project_type": "Biodiversity",
            "status": "Active",
        },
    )
    assert create_res.status_code == 201
    proj_data = create_res.json()
    proj_id = proj_data["id"]
    assert proj_data["name"] == "Iberian Lynx Forest Corridor"
    assert proj_data["project_type"] == "Biodiversity"

    # List projects
    list_res = client.get("/api/projects")
    assert list_res.status_code == 200
    items = list_res.json()
    assert any(p["id"] == proj_id for p in items)

    # Filter projects by type
    filter_res = client.get("/api/projects?project_type=Biodiversity")
    assert filter_res.status_code == 200
    assert all(p["project_type"] == "Biodiversity" for p in filter_res.json())

    # Get single project
    detail_res = client.get(f"/api/projects/{proj_id}")
    assert detail_res.status_code == 200
    assert detail_res.json()["name"] == "Iberian Lynx Forest Corridor"

    # Update project
    update_res = client.put(
        f"/api/projects/{proj_id}", headers=auth_headers, json={"status": "Completed"}
    )
    assert update_res.status_code == 200
    assert update_res.json()["status"] == "Completed"

    # Delete project
    del_res = client.delete(f"/api/projects/{proj_id}", headers=auth_headers)
    assert del_res.status_code == 200

    # Ensure 404 after deletion
    get_res = client.get(f"/api/projects/{proj_id}")
    assert get_res.status_code == 404
