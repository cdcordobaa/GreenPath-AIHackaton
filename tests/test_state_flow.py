#!/usr/bin/env python3
"""
Test script to verify the EIA-ADK state flow between agents.
This script simulates the agent workflow and checks state transitions.
"""

import os
import sys
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["EIA_USE_MOCKS"] = "0"  # Use real MCP tools

def test_state_flow():
    """Test the state flow through the agent chain."""
    print("🔄 Testing EIA-ADK State Flow")
    print("=" * 50)
    
    try:
        from src.eia_adk.agents.tools import (
            configure_project,
            structured_summary_via_mcp,
            geo2neo_from_structured_summary,
            geo_kb_search_from_state
        )
        
        # Step 1: Configure project (ingest_agent simulation)
        print("1️⃣ Testing ingest_agent → configure_project")
        state = configure_project(
            target_layers=["soils", "biotic", "hidrology"],
            project_path="data/sample_project/lines.geojson",
            layer_type="lines"
        )
        
        # Verify state.project exists
        project = state.get("project", {})
        print(f"   ✅ project_id: {project.get('project_id')}")
        print(f"   ✅ project_name: {project.get('project_name')}")
        print(f"   ✅ config.layers: {project.get('config', {}).get('layers')}")
        
        # Step 2: Get structured summary (geo_agent simulation)
        print("\n2️⃣ Testing geo_agent → structured_summary_via_mcp")
        print(f"   📖 Reading from: state.project.project_id = {project.get('project_id')}")
        
        state = structured_summary_via_mcp(state)
        
        # Verify state.geo.structured_summary exists
        geo_summary = state.get("geo", {}).get("structured_summary", {})
        if "error" in geo_summary:
            print(f"   ❌ Error: {geo_summary['error']}")
            return False
        else:
            count = geo_summary.get("count", 0)
            rows = geo_summary.get("rows", [])
            print(f"   ✅ structured_summary.count: {count}")
            print(f"   ✅ structured_summary.rows length: {len(rows)}")
            if rows:
                sample_row = rows[0]
                print(f"   ✅ Sample row: {sample_row}")
        
        # Step 3: Map to Neo4j categories (geo2neo_agent simulation)
        print("\n3️⃣ Testing geo2neo_agent → geo2neo_from_structured_summary")
        tipos = [row.get("tipo") for row in geo_summary.get("rows", []) if row.get("tipo")]
        print(f"   📖 Reading from: state.geo.structured_summary.rows → tipos: {list(set(tipos))}")
        
        state = geo2neo_from_structured_summary(state)
        
        # Verify state.legal.geo2neo exists
        geo2neo = state.get("legal", {}).get("geo2neo", {})
        alias_input = geo2neo.get("alias_input", [])
        alias_mapping = geo2neo.get("alias_mapping", {})
        print(f"   ✅ geo2neo.alias_input: {alias_input}")
        print(f"   ✅ geo2neo.alias_mapping.ok: {alias_mapping.get('ok')}")
        print(f"   ✅ geo2neo.alias_mapping.count: {alias_mapping.get('count', 0)}")
        
        # Step 4: Search knowledge base (geo_kb_agent simulation)
        print("\n4️⃣ Testing geo_kb_agent → geo_kb_search_from_state")
        print(f"   📖 Reading from: state.legal.geo2neo.alias_input: {alias_input}")
        print(f"   📖 Reading from: state.legal.geo2neo.alias_mapping.results: {len(alias_mapping.get('results', []))}")
        print(f"   📖 Reading from: state.geo.structured_summary.rows: {len(geo_summary.get('rows', []))}")
        
        state = geo_kb_search_from_state(state)
        
        # Verify state.legal.kb exists
        kb = state.get("legal", {}).get("kb", {})
        keywords = kb.get("keywords", [])
        scraped_pages = kb.get("scraped_pages", {})
        print(f"   ✅ kb.keywords: {keywords}")
        print(f"   ✅ kb.scraped_pages.count: {scraped_pages.get('count', 0)}")
        
        # Final state summary
        print("\n📊 FINAL STATE STRUCTURE:")
        final_keys = {
            "project": list(state.get("project", {}).keys()),
            "geo": list(state.get("geo", {}).keys()),
            "legal": {
                k: list(v.keys()) if isinstance(v, dict) else str(type(v)) 
                for k, v in state.get("legal", {}).items()
            }
        }
        print(f"   {json.dumps(final_keys, indent=2)}")
        
        # Verify all expected keys exist
        required_paths = [
            ("project", "project_id"),
            ("project", "project_name"),
            ("geo", "structured_summary"),
            ("legal", "geo2neo"),
            ("legal", "kb")
        ]
        
        all_paths_exist = True
        for path in required_paths:
            current_level = state
            path_str = ""
            for key in path:
                path_str += f".{key}" if path_str else key
                if key not in current_level:
                    print(f"   ❌ Missing: state.{path_str}")
                    all_paths_exist = False
                    break
                current_level = current_level[key]
            
            if key in current_level:
                print(f"   ✅ Found: state.{path_str}")
        
        return all_paths_exist
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    success = test_state_flow()
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 State flow verification PASSED!")
        print("\n✅ All agents correctly read from and write to shared state")
        print("✅ State dependencies are properly connected")
        print("✅ Ready for ADK web interface testing")
        print("\n🌐 Test in ADK web interface:")
        print('   "Analiza: project_path=data/sample_project/lines.geojson target_layers=[\\"soils\\",\\"biotic\\",\\"hidrology\\"]"')
    else:
        print("❌ State flow verification FAILED!")
        print("   Check the errors above and fix state reading/writing issues")

if __name__ == "__main__":
    main()
