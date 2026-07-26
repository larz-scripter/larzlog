"""larzlog — structured logging that refuses to leak secrets. Pure Python, zero deps.

Structured, context-aware logging where **secrets and PII are redacted
automatically**, before anything is written. Log events as data (a name plus
key/value fields), bind context that flows to every child line, and render as
JSON for machines or a readable line for humans — with no dependency to add.

    from larzlog import get_logger

    log = get_logger("billing")
    log.info("charge", user_id=42, amount_cents=1999)

    req = log.bind(request_id="r-abc")           # context carried forward
    req.warning("slow_db", ms=1200)

    # this line does NOT leak the key — larzlog redacts it
    log.info("api_call", api_key="sk_live_deadbeefdeadbeef1234")

The differentiator: redaction is **on by default and hard to bypass**. It matches
sensitive *field names* (password, token, authorization, card, ssn, …) and
sensitive *value shapes* (credit cards via Luhn, JWTs, secret keys), recursing
through nested payloads — so a log line is never the thing that leaks a secret.

Part of the Larz stack — https://github.com/larz-scripter/larzlog
"""

from .logger import Config, Logger, configure, get_logger
from .redact import DEFAULT_SENSITIVE_KEYS, Redactor

__version__ = "0.1.0"

__all__ = [
    "get_logger", "configure", "Logger", "Config",
    "Redactor", "DEFAULT_SENSITIVE_KEYS", "__version__",
]
