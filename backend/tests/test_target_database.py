import psycopg
import pytest

from app.connections import tester
from app.connections.tester import TargetParams, check_connection
from app.security.network_guard import NetworkPolicy, resolve_and_validate
from tests.helpers import (
    ADMIN_PASSWORD, ADMIN_USER, READONLY_PASSWORD, READONLY_USER, SAMPLE_DB, SAMPLE_HOST, SAMPLE_PORT,
)

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("sample_db_reachable")]

POLICY = NetworkPolicy(allowed_hosts=frozenset({SAMPLE_HOST}))


def _params(**overrides) -> TargetParams:
    values = dict(
        host=SAMPLE_HOST, port=SAMPLE_PORT, database=SAMPLE_DB,
        username=READONLY_USER, password=READONLY_PASSWORD, ssl_mode="prefer",
    )
    values.update(overrides)
    return TargetParams(**values)


def test_readonly_role_connects_cleanly():
    result = check_connection(_params(), POLICY)
    assert result.ok and result.read_only is True
    assert result.warnings == []
    assert result.server_version and result.latency_ms is not None


def test_superuser_role_triggers_warning():
    result = check_connection(_params(username=ADMIN_USER, password=ADMIN_PASSWORD), POLICY)
    assert result.ok and result.read_only is False
    assert any("superuser" in warning for warning in result.warnings)


def test_wrong_password_is_auth_failed():
    assert check_connection(_params(password="wrong"), POLICY).code == "auth_failed"


def test_unknown_database_is_reported():
    assert check_connection(_params(database="nope"), POLICY).code == "database_not_found"


def test_required_ssl_against_non_ssl_server_fails():
    assert check_connection(_params(ssl_mode="require"), POLICY).code == "ssl_failed"


def test_closed_port_is_refused_or_times_out():
    result = check_connection(_params(port=5999), POLICY)
    assert result.code in {"connection_refused", "connection_timeout"}


def test_every_session_is_read_only_even_for_a_superuser():
    params = _params(username=ADMIN_USER, password=ADMIN_PASSWORD)
    ip = resolve_and_validate(params.host, params.port, POLICY)
    with tester._connect(params, ip) as conn:
        with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
            conn.execute("CREATE TABLE should_not_exist (i int)")