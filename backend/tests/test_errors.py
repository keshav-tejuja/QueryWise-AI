from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.errors import AppError, register_exception_handlers
from app.core.middleware import RequestContextMiddleware
from app.main import app as real_app


def _build_app() -> FastAPI:
    test_app = FastAPI()
    test_app.add_middleware(RequestContextMiddleware)
    register_exception_handlers(test_app)

    @test_app.get("/app-error")
    def app_error():
        raise AppError("custom_code", "Something specific.", 418)

    @test_app.get("/boom")
    def boom():
        raise RuntimeError("secret-internal-detail")

    return test_app


def test_unknown_route_uses_error_envelope():
    client = TestClient(real_app)
    response = client.get("/api/v1/does-not-exist")
    assert response.status_code == 404
    error = response.json()["error"]
    assert error["code"] == "http_404"
    assert error["request_id"] == response.headers["X-Request-ID"]


def test_validation_error_does_not_echo_input():
    client = TestClient(real_app)
    response = client.post(
        "/api/v1/auth/register",
        json={"email": "not-an-email", "password": "hunter2-short", "display_name": ""},
    )
    assert response.status_code == 422
    body = response.json()["error"]
    assert body["code"] == "validation_error"
    assert {d["field"] for d in body["details"]} >= {"email", "display_name"}
    assert "hunter2-short" not in response.text


def test_app_error_maps_to_status_and_code():
    client = TestClient(_build_app())
    response = client.get("/app-error")
    assert response.status_code == 418
    assert response.json()["error"]["code"] == "custom_code"


def test_unhandled_exception_hides_internals():
    client = TestClient(_build_app(), raise_server_exceptions=False)
    response = client.get("/boom")
    assert response.status_code == 500
    assert response.json()["error"]["code"] == "internal_error"
    assert "secret-internal-detail" not in response.text


def test_client_supplied_request_id_is_validated():
    client = TestClient(real_app)
    good = client.get("/api/v1/health/live", headers={"X-Request-ID": "abc12345-good"})
    assert good.headers["X-Request-ID"] == "abc12345-good"
    bad = client.get("/api/v1/health/live", headers={"X-Request-ID": "bad id\nwith junk"})
    assert bad.headers["X-Request-ID"] != "bad id\nwith junk"