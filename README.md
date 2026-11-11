<p>
  <a href="https://github.com/tidybytetools">
    <picture>
      <source media="(prefers-color-scheme: dark)" srcset="https://raw.githubusercontent.com/tidybytetools/base64-lite/main/assets/tidybytetools-lockup-dark.png">
      <img alt="Tidy Byte Tools" src="https://raw.githubusercontent.com/tidybytetools/base64-lite/main/assets/tidybytetools-lockup-light.png" height="44">
    </picture>
  </a>
</p>

# base64-lite

[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](https://github.com/tidybytetools/base64-lite/blob/main/LICENSE)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![MCP server](https://img.shields.io/badge/MCP-stdio-purple.svg)](#use-it-from-claude-desktop-or-cursor-mcp)
[![Tests](https://github.com/tidybytetools/base64-lite/actions/workflows/tests.yml/badge.svg)](https://github.com/tidybytetools/base64-lite/actions/workflows/tests.yml)

Free tool that encodes or decodes Base64 for text and local files. Optional URL-safe alphabet and data-URI output.

Need it at scale or from an AI agent? Use the Apify version: **[base64-encode-decode on Apify](https://apify.com/tidybytetools/base64-encode-decode)**

Plain code, not AI, so the same input always gives the same output. Runs on your own computer. MIT license. Works with Python 3.10 and newer, on Windows, Mac and Linux.

## Links

- **[Apify (no-install cloud version)](https://apify.com/tidybytetools/base64-encode-decode)** — pay only for what you use, about $0.001 per unique item. Failed items are free. (This listing goes public this week.)

<!-- mcp-name: io.github.tidybytetools/base64-lite -->

## Before and after

Before (plain text):

```
hello world
```

After (Base64):

```
aGVsbG8gd29ybGQ=
```

Decode works the other way, including data URIs like `data:text/plain;base64,aGVsbG8gd29ybGQ=`.

## Install

```
pip install git+https://github.com/tidybytetools/base64-lite
```

Or use pipx, which keeps it in its own space:

```
pipx install git+https://github.com/tidybytetools/base64-lite
```

Or just download `base64_lite.py` and run it with `python3`. That one file uses only Python's standard library. (Installing with pip also adds the `mcp` package, which the MCP server needs.)

## Use it

```
printf 'hello world' | base64-lite --action encode
base64-lite photo.png --action encode --data-uri
printf 'aGVsbG8gd29ybGQ=' | base64-lite --action decode
base64-lite note.b64 --action decode
base64-lite file.bin --action decode --output out.bin   # when the bytes are not text
printf 'hello world' | base64-lite --json               # {"ok": true, "action": "encode", "base64": "..."}
```

`--action auto` (the default) decodes if the input looks like Base64, otherwise it encodes. Use `--action encode` or `--action decode` when you already know the direction. `--url-safe` uses `-` and `_` instead of `+` and `/` when encoding. Decoding always accepts both forms.

From Python:

```python
from base64_lite import convert
convert("hello world", None, action="encode")["base64"]  # 'aGVsbG8gd29ybGQ='
```

When you run it in a terminal it prints one short line about the Apify version to stderr after the result. It never goes into your output, it only shows when you are looking at a terminal, and `--quiet` turns it off.

## Known limits

- **`auto` can guess wrong** on short or unusual strings. Use `encode` or `decode` when you already know the direction.
- **Local files only.** This free tool does not fetch file links from the internet. The Apify version does.
- **5 MB cap in the MCP file tool.** The command line will read a larger local file, but very large jobs are a better fit for Apify.
- **It does not inspect decoded bytes** for viruses or hidden data.

## Lite vs Apify

| | lite (free, this repo) | [base64-encode-decode on Apify](https://apify.com/tidybytetools/base64-encode-decode) |
|---|---|---|
| Encode and decode text or files | yes, on your computer | yes, in the cloud |
| URL-safe alphabet and data URIs | yes | yes |
| Fetch file links | no | yes |
| Many items in one run | you can loop on your own | yes, and repeats in the same run are free |
| MCP server for local AI apps | yes | use Apify MCP for the cloud tool |
| Price | free | $0.001 per unique item. Failed items are free |

## Use it from Claude Desktop or Cursor (MCP)

There is a small free MCP server built in. It gives your AI app two tools. Both only read. They never write or change files, and they never use the internet. It needs [uv](https://docs.astral.sh/uv/).

Run it by hand to check it starts (it waits quietly for an app to talk to it):

```
uvx --from git+https://github.com/tidybytetools/base64-lite base64-lite mcp
```

Claude Desktop (`claude_desktop_config.json`) or Cursor (`~/.cursor/mcp.json`):

```json
{
  "mcpServers": {
    "base64-lite": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/tidybytetools/base64-lite", "base64-lite", "mcp"]
    }
  }
}
```

`uvx --from git+https://github.com/tidybytetools/base64-lite base64-lite-mcp` starts the same server.

Tools:

- `convert_text(text, action="auto", url_safe=false, data_uri=false)`: for text or Base64 in the chat.
- `convert_file(path, action="auto", url_safe=false, data_uri=false)`: for a local file, up to 5 MB. For decode, the file must be UTF-8 text of Base64.

Encoded results include `base64` (and `dataUri` if you asked). Decoded results include `text` when the bytes are UTF-8, or `isText` false if they are not.

## For AI agents

- **Use when:** you need to encode text or a local file to Base64, or decode Base64 / a data URI.
- **Don't use when:** you need to fetch a file from a URL, or the file is bigger than 5 MB in MCP. Use the Apify version for those jobs.
- **Input:** text on stdin or a file path. Optional `--action auto|encode|decode`, `--url-safe`, `--data-uri`, `--output FILE`.
- **MCP:** `uvx --from git+https://github.com/tidybytetools/base64-lite base64-lite mcp` gives two read-only tools, `convert_text` and `convert_file`.
- **Output:** with `--json`, one object such as `{"ok": true, "action": "encode", "base64": "...", "bytesIn": 11}`. On error `ok` is false. Exit code 0 ok, 1 error.
- Hint lines go to stderr only, and only in a terminal, so stdout is always clean. See also [`llms.txt`](https://github.com/tidybytetools/base64-lite/blob/main/llms.txt).

## Tests

```
pip install "mcp>=1.10,<2"
python3 -m unittest discover tests
```

The MCP tests are skipped if `mcp` is not installed.

## FAQ

**What input does it take?**
Text on stdin, or a local file. Use `--action encode` or `--action decode` if you already know the direction.

**Do my files leave my computer?**
No. The tool runs on your computer and never uses the internet.

**How is this different from the Apify version?**
The Apify version runs in the cloud, can fetch file links, and can process many items in one run. This lite tool is free and local.

**Does it work with AI apps?**
Yes. It includes a free MCP server. No API key.

## License

MIT. See `LICENSE`.
