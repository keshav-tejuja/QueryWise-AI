import pytest
from sqlalchemy import text

from app.security import rate_limit
from app.security.rate_limit import SlidingWindowLimiter
from tests.helpers import READONLY_PASSWORD, READONLY_USER, SAMPLE_DB, SAMPLE_HOST, SAMPLE_PORT

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("sample_db_reachable")]

SAMPLE = {
    "host": SAMPLE_HOST, "port": SAMPLE_PORT, "database": SAMPLE_DB,
    "username": READONLY_USER, "password": READONLY_PASSWORD, "ssl_mode": "prefer",
}
PASSWORD = "a-long-test-password"


def _auth(client, email="alice@example.com") -> dict[str, str]:
    client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD, "display_name": "T"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _create(client, headers, name="Demo", **overrides):
    return client.post("/api/v1/connections", json={"name": name, **SAMPLE, **overrides}, headers=headers)


def test_all_endpoints_require_auth(client):
    assert client.get("/api/v1/connections").status_code == 401
    assert client.post("/api/v1/connections/test", json=SAMPLE).status_code == 401


def test_unsaved_test_ok_for_sample_database(client):
    headers = _auth(client)
    body = client.post("/api/v1/connections/test", json=SAMPLE, headers=headers).json()
    assert body["ok"] is True and body["read_only"] is True


def test_unsaved_test_blocks_loopback_without_connecting(client):
    headers = _auth(client)
    body = client.post("/api/v1/connections/test", json={**SAMPLE, "host": "127.0.0.1"}, headers=headers).json()
    assert body["ok"] is False and body["code"] == "host_not_allowed"


def test_create_encrypts_password_and_never_returns_it(client, test_engine):
    headers = _auth(client)
    response = _create(client, headers)
    assert response.status_code == 201
    body = response.json()
    assert body["connection"]["status"] == "connected"
    assert body["check"]["ok"] is True
    assert READONLY_PASSWORD not in response.text and "password" not in body["connection"]

    with test_engine.connect() as conn:
        stored = conn.execute(text("SELECT password_encrypted FROM db_connections")).scalar_one()
    assert READONLY_PASSWORD not in stored and stored.startswith("gAAAA")

    listed = client.get("/api/v1/connections", headers=headers)
    assert READONLY_PASSWORD not in listed.text and len(listed.json()) == 1


def test_create_with_bad_password_saves_nothing(client):
    headers = _auth(client)
    response = _create(client, headers, password="wrong")
    assert response.status_code == 400 and response.json()["error"]["code"] == "auth_failed"
    assert client.get("/api/v1/connections", headers=headers).json() == []


def test_duplicate_name_rejected_case_insensitively(client):
    headers = _auth(client)
    assert _create(client, headers, name="Demo").status_code == 201
    duplicate = _create(client, headers, name="demo")
    assert duplicate.status_code == 409 and duplicate.json()["error"]["code"] == "connection_name_taken"


def test_users_cannot_see_or_touch_each_others_connections(client):
    alice = _auth(client, "alice@example.com")
    connection_id = _create(client, alice).json()["connection"]["id"]
    bob = _auth(client, "bob@example.com")
    base = f"/api/v1/connections/{connection_id}"

    assert client.get("/api/v1/connections", headers=bob).json() == []
    assert client.get(base, headers=bob).status_code == 404
    assert client.patch(base, json={"name": "mine now"}, headers=bob).status_code == 404
    assert client.post(f"{base}/test", headers=bob).status_code == 404
    assert client.post(f"{base}/disconnect", headers=bob).status_code == 404
    assert client.delete(base, headers=bob).status_code == 404
    assert client.get(base, headers=alice).status_code == 200  # still intact for the owner


def test_rename_does_not_retest(client):
    headers = _auth(client)
    connection_id = _create(client, headers).json()["connection"]["id"]
    response = client.patch(f"/api/v1/connections/{connection_id}", json={"name": "Renamed"}, headers=headers)
    assert response.status_code == 200
    assert response.json()["connection"]["name"] == "Renamed" and response.json()["check"] is None


def test_failed_edit_leaves_saved_connection_untouched(client):
    headers = _auth(client)
    connection_id = _create(client, headers).json()["connection"]["id"]
    bad = client.patch(f"/api/v1/connections/{connection_id}", json={"password": "wrong"}, headers=headers)
    assert bad.status_code == 400
    assert client.post(f"/api/v1/connections/{connection_id}/test", headers=headers).json()["check"]["ok"] is True


def test_disconnect_then_test_reconnects(client):
    headers = _auth(client)
    connection_id = _create(client, headers).json()["connection"]["id"]
    assert client.post(f"/api/v1/connections/{connection_id}/disconnect", headers=headers).json()["status"] == "disconnected"
    retest = client.post(f"/api/v1/connections/{connection_id}/test", headers=headers).json()
    assert retest["connection"]["status"] == "connected" and retest["check"]["ok"] is True


def test_delete_removes_connection(client):
    headers = _auth(client)
    connection_id = _create(client, headers).json()["connection"]["id"]
    assert client.delete(f"/api/v1/connections/{connection_id}", headers=headers).status_code == 204
    assert client.get("/api/v1/connections", headers=headers).json() == []


def test_tampered_host_makes_credentials_unreadable_instead_of_leaking(client, test_engine):
    headers = _auth(client)
    connection_id = _create(client, headers).json()["connection"]["id"]
    with test_engine.begin() as conn:
        conn.execute(text("UPDATE db_connections SET host = 'attacker.example.com'"))
    result = client.post(f"/api/v1/connections/{connection_id}/test", headers=headers).json()
    assert result["check"]["ok"] is False and result["check"]["code"] == "credentials_unreadable"
    assert result["connection"]["status"] == "error"


def test_connection_tests_are_rate_limited(client, monkeypatch):
    monkeypatch.setattr(rate_limit, "connection_test_limiter", SlidingWindowLimiter(1, 60))
    headers = _auth(client)
    payload = {**SAMPLE, "host": "127.0.0.1"}
    assert client.post("/api/v1/connections/test", json=payload, headers=headers).status_code == 200
    limited = client.post("/api/v1/connections/test", json=payload, headers=headers)
    assert limited.status_code == 429 and limited.json()["error"]["code"] == "rate_limited"