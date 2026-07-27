# -*- coding: utf-8 -*-
"""Structured logging - readable, level-filtered logs (text or JSON) for real apps.

When your app runs somewhere you can't see, logs are your eyes. larzlog is a small
structured logger: levels you can filter, key=value context fields, output as
human-readable text or machine-readable JSON, and ``bind`` to attach context (like
a request id) to every line. Everything is injectable (output, clock) so it's easy
to test. Pure Python, zero dependencies.

    from larzlog import Logger

    log = Logger("api", level="INFO")
    log.info("user signed up", user_id=42, plan="pro")
    # INFO api: user signed up user_id=42 plan=pro

    req = log.bind(request_id="abc123")   # context on every line
    req.warning("slow response", ms=812)
"""

import sys

__all__ = ["Logger", "get_logger", "LEVELS"]

LEVELS = {"DEBUG": 10, "INFO": 20, "WARNING": 30, "ERROR": 40, "CRITICAL": 50}


def _fmt_value(v):
    s = str(v)
    return '"%s"' % s if (" " in s or s == "") else s


class Logger(object):
    """A small structured logger. Filter by ``level``; ``bind`` adds context."""

    def __init__(self, name="app", level="INFO", output=None, json=False,
                 timestamp=False, clock=None, context=None):
        self.name = name
        self.level = LEVELS[level.upper()] if isinstance(level, str) else level
        self.output = output if output is not None else sys.stderr
        self.json = json
        self.timestamp = timestamp
        self.clock = clock
        self.context = dict(context or {})

    def bind(self, **fields):
        """Return a child logger carrying extra context fields on every line."""
        merged = dict(self.context)
        merged.update(fields)
        return Logger(self.name, self.level, self.output, self.json,
                      self.timestamp, self.clock, merged)

    def _ts(self):
        if self.clock is not None:
            return self.clock()
        import time
        return "%.3f" % time.time()

    def _emit(self, level_name, message, fields):
        if LEVELS[level_name] < self.level:
            return None
        data = dict(self.context)
        data.update(fields)
        if self.json:
            import json as _json
            record = {"level": level_name, "logger": self.name, "message": message}
            if self.timestamp:
                record["ts"] = self._ts()
            record.update(data)
            line = _json.dumps(record)
        else:
            parts = []
            if self.timestamp:
                parts.append(str(self._ts()))
            parts.append(level_name)
            parts.append(self.name + ":")
            parts.append(message)
            for k, v in data.items():
                parts.append("%s=%s" % (k, _fmt_value(v)))
            line = " ".join(parts)
        self.output.write(line + "\n")
        return line

    def debug(self, message, **fields):
        return self._emit("DEBUG", message, fields)

    def info(self, message, **fields):
        return self._emit("INFO", message, fields)

    def warning(self, message, **fields):
        return self._emit("WARNING", message, fields)

    def error(self, message, **fields):
        return self._emit("ERROR", message, fields)

    def critical(self, message, **fields):
        return self._emit("CRITICAL", message, fields)


def get_logger(name="app", **kwargs):
    """Convenience factory for a :class:`Logger`."""
    return Logger(name, **kwargs)
