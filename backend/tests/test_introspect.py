import uuid

import psycopg
import pytest

from app.connections.pool_manager import PoolManager
from app.connections.tester import TargetParams
from app.schema_intel.introspect import introspect
from app.security.network_guard import NetworkPolicy
from tests.helpers import (
    ADMIN_PASSWORD, ADMIN_USER, READONLY_PASSWORD, READONLY_USER, SAMPLE_DB, SAMPLE_HOST, SAMPLE_PORT,
)

pytestmark = [pytest.mark.integration, pytest.mark.usefixtures("sample_db_reachable")]

POLICY = NetworkPolicy(allowed_hosts=frozenset({SAMPLE_HOST}))
PARAMS = TargetParams(
    host=SAMPLE_HOST, port=SAMPLE_PORT, database=SAMPLE_DB,
    username=READONLY_USER, password=READONLY_PASSWORD, ssl_mode="prefer",
)


def _schema():
    manager = PoolManager()
    try:
        with manager.connection(uuid.uuid4(), PARAMS, POLICY) as conn:
            return {t.qualified_name: t for t in introspect(conn).tables}
    finally:
        manager.close_all()


def _admin():
    return psycopg.connect(
        host=SAMPLE_HOST, port=SAMPLE_PORT, dbname=SAMPLE_DB, user=ADMIN_USER, password=ADMIN_PASSWORD, autocommit=True
    )


def test_tables_columns_and_types():
    tables = _schema()
    assert {"public.customers", "public.orders"} <= set(tables)
    orders = {c.name: c for c in tables["public.orders"].columns}
    assert orders["total_amount"].data_type == "numeric(12,2)" and orders["total_amount"].nullable is False
    assert orders["id"].is_primary_key and orders["customer_id"].is_foreign_key
    assert orders["total_amount"].comment == "Order total before any refunds."


def test_keys_relationships_and_indexes():
    tables = _schema()
    assert tables["public.orders"].primary_key == ["id"]
    [foreign_key] = tables["public.orders"].foreign_keys
    assert (foreign_key.columns, foreign_key.referenced_schema, foreign_key.referenced_table,
            foreign_key.referenced_columns) == (["customer_id"], "public", "customers", ["id"])
    customers = tables["public.customers"]
    assert customers.unique_constraints == [["email"]]
    assert any(i.primary for i in customers.indexes) and any(i.unique and i.columns == ["email"] for i in customers.indexes)
    assert customers.comment and customers.comment.startswith("People")
    assert customers.estimated_rows is None or customers.estimated_rows >= 0


def test_objects_the_role_cannot_select_are_invisible():
    with _admin() as admin:
        admin.execute("CREATE SCHEMA qw_hidden")
        admin.execute("CREATE TABLE qw_hidden.secrets (id int)")
        try:
            assert not any(name.startswith("qw_hidden.") for name in _schema())
        finally:
            admin.execute("DROP SCHEMA qw_hidden CASCADE")