import contextvars
import json
import logging
import re
import sys
from datetime import datetime, timezone

request_id_ctx: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="-")

# postgresql://user:PASSWORD@host  ->  postgresql://user:***@host
_URL_PASSWORD = re.compile(r"(://[^:/\s@]+:)[^@\s]+(@)")
# password=..., token: ..., Authorization: Bearer ...
_KV_SECRET = re.compile(
    r"(?i)\b(password|passwd|secret|token|api[_-]?key|authorization)\b(\s*[=:]\s*)((?:Bearer\s+)?[^\s,;&]+)"
)


def redact(text: str) -> str:
    text = _URL_PASSWORD.sub(r"\1***\2", text)
    return _KV_SECRET.sub(r"\1\2***", text)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": redact(record.getMessage()),
            "request_id": request_id_ctx.get(),
        }
        extra = getattr(record, "extra_fields", None)
        if extra:
            payload.update(extra)
        if record.exc_info:
            payload["exception"] = redact(self.formatException(record.exc_info))
        return json.dumps(payload, default=str)


def setup_logging(level: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())

    # Route uvicorn's own logs through our formatter; we log requests ourselves.
    for name in ("uvicorn", "uvicorn.error"):
        lg = logging.getLogger(name)
        lg.handlers.clear()
        lg.propagate = True
    logging.getLogger("uvicorn.access").disabled = True