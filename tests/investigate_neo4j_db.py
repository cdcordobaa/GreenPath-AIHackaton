#!/usr/bin/env python3
"""
Deep investigation of Neo4j database content
"""
import asyncio
import json
import sys
from pathlib import Path


async def investigate_neo4j_database():
    """Comprehensive investigation of what's in the Neo4j database"""
    
    try:
        from mcp.client.session import ClientSession  # type: ignore
        from mcp.client.stdio import stdio_client, StdioServerParameters  # type: ignore
    except Exception as exc:
        print(f"❌ Missing mcp client: {exc}")
        return

    # Path to mcp-geo2neo server
    server_path = Path("mcp-geo2neo/run_stdio.py")
    venv_python = Path("mcp-geo2neo/.venv/bin/python")
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    params = StdioServerParameters(command=python_cmd, args=[str(server_path)])
    
    print("🔄 Connecting to mcp-geo2neo server for deep investigation...")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            print(f"📋 Available tools: {tool_names}")
            
            # Let's create custom Cypher queries to explore the database
            print(f"\n🔍 Let's investigate the database structure...")
            
            # First, let's see if we can run custom queries
            # We'll need to check if there's a way to run raw Cypher
            
            # Since we can't run raw Cypher directly through MCP tools,
            # let's try to understand what categories exist by testing many variations
            
            print(f"\n🧪 Testing extensive list of possible category aliases...")
            
            # Comprehensive list of possible aliases based on environmental categories
            possible_aliases = [
                # Spanish environmental terms
                "Flora", "Fauna", "Bosques", "Forestal", "Biodiversidad", "Ecosistemas",
                "Agua", "Suelo", "Aire", "Hidrología", "Hidrogeología", "Biología",
                "Suelos", "Biótico", "Gestión de Riesgo", "Compensación",
                
                # Full category names from your expected response
                "Gestión Integral de Flora y Bosques",
                "Flora y Bosques", "Recursos Hídricos", "Gestión del Agua",
                
                # Environmental management terms
                "Manejo Ambiental", "Impacto Ambiental", "Licencia Ambiental",
                "Permiso Ambiental", "Evaluación Ambiental",
                
                # Resource types
                "Recursos Naturales", "Recursos Forestales", "Recursos Hídricos",
                "Recursos Bióticos", "Recursos del Suelo",
                
                # Legal/regulatory terms
                "Normativa Ambiental", "Regulación Ambiental", "Marco Legal",
                "Instrumentos Legales", "Permisos", "Licencias",
                
                # Specific Colombian environmental terms
                "ANLA", "CAR", "MADS", "Ministerio Ambiente",
                "Corporación Autónoma Regional",
                
                # Technical categories
                "EIA", "Estudio Impacto Ambiental", "Plan Manejo Ambiental",
                "PMA", "Diagnóstico Ambiental",
                
                # Single letter/short codes that might be used
                "A", "B", "C", "F", "H", "S", "R", "E", "M", "L",
                
                # Numbers that might be category IDs
                "1", "2", "3", "4", "5", "10", "100",
                
                # Common English terms (in case DB has mixed languages)
                "Forest", "Water", "Soil", "Air", "Biodiversity", "Ecosystem",
                "Environmental", "Legal", "Permit", "License",
            ]
            
            # Test in batches to avoid overwhelming the system
            batch_size = 5
            found_matches = []
            
            for i in range(0, len(possible_aliases), batch_size):
                batch = possible_aliases[i:i+batch_size]
                print(f"\n🧪 Testing batch {i//batch_size + 1}: {batch}")
                
                try:
                    result = await session.call_tool("map_by_aliases", {
                        "input": {"aliases": batch}
                    })
                    
                    blocks = getattr(result, "content", [])
                    if blocks:
                        data = getattr(blocks[0], "data", None) or getattr(blocks[0], "text", None)
                        if isinstance(data, str):
                            try:
                                parsed = json.loads(data)
                                count = parsed.get('count', 0)
                                
                                if count > 0:
                                    print(f"   🎯 FOUND {count} MATCHES!")
                                    found_matches.extend(parsed.get('results', []))
                                    
                                    # Save this batch result
                                    filename = f"neo4j_found_batch_{i//batch_size + 1}.json"
                                    with open(filename, "w", encoding="utf-8") as f:
                                        json.dump(parsed, f, indent=2, ensure_ascii=False)
                                    print(f"   💾 Saved to: {filename}")
                                    
                                    # Show what we found
                                    for result_item in parsed.get('results', []):
                                        category = result_item.get('category', 'Unknown')
                                        print(f"      📂 Category: {category}")
                                else:
                                    print(f"   ❌ No matches in this batch")
                                    
                            except Exception as e:
                                print(f"   ❌ Parse error: {e}")
                        
                except Exception as exc:
                    print(f"   ❌ Call failed: {exc}")
                
                # Small delay to be nice to the database
                await asyncio.sleep(0.1)
            
            print(f"\n📊 INVESTIGATION SUMMARY:")
            print(f"   🔍 Tested {len(possible_aliases)} possible aliases")
            print(f"   🎯 Found {len(found_matches)} total matches")
            
            if found_matches:
                print(f"\n✅ SUCCESS! Found categories in the database:")
                unique_categories = set()
                for match in found_matches:
                    category = match.get('category', 'Unknown')
                    unique_categories.add(category)
                    
                for category in sorted(unique_categories):
                    print(f"   📂 {category}")
                
                # Save all found matches
                with open("neo4j_all_found_matches.json", "w", encoding="utf-8") as f:
                    json.dump(found_matches, f, indent=2, ensure_ascii=False)
                print(f"\n💾 All matches saved to: neo4j_all_found_matches.json")
                
            else:
                print(f"\n❌ No matches found. Possible reasons:")
                print(f"   - Neo4j database is empty")
                print(f"   - Database connection issues")
                print(f"   - Category aliases are completely different")
                print(f"   - Database structure is different than expected")
                
                # Let's also try some edge cases
                print(f"\n🔬 Trying edge cases...")
                edge_cases = [
                    [],  # Empty array
                    [""],  # Empty string
                    [" "],  # Whitespace
                    ["*"],  # Wildcard
                    ["test"],  # Generic test
                ]
                
                for edge_case in edge_cases:
                    try:
                        result = await session.call_tool("map_by_aliases", {
                            "input": {"aliases": edge_case}
                        })
                        blocks = getattr(result, "content", [])
                        if blocks:
                            data = getattr(blocks[0], "data", None) or getattr(blocks[0], "text", None)
                            if isinstance(data, str):
                                parsed = json.loads(data)
                                print(f"   Edge case {edge_case}: {parsed.get('count', 0)} results")
                    except Exception as e:
                        print(f"   Edge case {edge_case}: Error - {e}")


if __name__ == "__main__":
    asyncio.run(investigate_neo4j_database())
