"""Logging setup that avoids leaking secrets or user data."""

from __future__ import annotations

import logging
import re

_SECRET_PATTERNS = [
    re.compile(r"(key=)[^&\s]+", re.IGNORECASE),
    re.compile(r"(Bearer\s+)[A-Za-z0-9._\-]+"),
    re.compile(r"(postgres(?:ql)?://[^:]+:)[^@]+(@)"),
    re.compile(r"(AIza)[0-9A-Za-z\-_]{20,}"),
]


class RedactingFilter(logging.Filter):
    """Masks API keys, bearer tokens and DB passwords that may end up in log messages."""

    def filter(self, record: logging.LogRecord) -> bool:
        message = record.getMessage()
        for pattern in _SECRET_PATTERNS:
            message = pattern.sub(lambda m: m.group(1) + "***" + (m.group(2) if m.lastindex == 2 else ""), message)
        record.msg = message
        record.args = None
        return True


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("%(asctime)s %(levelname)s %(name)s: %(message)s"))
    handler.addFilter(RedactingFilter())
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
    # Third-party HTTP clients log full URLs (which may contain keys) at INFO.
    for noisy in ("httpx", "httpcore", "google_genai"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
