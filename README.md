# larzlog

**Structured logging — readable, level-filtered logs (text or JSON) for real apps.**

When your app runs somewhere you can't see, logs are your eyes. larzlog is a small
structured logger: levels you can filter, `key=value` context fields, output as
human-readable text or machine-readable JSON, and `bind` to attach context (like a
request id) to every line. Everything is injectable (output, clock) so it's easy to
test. Zero dependencies.

## Install

```bash
pip install larzlog
```

## Use

```python
from larzlog import Logger

log = Logger("api", level="INFO")
log.info("user signed up", user_id=42, plan="pro")
# INFO api: user signed up user_id=42 plan=pro

req = log.bind(request_id="abc123")
req.warning("slow response", ms=812)
```

## Learn to code with Larz

Part of the **learn-to-code toolkit** in the [Larz stack](https://github.com/larz-scripter) —
see the [Learn to Code platform](https://larzos.com/learn/). A building block for
running apps in production.

## Tests

```bash
python -m unittest discover -s tests -v   # 5 tests
```

## License

MIT (c) larz-scripter
