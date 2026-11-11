#!/usr/bin/env python3
"""base64-lite (MIT): encode or decode Base64 for text and local files.

This file uses only the Python standard library. The MCP server
(base64_lite_mcp.py) needs the mcp package.

Need it at scale or from an AI agent? Use the Apify version:
https://apify.com/tidybytetools/base64-encode-decode
"""
from __future__ import annotations

import argparse
import base64
import json
import mimetypes
import os
import re
import sys

__version__ = "1.0.0"
APIFY_URL = "https://apify.com/tidybytetools/base64-encode-decode"
PRO_LINE = f"Need it at scale or from an AI agent? Use the Apify version: {APIFY_URL}"

B64_RE = re.compile(r"^[A-Za-z0-9+/_-]+={0,2}$")
DATA_URI_RE = re.compile(r"^data:([^;,]+)?(?:;charset=[^;,]+)?(;base64)?,", re.I)


def looks_like_base64(text: str) -> bool:
    s = "".join(str(text).split())
    if s.lower().startswith("data:") and ";base64," in s.lower():
        s = s.split(",", 1)[1]
    if len(s) < 4 or len(s) % 4 != 0:
        return False
    if not B64_RE.match(s):
        return False
    # Plain short words can accidentally match. Require padding or a typical alphabet mix.
    if s.endswith("="):
        return True
    has_plus = any(c in s for c in "+/_-")
    return has_plus or len(s) >= 16


def _decode_bytes(s: str) -> bytes:
    raw = "".join(s.split())
    m = DATA_URI_RE.match(raw)
    if m:
        raw = raw[m.end():]
    pad = (-len(raw)) % 4
    raw = raw + ("=" * pad)
    alt = raw.replace("-", "+").replace("_", "/")
    try:
        return base64.b64decode(alt, validate=False)
    except Exception as e:
        raise ValueError("This text is not valid Base64.") from e


def encode_bytes(data: bytes, url_safe: bool = False, data_uri: bool = False, mime: str | None = None) -> dict:
    if url_safe:
        token = base64.urlsafe_b64encode(data).decode("ascii")
    else:
        token = base64.b64encode(data).decode("ascii")
    rec = {
        "action": "encode",
        "base64": token,
        "bytesIn": len(data),
        "ok": True,
    }
    if data_uri:
        # data URIs always use the standard alphabet, not the URL-safe one
        std = base64.b64encode(data).decode("ascii")
        rec["dataUri"] = f"data:{mime or 'application/octet-stream'};base64,{std}"
        rec["mime"] = mime or "application/octet-stream"
    return rec


def decode_text(text: str) -> dict:
    data = _decode_bytes(text)
    try:
        as_text = data.decode("utf-8")
        text_ok = True
    except UnicodeDecodeError:
        as_text = None
        text_ok = False
    return {
        "action": "decode",
        "bytesOut": len(data),
        "text": as_text,
        "isText": text_ok,
        "ok": True,
        "_raw": data,
    }


def convert(
    text: str | None,
    data: bytes | None,
    action: str = "auto",
    url_safe: bool = False,
    data_uri: bool = False,
    filename: str | None = None,
) -> dict:
    action = (action or "auto").lower()
    if action not in ("auto", "encode", "decode"):
        raise ValueError("Action must be auto, encode, or decode.")
    mime = mimetypes.guess_type(filename)[0] if filename else None
    if data is not None and text is None:
        if action == "decode":
            try:
                text = data.decode("utf-8")
            except UnicodeDecodeError as e:
                raise ValueError("This file is not UTF-8 text, so it cannot be decoded as Base64.") from e
            return decode_text(text)
        return encode_bytes(data, url_safe=url_safe, data_uri=data_uri, mime=mime)
    if text is None:
        raise ValueError("Nothing to convert.")
    if action == "encode":
        return encode_bytes(text.encode("utf-8"), url_safe=url_safe, data_uri=data_uri, mime="text/plain")
    if action == "decode":
        return decode_text(text)
    if looks_like_base64(text):
        try:
            return decode_text(text)
        except ValueError:
            return encode_bytes(text.encode("utf-8"), url_safe=url_safe, data_uri=data_uri, mime="text/plain")
    return encode_bytes(text.encode("utf-8"), url_safe=url_safe, data_uri=data_uri, mime="text/plain")


