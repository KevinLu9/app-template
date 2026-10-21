"""Logging setup: one line per record, request ID attached, credentials redacted."""

import logging
import re

from flask import g, has_request_context

# Databricks PATs (dapi...) and OAuth/JWT access tokens (eyJ...).
_SECRET_PATTERNS = [
    re.compile(r"dapi[0-9a-f]{32}(-\d+)?"),
    re.compile(r"eyJ[\w-]+\.[\w-]+\.[\w-]+"),
]


def redact(text: str) -> str:
    for pattern in _SECRET_PATTERNS:
        text = pattern.sub("***", text)
    return text


class RedactingFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        record.msg = redact(record.getMessage())
        record.args = None
        record.request_id = g.get("request_id", "-") if has_request_context() else "-"
        return True


def configure_logging(level: str) -> None:
    handler = logging.StreamHandler()
    handler.addFilter(RedactingFilter())
    handler.setFormatter(
        logging.Formatter("%(asctime)s %(levelname)s [%(request_id)s] %(name)s: %(message)s")
    )
    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level.upper())
