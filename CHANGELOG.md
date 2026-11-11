# Changelog

What changed in base64-lite, newest first.

## 1.0.0 - 2026-11-10

- First release.
- Encodes or decodes Base64 for text and local files. Optional URL-safe alphabet and data-URI output.
- `--action auto` (default) decodes if the input looks like Base64, otherwise it encodes. You can force encode or decode.
- `--json` gives one clean object for scripts and AI agents. `--quiet` hides the tip line.
- A free MCP server with two read-only tools: `convert_text` and `convert_file`.
- Needs Python 3.10 or newer.
