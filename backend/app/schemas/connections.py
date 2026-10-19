import ipaddress
import re
import uuid
from datetime import datetime
from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, StringConstraints

SslMode = Literal["disable", "prefer", "require", "verify-ca", "verify-full"]

_HOSTNAME_RE = re.compile(r"^[A-Za-z0-9_]([A-Za-z0-9_.-]{0,251}[A-Za-z0-9_])?$")


def _validate_host(value: str) -> str:
    value = value.strip().lower().rstrip(".")
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    if not value:
        raise ValueError("Host is required.")
    try:
        ipaddress.ip_address(value)
        return value
    except ValueError:
        pass
    if not _HOSTNAME_RE.match(value):
        raise ValueError("Host contains invalid characters.")
    return value


Host = Annotated[str, StringConstraints(max_length=255), AfterValidator(_validate_host)]
ConnectionName = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]


class ConnectionTestRequest(BaseModel):
    host: Host
    port: int = Field(5432, ge=1, le=65535)
    database: str = Field(min_length=1, max_length=128)
    username: str = Field(min_length=1, max_length=128)
    password: str = Field(min_length=1, max_length=256)
    ssl_mode: SslMode = "prefer"


class ConnectionCreate(ConnectionTestRequest):
    name: ConnectionName


class ConnectionUpdate(BaseModel):
    """Partial update: omitted/null fields are left unchanged."""

    name: ConnectionName | None = None
    host: Host | None = None
    port: int | None = Field(None, ge=1, le=65535)
    database: str | None = Field(None, min_length=1, max_length=128)
    username: str | None = Field(None, min_length=1, max_length=128)
    password: str | None = Field(None, min_length=1, max_length=256)
    ssl_mode: SslMode | None = None


class ConnectionOut(BaseModel):
    """Note: there is deliberately no password field, encrypted or otherwise."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    name: str
    host: str
    port: int
    database: str
    username: str
    ssl_mode: str
    status: str
    last_tested_at: datetime | None
    created_at: datetime


class ConnectionCheckOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    ok: bool
    code: str
    message: str
    latency_ms: int | None = None
    server_version: str | None = None
    read_only: bool | None = None
    warnings: list[str] = Field(default_factory=list)


class ConnectionWithCheck(BaseModel):
    connection: ConnectionOut
    check: ConnectionCheckOut | None = None