import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_root():
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


def test_health_check():
    """Test health check endpoint."""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


@pytest.mark.skip("Requires FastF1 data")
def test_get_sessions():
    """Test sessions endpoint."""
    response = client.get("/sessions?season=2024&round=1")
    assert response.status_code == 200

