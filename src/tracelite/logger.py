
"""Structured, lightweight logging utilities for Python applications."""

from __future__ import annotations

import json
import logging
import traceback
from datetime import datetime, timezone
from functools import wraps
from pathlib import Path
from typing import Any, Callable, TypeVar

F = TypeVar("F", bound=Callable[..., Any])

_LEVELS = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}

_SENSITIVE_KEYS = {
    "password", "passwd", "secret", "token", "access_token",
    "refresh_token", "authorization", "api_key", "apikey",
}


def _safe_context(context: dict[str, Any] | None) -> dict[str, Any]:
    """Redact common secret-like fields from a shallow context dictionary."""
    safe: dict[str, Any] = {}

    for key, value in (context or {}).items():
        if key.lower() in _SENSITIVE_KEYS:
            safe[key] = "[REDACTED]"
        elif isinstance(value, (str, int, float, bool)) or value is None:
            safe[key] = value
        else:
            safe[key] = repr(value)

    return safe


class TraceLite:
    """Write structured JSON or readable console log events."""

    def __init__(
        self,
        log_file: str | Path | None = None,
        *,
        console: bool = True,
        level: str = "INFO",
        format: str = "console",
    ) -> None:
        level_name = level.upper()

        if level_name not in _LEVELS:
            raise ValueError(f"Unsupported log level: {level!r}")

        if format not in {"console", "json"}:
            raise ValueError(
                "Unsupported format. Choose 'console' or 'json'."
            )

        if not console and log_file is None:
            raise ValueError("Enable console output or provide log_file.")

        self.level = getattr(logging, level_name)
        self.log_file = Path(log_file) if log_file is not None else None
        self.console = console
        self.format = format

        if self.log_file is not None:
            self.log_file.parent.mkdir(parents=True, exist_ok=True)

    def _write(self, event: dict[str, Any], severity: str) -> None:
        if getattr(logging, severity) < self.level:
            return

        if self.format == "json":
            line = json.dumps(event, ensure_ascii=False, default=str)
        else:
            timestamp = event["timestamp"]
            level = event["level"]
            message = event["message"]

            line = f"{timestamp} | {level:<8} | {message}"

            context = event.get("context", {})
            if context:
                line += f" | context={json.dumps(context, ensure_ascii=False)}"

            exception = event.get("exception")
            if exception:
                line += (
                    f"\n  {exception['type']}: "
                    f"{exception['message']}"
                )
                line += f"\n{exception['traceback']}"

        if self.console:
            print(line)

        if self.log_file is not None:
            with self.log_file.open("a", encoding="utf-8") as stream:
                stream.write(line + "\n")

    def log(
        self,
        level: str,
        message: str,
        *,
        context: dict[str, Any] | None = None,
    ) -> None:
        severity = level.upper()

        if severity not in _LEVELS:
            raise ValueError(f"Unsupported log level: {level!r}")

        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": severity,
            "message": str(message),
            "context": _safe_context(context),
        }

        self._write(event, severity)

    def debug(
        self, message: str, *, context: dict[str, Any] | None = None
    ) -> None:
        self.log("DEBUG", message, context=context)

    def info(
        self, message: str, *, context: dict[str, Any] | None = None
    ) -> None:
        self.log("INFO", message, context=context)

    def warning(
        self, message: str, *, context: dict[str, Any] | None = None
    ) -> None:
        self.log("WARNING", message, context=context)

    def error(
        self, message: str, *, context: dict[str, Any] | None = None
    ) -> None:
        self.log("ERROR", message, context=context)

    def critical(
        self, message: str, *, context: dict[str, Any] | None = None
    ) -> None:
        self.log("CRITICAL", message, context=context)

    def exception(
        self,
        message: str,
        exc: BaseException,
        *,
        context: dict[str, Any] | None = None,
    ) -> None:
        """Record an exception with its type and formatted traceback."""
        event = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": "ERROR",
            "message": str(message),
            "exception": {
                "type": type(exc).__name__,
                "message": str(exc),
                "traceback": "".join(
                    traceback.format_exception(
                        type(exc), exc, exc.__traceback__
                    )
                ),
            },
            "context": _safe_context(context),
        }

        self._write(event, "ERROR")


def trace_errors(
    logger: TraceLite,
    *,
    context: dict[str, Any] | None = None,
) -> Callable[[F], F]:
    """Log function exceptions and re-raise them."""

    def decorator(function: F) -> F:
        @wraps(function)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            try:
                return function(*args, **kwargs)
            except Exception as exc:
                logger.exception(
                    f"Unhandled exception in "
                    f"{function.__module__}.{function.__qualname__}",
                    exc,
                    context=context,
                )
                raise

        return wrapper  # type: ignore[return-value]

    return decorator
