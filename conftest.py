import os
import sys

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.auth.security import create_access_token, get_password_hash
from app.database.session import Base, get_db
from app.main import app
from app.models.user import User

TEST_DB_URL = "sqlite:///./test_darukaa.db"
test_engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


@pytest.fixture(scope="session", autouse=True)
def setup_test_db():
    Base.metadata.drop_all(bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    yield
    Base.metadata.drop_all(bind=test_engine)
    if os.path.exists("./test_darukaa.db"):
        try:
            os.remove("./test_darukaa.db")
        except Exception:
            pass


@pytest.fixture
def db():
    connection = test_engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def client(db):
    def override_get_db():
        try:
            yield db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers(db):
    # Ensure test admin user exists
    user = db.query(User).filter(User.email == "tester@darukaa.earth").first()
    if not user:
        user = User(
            name="Test User",
            email="tester@darukaa.earth",
            password_hash=get_password_hash("Password@123"),
            role="admin",
        )
        db.add(user)
        db.commit()
        db.refresh(user)

    token = create_access_token(data={"sub": user.email, "id": user.id, "role": user.role})
    return {"Authorization": f"Bearer {token}"}
