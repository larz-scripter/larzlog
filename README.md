# larzlog

**Structured logging that refuses to leak secrets. Pure Python, zero dependencies.**

Structured, context-aware logging where **secrets and PII are redacted
automatically** — before anything is written. Log events as data, bind context
that flows to every child line, and render as JSON for machines or a readable
line for humans, with no dependency to add.

```python
from larzlog import get_logger

log = get_logger("billing")
log.info("charge", user_id=42, amount_cents=1999)

req = log.bind(request_id="r-abc")           # context carried to every line
req.warning("slow_db", ms=1200)

# this line does NOT leak the key — larzlog redacts it
log.info("api_call", api_key="sk_live_deadbeefdeadbeef1234", ok=True)
```

## What makes it different

Plenty of libraries do structured logging. larzlog's edge is that **redaction is
on by default and hard to bypass** — because the log is exactly where secrets
tend to escape.

- **Redacts by field name** — `password`, `token`, `authorization`, `secret`,
  `card`, `cvv`, `ssn`, `session`, `api_key`, `seed`, `passphrase`, and more.
- **Redacts by value shape** — even in an innocently-named field, it catches
  **credit-card numbers** (validated with Luhn, so it doesn't nuke random
  digits), **JWTs**, and **secret keys** (`sk_live_…`).
- **Recurses** — nested dicts and lists in a payload are scrubbed too.
- **You extend it, you don't disable it** — add extra sensitive keys; the safe
  defaults always apply.

Everything else is a clean structured logger: events as key/value data, context
binding, JSON or console output, level filtering, thread-safe writes — zero
dependencies.

## Install

```bash
pip install larzlog
```

## Usage

```python
from larzlog import get_logger, configure
import sys

configure(level="info", renderer="json", stream=sys.stdout)

log = get_logger("api")
log.info("request", method="GET", path="/users", ms=12)
log.error("db_error", code=500)

try:
    ...
except Exception:
    log.exception("job_failed", job_id="j-1")   # attaches the traceback

# context binding
user_log = log.bind(user_id=42, request_id="r-99")
user_log.info("action", name="export")          # both ids included
```

### JSON out (default)

```json
{"ts":"2026-07-27T10:00:00.123Z","level":"info","logger":"api","event":"request","method":"GET","path":"/users","ms":12}
```

### Console out (human-readable, optional colour)

```python
configure(renderer="console")
# 2026-07-27T10:00:00 [INFO    ] request  method=GET path=/users ms=12
```

### Redaction, tuned

```python
from larzlog import configure

configure(redact=["employee_id", "internal_ref"])   # add to the defaults
```

The defaults are never removed — you can only add to them.

## Tests

```bash
python -m unittest discover -s tests -v   # 16 tests incl. card/JWT/nested redaction
```

## The Larz stack

Pure-Python, zero-dependency building blocks: **[larz](https://github.com/larz-scripter/larz)** · **[larzchain](https://github.com/larz-scripter/larzchain)** · **[larzmoney](https://github.com/larz-scripter/larzmoney)** · **[larzcrypt](https://github.com/larz-scripter/larzcrypt)** · **[larzdb](https://github.com/larz-scripter/larzdb)** · **[larzagent](https://github.com/larz-scripter/larzagent)** · **[larzchart](https://github.com/larz-scripter/larzchart)** · **[larzmark](https://github.com/larz-scripter/larzmark)** · **[larztask](https://github.com/larz-scripter/larztask)** · **[larzvault](https://github.com/larz-scripter/larzvault)** · **[larzvm](https://github.com/larz-scripter/larzvm)** · **[larzcache](https://github.com/larz-scripter/larzcache)** · **[larzvalidate](https://github.com/larz-scripter/larzvalidate)** · **[larzid](https://github.com/larz-scripter/larzid)** · **[larzrpc](https://github.com/larz-scripter/larzrpc)** · **[larzstate](https://github.com/larz-scripter/larzstate)** · **[larzhttp](https://github.com/larz-scripter/larzhttp)** · **[larzconf](https://github.com/larz-scripter/larzconf)** · **[larzcron](https://github.com/larz-scripter/larzcron)** · **[larzlimit](https://github.com/larz-scripter/larzlimit)** · **larzlog**

## License

MIT © larz-scripter
