import pytest

pytestmark = pytest.mark.integration

PASSWORD = "a-long-test-password"


def _register(client, email="alice@example.com", password=PASSWORD):
    return client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "display_name": "Alice"},
    )


def _login(client, email="alice@example.com", password=PASSWORD):
    return client.post("/api/v1/auth/login", json={"email": email, "password": password})


def test_register_success_hides_password(client):
    response = _register(client)
    assert response.status_code == 201
    body = response.json()
    assert body["email"] == "alice@example.com"
    assert "password" not in response.text and "hash" not in response.text


def test_register_duplicate_email_case_insensitive(client):
    assert _register(client).status_code == 201
    duplicate = _register(client, email="ALICE@example.com")
    assert duplicate.status_code == 409
    assert duplicate.json()["error"]["code"] == "email_taken"


def test_register_rejects_short_password(client):
    assert _register(client, password="short").status_code == 422


def test_login_sets_httponly_refresh_cookie_not_in_body(client):
    _register(client)
    response = _login(client)
    assert response.status_code == 200
    cookie_header = response.headers["set-cookie"].lower()
    assert "qw_refresh=" in cookie_header
    assert "httponly" in cookie_header
    assert "samesite=lax" in cookie_header
    raw_refresh = response.cookies.get("qw_refresh")
    assert raw_refresh and raw_refresh not in response.text


def test_login_failures_are_indistinguishable(client):
    _register(client)
    wrong_password = _login(client, password="wrong-password-here")
    unknown_email = _login(client, email="nobody@example.com")
    assert wrong_password.status_code == unknown_email.status_code == 401
    assert wrong_password.json()["error"]["message"] == unknown_email.json()["error"]["message"]


def test_me_requires_valid_token(client):
    assert client.get("/api/v1/auth/me").status_code == 401
    bad = client.get("/api/v1/auth/me", headers={"Authorization": "Bearer garbage"})
    assert bad.status_code == 401
    _register(client)
    token = _login(client).json()["access_token"]
    ok = client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert ok.status_code == 200
    assert ok.json()["email"] == "alice@example.com"


def test_refresh_rotates_and_reuse_revokes_everything(client):
    _register(client)
    first = _login(client)
    old_cookie = first.cookies.get("qw_refresh")

    rotated = client.post("/api/v1/auth/refresh")  # client jar sends the current cookie
    assert rotated.status_code == 200
    new_cookie = rotated.cookies.get("qw_refresh")
    assert new_cookie and new_cookie != old_cookie

    # Presenting the OLD (already rotated) token again simulates theft...
    replay = client.post("/api/v1/auth/refresh", headers={"Cookie": f"qw_refresh={old_cookie}"})
    assert replay.status_code == 401

    # ...and must also have revoked the newer token.
    after = client.post("/api/v1/auth/refresh", headers={"Cookie": f"qw_refresh={new_cookie}"})
    assert after.status_code == 401


def test_refresh_without_cookie_is_401(client):
    assert client.post("/api/v1/auth/refresh").status_code == 401


def test_logout_revokes_refresh_token(client):
    _register(client)
    login = _login(client)
    cookie = login.cookies.get("qw_refresh")
    assert client.post("/api/v1/auth/logout").status_code == 204
    after = client.post("/api/v1/auth/refresh", headers={"Cookie": f"qw_refresh={cookie}"})
    assert after.status_code == 401


def test_logout_without_cookie_is_ok(client):
    assert client.post("/api/v1/auth/logout").status_code == 204