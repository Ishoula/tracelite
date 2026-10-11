# TraceLite

TraceLite is a small, dependency-free Python package for recording structured log events and exceptions.

## Features

- JSON Lines logs (one JSON object per line)
- Console and file output
- Exception type, message, and traceback capture
- Extra context such as request IDs
- `@trace_errors` decorator that logs and re-raises exceptions
- Basic secret redaction for common sensitive field names

## Installation

Install TraceLite from PyPI:

```bash
python -m pip install tracelight-logger
```

## Quick Start

```python
from tracelite import TraceLite, trace_errors

logger = TraceLite(log_file="app.log")

logger.info(
    "Application started",
    context={"service": "demo"}
)

try:
    10 / 0
except ZeroDivisionError as exc:
    logger.exception(
        "Calculation failed",
        exc,
        context={"operation": "divide"}
    )
```

## Using the `@trace_errors` Decorator

The decorator automatically logs exceptions and re-raises them so your application can handle them.

```python
from tracelite import TraceLite, trace_errors

logger = TraceLite(log_file="app.log")

@trace_errors(logger)
def calculate():
    return 10 / 0

calculate()  # Logs the exception, then raises it again.
```

## Development Setup

To contribute to TraceLite or run its tests locally, clone the repository and install it in development mode:

```bash
python -m venv .venv
```

**Windows PowerShell:**

```powershell
.venv\Scripts\Activate.ps1
```

**macOS/Linux:**

```bash
source .venv/bin/activate
```

Install the package with its development dependencies:

```bash
python -m pip install -e ".[dev]"
```

Run the tests:

```bash
pytest
```

## Security Notes

- Do not put passwords, access tokens, personal data, or other secrets into log messages.
- TraceLite redacts common sensitive keys in context dictionaries, but automatic redaction is not perfect.
- This first version writes to a local file and/or the console. It does not send data to a remote service.

## Package Information

- **PyPI package:** `tracelight-logger`
- **Python import:** `tracelite`
- **License:** MIT
