#!/usr/bin/env python3
"""
Test the fixed geo-fetch-mcp to see if it returns table names as tipo
"""
import asyncio
import json
import sys
from pathlib import Path


async def test_fixed_geo_fetch():
    """Test the fixed get_structured_resource_summary"""
    
    try:
        from mcp.client.session import ClientSession  # type: ignore
        from mcp.client.stdio import stdio_client, StdioServerParameters  # type: ignore
    except Exception as exc:
        print(f"❌ Missing mcp client: {exc}")
        return

    server_path = Path("geo-fetch-mcp/run_stdio.py")
    venv_python = Path("geo-fetch-mcp/.venv/bin/python")
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    params = StdioServerParameters(command=python_cmd, args=[str(server_path)])
    
    print("🧪 Testing FIXED geo-fetch-mcp...")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print("📋 Testing get_structured_resource_summary...")
            
            try:
                result = await session.call_tool("get_structured_resource_summary", {
                    "project_id": "test_project"
                })
                
                blocks = getattr(result, "content", [])
                if blocks:
                    data = getattr(blocks[0], "data", None) or getattr(blocks[0], "text", None)
                    if isinstance(data, str):
                        parsed = json.loads(data)
                        
                        print(f"✅ Success! Got {parsed.get('count', 0)} resources")
                        
                        rows = parsed.get('rows', [])
                        if rows:
                            print(f"\n📊 Sample rows with 'tipo' field:")
                            for i, row in enumerate(rows[:5], 1):
                                recurso = row.get('recurso', 'N/A')
                                tipo = row.get('tipo', 'N/A')  # This should now be the table name
                                categoria = row.get('categoria', 'N/A')
                                cantidad = row.get('cantidad', 0)
                                
                                print(f"   {i}. {recurso}")
                                print(f"      tipo: '{tipo}' (should be table name)")
                                print(f"      categoria: {categoria}")
                                print(f"      cantidad: {cantidad}")
                            
                            # Extract unique tipos for Neo4j testing
                            unique_tipos = list(set(row.get('tipo') for row in rows if row.get('tipo')))
                            print(f"\n🎯 Unique 'tipo' values (for Neo4j aliases): {unique_tipos}")
                            
                            # Save for testing
                            with open("fixed_geo_fetch_result.json", "w", encoding="utf-8") as f:
                                json.dump(parsed, f, indent=2, ensure_ascii=False)
                            print(f"💾 Results saved to: fixed_geo_fetch_result.json")
                            
                            return unique_tipos
                        
            except Exception as exc:
                print(f"❌ Test failed: {exc}")
                import traceback
                traceback.print_exc()
                return []


async def test_neo4j_with_fixed_tipos():
    """Test Neo4j with the fixed tipos from geo-fetch-mcp"""
    
    # First get the tipos from geo-fetch-mcp
    tipos = await test_fixed_geo_fetch()
    
    if not tipos:
        print("❌ No tipos to test with Neo4j")
        return
    
    print(f"\n🔄 Now testing these tipos with Neo4j...")
    
    try:
        from mcp.client.session import ClientSession  # type: ignore
        from mcp.client.stdio import stdio_client, StdioServerParameters  # type: ignore
    except Exception as exc:
        print(f"❌ Missing mcp client: {exc}")
        return

    server_path = Path("mcp-geo2neo/run_stdio.py")
    venv_python = Path("mcp-geo2neo/.venv/bin/python")
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    params = StdioServerParameters(command=python_cmd, args=[str(server_path)])
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            print(f"🧪 Testing map_by_aliases with tipos: {tipos}")
            
            try:
                result = await session.call_tool("map_by_aliases", {
                    "input": {"aliases": tipos}
                })
                
                blocks = getattr(result, "content", [])
                if blocks:
                    data = getattr(blocks[0], "data", None) or getattr(blocks[0], "text", None)
                    if isinstance(data, str):
                        parsed = json.loads(data)
                        count = parsed.get('count', 0)
                        
                        print(f"\n🎉 SUCCESS! Neo4j found {count} matches with fixed tipos!")
                        
                        if count > 0:
                            with open("neo4j_with_fixed_tipos.json", "w", encoding="utf-8") as f:
                                json.dump(parsed, f, indent=2, ensure_ascii=False)
                            print(f"💾 Neo4j results saved to: neo4j_with_fixed_tipos.json")
                            
                            results = parsed.get('results', [])
                            for i, result in enumerate(results, 1):
                                category = result.get('category', 'Unknown')
                                instruments = result.get('instrumentsAndPermits', [])
                                norms = result.get('associatedNorms', [])
                                print(f"   📂 {i}. {category}: {len(instruments)} instruments, {len(norms)} norms")
                        else:
                            print(f"❌ Still no matches - tipos might not match Neo4j aliases exactly")
                        
            except Exception as exc:
                print(f"❌ Neo4j test failed: {exc}")


if __name__ == "__main__":
    asyncio.run(test_neo4j_with_fixed_tipos())
