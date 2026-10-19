import uuid

import psycopg
import pytest

from app.connections import pool_manager
from app.connections.pool_manager import PoolManager
from app.connections.tester import TargetParams
from app.security.network_guard import NetworkPolicy
from tests.helpers import READONLY_PASSWORD, READONLY_USER, SAMPLE_DB, SAMPLE_HOST, SAMPLE_PORT

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("sample_db_reachable")]

POLICY = NetworkPolicy(allowed_hosts=frozenset({SAMPLE_HOST}))
PARAMS = TargetParams(
    host=SAMPLE_HOST, port=SAMPLE_PORT, database=SAMPLE_DB,
    username=READONLY_USER, password=READONLY_PASSWORD, ssl_mode="prefer",
)


def test_pool_runs_queries_and_is_reused():
    manager, cid = PoolManager(), uuid.uuid4()
    try:
        with manager.connection(cid, PARAMS, POLICY) as conn:
            assert conn.execute("SELECT count(*) FROM customers").fetchone()[0] == 5
        first = manager._pools[cid].pool
        with manager.connection(cid, PARAMS, POLICY) as conn:
            conn.execute("SELECT 1")
        assert manager._pools[cid].pool is first
    finally:
        manager.close_all()


def test_pooled_sessions_are_read_only():
    manager, cid = PoolManager(), uuid.uuid4()
    try:
        with manager.connection(cid, PARAMS, POLICY) as conn:
            with pytest.raises(psycopg.errors.ReadOnlySqlTransaction):
                conn.execute("CREATE TABLE should_not_exist (i int)")
    finally:
        manager.close_all()


def test_pool_is_rebuilt_and_revalidated_after_ttl(monkeypatch):
    now = [0.0]
    manager, cid = PoolManager(ttl_seconds=60, clock=lambda: now[0]), uuid.uuid4()
    calls: list[int] = []
    real = pool_manager.resolve_and_validate

    def counting(*args, **kwargs):
        calls.append(1)
        return real(*args, **kwargs)

    monkeypatch.setattr(pool_manager, "resolve_and_validate", counting)
    try:
        first = manager._pool_for(cid, PARAMS, POLICY)
        assert manager._pool_for(cid, PARAMS, POLICY) is first and len(calls) == 1
        now[0] = 61.0
        second = manager._pool_for(cid, PARAMS, POLICY)
        assert second is not first and len(calls) == 2  # re-resolved and re-validated
    finally:
        manager.close_all()


def test_changed_credentials_build_a_new_pool_and_discard_removes_it():
    manager, cid = PoolManager(), uuid.uuid4()
    try:
        first = manager._pool_for(cid, PARAMS, POLICY)
        changed = TargetParams(**{**PARAMS.__dict__, "password": "something-else"})
        assert manager._pool_for(cid, changed, POLICY) is not first
        manager.discard(cid)
        assert cid not in manager._pools
    finally:
        manager.close_all()