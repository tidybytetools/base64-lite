import io, os, sys, tempfile, unittest
from contextlib import redirect_stdout, redirect_stderr
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import base64_lite as b64

class T(unittest.TestCase):
    def test_encode_hello(self):
        r = b64.convert("hello world", None, action="encode")
        self.assertEqual(r["action"], "encode")
        self.assertEqual(r["base64"], "aGVsbG8gd29ybGQ=")
        self.assertEqual(r["bytesIn"], 11)

    def test_decode_hello(self):
        r = b64.convert("aGVsbG8gd29ybGQ=", None, action="decode")
        self.assertEqual(r["action"], "decode")
        self.assertEqual(r["text"], "hello world")
        self.assertTrue(r["isText"])

    def test_auto_decode(self):
        r = b64.convert("aGVsbG8gd29ybGQ=", None, action="auto")
        self.assertEqual(r["action"], "decode")
        self.assertEqual(r["text"], "hello world")

    def test_auto_encode_plain(self):
        r = b64.convert("hello world", None, action="auto")
        self.assertEqual(r["action"], "encode")
        self.assertEqual(r["base64"], "aGVsbG8gd29ybGQ=")

    def test_url_safe_and_data_uri(self):
        r = b64.convert("hi?", None, action="encode", url_safe=True, data_uri=True)
        self.assertTrue("-" in r["base64"] or "_" in r["base64"] or r["base64"].endswith("="))
        self.assertTrue(r["dataUri"].startswith("data:text/plain;base64,"))
        # data URI uses the standard alphabet
        self.assertNotIn("-", r["dataUri"].split(",", 1)[1])
        # decode accepts the URL-safe form
        back = b64.convert(r["base64"], None, action="decode")
        self.assertEqual(back["text"], "hi?")

    def test_file_encode(self):
        r = b64.convert(None, b"\x00\x01\x02", action="encode", data_uri=True, filename="x.bin")
        self.assertEqual(r["bytesIn"], 3)
        self.assertIn("base64", r)

    def test_looks_like(self):
        self.assertTrue(b64.looks_like_base64("aGVsbG8gd29ybGQ="))
        self.assertFalse(b64.looks_like_base64("hello world"))

    def test_decode_data_uri(self):
        r = b64.convert("data:text/plain;base64,aGVsbG8=", None, action="decode")
        self.assertEqual(r["text"], "hello")

    def test_decode_binary_is_not_text(self):
        rec = b64.encode_bytes(b"\x00\xff")
        r = b64.convert(rec["base64"], None, action="decode")
        self.assertFalse(r["isText"])
        self.assertIsNone(r["text"])
        self.assertEqual(r["_raw"], b"\x00\xff")

    def test_public_result_drops_raw(self):
        r = b64.public_result(b64.convert("aGVsbG8=", None, action="decode"))
        self.assertNotIn("_raw", r)
        self.assertEqual(r["text"], "hello")

    def test_bad_action(self):
        with self.assertRaises(ValueError):
            b64.convert("hello", None, action="flip")

    def test_nothing(self):
        with self.assertRaises(ValueError):
            b64.convert(None, None)

    def run_main(self, argv, stdin=b"", stdin_text=None):
        out, err = io.StringIO(), io.StringIO()
        raw = stdin_text.encode("utf-8") if stdin_text is not None else stdin
        old = sys.stdin
        sys.stdin = io.TextIOWrapper(io.BytesIO(raw), encoding="utf-8")
        # also expose .buffer for binary stdin reads
        try:
            with redirect_stdout(out), redirect_stderr(err):
                code = b64.main(argv)
        finally:
            sys.stdin = old
        return code, out.getvalue(), err.getvalue()

    def test_cli_json_encode(self):
        code, out, err = self.run_main(["--json", "--action", "encode"], stdin_text="hello world")
        self.assertEqual(code, 0)
        self.assertIn('"ok": true', out)
        self.assertIn("aGVsbG8gd29ybGQ=", out)
        self.assertNotIn("apify.com", out)

    def test_cli_plain_encode(self):
        code, out, err = self.run_main(["--action", "encode"], stdin_text="hello world")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "aGVsbG8gd29ybGQ=")

    def test_cli_plain_decode(self):
        code, out, err = self.run_main(["--action", "decode"], stdin_text="aGVsbG8gd29ybGQ=")
        self.assertEqual(code, 0)
        self.assertEqual(out.strip(), "hello world")

    def test_cli_help_has_apify_link(self):
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit):
            b64.main(["--help"])
        self.assertIn("https://apify.com/tidybytetools/base64-encode-decode", out.getvalue())

    def test_bad_file(self):
        code, out, err = self.run_main(["--json", "/nope/missing.txt"], stdin_text="")
        self.assertEqual(code, 1)
        self.assertIn('"ok": false', out)

    def test_cli_output_binary(self):
        rec = b64.encode_bytes(b"\x00\xff")
        with tempfile.TemporaryDirectory() as td:
            dest = os.path.join(td, "out.bin")
            code, out, err = self.run_main(["--action", "decode", "--output", dest], stdin_text=rec["base64"])
            self.assertEqual(code, 0)
            with open(dest, "rb") as f:
                self.assertEqual(f.read(), b"\x00\xff")

    def test_cli_file_encode(self):
        with tempfile.TemporaryDirectory() as td:
            path = os.path.join(td, "hello.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("hello world")
            code, out, err = self.run_main(["--action", "encode", path])
            self.assertEqual(code, 0)
            self.assertEqual(out.strip(), "aGVsbG8gd29ybGQ=")

    def test_version(self):
        out = io.StringIO()
        with redirect_stdout(out), self.assertRaises(SystemExit) as ctx:
            b64.main(["--version"])
        self.assertIn(ctx.exception.code, (0, None))
        self.assertIn("1.0.0", out.getvalue())


if __name__ == "__main__":
    unittest.main()
