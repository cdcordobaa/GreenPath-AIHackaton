#!/usr/bin/env python3
"""
Test script for the EIA-ADK workflow.

This script will test the multi-agent pipeline step by step to help debug any issues.
"""

import os
import sys
import json
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Set environment variables
os.environ["EIA_USE_MOCKS"] = "0"  # Use real MCP tools
os.environ["EIA_MODEL_PRIMARY"] = "gemini-2.5-flash"
os.environ["EIA_MODEL_FALLBACK"] = "gemini-1.5-flash"

def test_mcp_connectivity():
    """Test that MCP servers are accessible."""
    print("🔌 Testing MCP server connectivity...")
    
    # Test geo-fetch-mcp
    try:
        from src.eia_adk.agents.tools import structured_summary_via_mcp
        result = structured_summary_via_mcp({
            "project": {"project_id": "test-project"}
        })
        geo_status = "✅" if result.get("geo", {}).get("structured_summary", {}).get("count", 0) > 0 else "⚠️"
        print(f"   {geo_status} geo-fetch-mcp: {result.get('geo', {}).get('structured_summary', {}).get('count', 0)} resources")
    except Exception as e:
        print(f"   ❌ geo-fetch-mcp error: {e}")
    
    # Test mcp-geo2neo
    try:
        from src.eia_adk.agents.tools import geo2neo_from_structured_summary
        test_state = {
            "geo": {
                "structured_summary": {
                    "rows": [
                        {"tipo": "Suelos"},
                        {"tipo": "Hidrología"}
                    ]
                }
            }
        }
        result = geo2neo_from_structured_summary(test_state)
        geo2neo_status = "✅" if result.get("legal", {}).get("geo2neo", {}).get("alias_mapping", {}).get("ok") else "⚠️"
        print(f"   {geo2neo_status} mcp-geo2neo: {result.get('legal', {}).get('geo2neo', {}).get('alias_mapping', {}).get('count', 0)} mappings")
    except Exception as e:
        print(f"   ❌ mcp-geo2neo error: {e}")

def test_pipeline_steps():
    """Test the pipeline step by step."""
    print("\n🔧 Testing pipeline steps...")
    
    # Import the pipeline components
    try:
        from src.eia_adk.agents.tools import (
            configure_project,
            run_geospatial_with_config,
            synthesize_intersections,
            summarize_impacts,
            resolve_legal_scope,
            legal_requirements,
            assemble_report
        )
        
        # Step 1: Configure project
        print("   1️⃣ Configuring project...")
        state = configure_project(
            target_layers=["soils", "biotic", "hidrology"],
            project_path="data/sample_project/lines.geojson",
            layer_type="lines"
        )
        print(f"      ✅ Project configured: {state.get('project', {}).get('project_name', 'Unknown')}")
        
        # Step 2: Run geospatial analysis
        print("   2️⃣ Running geospatial analysis...")
        state = run_geospatial_with_config(state)
        geo_count = state.get("geo", {}).get("structured_summary", {}).get("count", 0)
        print(f"      ✅ Geospatial analysis: {geo_count} resources found")
        
        # Step 3: Geo2Neo mapping
        print("   3️⃣ Running geo2neo mapping...")
        from src.eia_adk.agents.tools import geo2neo_from_structured_summary
        state = geo2neo_from_structured_summary(state)
        mapping_count = state.get("legal", {}).get("geo2neo", {}).get("alias_mapping", {}).get("count", 0)
        print(f"      ✅ Geo2Neo mapping: {mapping_count} categories mapped")
        
        # Step 4: Knowledge base search
        print("   4️⃣ Running knowledge base search...")
        from src.eia_adk.agents.tools import geo_kb_search_from_state
        state = geo_kb_search_from_state(state)
        kb_count = state.get("legal", {}).get("kb", {}).get("scraped_pages", {}).get("count", 0)
        print(f"      ✅ Knowledge base search: {kb_count} documents found")
        
        print(f"\n📊 Final state summary:")
        print(f"   • Resources: {state.get('geo', {}).get('structured_summary', {}).get('count', 0)}")
        print(f"   • Mappings: {state.get('legal', {}).get('geo2neo', {}).get('alias_mapping', {}).get('count', 0)}")
        print(f"   • Documents: {state.get('legal', {}).get('kb', {}).get('scraped_pages', {}).get('count', 0)}")
        
        return state
        
    except Exception as e:
        print(f"   ❌ Pipeline error: {e}")
        import traceback
        traceback.print_exc()
        return None

def test_agent_interaction():
    """Test the agent interaction using ADK tools."""
    print("\n🤖 Testing agent interactions...")
    
    try:
        # Import the root agent
        from src.root_agent import root_agent
        
        # Test the pipeline tool
        from src.eia_adk.agents.tools import run_pipeline_tool
        result = run_pipeline_tool(
            project_path="data/sample_project/lines.geojson",
            target_layers=["soils", "biotic", "hidrology"]
        )
        
        print(f"   ✅ Pipeline tool executed successfully")
        print(f"   📊 Result keys: {list(result.keys()) if isinstance(result, dict) else 'Not a dict'}")
        
        return result
        
    except Exception as e:
        print(f"   ❌ Agent interaction error: {e}")
        import traceback
        traceback.print_exc()
        return None

def main():
    """Main test function."""
    print("🚀 EIA-ADK Workflow Test")
    print("=" * 50)
    
    # Test 1: MCP connectivity
    test_mcp_connectivity()
    
    # Test 2: Pipeline steps
    pipeline_result = test_pipeline_steps()
    
    # Test 3: Agent interaction
    agent_result = test_agent_interaction()
    
    print("\n" + "=" * 50)
    if pipeline_result and agent_result:
        print("🎉 All tests passed! The workflow is working correctly.")
        print("\n📝 You can now test in the ADK web interface:")
        print("   1. Open http://127.0.0.1:8000/dev-ui")
        print("   2. Select app 'src'")
        print('   3. Try: "Analiza: project_path=data/sample_project/lines.geojson target_layers=[\\"soils\\",\\"biotic\\",\\"hidrology\\"]"')
    else:
        print("❌ Some tests failed. Check the errors above.")

if __name__ == "__main__":
    main()
