"""
test_api_endpoints.py — Integration and API tests for Phase 8 endpoints & Phase 9 QA.
Tests that require a live PostgreSQL connection are automatically skipped
when running outside the Docker environment.
"""

import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)


def _db_available() -> bool:
    """Return True only if the PostgreSQL database is reachable."""
    try:
        from backend.app.database.session import SessionLocal
        db = SessionLocal()
        db.execute(__import__("sqlalchemy").text("SELECT 1"))
        db.close()
        return True
    except Exception:
        return False


requires_db = pytest.mark.skipif(
    not _db_available(),
    reason="PostgreSQL database not available (run via Docker Compose)"
)


@requires_db
def test_health_check_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@requires_db
def test_user_registration_and_login_json():
    # Register
    user_payload = {
        "email": "testuser_qa@example.com",
        "username": "testuser_qa",
        "password": "SecurePassword123!"
    }
    reg_res = client.post("/api/v1/auth/register", json=user_payload)
    assert reg_res.status_code in [201, 400]

    # Login via JSON
    login_payload = {
        "username_or_email": "testuser_qa@example.com",
        "password": "SecurePassword123!"
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    res_data = login_res.json()
    assert "access_token" in res_data or "data" in res_data
    token = res_data.get("access_token") or res_data.get("data", {}).get("access_token")
    assert token is not None


@requires_db
def test_unauthorized_projects_access():
    res = client.get("/api/v1/projects")
    assert res.status_code in [401, 403]


def test_api_endpoints_module_importable():
    """Verify the FastAPI app and all routers import without errors."""
    from backend.app.main import app as _app
    assert _app is not None

