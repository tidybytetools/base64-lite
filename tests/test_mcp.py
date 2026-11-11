"""Starts the MCP server over stdio (both ways it can start), lists tools, and calls them."""
import asyncio, json, os, sys, unittest
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
except ImportError:
    ClientSession = None

READ_ONLY = {"readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False}


def _data(res):
    """The tool result as Python data (structured content if present, else the JSON text)."""
    if res.structuredContent is not None:
        sc = res.structuredContent
        return sc.get("result", sc) if set(sc) == {"result"} else sc
    return json.loads(res.content[0].text)


async def _session(args, fn):
    params = StdioServerParameters(command=sys.executable, args=args, cwd=ROOT)
    async with stdio_client(params) as (r, w):
        async with ClientSession(r, w) as s:
            await s.initialize()
            return await fn(s)


@unittest.skipIf(ClientSession is None, "mcp not installed")
class MCP(unittest.TestCase):
    def test_tools_and_annotations(self):
        async def go(s):
            return (await s.list_tools()).tools
        tools = asyncio.run(_session([os.path.join(ROOT, "base64_lite_mcp.py")], go))
        self.assertEqual(sorted(t.name for t in tools), ["convert_file", "convert_text"])
        for t in tools:
            self.assertTrue(t.title)
            self.assertIn("Use this when", t.description)
            for k, v in READ_ONLY.items():
                self.assertIs(getattr(t.annotations, k), v, f"{t.name} {k}")

    def test_calls(self):
        async def go(s):
            enc = await s.call_tool("convert_text", {"text": "hello world", "action": "encode"})
            dec = await s.call_tool("convert_text", {"text": "aGVsbG8gd29ybGQ=", "action": "decode"})
            auto = await s.call_tool("convert_text", {"text": "hello world"})
            f = await s.call_tool("convert_file", {"path": os.path.join(HERE, "fixtures", "hello.txt"), "action": "encode"})
            missing = await s.call_tool("convert_file", {"path": "/nope/missing.bin"})
            bad = await s.call_tool("convert_text", {"text": "hello", "action": "flip"})
            return enc, dec, auto, f, missing, bad
        enc, dec, auto, f, missing, bad = asyncio.run(_session([os.path.join(ROOT, "base64_lite_mcp.py")], go))
        self.assertEqual(_data(enc)["base64"], "aGVsbG8gd29ybGQ=")
        self.assertEqual(_data(dec)["text"], "hello world")
        self.assertEqual(_data(auto)["action"], "encode")
        self.assertEqual(_data(f)["base64"], "aGVsbG8gd29ybGQ=")
        self.assertTrue(missing.isError)
        self.assertTrue(bad.isError)

    def test_cli_mcp_subcommand_starts_server(self):
        async def go(s):
            return [t.name for t in (await s.list_tools()).tools]
        names = asyncio.run(_session([os.path.join(ROOT, "base64_lite.py"), "mcp"], go))
        self.assertIn("convert_text", names)


if __name__ == "__main__":
    unittest.main()
