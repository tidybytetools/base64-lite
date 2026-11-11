"""Free MCP server for base64-lite (stdio).

Run:  uvx --from git+https://github.com/tidybytetools/base64-lite base64-lite mcp
  or: uvx --from git+https://github.com/tidybytetools/base64-lite base64-lite-mcp
"""
import os
from typing import Annotated, Literal
from pydantic import Field
from mcp.server.fastmcp import FastMCP
from mcp.types import ToolAnnotations
import base64_lite as lite

MAX_BYTES = 5_000_000  # 5 MB is plenty for local text and small files

mcp = FastMCP("base64-lite")

READ_ONLY = dict(
    readOnlyHint=True,       # only reads; never writes or changes anything
    destructiveHint=False,
    idempotentHint=True,     # same input always gives the same result
    openWorldHint=False,     # no network; works on the text or local file you give it
)

Action = Annotated[
    Literal["auto", "encode", "decode"],
    Field(description='What to do. "auto" (default) decodes if the input looks like Base64, otherwise it encodes. Use "encode" or "decode" when you already know the direction.'),
]


def _check_file(path: str):
    path = os.path.expanduser(path)
    if not os.path.isfile(path):
        raise FileNotFoundError(f"file not found: {path}")
    if os.path.getsize(path) > MAX_BYTES:
        raise ValueError("file is bigger than 5 MB")
    with open(path, "rb") as f:
        return path, f.read()


@mcp.tool(
    title="Encode or decode Base64 text",
    annotations=ToolAnnotations(title="Encode or decode Base64 text", **READ_ONLY),
)
def convert_text(
    text: Annotated[str, Field(description="The text to encode, or the Base64 (or data URI) to decode.")],
    action: Action = "auto",
    url_safe: Annotated[bool, Field(description="If true, encode with - and _ instead of + and /. Decoding always accepts both.")] = False,
    data_uri: Annotated[bool, Field(description="If true, encoded results also include a data: URI.")] = False,
) -> dict:
    """Encode pasted text to Base64, or decode Base64 (or a data URI) back to text.

    Use this when you have text or a Base64 string in the conversation. It is plain
    code, not an AI model, so the same input always gives the same output and nothing
    is made up. Do not use it for a file on disk (use convert_file for files), and do
    not use auto on short or unusual strings if you already know the direction — pass
    encode or decode instead.

    Returns a result object. Encoded results include "action", "base64", "bytesIn",
    and "dataUri" plus "mime" when data_uri is true. Decoded results include "action",
    "bytesOut", "isText", and "text" (UTF-8 text, or null if the bytes are not text).
    """
    if action not in ("auto", "encode", "decode"):
        raise ValueError("action must be auto, encode or decode")
    return lite.public_result(lite.convert(text, None, action=action, url_safe=url_safe, data_uri=data_uri))


@mcp.tool(
    title="Encode or decode a local file as Base64",
    annotations=ToolAnnotations(title="Encode or decode a local file as Base64", **READ_ONLY),
)
def convert_file(
    path: Annotated[str, Field(description="Full path to a local file, up to 5 MB. For decode, the file must be UTF-8 text of Base64.")],
    action: Action = "auto",
    url_safe: Annotated[bool, Field(description="If true, encode with - and _ instead of + and /. Decoding always accepts both.")] = False,
    data_uri: Annotated[bool, Field(description="If true, encoded results also include a data: URI. The MIME type is guessed from the file name when we can.")] = False,
) -> dict:
    """Read a local file and encode its bytes to Base64, or decode a Base64 text file.

    Use this when the data is in a file on this computer, so you don't have to paste
    it. The file is only read, never changed. Files larger than 5 MB are rejected;
    use the Apify version for bigger jobs. For decode, the file must be UTF-8 text
    containing Base64 (or a data URI), not a binary file.

    path: full path to a file, up to 5 MB.

    Returns the same result object as convert_text. If the decoded bytes are not
    UTF-8 text, "isText" is false and "text" is null.
    """
    if action not in ("auto", "encode", "decode"):
        raise ValueError("action must be auto, encode or decode")
    path, data = _check_file(path)
    return lite.public_result(lite.convert(None, data, action=action, url_safe=url_safe, data_uri=data_uri, filename=path))


def main():
    mcp.run()


if __name__ == "__main__":
    main()
