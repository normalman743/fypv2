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
from app.crud.semester import semester as crud_semester
from app.schemas.semester import SemesterCreate

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

def test_create_semester_success(client: TestClient, test_user: dict):
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
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["data"]["semester"]["name"] == "2025 Fall"
    assert data["data"]["semester"]["code"] == "2025FA"
    assert "id" in data["data"]["semester"]

def test_create_semester_duplicate_code(client: TestClient, test_user: dict):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    semester_data = {
        "name": "2025 Fall",
        "code": "2025FA",
        "start_date": datetime(2025, 9, 1, 0, 0, 0).isoformat(),
        "end_date": datetime(2025, 12, 31, 23, 59, 59).isoformat()
    }
    client.post(
        "/api/v1/semesters",
        json=semester_data,
        headers=headers
    )
    response = client.post(
        "/api/v1/semesters",
        json=semester_data,
        headers=headers
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Semester with this code already exists"}

def test_create_semester_unauthenticated(client: TestClient):
    semester_data = {
        "name": "2026 Spring",
        "code": "2026SP",
        "start_date": datetime(2026, 1, 1, 0, 0, 0).isoformat(),
        "end_date": datetime(2026, 5, 31, 23, 59, 59).isoformat()
    }
    response = client.post(
        "/api/v1/semesters",
        json=semester_data
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_create_semester_invalid_data(client: TestClient, test_user: dict):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    semester_data = {
        "name": "Invalid Semester",
        "code": "INV",
        "start_date": "invalid-date", # Invalid date format
        "end_date": datetime(2026, 5, 31, 23, 59, 59).isoformat()
    }
    response = client.post(
        "/api/v1/semesters",
        json=semester_data,
        headers=headers
    )
    assert response.status_code == 422 # Unprocessable Entity

def test_get_semesters_success(client: TestClient, test_user: dict, db_session: Session):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    # Create a few semesters
    semester_data_1 = SemesterCreate(name="2025 Fall", code="2025FA", start_date=datetime(2025, 9, 1), end_date=datetime(2025, 12, 31, 23, 59, 59))
    semester_data_2 = SemesterCreate(name="2026 Spring", code="2026SP", start_date=datetime(2026, 1, 1), end_date=datetime(2026, 5, 31, 23, 59, 59))
    crud_semester.create(db_session, obj_in=semester_data_1)
    crud_semester.create(db_session, obj_in=semester_data_2)

    response = client.get(
        "/api/v1/semesters",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["semesters"]) == 2
    assert data["data"]["semesters"][0]["name"] == "2025 Fall"
    assert data["data"]["semesters"][1]["name"] == "2026 Spring"

def test_get_semesters_pagination(client: TestClient, test_user: dict, db_session: Session):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    # Create more semesters for pagination test
    for i in range(5):
        crud_semester.create(db_session, obj_in=SemesterCreate(
            name=f"Semester {i}",
            code=f"S{i}",
            start_date=datetime(2025, 1, 1),
            end_date=datetime(2025, 12, 31)
        ))
    
    response = client.get(
        "/api/v1/semesters?skip=1&limit=2",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["semesters"]) == 2
    assert data["data"]["semesters"][0]["name"] == "Semester 1"
    assert data["data"]["semesters"][1]["name"] == "Semester 2"

def test_get_semesters_empty_list(client: TestClient, test_user: dict):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.get(
        "/api/v1/semesters",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["data"]["semesters"]) == 0

def test_get_semesters_unauthenticated(client: TestClient):
    response = client.get(
        "/api/v1/semesters"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}

def test_get_semester_by_id_success(client: TestClient, test_user: dict, db_session: Session):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    semester_data = SemesterCreate(name="Unique Semester", code="UNIQUE", start_date=datetime(2025, 1, 1), end_date=datetime(2025, 12, 31))
    created_semester = crud_semester.create(db_session, obj_in=semester_data)

    response = client.get(
        f"/api/v1/semesters/{created_semester.id}",
        headers=headers
    )
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert data["data"]["semester"]["name"] == "Unique Semester"
    assert data["data"]["semester"]["code"] == "UNIQUE"
    assert data["data"]["semester"]["id"] == created_semester.id

def test_get_semester_by_id_not_found(client: TestClient, test_user: dict):
    headers = {"Authorization": f"Bearer {test_user['token']}"}
    response = client.get(
        "/api/v1/semesters/999", # Non-existent ID
        headers=headers
    )
    assert response.status_code == 404
    assert response.json() == {"detail": "Semester not found"}

def test_get_semester_by_id_unauthenticated(client: TestClient):
    response = client.get(
        "/api/v1/semesters/1"
    )
    assert response.status_code == 401
    assert response.json() == {"detail": "Not authenticated"}