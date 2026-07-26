# Changelog

## 0.1.0

First release. Pure Python, zero dependencies, thread-safe.

- Structured event logging (name + key/value fields), JSON or console renderer.
- Automatic redaction (on by default): sensitive field names (password/token/
  authorization/card/ssn/...) AND value shapes (Luhn-valid cards, JWTs, secret
  keys), recursing through nested dicts/lists. Extend with extra keys.
- Context binding: log.bind(**ctx) -> child logger; immutable.
- Levels debug..critical + exception() with traceback; level filtering.
- configure()/get_logger(); injectable clock + stream for testing.
- 16 tests.
