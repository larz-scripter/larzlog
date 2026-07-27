"""larzlog test suite - pure stdlib unittest, zero dependencies."""
import io
import json
import unittest
from larzlog import Logger


class TestText(unittest.TestCase):
    def test_basic_line(self):
        out = io.StringIO()
        log = Logger("api", level="INFO", output=out)
        line = log.info("hi", user=42)
        self.assertEqual(line, "INFO api: hi user=42")
        self.assertEqual(out.getvalue(), "INFO api: hi user=42\n")

    def test_level_filtering(self):
        out = io.StringIO()
        log = Logger("api", level="WARNING", output=out)
        self.assertIsNone(log.info("skipped"))      # below threshold
        self.assertIsNotNone(log.error("kept"))
        self.assertNotIn("skipped", out.getvalue())
        self.assertIn("kept", out.getvalue())

    def test_value_with_space_quoted(self):
        out = io.StringIO()
        line = Logger("a", output=out).info("m", note="two words")
        self.assertIn('note="two words"', line)

    def test_bind_context(self):
        out = io.StringIO()
        log = Logger("a", output=out).bind(request_id="abc")
        line = log.info("done", ms=5)
        self.assertIn("request_id=abc", line)
        self.assertIn("ms=5", line)


class TestJson(unittest.TestCase):
    def test_json_output(self):
        out = io.StringIO()
        log = Logger("api", output=out, json=True)
        line = log.error("boom", code=500)
        rec = json.loads(line)
        self.assertEqual(rec["level"], "ERROR")
        self.assertEqual(rec["logger"], "api")
        self.assertEqual(rec["message"], "boom")
        self.assertEqual(rec["code"], 500)


if __name__ == "__main__":
    unittest.main()
