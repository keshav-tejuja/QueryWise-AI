from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_live_returns_200():
    response = client.get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "live"}


def test_ready_ok_when_database_reachable(monkeypatch):
    monkeypatch.setattr("app.api.v1.health.check_database", lambda: None)
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 200
    assert response.json() == {"status": "ready", "database": "ok"}


def test_ready_503_when_database_down(monkeypatch):
    def boom():
        raise RuntimeError("connection refused")

    monkeypatch.setattr("app.api.v1.health.check_database", boom)
    response = client.get("/api/v1/health/ready")
    assert response.status_code == 503
    assert response.json() == {"status": "not_ready", "database": "unavailable"}