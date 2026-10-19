import hashlib
import threading
import time
import uuid
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass

import psycopg
from psycopg_pool import ConnectionPool

from app.connections.tester import TargetParams, connect_kwargs
from app.security.network_guard import NetworkPolicy, resolve_and_validate


@dataclass
class _Entry:
    pool: ConnectionPool
    fingerprint: tuple
    created_at: float


class PoolManager:
    """One small pool per saved connection.

    - Every pool is pinned to an IP that passed the network policy when the pool was built.
    - Pools are rebuilt (and the host re-resolved and re-validated) after `ttl_seconds`, so a
      DNS change cannot keep us attached to an address that is no longer acceptable.
    - Pool sessions use the same read-only/timeout options as every other session we open.
    """

    def __init__(
        self, ttl_seconds: float = 300, max_size: int = 3, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self._ttl = ttl_seconds
        self._max_size = max_size
        self._clock = clock
        self._pools: dict[uuid.UUID, _Entry] = {}
        self._lock = threading.Lock()

    @staticmethod
    def _fingerprint(params: TargetParams) -> tuple:
        password_digest = hashlib.sha256(params.password.encode()).hexdigest()[:16]
        return (params.host, params.port, params.database, params.username, params.ssl_mode, password_digest)

    def _pool_for(
        self, connection_id: uuid.UUID, params: TargetParams, policy: NetworkPolicy | None
    ) -> ConnectionPool:
        fingerprint = self._fingerprint(params)
        with self._lock:
            entry = self._pools.get(connection_id)
            now = self._clock()
            if entry and entry.fingerprint == fingerprint and now - entry.created_at < self._ttl:
                return entry.pool
            if entry:
                entry.pool.close(timeout=2)
                del self._pools[connection_id]

            ip = resolve_and_validate(params.host, params.port, policy)  # raises NetworkPolicyError
            pool = ConnectionPool(
                conninfo="",
                kwargs=connect_kwargs(params, ip),
                min_size=0,
                max_size=self._max_size,
                max_idle=30,
                max_lifetime=self._ttl,
                timeout=10,
                open=True,
                name=f"qw-{connection_id}",
            )
            self._pools[connection_id] = _Entry(pool, fingerprint, now)
            return pool

    @contextmanager
    def connection(
        self, connection_id: uuid.UUID, params: TargetParams, policy: NetworkPolicy | None = None
    ) -> Iterator[psycopg.Connection]:
        pool = self._pool_for(connection_id, params, policy)
        with pool.connection() as conn:
            yield conn

    def discard(self, connection_id: uuid.UUID) -> None:
        with self._lock:
            entry = self._pools.pop(connection_id, None)
        if entry:
            entry.pool.close(timeout=2)

    def close_all(self) -> None:
        with self._lock:
            entries, self._pools = list(self._pools.values()), {}
        for entry in entries:
            entry.pool.close(timeout=2)


pools = PoolManager()