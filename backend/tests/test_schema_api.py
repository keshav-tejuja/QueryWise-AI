import psycopg
import pytest
from sqlalchemy import text

from tests.helpers import (
    ADMIN_PASSWORD, ADMIN_USER, READONLY_PASSWORD, READONLY_USER, SAMPLE_DB, SAMPLE_HOST, SAMPLE_PORT,
)

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("sample_db_reachable")]

PASSWORD = "a-long-test-password"
SAMPLE = {"host": SAMPLE_HOST, "port": SAMPLE_PORT, "database": SAMPLE_DB, "username": READONLY_USER,
          "password": READONLY_PASSWORD, "ssl_mode": "prefer"}


def _auth(client, email="alice@example.com"):
    client.post("/api/v1/auth/register", json={"email": email, "password": PASSWORD, "display_name": "T"})
    token = client.post("/api/v1/auth/login", json={"email": email, "password": PASSWORD}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def _connection(client, headers) -> str:
    return client.post("/api/v1/connections", json={"name": "Demo", **SAMPLE}, headers=headers).json()["connection"]["id"]


def _admin():
    return psycopg.connect(
        host=SAMPLE_HOST, port=SAMPLE_PORT, dbname=SAMPLE_DB, user=ADMIN_USER, password=ADMIN_PASSWORD, autocommit=True
    )


def test_schema_is_discovered_automatically_after_saving(client):
    headers = _auth(client)
    cid = _connection(client, headers)
    body = client.get(f"/api/v1/connections/{cid}/schema", headers=headers).json()
    assert {"public.customers", "public.orders"} <= {t["qualified_name"] for t in body["tables"]}
    assert len(body["schema_hash"]) == 64


def test_schema_not_loaded_is_a_clear_404(client, test_engine):
    headers = _auth(client)
    cid = _connection(client, headers)
    with test_engine.begin() as conn:
        conn.execute(text("DELETE FROM schema_snapshots"))
    response = client.get(f"/api/v1/connections/{cid}/schema", headers=headers)
    assert response.status_code == 404 and response.json()["error"]["code"] == "schema_not_loaded"
    refreshed = client.post(f"/api/v1/connections/{cid}/schema/refresh", headers=headers)
    assert refreshed.status_code == 200 and refreshed.json()["changed"] is True


def test_refresh_reports_unchanged_then_detects_a_real_change(client):
    headers = _auth(client)
    cid = _connection(client, headers)
    url = f"/api/v1/connections/{cid}/schema"
    first_hash = client.get(url, headers=headers).json()["schema_hash"]

    unchanged = client.post(f"{url}/refresh", headers=headers).json()
    assert unchanged["changed"] is False and unchanged["diff"] is None

    with _admin() as admin:
        admin.execute("ALTER TABLE customers ADD COLUMN loyalty_tier TEXT")
        try:
            changed = client.post(f"{url}/refresh", headers=headers).json()
            assert changed["changed"] is True and changed["snapshot"]["schema_hash"] != first_hash
            assert changed["diff"]["changed_tables"] == ["public.customers"]
            customers = next(t for t in changed["snapshot"]["tables"] if t["name"] == "customers")
            assert "loyalty_tier" in {c["name"] for c in customers["columns"]}
        finally:
            admin.execute("ALTER TABLE customers DROP COLUMN loyalty_tier")
    reverted = client.post(f"{url}/refresh", headers=headers).json()
    assert reverted["changed"] is True and reverted["snapshot"]["schema_hash"] == first_hash


def test_retrieval_endpoint_finds_tables_and_join_path(client):
    headers = _auth(client)
    cid = _connection(client, headers)
    response = client.post(
        f"/api/v1/connections/{cid}/schema/retrieve",
        json={"question": "total order amount per customer"}, headers=headers,
    )
    assert response.status_code == 200
    body = response.json()
    assert {t["qualified_name"] for t in body["tables"]} == {"public.customers", "public.orders"}
    assert body["join_paths"] and body["unconnected_pairs"] == []


def test_schema_endpoints_are_owner_only(client):
    alice = _auth(client, "alice@example.com")
    cid = _connection(client, alice)
    bob = _auth(client, "bob@example.com")
    base = f"/api/v1/connections/{cid}/schema"
    assert client.get(base, headers=bob).status_code == 404
    assert client.post(f"{base}/refresh", headers=bob).status_code == 404
    assert client.post(f"{base}/retrieve", json={"question": "customers"}, headers=bob).status_code == 404
    assert client.get(base, headers=alice).status_code == 200


def test_refresh_refuses_disconnected_connections(client):
    headers = _auth(client)
    cid = _connection(client, headers)
    client.post(f"/api/v1/connections/{cid}/disconnect", headers=headers)
    response = client.post(f"/api/v1/connections/{cid}/schema/refresh", headers=headers)
    assert response.status_code == 409 and response.json()["error"]["code"] == "connection_disconnected"