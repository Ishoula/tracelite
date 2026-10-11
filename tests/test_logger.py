import json

import pytest

from tracelite import TraceLite, trace_errors


def test_info_writes_json_line(tmp_path):
    log_path = tmp_path / "logs" / "app.jsonl"
    logger = TraceLite(log_file=log_path, console=False)
    logger.info("Started", context={"request_id": "abc-123"})

    event = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert event["level"] == "INFO"
    assert event["message"] == "Started"
    assert event["context"]["request_id"] == "abc-123"
    assert "timestamp" in event


def test_sensitive_context_is_redacted(tmp_path):
    log_path = tmp_path / "app.jsonl"
    logger = TraceLite(log_file=log_path, console=False)
    logger.info("Login attempt", context={"password": "dont-log-me", "user_id": 7})

    event = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert event["context"]["password"] == "[REDACTED]"
    assert event["context"]["user_id"] == 7
    assert "dont-log-me" not in log_path.read_text(encoding="utf-8")


def test_exception_records_traceback(tmp_path):
    log_path = tmp_path / "app.jsonl"
    logger = TraceLite(log_file=log_path, console=False)

    try:
        1 / 0
    except ZeroDivisionError as exc:
        logger.exception("Math failed", exc)

    event = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert event["exception"]["type"] == "ZeroDivisionError"
    assert "ZeroDivisionError" in event["exception"]["traceback"]


def test_decorator_logs_and_reraises(tmp_path):
    log_path = tmp_path / "app.jsonl"
    logger = TraceLite(log_file=log_path, console=False)

    @trace_errors(logger, context={"operation": "divide"})
    def fail():
        raise ValueError("bad input")

    with pytest.raises(ValueError, match="bad input"):
        fail()

    event = json.loads(log_path.read_text(encoding="utf-8").strip())
    assert event["exception"]["type"] == "ValueError"
    assert event["context"]["operation"] == "divide"


def test_requires_some_output():
    with pytest.raises(ValueError):
        TraceLite(console=False)


def test_invalid_level_is_rejected():
    with pytest.raises(ValueError):
        TraceLite(level="LOUD")
