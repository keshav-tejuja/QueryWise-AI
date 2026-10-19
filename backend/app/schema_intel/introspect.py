from collections import defaultdict

import psycopg

from app.schema_intel.models import ColumnInfo, ForeignKey, IndexInfo, SchemaData, TableInfo

MAX_TABLES = 500

# Only objects the connected role may SELECT are listed: the LLM never hears about anything else.
TABLES_SQL = """
SELECT c.oid::bigint, n.nspname, c.relname, c.relkind, c.reltuples::bigint,
       obj_description(c.oid, 'pg_class')
FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
WHERE c.relkind IN ('r', 'p', 'v', 'm')
  AND n.nspname NOT IN ('pg_catalog', 'information_schema')
  AND n.nspname NOT LIKE 'pg\\_%'
  AND NOT c.relispartition
  AND has_table_privilege(c.oid, 'SELECT')
ORDER BY n.nspname, c.relname
"""

COLUMNS_SQL = """
SELECT a.attrelid::bigint, a.attnum, a.attname, format_type(a.atttypid, a.atttypmod),
       a.attnotnull, col_description(a.attrelid, a.attnum)
FROM pg_attribute a
WHERE a.attrelid::bigint = ANY(%s::bigint[]) AND a.attnum > 0 AND NOT a.attisdropped
ORDER BY a.attrelid, a.attnum
"""

CONSTRAINTS_SQL = """
SELECT con.conrelid::bigint, con.conname, con.contype, con.conkey, con.confrelid::bigint, con.confkey
FROM pg_constraint con
WHERE con.conrelid::bigint = ANY(%s::bigint[]) AND con.contype IN ('p', 'u', 'f')
ORDER BY con.conrelid, con.conname
"""

INDEXES_SQL = """
SELECT i.indrelid::bigint, ic.relname, i.indisunique, i.indisprimary,
       string_to_array(i.indkey::text, ' ')::int2[]
FROM pg_index i JOIN pg_class ic ON ic.oid = i.indexrelid
WHERE i.indrelid::bigint = ANY(%s::bigint[]) AND i.indisvalid
ORDER BY i.indrelid, ic.relname
"""

_KINDS = {"r": "table", "p": "table", "v": "view", "m": "materialized_view"}


def introspect(conn: psycopg.Connection) -> SchemaData:
    rows = conn.execute(TABLES_SQL).fetchall()
    truncated = len(rows) > MAX_TABLES
    rows = rows[:MAX_TABLES]
    if not rows:
        return SchemaData(tables=[], truncated=False)
    oids = [row[0] for row in rows]

    columns: dict[int, list[ColumnInfo]] = defaultdict(list)
    attnum_names: dict[int, dict[int, str]] = defaultdict(dict)
    for oid, attnum, name, data_type, not_null, comment in conn.execute(COLUMNS_SQL, (oids,)).fetchall():
        columns[oid].append(
            ColumnInfo(name=name, data_type=data_type, nullable=not not_null, position=attnum, comment=comment)
        )
        attnum_names[oid][attnum] = name

    by_oid = {row[0]: (row[1], row[2]) for row in rows}  # oid -> (schema, table)
    primary_keys: dict[int, list[str]] = defaultdict(list)
    uniques: dict[int, list[list[str]]] = defaultdict(list)
    foreign_keys: dict[int, list[ForeignKey]] = defaultdict(list)
    for oid, name, contype, conkey, ref_oid, confkey in conn.execute(CONSTRAINTS_SQL, (oids,)).fetchall():
        local = [attnum_names[oid][n] for n in conkey if n in attnum_names[oid]]
        if contype == "p":
            primary_keys[oid] = local
        elif contype == "u":
            uniques[oid].append(local)
        elif contype == "f" and ref_oid in by_oid:  # skip references to tables we cannot see
            ref_schema, ref_table = by_oid[ref_oid]
            referenced = [attnum_names[ref_oid][n] for n in confkey if n in attnum_names[ref_oid]]
            foreign_keys[oid].append(
                ForeignKey(
                    name=name,
                    columns=local,
                    referenced_schema=ref_schema,
                    referenced_table=ref_table,
                    referenced_columns=referenced,
                )
            )

    indexes: dict[int, list[IndexInfo]] = defaultdict(list)
    for oid, name, unique, primary, key_attnums in conn.execute(INDEXES_SQL, (oids,)).fetchall():
        names = [attnum_names[oid][n] for n in key_attnums if n in attnum_names[oid]]  # expression columns are skipped
        indexes[oid].append(IndexInfo(name=name, columns=names, unique=unique, primary=primary))

    tables: list[TableInfo] = []
    for oid, schema_name, name, relkind, reltuples, comment in rows:
        pk = set(primary_keys[oid])
        fk_columns = {c for fk in foreign_keys[oid] for c in fk.columns}
        table_columns = [
            c.model_copy(update={"is_primary_key": c.name in pk, "is_foreign_key": c.name in fk_columns})
            for c in columns[oid]
        ]
        kind = _KINDS[relkind]
        tables.append(
            TableInfo(
                schema_name=schema_name,
                name=name,
                kind=kind,
                comment=comment,
                estimated_rows=reltuples if kind != "view" and reltuples >= 0 else None,
                columns=table_columns,
                primary_key=primary_keys[oid],
                unique_constraints=uniques[oid],
                foreign_keys=foreign_keys[oid],
                indexes=indexes[oid],
            )
        )
    return SchemaData(tables=tables, truncated=truncated)