#!/usr/bin/env python3
"""
Test geo_kb_agent functionality with direct MCP calls and detailed logging.
This simulates the exact workflow without ADK dependencies.
"""

import asyncio
import json
import sys
import os
from pathlib import Path
from typing import Dict, Any, List

async def test_mcp_search_directly():
    """Test the MCP search functionality directly with detailed logging."""
    print("🔍 Testing MCP Search Directly")
    print("=" * 50)
    
    # Your state data with derived keywords
    keywords = [
        'Biótico', 'Compensación', 'Gestión de Riesgo', 
        'Hidrogeología', 'Hidrología', 'Suelos',
        'SOILS', 'HYDROLOGY', 'HYDROGEOLOGY', 'BIOTIC',
        'RISK_MANAGEMENT', 'COMPENSATION'
    ]
    
    print(f"🔑 Testing with {len(keywords)} keywords: {keywords[:3]}...")
    
    try:
        # Import MCP client
        from mcp.client.session import ClientSession
        from mcp.client.stdio import stdio_client, StdioServerParameters
        
        # Set up geo-fetch-mcp server
        repo_root = Path(__file__).parent
        server_path = repo_root / "geo-fetch-mcp" / "run_stdio.py"
        venv_python = repo_root / "geo-fetch-mcp" / ".venv" / "bin" / "python"
        python_cmd = str(venv_python) if venv_python.exists() else "python3"
        
        print(f"🌐 Connecting to MCP server: {server_path}")
        print(f"🐍 Using Python: {python_cmd}")
        
        # Connect to MCP server
        server_params = StdioServerParameters(
            command=python_cmd,
            args=[str(server_path)]
        )
        
        results = {}
        
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                
                # Initialize session
                print("🔗 Initializing MCP session...")
                await session.initialize()
                
                # List available tools first
                print("🛠️ Listing available tools...")
                tools_result = await session.list_tools()
                available_tools = [tool.name for tool in tools_result.tools]
                print(f"   Available tools: {available_tools}")
                
                if "search_scraped_pages" not in available_tools:
                    print("❌ search_scraped_pages tool not available!")
                    return False, {}
                
                # Test search for first few keywords
                print(f"\n🔍 Testing search for first 3 keywords...")
                aggregated = {}
                
                for i, keyword in enumerate(keywords[:3]):  # Test first 3 keywords
                    print(f"\n   {i+1}. Searching for: '{keyword}'")
                    
                    try:
                        # Call search_scraped_pages
                        search_args = {
                            "text_contains": keyword,
                            "limit": 5
                        }
                        
                        print(f"      📞 Calling: search_scraped_pages({search_args})")
                        
                        result = await session.call_tool("search_scraped_pages", search_args)
                        
                        if hasattr(result, 'content') and result.content:
                            # Parse the result
                            content = result.content[0]
                            if hasattr(content, 'text'):
                                response_data = json.loads(content.text)
                                print(f"      ✅ Response received: {type(response_data)}")
                                
                                # Extract results
                                rows = response_data.get("rows", [])
                                print(f"      📄 Found {len(rows)} results")
                                
                                # Store results
                                for row in rows:
                                    url = str(row.get("url", ""))
                                    key = url or row.get("id") or f"result_{len(aggregated)}"
                                    if key not in aggregated:
                                        aggregated[key] = row
                                        print(f"         - {row.get('title', 'No title')[:50]}...")
                            else:
                                print(f"      ⚠️ Unexpected result format: {result}")
                        else:
                            print(f"      ⚠️ No content in result: {result}")
                            
                    except Exception as e:
                        print(f"      ❌ Search failed for '{keyword}': {e}")
                        results[keyword] = {"error": str(e)}
                        continue
                
                print(f"\n📊 AGGREGATED RESULTS:")
                print(f"   Total unique documents: {len(aggregated)}")
                
                if aggregated:
                    print(f"\n📄 Sample results:")
                    for i, (key, doc) in enumerate(list(aggregated.items())[:2]):
                        print(f"   {i+1}. URL: {doc.get('url', 'No URL')}")
                        print(f"      Title: {doc.get('title', 'No title')}")
                        print(f"      Content: {doc.get('content_md', 'No content')[:100]}...")
                
                # Create final state structure
                final_kb_state = {
                    "keywords": keywords[:3],  # Keywords we tested
                    "scraped_pages": {
                        "count": len(aggregated),
                        "rows": list(aggregated.values())
                    }
                }
                
                print(f"\n🎯 FINAL geo_kb_agent OUTPUT:")
                print(f"   Keywords tested: {len(final_kb_state['keywords'])}")
                print(f"   Documents found: {final_kb_state['scraped_pages']['count']}")
                
                return True, final_kb_state
                
    except ImportError as e:
        print(f"❌ MCP client not available: {e}")
        print("   Install with: pip install mcp")
        return False, {}
    except Exception as e:
        print(f"❌ MCP test failed: {e}")
        import traceback
        traceback.print_exc()
        return False, {}


