#!/usr/bin/env python3
"""
Test script to test ONLY the geo_kb_agent (the last node) with provided state data.
This simulates what happens after geo2neo_agent has completed.
"""

import os
import sys
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["EIA_USE_MOCKS"] = "0"  # Use real MCP tools

def test_geo_kb_agent_only():
    """Test ONLY the geo_kb_agent with the provided state data."""
    print("🔍 Testing geo_kb_agent (Last Node) Only")
    print("=" * 60)
    
    # Your provided state data
    state_data = {
        "config": {
            "layers": [
                "soils",
                "biotic",
                "hidrology"
            ]
        },
        "geo": {
            "by_layer": {},
            "intersections": {},
            "structured_summary": {
                "count": 21,
                "rows": [
                    {
                        "cantidad": 505,
                        "categoria": "SOILS",
                        "recurso": "Suelos",
                        "recurso1": "Suelos",
                        "tipo": "Suelos"
                    },
                    {
                        "cantidad": 19,
                        "categoria": "HYDROLOGY",
                        "recurso": "Cuencas Hidrográficas",
                        "recurso1": "Cuencas Hidrográficas",
                        "tipo": "Hidrología"
                    },
                    {
                        "cantidad": 2,
                        "categoria": "HYDROLOGY",
                        "recurso": "Ocupación de Cauce",
                        "recurso1": "Ocupación de Cauce",
                        "tipo": "Hidrología"
                    },
                    {
                        "cantidad": 32,
                        "categoria": "HYDROLOGY",
                        "recurso": "Agua Superficial",
                        "recurso1": "Agua Superficial",
                        "tipo": "Hidrología"
                    },
                    {
                        "cantidad": 174,
                        "categoria": "HYDROLOGY",
                        "recurso": "Uso Recursos Hídricos",
                        "recurso1": "Uso Recursos Hídricos",
                        "tipo": "Hidrología"
                    },
                    {
                        "cantidad": 208,
                        "categoria": "HYDROGEOLOGY",
                        "recurso": "Hidrogeología",
                        "recurso1": "Hidrogeología",
                        "tipo": "Hidrogeología"
                    },
                    {
                        "cantidad": 21,
                        "categoria": "HYDROGEOLOGY",
                        "recurso": "Agua Subterránea",
                        "recurso1": "Agua Subterránea",
                        "tipo": "Hidrogeología"
                    },
                    {
                        "cantidad": 1000,
                        "categoria": "BIOTIC",
                        "recurso": "Aprovechamiento Forestal (Polígono)",
                        "recurso1": "Aprovechamiento Forestal (Polígono)",
                        "tipo": "Biótico"
                    },
                    {
                        "cantidad": 1000,
                        "categoria": "BIOTIC",
                        "recurso": "Aprovechamiento Forestal (Punto)",
                        "recurso1": "Aprovechamiento Forestal (Punto)",
                        "tipo": "Biótico"
                    },
                    {
                        "cantidad": 1000,
                        "categoria": "BIOTIC",
                        "recurso": "Cobertura de Tierra",
                        "recurso1": "Cobertura de Tierra",
                        "tipo": "Biótico"
                    },
                    {
                        "cantidad": 1000,
                        "categoria": "BIOTIC",
                        "recurso": "Ecosistemas",
                        "recurso1": "Ecosistemas",
                        "tipo": "Biótico"
                    },
                    {
                        "cantidad": 253,
                        "categoria": "BIOTIC",
                        "recurso": "Fauna",
                        "recurso1": "Fauna",
                        "tipo": "Biótico"
                    },
                    {
                        "cantidad": 501,
                        "categoria": "BIOTIC",
                        "recurso": "Flora",
                        "recurso1": "Flora",
                        "tipo": "Biótico"
                    },
                    {
                        "cantidad": 187,
                        "categoria": "BIOTIC",
                        "recurso": "Transectos Fauna",
                        "recurso1": "Transectos Fauna",
                        "tipo": "Biótico"
                    },
                    {
                        "cantidad": 1000,
                        "categoria": "RISK_MANAGEMENT",
                        "recurso": "amenazaotras",
                        "recurso1": "amenazaotras",
                        "tipo": "Gestión de Riesgo"
                    },
                    {
                        "cantidad": 1000,
                        "categoria": "RISK_MANAGEMENT",
                        "recurso": "elementosexpuestosln",
                        "recurso1": "elementosexpuestosln",
                        "tipo": "Gestión de Riesgo"
                    },
                    {
                        "cantidad": 1000,
                        "categoria": "RISK_MANAGEMENT",
                        "recurso": "elementosexpuestospt",
                        "recurso1": "elementosexpuestospt",
                        "tipo": "Gestión de Riesgo"
                    },
                    {
                        "cantidad": 1000,
                        "categoria": "RISK_MANAGEMENT",
                        "recurso": "suscept_incendios",
                        "recurso1": "suscept_incendios",
                        "tipo": "Gestión de Riesgo"
                    },
                    {
                        "cantidad": 280,
                        "categoria": "RISK_MANAGEMENT",
                        "recurso": "suscept_inundaciones",
                        "recurso1": "suscept_inundaciones",
                        "tipo": "Gestión de Riesgo"
                    },
                    {
                        "cantidad": 1000,
                        "categoria": "RISK_MANAGEMENT",
                        "recurso": "vulnerabilidad_pt",
                        "recurso1": "vulnerabilidad_pt",
                        "tipo": "Gestión de Riesgo"
                    },
                    {
                        "cantidad": 37,
                        "categoria": "COMPENSATION",
                        "recurso": "Compensación Biodiversidad",
                        "recurso1": "Compensación Biodiversidad",
                        "tipo": "Compensación"
                    }
                ]
            },
            "summary": {}
        },
        "impacts": {
            "categories": [],
            "entities": []
        },
        "legal": {
            "candidates": [],
            "geo2neo": {
                "alias_input": [
                    "Biótico",
                    "Compensación",
                    "Gestión de Riesgo",
                    "Hidrogeología",
                    "Hidrología",
                    "Suelos"
                ],
                "alias_mapping": {
                    "count": 0,
                    "meta": {
                        "counters": {},
                        "t_consumed": 3,
                        "t_first": 105
                    },
                    "ok": True,
                    "results": []
                }
            },
            "requirements": []
        },
        "project": {
            "project_id": "proj_001",
            "project_name": "Linea_110kV_Z"
        }
    }
    
    try:
        # Direct import to avoid ADK dependencies
        sys.path.insert(0, str(Path(__file__).parent / "src" / "eia_adk" / "agents"))
        from tools import geo_kb_search_from_state
        
        print("📋 INPUT STATE FOR geo_kb_agent:")
        print("=" * 40)
        
        # Show what the agent will read
        geo2neo_data = state_data.get("legal", {}).get("geo2neo", {})
        structured_summary = state_data.get("geo", {}).get("structured_summary", {})
        
        print(f"📖 Reading state.legal.geo2neo.alias_input: {geo2neo_data.get('alias_input', [])}")
        print(f"📖 Reading state.legal.geo2neo.alias_mapping.results: {len(geo2neo_data.get('alias_mapping', {}).get('results', []))}")
        print(f"📖 Reading state.geo.structured_summary.rows: {len(structured_summary.get('rows', []))}")
        
        # Extract unique tipos for reference
        tipos = list(set(row.get("tipo") for row in structured_summary.get("rows", []) if row.get("tipo")))
        print(f"📖 Available tipos in structured_summary: {tipos}")
        
        # Execute the geo_kb_agent function
        print("\n🔍 EXECUTING geo_kb_search_from_state...")
        print("=" * 40)
        
        result_state = geo_kb_search_from_state(state_data)
        
        # Verify the output
        kb_data = result_state.get("legal", {}).get("kb", {})
        keywords = kb_data.get("keywords", [])
        scraped_pages = kb_data.get("scraped_pages", {})
        
        print("✅ RESULTS:")
        print(f"   📝 Keywords derived: {keywords}")
        print(f"   📄 Scraped pages count: {scraped_pages.get('count', 0)}")
        print(f"   📄 Scraped pages rows: {len(scraped_pages.get('rows', []))}")
        
        if scraped_pages.get('rows'):
            print("\n📄 Sample scraped page:")
            sample = scraped_pages['rows'][0]
            for key, value in sample.items():
                if isinstance(value, str) and len(value) > 100:
                    print(f"   {key}: {value[:100]}...")
                else:
                    print(f"   {key}: {value}")
        
        # Verify state structure
        print("\n📊 FINAL STATE STRUCTURE:")
        print("=" * 40)
        final_legal = result_state.get("legal", {})
        print(f"   legal.geo2neo: {list(final_legal.get('geo2neo', {}).keys())}")
        print(f"   legal.kb: {list(final_legal.get('kb', {}).keys())}")
        
        # Check if kb was properly populated
        kb_present = 'kb' in final_legal and len(final_legal['kb'].get('keywords', [])) > 0
        
        print(f"\n{'✅' if kb_present else '❌'} geo_kb_agent {'SUCCESS' if kb_present else 'FAILED'}")
        
        if kb_present:
            print("\n🎉 geo_kb_agent completed successfully!")
            print(f"   📝 Derived {len(keywords)} keywords")
            print(f"   📄 Found {scraped_pages.get('count', 0)} relevant pages")
            print("\n🌟 This was the final step in your workflow!")
            print("   Your workflow is now complete with legal knowledge base populated.")
        else:
            print("\n❌ geo_kb_agent failed to populate legal.kb")
            print("   Check MCP connection and keyword derivation logic")
            
        return kb_present
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main test function."""
    print("🚀 Testing the LAST NODE (geo_kb_agent) only")
    print("This simulates what happens after all previous agents completed\n")
    
    success = test_geo_kb_agent_only()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 geo_kb_agent (LAST NODE) test PASSED!")
        print("\n✅ Successfully populated legal.kb with scraped pages")
        print("✅ Derived keywords from geo2neo and structured_summary")
        print("✅ Workflow completed - ready for next phase")
    else:
        print("❌ geo_kb_agent (LAST NODE) test FAILED!")
        print("   Check MCP connectivity and troubleshoot the specific issue")
        
    print("\n💡 TIP: If this works, your full workflow should work!")
    print("   The previous agents already populated the state correctly.")


if __name__ == "__main__":
    main()
