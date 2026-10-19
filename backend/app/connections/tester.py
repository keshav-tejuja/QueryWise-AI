import logging
import time
from dataclasses import dataclass, field

import psycopg

from app.core.config import settings
from app.security.network_guard import NetworkPolicy, NetworkPolicyError, resolve_and_validate

logger = logging.getLogger(__name__)

# Applied to EVERY session we open on a user's database: a second boundary besides SQL validation.
SESSION_OPTIONS = (
    "-c default_transaction_read_only=on "
    "-c statement_timeout=10000 "
    "-c lock_timeout=2000 "
    "-c idle_in_transaction_session_timeout=10000"
)

FAILURE_MESSAGES = {
    "connection_timeout": "The database didn't respond in time. Check the host, port and any firewall rules.",
    "connection_refused": "The server refused the connection. Check the port and that PostgreSQL accepts connections.",
    "auth_failed": "Authentication failed. Check the username and password.",
    "database_not_found": "That database doesn't exist on the server. Check the database name.",
    "ssl_failed": "The SSL handshake failed. Try a different SSL mode or check the server's certificate.",
    "access_denied": "The server rejected this client. Its access rules (pg_hba.conf) may not allow this address or SSL setting.",
    "connection_failed": "Couldn't connect to the database. Check the connection details and try again.",
}


@dataclass(frozen=True)
class TargetParams:
    host: str
    port: int
    database: str
    username: str
    password: str = field(repr=False)  # never appears in repr/log output
    ssl_mode: str = "prefer"


@dataclass
class CheckResult:
    ok: bool
    code: str
    message: str
    latency_ms: int | None = None
    server_version: str | None = None
    read_only: bool | None = None
    warnings: list[str] = field(default_factory=list)


PRIVILEGE_SQL = """
SELECT r.rolsuper, r.rolcreaterole, r.rolcreatedb,
       has_database_privilege(current_user, current_database(), 'CREATE'),
       (SELECT count(*) FROM information_schema.tables t
         WHERE t.table_type = 'BASE TABLE'
           AND t.table_schema NOT IN ('pg_catalog', 'information_schema')),
       (SELECT count(*) FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
         WHERE c.relkind IN ('r', 'p')
           AND n.nspname NOT IN ('pg_catalog', 'information_schema')
           AND n.nspname NOT LIKE 'pg\\_%'
           AND (has_table_privilege(c.oid, 'INSERT') OR has_table_privilege(c.oid, 'UPDATE')
                OR has_table_privilege(c.oid, 'DELETE') OR has_table_privilege(c.oid, 'TRUNCATE')))
FROM pg_roles r WHERE r.rolname = current_user
"""


def _connect(params: TargetParams, ip: str) -> psycopg.Connection:
    """Open a session to the VALIDATED ip. `host` is kept only for TLS verification and auth."""
    kwargs: dict = {
        "host": params.host,
        "hostaddr": ip,
        "port": params.port,
        "dbname": params.database,
        "user": params.username,
        "password": params.password,
        "sslmode": params.ssl_mode,
        "connect_timeout": settings.db_connect_timeout_seconds,
        "application_name": "querywise",
        "options": SESSION_OPTIONS,
        "autocommit": True,
    }
    if params.ssl_mode in ("verify-ca", "verify-full"):
        kwargs["sslrootcert"] = "system"  # trust the operating system's CA bundle
    return psycopg.connect(**kwargs)


def classify_error(exc: BaseException) -> str:
    sqlstate = getattr(exc, "sqlstate", None)
    message = str(exc).lower()
    if sqlstate in ("28P01", "28000") or "password authentication failed" in message:
        return "auth_failed"
    if sqlstate == "3D000" or ("database" in message and "does not exist" in message):
        return "database_not_found"
    if "pg_hba.conf" in message:
        return "access_denied"
    if "ssl" in message or "tls" in message or "certificate" in message:
        return "ssl_failed"
    if "timeout expired" in message or "timed out" in message:
        return "connection_timeout"
    if "refused" in message:
        return "connection_refused"
    return "connection_failed"


def _inspect(conn: psycopg.Connection) -> CheckResult:
    row = conn.execute(PRIVILEGE_SQL).fetchone()
    version = str(conn.execute("SHOW server_version").fetchone()[0])
    version_num = int(conn.execute("SHOW server_version_num").fetchone()[0])

    is_super, can_create_role, can_create_db, can_create_in_db, table_count, writable = (
        (bool(row[0]), bool(row[1]), bool(row[2]), bool(row[3]), int(row[4]), int(row[5]))
        if row
        else (False, False, False, False, 0, 0)
    )

    warnings: list[str] = []
    if is_super:
        warnings.append(
            "This role is a superuser. Use a dedicated read-only role so a mistake can never modify data."
        )
    elif writable > 0:
        warnings.append(
            f"This role can modify {writable} table(s). QueryWise only runs read-only queries, "
            "but a read-only role is strongly recommended."
        )
    if not is_super and (can_create_role or can_create_db or can_create_in_db):
        warnings.append("This role can create databases, roles or objects. A read-only role is recommended.")
    if table_count == 0:
        warnings.append(
            "No accessible tables were found. Check that this role has SELECT privileges on the schemas you want to query."
        )
    if version_num < 120000:
        warnings.append(f"PostgreSQL {version} is older than version 12, which QueryWise is designed for.")

    read_only = not (is_super or writable > 0 or can_create_role or can_create_db or can_create_in_db)
    return CheckResult(
        ok=True,
        code="ok",
        message="Connection successful.",
        server_version=version,
        read_only=read_only,
        warnings=warnings,
    )


def check_connection(params: TargetParams, policy: NetworkPolicy | None = None) -> CheckResult:
    """Never raises: failures are returned as a sanitized CheckResult."""
    started = time.perf_counter()
    try:
        ip = resolve_and_validate(params.host, params.port, policy)
    except NetworkPolicyError as exc:
        return CheckResult(False, exc.code, exc.message)

    try:
        with _connect(params, ip) as conn:
            result = _inspect(conn)
    except psycopg.Error as exc:
        code = classify_error(exc)
        # Log the category only: the raw driver message can contain host and user details.
        logger.warning(
            "Target connection check failed",
            extra={"extra_fields": {"code": code, "sqlstate": getattr(exc, "sqlstate", None), "error_type": type(exc).__name__}},
        )
        return CheckResult(False, code, FAILURE_MESSAGES[code])
    except Exception:
        logger.exception("Unexpected error during connection check")
        return CheckResult(False, "connection_failed", FAILURE_MESSAGES["connection_failed"])

    result.latency_ms = round((time.perf_counter() - started) * 1000)
    return result