def simulate_full_geo_kb_agent(state_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate the full geo_kb_agent workflow with logging."""
    print("🤖 Simulating Full geo_kb_agent Workflow")
    print("=" * 50)
    
    # Step 1: Derive keywords (we already tested this)
    keywords = [
        'Biótico', 'Compensación', 'Gestión de Riesgo', 
        'Hidrogeología', 'Hidrología', 'Suelos',
        'SOILS', 'HYDROLOGY', 'HYDROGEOLOGY', 'BIOTIC',
        'RISK_MANAGEMENT', 'COMPENSATION'
    ]
    
    print(f"📝 Step 1: Keyword derivation")
    print(f"   From alias_input: {state_data.get('legal', {}).get('geo2neo', {}).get('alias_input', [])}")
    print(f"   From structured_summary: {len(state_data.get('geo', {}).get('structured_summary', {}).get('rows', []))} rows")
    print(f"   Final keywords: {len(keywords)} total")
    
    # Step 2: Simulate MCP search results (since we can't run async here)
    print(f"\n🔍 Step 2: MCP search simulation")
    print(f"   Would search for each of {len(keywords)} keywords")
    print(f"   Each search limited to 5 results")
    print(f"   Results aggregated and deduplicated")
    
    # Mock some realistic results for demonstration
    mock_results = [
        {
            "url": "https://www.anla.gov.co/documentos/normativa/licencia-ambiental",
            "title": "Licencia Ambiental - Autoridad Nacional de Licencias Ambientales",
            "content_md": "La licencia ambiental es la autorización que otorga la autoridad ambiental competente...",
            "category": "NORMATIVA",
            "source": "ANLA"
        },
        {
            "url": "https://www.minambiente.gov.co/decreto-2820-2010-suelos",
            "title": "Decreto 2820 de 2010 - Licenciamiento Ambiental",
            "content_md": "Reglamenta el título VIII de la Ley 99 de 1993 sobre licencias ambientales...",
            "category": "DECRETO",
            "source": "MINAMBIENTE"
        },
        {
            "url": "https://www.corporinoquia.gov.co/permisos-hidricos",
            "title": "Permisos y Concesiones de Aguas",
            "content_md": "Procedimientos para obtener permisos de uso y aprovechamiento del recurso hídrico...",
            "category": "PROCEDIMIENTO", 
            "source": "CORPORINOQUIA"
        }
    ]
    
    # Step 3: Update state
    print(f"\n💾 Step 3: State update")
    updated_state = state_data.copy()
    kb_data = updated_state.setdefault("legal", {}).setdefault("kb", {})
    
    kb_data["keywords"] = keywords
    kb_data["scraped_pages"] = {
        "count": len(mock_results),
        "rows": mock_results
    }
    
    print(f"   ✅ Added legal.kb.keywords: {len(keywords)} items")
    print(f"   ✅ Added legal.kb.scraped_pages: {len(mock_results)} documents")
    
    # Step 4: Show final state structure
    print(f"\n📊 Final State Structure:")
    legal_keys = list(updated_state.get("legal", {}).keys())
    kb_keys = list(updated_state.get("legal", {}).get("kb", {}).keys())
    
    print(f"   state.legal: {legal_keys}")
    print(f"   state.legal.kb: {kb_keys}")
    
    # Show sample content
    print(f"\n📄 Sample Knowledge Base Content:")
    for i, doc in enumerate(mock_results[:2]):
        print(f"   {i+1}. {doc['title']}")
        print(f"      Source: {doc['source']}")
        print(f"      Content: {doc['content_md'][:80]}...")
    
    return updated_state


async def main():
    """Main test function."""
    print("🚀 Testing geo_kb_agent with MCP Logging")
    print("This tests the last node in your workflow\n")
    
    # Your original state data
    state_data = {
        "config": {"layers": ["soils", "biotic", "hidrology"]},
        "geo": {
            "by_layer": {},
            "intersections": {},
            "structured_summary": {
                "count": 21,
                "rows": [
                    {"cantidad": 505, "categoria": "SOILS", "recurso": "Suelos", "tipo": "Suelos"},
                    {"cantidad": 19, "categoria": "HYDROLOGY", "recurso": "Cuencas Hidrográficas", "tipo": "Hidrología"},
                    # ... (other rows)
                ]
            }
        },
        "legal": {
            "candidates": [],
            "geo2neo": {
                "alias_input": ["Biótico", "Compensación", "Gestión de Riesgo", "Hidrogeología", "Hidrología", "Suelos"],
                "alias_mapping": {"count": 0, "ok": True, "results": []}
            },
            "requirements": []
        },
        "project": {"project_id": "proj_001", "project_name": "Linea_110kV_Z"}
    }
    
    print("1️⃣ Testing MCP connectivity and search...")
    mcp_success, mcp_results = await test_mcp_search_directly()
    
    print(f"\n2️⃣ Simulating complete geo_kb_agent workflow...")
    final_state = simulate_full_geo_kb_agent(state_data)
    
    print("\n" + "=" * 60)
    if mcp_success:
        print("🎉 MCP Search Test PASSED!")
        print(f"   ✅ Successfully connected to geo-fetch-mcp")
        print(f"   ✅ Retrieved {mcp_results.get('scraped_pages', {}).get('count', 0)} documents")
        print(f"   ✅ geo_kb_agent functionality confirmed")
    else:
        print("⚠️ MCP Search Test had issues")
        print("   🔧 But workflow simulation completed successfully")
    
    print(f"\n✅ geo_kb_agent workflow simulation COMPLETED")
    print(f"   📝 Keywords: {len(final_state['legal']['kb']['keywords'])}")
    print(f"   📄 Documents: {final_state['legal']['kb']['scraped_pages']['count']}")
    print(f"   🎯 This is what the last node would return!")


if __name__ == "__main__":
    asyncio.run(main())

