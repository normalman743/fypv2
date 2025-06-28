import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from dotenv import load_dotenv

load_dotenv() # Load environment variables from .env

from main import app
from app.db.base import Base
from app.db.session import get_db

# Setup a test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
# SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:" # Use in-memory for faster tests

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

def test_create_user_success(client: TestClient):
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword",
            "invite_code": "ADMIN_INVITE_CODE_HERE" # Assuming a valid invite code for now
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["username"] == "testuser"
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data

def test_create_user_duplicate_username(client: TestClient):
    # Create user first
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "test@example.com",
            "password": "testpassword",
            "invite_code": "ADMIN_INVITE_CODE_HERE"
        },
    )
    # Try to create again with same username
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser",
            "email": "another@example.com",
            "password": "anotherpassword",
            "invite_code": "ADMIN_INVITE_CODE_HERE"
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Username already registered"}

def test_create_user_duplicate_email(client: TestClient):
    # Create user first
    client.post(
        "/api/v1/auth/register",
        json={
            "username": "testuser_email",
            "email": "test_email@example.com",
            "password": "testpassword",
            "invite_code": "ADMIN_INVITE_CODE_HERE"
        },
    )
    # Try to create again with same email
    response = client.post(
        "/api/v1/auth/register",
        json={
            "username": "another_user_email",
            "email": "test_email@example.com",
            "password": "anotherpassword",
            "invite_code": "ADMIN_INVITE_CODE_HERE"
        },
    )
    assert response.status_code == 400
    assert response.json() == {"detail": "Email already registered"}