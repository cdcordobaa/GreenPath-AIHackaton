import asyncio
import json
import sys
from pathlib import Path


async def main() -> None:
    """Test only the MCP tools that are actually used by ADK agents in mcp-geo2neo."""
    
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
            
            print(f"📋 Available tools: {len(tool_names)}")
            print(f"Tools: {sorted(tool_names)}\n")

            async def call_tool_json(name: str, args: dict) -> dict:
                try:
                    res = await session.call_tool(name, args)
                    blocks = getattr(res, "content", [])
                    for blk in blocks:
                        data = getattr(blk, "data", None) or getattr(blk, "text", None)
                        if isinstance(data, dict):
                            return data
                        if isinstance(data, str):
                            try:
                                parsed = json.loads(data)
                                if isinstance(parsed, dict):
                                    return parsed
                            except Exception:
                                pass
                    return {"ok": True, "raw": str(blocks[0].text) if blocks else None}
                except Exception as exc:
                    return {"ok": False, "error": str(exc)}

            # Define the tools actually used by ADK agents
            used_tools = [
                "map_by_aliases"  # Used by geo2neo_from_structured_summary
            ]
            
            print("🎯 Testing only MCP tools used by ADK agents in mcp-geo2neo:\n")
            
            # Test 1: map_by_aliases (used by geo2neo_from_structured_summary)
            if "map_by_aliases" in tool_names:
                print("1️⃣ Testing map_by_aliases...")
                test_aliases = ["Suelos", "Hidrología", "Biótico"]
                res = await call_tool_json("map_by_aliases", {
                    "input": {"aliases": test_aliases}
                })
                success = res.get("ok", False) and res.get("error") is None
                count = res.get("count", 0)
                print(f"   {'✅' if success else '❌'} map_by_aliases: ok={success}, count={count}")
                
                if success and count > 0:
                    results = res.get("results", [])
                    print(f"   📊 Found mappings for {len(results)} categories:")
                    for i, result in enumerate(results[:2]):  # Show first 2
                        category = result.get("category", "Unknown")
                        instruments = result.get("instrumentsAndPermits", [])
                        print(f"      {i+1}. {category}: {len(instruments)} instruments")
                else:
                    print(f"   ℹ️  No mappings found (this is normal if test aliases don't exist in knowledge graph)")
            else:
                print("1️⃣ ❌ map_by_aliases tool not found")
            
            print()
            
            # Summary
            available_used_tools = [tool for tool in used_tools if tool in tool_names]
            missing_used_tools = [tool for tool in used_tools if tool not in tool_names]
            unused_tools = [tool for tool in tool_names if tool not in used_tools]
            
            print("📊 SUMMARY:")
            print(f"   ✅ Used tools available: {len(available_used_tools)}/{len(used_tools)}")
            print(f"      {available_used_tools}")
            
            if missing_used_tools:
                print(f"   ❌ Used tools missing: {missing_used_tools}")
            
            print(f"   🗑️  Unused tools that were cleaned up: {len(unused_tools)}")
            if unused_tools:
                print(f"      {unused_tools}")
            
            print()
            print("🎯 ADK Agent Tool Usage:")
            print("   • geo2neo_agent calls: map_by_aliases")
            print("   • All other tools in the MCP server are not called by ADK agents")


if __name__ == "__main__":
    asyncio.run(main())
