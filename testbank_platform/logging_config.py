"""
Logging helpers for testbank_platform.

Provides a JSON log formatter for production / log-aggregator consumption
(GCP Cloud Logging, Datadog, Loki, etc.) and a Sentry wiring helper that
only initializes when SENTRY_DSN is set, so dev environments stay quiet.

Design notes:
- JSONFormatter is dependency-free (no python-json-logger) to keep the
  requirements surface small. It's intentionally minimal.
- Extra attributes attached to a LogRecord via `logger.info("...", extra={...})`
  are serialized into the JSON output.
- Sentry is opt-in: no DSN → no SDK call, no network chatter.
"""

from __future__ import annotations

import json
import logging
import time
from typing import Any

# Standard LogRecord attributes we shouldn't re-serialize — everything else
# attached via `extra=` gets included.
_STANDARD_LOGRECORD_ATTRS = frozenset({
    'args', 'asctime', 'created', 'exc_info', 'exc_text', 'filename',
    'funcName', 'levelname', 'levelno', 'lineno', 'message', 'module',
    'msecs', 'msg', 'name', 'pathname', 'process', 'processName',
    'relativeCreated', 'stack_info', 'thread', 'threadName', 'taskName',
})


class JSONFormatter(logging.Formatter):
    """Emit each log record as a single-line JSON document."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            'timestamp': time.strftime(
                '%Y-%m-%dT%H:%M:%S', time.gmtime(record.created)
            ) + f'.{int(record.msecs):03d}Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'line': record.lineno,
        }

        if record.exc_info:
            payload['exception'] = self.formatException(record.exc_info)
        if record.stack_info:
            payload['stack'] = record.stack_info

        # Pull anything the caller attached via `extra={...}`
        for key, value in record.__dict__.items():
            if key in _STANDARD_LOGRECORD_ATTRS or key.startswith('_'):
                continue
            try:
                json.dumps(value)  # serializability probe
                payload[key] = value
            except (TypeError, ValueError):
                payload[key] = repr(value)

        return json.dumps(payload, default=str)


def init_sentry(dsn: str, *, environment: str, release: str | None = None,
                traces_sample_rate: float = 0.1) -> None:
    """Initialize Sentry SDK with the Django integration.

    Called from settings.py only when SENTRY_DSN is set. Keeping the import
    lazy keeps cold-start fast when Sentry isn't configured.
    """
    import sentry_sdk
    from sentry_sdk.integrations.django import DjangoIntegration
    from sentry_sdk.integrations.logging import LoggingIntegration

    sentry_sdk.init(
        dsn=dsn,
        environment=environment,
        release=release,
        integrations=[
            DjangoIntegration(
                transaction_style='url',
                middleware_spans=True,
                signals_spans=False,
            ),
            LoggingIntegration(
                level=logging.INFO,       # breadcrumbs at INFO+
                event_level=logging.ERROR,  # events at ERROR+
            ),
        ],
        # Performance tracing is off by default; flip on in prod if needed.
        traces_sample_rate=traces_sample_rate,
        send_default_pii=False,
    )
