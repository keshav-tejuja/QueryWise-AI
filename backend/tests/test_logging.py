import json
import logging

from app.core.logging import JsonFormatter, redact


def test_redacts_password_in_connection_url():
    text = redact("failed: postgresql+psycopg://alice:hunter2@db:5432/app")
    assert "hunter2" not in text
    assert "alice" in text


def test_redacts_key_value_secrets():
    text = redact("password=hunter2 token: abc123 Authorization: Bearer xyz789")
    assert "hunter2" not in text
    assert "abc123" not in text
    assert "xyz789" not in text


def test_does_not_over_redact_similar_names():
    assert redact("access_token_minutes=15") == "access_token_minutes=15"


def test_json_formatter_outputs_valid_redacted_json():
    record = logging.LogRecord(
        "test", logging.INFO, __file__, 1, "connecting with password=%s", ("hunter2",), None
    )
    parsed = json.loads(JsonFormatter().format(record))
    assert parsed["level"] == "INFO"
    assert "hunter2" not in parsed["message"]
    assert "request_id" in parsed