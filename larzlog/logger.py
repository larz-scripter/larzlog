"""Structured, context-aware logging with secrets redacted by default.

Every log call is a structured *event* — a name plus key/value fields — not a
pre-formatted string. That means your logs are queryable data, and it's what lets
larzlog redact secrets reliably (see :mod:`larzlog.redact`).

    from larzlog import get_logger

    log = get_logger("billing")
    log.info("charge_succeeded", user_id=42, amount_cents=1999)

    # context flows to every child log line
    req = log.bind(request_id="r-abc")
    req.warning("slow_db", ms=1200)

    # secrets are redacted automatically — this does NOT leak the key
    log.info("api_call", api_key="sk_live_deadbeefdeadbeef1234", ok=True)

Records render as one JSON object per line (great for ingestion) or as a
readable, optionally-coloured console line. Output is thread-safe.
"""

import json
import sys
import threading
import time
import traceback

from .redact import Redactor

LEVELS = {"debug": 10, "info": 20, "warning": 30, "error": 40, "critical": 50}
_COLORS = {"debug": "\033[90m", "info": "\033[36m", "warning": "\033[33m",
           "error": "\033[31m", "critical": "\033[41m\033[97m"}
_RESET = "\033[0m"


class Config(object):
    """Shared output configuration for all loggers created from it."""

    def __init__(self, level="info", renderer="json", stream=None,
                 redactor=None, colors=None, clock=None, utc=True):
        self.min_level = LEVELS[level] if isinstance(level, str) else level
        self.renderer = renderer                # "json" | "console"
        self.stream = stream or sys.stderr
        self.redactor = redactor or Redactor()
        self.colors = self.stream.isatty() if colors is None else colors
        self.clock = clock or time.time
        self.utc = utc
        self._lock = threading.Lock()

    def set_level(self, level):
        self.min_level = LEVELS[level] if isinstance(level, str) else level

    def _timestamp(self):
        t = self.clock()
        lt = time.gmtime(t) if self.utc else time.localtime(t)
        return time.strftime("%Y-%m-%dT%H:%M:%S", lt) + (".%03dZ" % ((t % 1) * 1000)
                                                         if self.utc else "")

    def emit(self, record):
        record = self.redactor.redact(record)
        line = self._render(record)
        with self._lock:
            self.stream.write(line + "\n")
            self.stream.flush()

    def _render(self, record):
        if self.renderer == "console":
            return self._render_console(record)
        return json.dumps(record, default=str, sort_keys=False)

    def _render_console(self, record):
        level = record.get("level", "info")
        ts = record.get("ts", "")
        event = record.get("event", "")
        extras = " ".join("%s=%s" % (k, _fmt(v)) for k, v in record.items()
                          if k not in ("ts", "level", "event", "logger"))
        head = "%s [%-8s] %s" % (ts, level.upper(), event)
        if self.colors:
            c = _COLORS.get(level, "")
            head = c + head + _RESET
        return head + (("  " + extras) if extras else "")


def _fmt(v):
    if isinstance(v, str) and " " in v:
        return '"%s"' % v
    return v


class Logger(object):
    """A logger bound to a name and an accumulated context. Immutable —
    :meth:`bind` returns a new logger with extra context."""

    def __init__(self, name, config, context=None):
        self.name = name
        self.config = config
        self.context = context or {}

    def bind(self, **fields):
        """Return a child logger that adds ``fields`` to every record."""
        ctx = dict(self.context)
        ctx.update(fields)
        return Logger(self.name, self.config, ctx)

    def _log(self, level, event, fields):
        if LEVELS[level] < self.config.min_level:
            return
        record = {"ts": self.config._timestamp(), "level": level,
                  "logger": self.name, "event": event}
        record.update(self.context)
        record.update(fields)
        self.config.emit(record)

    def debug(self, event, **fields):
        self._log("debug", event, fields)

    def info(self, event, **fields):
        self._log("info", event, fields)

    def warning(self, event, **fields):
        self._log("warning", event, fields)

    warn = warning

    def error(self, event, **fields):
        self._log("error", event, fields)

    def critical(self, event, **fields):
        self._log("critical", event, fields)

    def exception(self, event, **fields):
        """Log at error level, attaching the current exception traceback."""
        fields.setdefault("traceback", traceback.format_exc().rstrip())
        self._log("error", event, fields)


# -- module-level default config + factory --------------------------------

_default_config = Config()


def configure(level=None, renderer=None, stream=None, redact=None,
              colors=None, utc=None):
    """Reconfigure the global default used by :func:`get_logger`. ``redact`` is a
    list of extra sensitive key fragments (defaults are always kept)."""
    global _default_config
    kw = {}
    if level is not None:
        kw["level"] = level
    if renderer is not None:
        kw["renderer"] = renderer
    if stream is not None:
        kw["stream"] = stream
    if colors is not None:
        kw["colors"] = colors
    if utc is not None:
        kw["utc"] = utc
    if redact is not None:
        kw["redactor"] = Redactor(extra_keys=redact)
    _default_config = Config(
        level=kw.get("level", "info"),
        renderer=kw.get("renderer", _default_config.renderer),
        stream=kw.get("stream", _default_config.stream),
        redactor=kw.get("redactor", _default_config.redactor),
        colors=kw.get("colors", None),
        utc=kw.get("utc", _default_config.utc),
    )
    return _default_config


def get_logger(name="app", config=None):
    """Get a :class:`Logger`. Uses the global config unless one is passed."""
    return Logger(name, config or _default_config)
