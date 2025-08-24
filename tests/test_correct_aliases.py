#!/usr/bin/env python3
"""
Test with the correct aliases found in the Neo4j database
"""
import asyncio
import json
import sys
from pathlib import Path


async def test_correct_aliases():
    """Test map_by_aliases with the actual aliases from the database"""
    
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
    
    print("🧪 Testing with CORRECT aliases from Neo4j database...")
    
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            
            # Test with the actual aliases we found in the database
            correct_aliases = [
                # From Gestión Integral del Recurso Hídrico
                'puntohidrogeologico',
                'puntomuestreoaguasubter', 
                'puntomuestreoaguasuper',
                'usosyusuariosrecursohidrico',
                
                # From Gestión Integral de Flora y Bosques  
                'aprovechaforestalpg',
                'aprovechaforestalpt',
                'puntomuestreoflora',
                
                # From Gestión Integral de la Biodiversidad
                'compensacionbiodiversidad',
                'puntomuestreofauna', 
                'transectomuestreofauna'
            ]
            
            print(f"🎯 Testing with aliases: {correct_aliases}")
            
            try:
                result = await session.call_tool("map_by_aliases", {
                    "input": {"aliases": correct_aliases}
                })
                
                blocks = getattr(result, "content", [])
                if blocks:
                    data = getattr(blocks[0], "data", None) or getattr(blocks[0], "text", None)
                    if isinstance(data, str):
                        parsed = json.loads(data)
                        count = parsed.get('count', 0)
                        
                        print(f"\n🎉 SUCCESS! Found {count} matches!")
                        
                        if count > 0:
                            # Save the results
                            with open("neo4j_correct_results.json", "w", encoding="utf-8") as f:
                                json.dump(parsed, f, indent=2, ensure_ascii=False)
                            print(f"💾 Results saved to: neo4j_correct_results.json")
                            
                            # Show the structure
                            results = parsed.get('results', [])
                            for i, result in enumerate(results, 1):
                                category = result.get('category', 'Unknown')
                                instruments = result.get('instrumentsAndPermits', [])
                                norms = result.get('associatedNorms', [])
                                
                                print(f"\n📂 {i}. Category: {category}")
                                print(f"   🔧 Instruments: {len(instruments)}")
                                print(f"   📜 Norms: {len(norms)}")
                                
                                # Show first instrument details
                                if instruments:
                                    first_instrument = instruments[0]
                                    print(f"   📋 First Instrument: {first_instrument.get('instrumentName', 'N/A')}")
                                    modalities = first_instrument.get('modalities', [])
                                    print(f"      Modalities: {len(modalities)}")
                                
                                # Show first norm details  
                                if norms:
                                    first_norm = norms[0]
                                    print(f"   📋 First Norm: {first_norm.get('normName', 'N/A')}")
                                    print(f"      Issuer: {first_norm.get('issuer', 'N/A')}")
                        
                        print(f"\n✅ This confirms the database has the expected complex structure!")
                        print(f"🔧 Now we need to fix the alias mapping in geo-fetch-mcp")
                        
            except Exception as exc:
                print(f"❌ Test failed: {exc}")
                import traceback
                traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_correct_aliases())