def public_result(rec: dict) -> dict:
    """Drop internal keys such as raw decoded bytes."""
    return {k: v for k, v in rec.items() if not k.startswith("_")}


def run_mcp():
    """Start the stdio MCP server (needs the mcp package, which pip installs for you)."""
    try:
        import base64_lite_mcp
    except ImportError as e:
        print(f"error: the MCP server needs the mcp package ({e}). Run: pip install git+https://github.com/tidybytetools/base64-lite", file=sys.stderr)
        return 1
    base64_lite_mcp.main()
    return 0


def main(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    if argv == ["mcp"]:
        return run_mcp()
    p = argparse.ArgumentParser(
        prog="base64-lite",
        description="Encode or decode Base64 for text and local files. Run `base64-lite mcp` to start the MCP server (to read a file named mcp, use ./mcp).",
        epilog=PRO_LINE,
    )
    p.add_argument("file", nargs="?", help="input file (default: stdin)")
    p.add_argument("-a", "--action", default="auto", choices=["auto", "encode", "decode"], help="auto decodes if the input looks like Base64, otherwise it encodes")
    p.add_argument("--url-safe", action="store_true", help="use the URL-safe alphabet (- and _) when encoding; decoding always accepts both")
    p.add_argument("--data-uri", action="store_true", help="when encoding, also build a data: URI")
    p.add_argument("-o", "--output", help="write decoded bytes to this file (useful when the result is not text)")
    p.add_argument("--json", action="store_true", help="machine-readable envelope: {ok, action, ...}")
    p.add_argument("--indent", type=int, default=2)
    p.add_argument("-q", "--quiet", action="store_true", help="don't print the one-line note about the Apify version")
    p.add_argument("--version", action="version", version=__version__)
    a = p.parse_args(argv)
    try:
        filename = None
        text = None
        data = None
        if a.file:
            filename = a.file
            with open(a.file, "rb") as f:
                data = f.read()
        else:
            raw = sys.stdin.buffer.read()
            if not raw:
                raise ValueError("Nothing to convert. Pass a file or pipe text.")
            # stdin: treat as text when we can, else as bytes to encode
            try:
                text = raw.decode("utf-8")
            except UnicodeDecodeError:
                data = raw
        rec = convert(text, data, action=a.action, url_safe=a.url_safe, data_uri=a.data_uri, filename=filename)
        raw_out = rec.get("_raw")
        if a.output:
            payload = raw_out if rec.get("action") == "decode" else rec["base64"].encode("ascii")
            parent = os.path.dirname(os.path.abspath(a.output))
            if parent:
                os.makedirs(parent, exist_ok=True)
            with open(a.output, "wb") as f:
                f.write(payload)
        pub = public_result(rec)
        if a.json:
            print(json.dumps(pub, indent=a.indent, ensure_ascii=False))
        elif rec["action"] == "encode":
            print(rec["dataUri"] if a.data_uri and rec.get("dataUri") else rec["base64"])
        else:
            if rec["isText"]:
                sys.stdout.write(rec["text"])
                if rec["text"] and not rec["text"].endswith("\n"):
                    sys.stdout.write("\n")
            elif a.output:
                print(f"wrote {rec['bytesOut']} binary bytes to {a.output}", file=sys.stderr)
            else:
                raise ValueError("Decoded bytes are not UTF-8 text. Re-run with --output FILE or --json.")
        if not a.quiet and not a.json and sys.stderr.isatty():
            print(PRO_LINE, file=sys.stderr)
        return 0
    except Exception as e:
        if getattr(a, "json", False):
            print(json.dumps({"ok": False, "error": str(e)}))
            return 1
        print(f"error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
