import asyncio
import json
import os
import sys
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv, find_dotenv


async def main() -> None:
    """Test only the MCP tools that are actually used by ADK agents."""
    # Load environment variables from .env if present
    try:
        load_dotenv(find_dotenv())
    except Exception:
        pass
    
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
                "ping",
                "get_structured_resource_summary", 
                "search_scraped_pages"
            ]
            
            print("🎯 Testing only MCP tools used by ADK agents:\n")
            
            # Test 1: ping (used by search_scraped_pages_via_mcp)
            if "ping" in tool_names:
                print("1️⃣ Testing ping...")
                res = await call_tool_json("ping", {})
                print(f"   ✅ ping: {res}")
            else:
                print("1️⃣ ❌ ping tool not found")
            
            print()
            
            # Test 2: get_structured_resource_summary (used by structured_summary_via_mcp)
            have_supabase = bool(
                os.environ.get("SUPABASE_URL") and 
                (os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY"))
            )
            project_id = os.environ.get("PROJECT_ID", "demo-project")
            
            if not have_supabase:
                print("⚠️  Supabase credentials missing - skipping data tools")
                print("   Set SUPABASE_URL and SUPABASE_KEY/SUPABASE_ANON_KEY to test data tools\n")
            else:
                if "get_structured_resource_summary" in tool_names:
                    print("2️⃣ Testing get_structured_resource_summary...")
                    res = await call_tool_json("get_structured_resource_summary", {"project_id": project_id})
                    success = res.get("ok", False) and res.get("error") is None
                    count = res.get("count", 0)
                    print(f"   {'✅' if success else '❌'} get_structured_resource_summary: ok={success}, count={count}")
                    
                    if success and count > 0:
                        # Show sample rows
                        rows = res.get("rows", [])
                        print(f"   📊 Sample data (first 3 rows):")
                        for i, row in enumerate(rows[:3]):
                            print(f"      {i+1}. {row}")
                else:
                    print("2️⃣ ❌ get_structured_resource_summary tool not found")
                
                print()
                
                # Test 3: search_scraped_pages (used by search_scraped_pages_via_mcp)
                if "search_scraped_pages" in tool_names:
                    print("3️⃣ Testing search_scraped_pages...")
                    res = await call_tool_json("search_scraped_pages", {
                        "limit": 5,
                        "text_contains": "ley"  # Search for Spanish law content
                    })
                    success = res.get("ok", True) and res.get("error") is None
                    count = res.get("count", 0)
                    print(f"   {'✅' if success else '❌'} search_scraped_pages: ok={success}, count={count}")
                    
                    if count > 0:
                        rows = res.get("rows", [])
                        print(f"   📄 Found {count} pages with 'ley' content")
                        for i, row in enumerate(rows[:2]):  # Show first 2 results
                            url = row.get("url", "No URL")[:50] + "..." if len(row.get("url", "")) > 50 else row.get("url", "No URL")
                            print(f"      {i+1}. {url}")
                else:
                    print("3️⃣ ❌ search_scraped_pages tool not found")
            
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
            
            print(f"   🗑️  Unused tools that could be cleaned up: {len(unused_tools)}")
            if unused_tools and len(unused_tools) <= 10:
                print(f"      {unused_tools[:10]}")
            elif unused_tools:
                print(f"      {unused_tools[:5]} ... and {len(unused_tools)-5} more")
            
            print()
            print("🎯 ADK Agent Tool Usage:")
            print("   • geo_agent calls: get_structured_resource_summary")
            print("   • geo_kb_agent calls: search_scraped_pages (+ ping)")
            print("   • All other tools in the MCP server are not called by ADK agents")


if __name__ == "__main__":
    asyncio.run(main())
