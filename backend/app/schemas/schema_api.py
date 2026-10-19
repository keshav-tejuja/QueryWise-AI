import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from app.schema_intel.models import SchemaDiff, TableInfo


class SchemaOut(BaseModel):
    connection_id: uuid.UUID
    schema_hash: str
    captured_at: datetime
    truncated: bool
    tables: list[TableInfo]


class RefreshOut(BaseModel):
    snapshot: SchemaOut
    changed: bool
    diff: SchemaDiff | None = None


class RetrieveRequest(BaseModel):
    question: Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=1000)]
    max_tables: int = Field(8, ge=1, le=20)