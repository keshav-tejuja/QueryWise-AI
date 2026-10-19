import hashlib
import json
from typing import Literal

from pydantic import BaseModel, Field, computed_field

TableKind = Literal["table", "view", "materialized_view"]


class ColumnInfo(BaseModel):
    name: str
    data_type: str
    nullable: bool
    position: int
    comment: str | None = None
    is_primary_key: bool = False
    is_foreign_key: bool = False


class ForeignKey(BaseModel):
    name: str
    columns: list[str]
    referenced_schema: str
    referenced_table: str
    referenced_columns: list[str]


class IndexInfo(BaseModel):
    name: str
    columns: list[str]
    unique: bool
    primary: bool


class TableInfo(BaseModel):
    schema_name: str
    name: str
    kind: TableKind = "table"
    comment: str | None = None
    estimated_rows: int | None = None
    columns: list[ColumnInfo] = Field(default_factory=list)
    primary_key: list[str] = Field(default_factory=list)
    unique_constraints: list[list[str]] = Field(default_factory=list)
    foreign_keys: list[ForeignKey] = Field(default_factory=list)
    indexes: list[IndexInfo] = Field(default_factory=list)

    @computed_field  # type: ignore[prop-decorator]
    @property
    def qualified_name(self) -> str:
        return f"{self.schema_name}.{self.name}"


class SchemaData(BaseModel):
    tables: list[TableInfo] = Field(default_factory=list)
    truncated: bool = False  # True when the database has more tables than we introspect


class SchemaDiff(BaseModel):
    added_tables: list[str] = Field(default_factory=list)
    removed_tables: list[str] = Field(default_factory=list)
    changed_tables: list[str] = Field(default_factory=list)


def table_signature(table: TableInfo) -> str:
    # estimated_rows is excluded: it drifts constantly and is not a schema change.
    return json.dumps(
        table.model_dump(mode="json", exclude={"estimated_rows"}), sort_keys=True, separators=(",", ":")
    )


def compute_schema_hash(data: SchemaData) -> str:
    digest = hashlib.sha256()
    digest.update(b"truncated" if data.truncated else b"complete")
    for table in sorted(data.tables, key=lambda t: t.qualified_name):
        digest.update(table_signature(table).encode())
    return digest.hexdigest()


def diff_schemas(old: SchemaData, new: SchemaData) -> SchemaDiff:
    old_map = {t.qualified_name: table_signature(t) for t in old.tables}
    new_map = {t.qualified_name: table_signature(t) for t in new.tables}
    return SchemaDiff(
        added_tables=sorted(new_map.keys() - old_map.keys()),
        removed_tables=sorted(old_map.keys() - new_map.keys()),
        changed_tables=sorted(n for n in new_map.keys() & old_map.keys() if new_map[n] != old_map[n]),
    )


# ---- Retrieval result models (also used as API responses) ----


class RetrievedTable(BaseModel):
    qualified_name: str
    role: Literal["match", "bridge"]
    score: float
    reasons: list[str] = Field(default_factory=list)
    columns: list[str] = Field(default_factory=list)


class JoinEdge(BaseModel):
    from_table: str
    from_columns: list[str]
    to_table: str
    to_columns: list[str]
    constraint: str


class JoinStep(BaseModel):
    from_table: str
    to_table: str
    edges: list[JoinEdge]  # more than one edge = several foreign keys link these tables (ambiguous)


class JoinPath(BaseModel):
    tables: list[str]
    steps: list[JoinStep]
    ambiguous: bool = False


class RetrievalResult(BaseModel):
    question: str
    terms: list[str]
    tables: list[RetrievedTable]
    join_paths: list[JoinPath]
    unconnected_pairs: list[list[str]]
    unmatched_terms: list[str]
    warnings: list[str]