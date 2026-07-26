"""Automatic redaction of secrets and PII from log records.

This is larzlog's whole reason for existing: **a log line should never be the
thing that leaks a password, a card number, or an API key.** Redaction runs on
every record before it's written, matching both by field *name* (``password``,
``token``, ``authorization`` …) and by value *shape* (things that look like
credit cards, JWTs, or long secret keys). It walks nested dicts and lists, so a
secret buried three levels deep in a payload is still caught.

You extend it, you don't opt out: pass extra sensitive key fragments to
:func:`Redactor`, but the safe defaults are always on.
"""

import re

#: Substrings that mark a field name as sensitive (matched case-insensitively).
DEFAULT_SENSITIVE_KEYS = frozenset({
    "password", "passwd", "pwd", "secret", "token", "api_key", "apikey",
    "access_key", "private_key", "privatekey", "authorization", "auth",
    "credential", "card", "card_number", "cardnumber", "pan", "cvv", "cvc",
    "cvv2", "pin", "ssn", "session", "cookie", "otp", "seed", "mnemonic",
    "passphrase",
})

_REDACTED = "***REDACTED***"

# value-shape patterns (belt-and-suspenders for mis-named fields)
_CARD_RE = re.compile(r"\b(?:\d[ -]?){13,19}\b")
_JWT_RE = re.compile(r"\beyJ[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\.[A-Za-z0-9_-]{5,}\b")
_SECRET_KEY_RE = re.compile(r"\b(?:sk|pk|rk|ak)_[A-Za-z0-9]{16,}\b")


def _luhn_ok(digits):
    total, alt = 0, False
    for d in reversed(digits):
        n = int(d)
        if alt:
            n *= 2
            if n > 9:
                n -= 9
        total += n
        alt = not alt
    return total % 10 == 0


class Redactor(object):
    """Redacts sensitive fields (by name and by value shape). Add extra key
    fragments; defaults are always applied."""

    def __init__(self, extra_keys=None, redact_values=True, mask=_REDACTED):
        keys = set(DEFAULT_SENSITIVE_KEYS)
        if extra_keys:
            keys |= {k.lower() for k in extra_keys}
        self.keys = keys
        self.redact_values = redact_values
        self.mask = mask

    def _key_is_sensitive(self, key):
        k = str(key).lower()
        return any(frag in k for frag in self.keys)

    def _redact_value(self, value):
        if not self.redact_values or not isinstance(value, str):
            return value
        if _JWT_RE.search(value) or _SECRET_KEY_RE.search(value):
            return self.mask
        m = _CARD_RE.search(value)
        if m:
            digits = re.sub(r"[ -]", "", m.group(0))
            if 13 <= len(digits) <= 19 and _luhn_ok(digits):
                return self.mask
        return value

    def redact(self, obj):
        """Return a redacted copy of a record (dict/list/scalar)."""
        if isinstance(obj, dict):
            out = {}
            for k, v in obj.items():
                if self._key_is_sensitive(k):
                    out[k] = self.mask
                else:
                    out[k] = self.redact(v)
            return out
        if isinstance(obj, (list, tuple)):
            return [self.redact(v) for v in obj]
        return self._redact_value(obj)
