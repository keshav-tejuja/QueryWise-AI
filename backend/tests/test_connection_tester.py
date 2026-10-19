import psycopg
import pytest

from app.connections import tester
from app.connections.tester import TargetParams, check_connection, classify_error
from app.security.network_guard import NetworkPolicy

PARAMS = TargetParams(host="example.com", port=5432, database="d", username="u", password="topsecret")


@pytest.mark.parametrize(
    ("message", "expected"),
    [
        ('FATAL: password authentication failed for user "x"', "auth_failed"),
        ('FATAL: database "nope" does not exist', "database_not_found"),
        ("FATAL: no pg_hba.conf entry for host, no encryption", "access_denied"),
        ("server does not support SSL, but SSL was required", "ssl_failed"),
        ("connection timeout expired", "connection_timeout"),
        ("connection failed: Connection refused", "connection_refused"),
        ("something unexpected", "connection_failed"),
    ],
)
def test_classify_error(message, expected):
    assert classify_error(psycopg.OperationalError(message)) == expected


def test_blocked_host_never_attempts_a_connection(monkeypatch):
    def forbidden(*args, **kwargs):
        raise AssertionError("must not connect to a blocked host")

    monkeypatch.setattr(tester.psycopg, "connect", forbidden)
    result = check_connection(
        TargetParams(host="127.0.0.1", port=5432, database="d", username="u", password="p"),
        NetworkPolicy(),
    )
    assert not result.ok
    assert result.code == "host_not_allowed"


def test_driver_errors_are_sanitized(monkeypatch):
    monkeypatch.setattr(tester, "resolve_and_validate", lambda host, port, policy=None: "203.0.113.10")

    def failing_connect(params, ip):
        raise psycopg.OperationalError("connection to 203.0.113.10 failed: password=topsecret user=u")

    monkeypatch.setattr(tester, "_connect", failing_connect)
    result = check_connection(PARAMS)
    assert not result.ok
    assert "topsecret" not in result.message
    assert "203.0.113.10" not in result.message


def test_params_repr_hides_password():
    assert "topsecret" not in repr(PARAMS)