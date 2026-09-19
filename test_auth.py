def test_user_registration(client):
    res = client.post(
        "/api/auth/register",
        json={
            "name": "Maria Santos",
            "email": "maria@darukaa.earth",
            "password": "SecurePassword123!",
        },
    )
    assert res.status_code == 201
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["user"]["email"] == "maria@darukaa.earth"


def test_duplicate_registration_fails(client):
    # First register
    client.post(
        "/api/auth/register",
        json={
            "name": "Maria Duplicate",
            "email": "duplicate@darukaa.earth",
            "password": "AnotherPassword123!",
        },
    )
    # Try registering same email again
    res = client.post(
        "/api/auth/register",
        json={
            "name": "Maria Duplicate 2",
            "email": "duplicate@darukaa.earth",
            "password": "AnotherPassword123!",
        },
    )
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


def test_user_login(client):
    # Register first
    client.post(
        "/api/auth/register",
        json={
            "name": "Login Tester",
            "email": "login.test@darukaa.earth",
            "password": "SecurePassword123!",
        },
    )
    res = client.post(
        "/api/auth/login",
        json={"email": "login.test@darukaa.earth", "password": "SecurePassword123!"},
    )
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data


def test_login_invalid_password(client):
    res = client.post(
        "/api/auth/login", json={"email": "maria@darukaa.earth", "password": "WrongPassword999"}
    )
    assert res.status_code == 401
    assert "Invalid email address or password" in res.json()["detail"]


def test_auth_me_endpoint(client, auth_headers):
    res = client.get("/api/auth/me", headers=auth_headers)
    assert res.status_code == 200
    assert res.json()["email"] == "tester@darukaa.earth"
