"""larzlog test suite — pure stdlib unittest, zero dependencies."""

import io
import json
import unittest

from larzlog import Config, Redactor, get_logger


def cap(level="debug", renderer="json", **kw):
    buf = io.StringIO()
    cfg = Config(level=level, renderer=renderer, stream=buf, colors=False,
                 clock=lambda: 1700000000.5, **kw)
    return buf, get_logger("test", cfg)


def lines(buf):
    return [json.loads(l) for l in buf.getvalue().splitlines() if l]


class TestStructured(unittest.TestCase):
    def test_basic_event(self):
        buf, log = cap()
        log.info("user_login", user_id=42, ip="1.2.3.4")
        rec = lines(buf)[0]
        self.assertEqual(rec["event"], "user_login")
        self.assertEqual(rec["level"], "info")
        self.assertEqual(rec["logger"], "test")
        self.assertEqual(rec["user_id"], 42)
        self.assertIn("ts", rec)

    def test_levels(self):
        buf, log = cap(level="warning")
        log.debug("d")
        log.info("i")
        log.warning("w")
        log.error("e")
        recs = lines(buf)
        self.assertEqual([r["event"] for r in recs], ["w", "e"])  # debug/info filtered

    def test_all_level_methods(self):
        buf, log = cap()
        for m in ("debug", "info", "warning", "error", "critical"):
            getattr(log, m)("evt_" + m)
        self.assertEqual(len(lines(buf)), 5)

    def test_exception_adds_traceback(self):
        buf, log = cap()
        try:
            raise ValueError("boom")
        except ValueError:
            log.exception("handler_failed")
        rec = lines(buf)[0]
        self.assertIn("traceback", rec)
        self.assertIn("ValueError: boom", rec["traceback"])


class TestContextBinding(unittest.TestCase):
    def test_bind_carries_context(self):
        buf, log = cap()
        child = log.bind(request_id="abc", tenant="acme")
        child.info("event")
        rec = lines(buf)[0]
        self.assertEqual(rec["request_id"], "abc")
        self.assertEqual(rec["tenant"], "acme")

    def test_bind_is_immutable(self):
        buf, log = cap()
        log.bind(a=1)
        log.info("evt")
        self.assertNotIn("a", lines(buf)[0])   # original logger unaffected

    def test_nested_bind(self):
        buf, log = cap()
        log.bind(a=1).bind(b=2).info("evt")
        rec = lines(buf)[0]
        self.assertEqual((rec["a"], rec["b"]), (1, 2))


class TestRedaction(unittest.TestCase):
    def test_sensitive_keys_redacted(self):
        buf, log = cap()
        log.info("login", username="ada", password="hunter2", token="abc123")
        rec = lines(buf)[0]
        self.assertEqual(rec["username"], "ada")
        self.assertNotEqual(rec["password"], "hunter2")
        self.assertNotEqual(rec["token"], "abc123")
        self.assertNotIn("hunter2", buf.getvalue())

    def test_authorization_and_card_keys(self):
        buf, log = cap()
        log.info("req", authorization="Bearer xyz", card_number="4111 1111 1111 1111")
        rec = lines(buf)[0]
        self.assertNotIn("Bearer xyz", buf.getvalue())
        self.assertNotIn("4111", buf.getvalue())

    def test_nested_redaction(self):
        buf, log = cap()
        log.info("evt", payload={"user": {"api_key": "sk_live_x"}, "ok": True})
        out = buf.getvalue()
        self.assertNotIn("sk_live_x", out)
        self.assertIn("ok", out)

    def test_value_shape_card_luhn(self):
        buf, log = cap()
        # a Luhn-valid test card in a non-obvious field name
        log.info("evt", note="paid with 4242424242424242 today")
        self.assertNotIn("4242424242424242", buf.getvalue())

    def test_value_shape_jwt(self):
        buf, log = cap()
        jwt = "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.SflKxwRJSMeKKF2QTabc"
        log.info("evt", header=jwt)
        self.assertNotIn(jwt, buf.getvalue())

    def test_non_secret_number_kept(self):
        buf, log = cap()
        log.info("evt", amount=1999, count=42)     # not redacted
        rec = lines(buf)[0]
        self.assertEqual(rec["amount"], 1999)

    def test_extra_keys(self):
        buf = io.StringIO()
        cfg = Config(stream=buf, colors=False, redactor=Redactor(extra_keys=["employee_id"]))
        log = get_logger("t", cfg)
        log.info("evt", employee_id="E123")
        self.assertNotIn("E123", buf.getvalue())


class TestConsoleRenderer(unittest.TestCase):
    def test_console_line(self):
        buf, log = cap(renderer="console")
        log.info("started", port=8080)
        out = buf.getvalue()
        self.assertIn("STARTED".lower(), out.lower())
        self.assertIn("port=8080", out)
        self.assertNotIn("{", out)             # not JSON


class TestRedactorUnit(unittest.TestCase):
    def test_redactor_direct(self):
        r = Redactor()
        out = r.redact({"password": "x", "list": [{"token": "y"}], "keep": 1})
        self.assertNotEqual(out["password"], "x")
        self.assertNotEqual(out["list"][0]["token"], "y")
        self.assertEqual(out["keep"], 1)


if __name__ == "__main__":
    unittest.main()
