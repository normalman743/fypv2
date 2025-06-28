import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv
from datetime import datetime

load_dotenv() # Load environment variables from .env

from main import app
from app.db.base import Base
from app.db.session import get_db
from app.core.config import settings

# Setup a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="db_session")
def override_get_db_session():
    Base.metadata.create_all(bind=engine)  # Create tables
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)  # Drop tables after test

@pytest.fixture(name="client")
def test_client(db_session: Session):
    def _get_test_db():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _get_test_db
    with TestClient(app) as client:
        yield client
    app.dependency_overrides.clear() # Clear overrides after test

@pytest.fixture(name="test_user")
def create_test_user(client: TestClient):
    user_data = {
        "username": "testuser_semester",
        "email": "test_semester@example.com",
        "password": "testpassword",
        "invite_code": settings.ADMIN_INVITE_CODE # Use admin invite code for simplicity in test
    }
    client.post("/api/v1/auth/register", json=user_data)
    
    login_data = {
        "username": "testuser_semester",
        "password": "testpassword"
    }
    response = client.post("/api/v1/auth/login", data=login_data)
    token = response.json()["access_token"]
    return {"username": "testuser_semester", "token": token}

def test_create_semester(client: TestClient, test_user: dict):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    semester_data = {
        "name": "2025 Fall",
        "code": "2025FA",
        "start_date": datetime(2025, 9, 1, 0, 0, 0).isoformat(), # Converted to ISO format string
        "end_date": datetime(2025, 12, 31, 23, 59, 59).isoformat() # Converted to ISO format string
    }
    response = client.post(
        "/api/v1/semesters",
        json=semester_data,
        headers=headers
    )
    assert response.status_code == 201 # Changed to 201 as per API design
    data = response.json()
    assert data["success"] is True
    assert data["data"]["semester"]["name"] == "2025 Fall"
    assert data["data"]["semester"]["code"] == "2025FA"
    assert "id" in data["data"]["semester"]
