import asyncio
import sys
from pathlib import Path


async def main() -> None:
    try:
        from mcp.client.session import ClientSession  # type: ignore
        from mcp.client.stdio import stdio_client, StdioServerParameters  # type: ignore
    except Exception as exc:
        print({"ok": False, "error": f"Missing mcp client: {exc}"})
        return

    entry = Path(__file__).with_name("run_stdio.py")
    server = StdioServerParameters(command=sys.executable, args=[str(entry)])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            print({"tools": tool_names})
            if "ping" in tool_names:
                res = await session.call_tool("ping", {})
                out = {"ok": True}
                try:
                    blocks = getattr(res, "content", [])
                    if blocks:
                        data = getattr(blocks[0], "data", None) or getattr(blocks[0], "text", None)
                        if isinstance(data, dict):
                            out.update(data)
                        elif isinstance(data, str):
                            out["message"] = data
                except Exception:
                    pass
                print(out)


if __name__ == "__main__":
    asyncio.run(main())


