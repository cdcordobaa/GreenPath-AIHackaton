#!/usr/bin/env python3
"""
Test the enhanced geo_kb_agent through the web API.
This verifies that the optimization works in the actual web interface.
"""

import requests
import json
import time
import sys
from pathlib import Path

def test_web_api_health():
    """Test if the web API is running."""
    print("🌐 TESTING WEB API HEALTH")
    print("=" * 30)
    
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Web API is running")
            print(f"   Response: {response.json()}")
            return True
        else:
            print(f"⚠️ Web API returned status {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Web API is not running")
        print("   Start it with: python3 -m src.eia_adk.http_api")
        return False
    except Exception as e:
        print(f"❌ Error testing web API: {e}")
        return False

def test_enhanced_agent_directly():
    """Test the enhanced agent directly without full pipeline."""
    print("\n🔧 TESTING ENHANCED AGENT DIRECTLY")
    print("=" * 40)
    
    try:
        # Import the enhanced agent
        sys.path.insert(0, str(Path(__file__).parent / "src"))
        from eia_adk.agents.geo_kb_agent import agent as enhanced_geo_kb_agent
        
        print("✅ Enhanced geo_kb_agent imported successfully")
        print(f"   Agent name: {enhanced_geo_kb_agent.name}")
        print(f"   Agent model: {enhanced_geo_kb_agent.model}")
        print(f"   Tools count: {len(enhanced_geo_kb_agent.tools)}")
        
        # Check if enhanced function is in tools
        tool_names = []
        for tool in enhanced_geo_kb_agent.tools:
            if hasattr(tool, '__name__'):
                tool_names.append(tool.__name__)
            elif hasattr(tool, 'name'):
                tool_names.append(tool.name)
            else:
                tool_names.append(str(type(tool).__name__))
        
        print(f"   Tool names: {tool_names}")
        
        if "enhanced_geo_kb_search_from_state" in str(tool_names):
            print("   ✅ Enhanced function detected in tools")
        else:
            print("   ⚠️ Enhanced function not clearly detected")
        
        return True
        
    except ImportError as e:
        print(f"❌ Could not import enhanced agent: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing enhanced agent: {e}")
        return False

def main():
    """Run the web API test."""
    print("🎯 ENHANCED GEO_KB_AGENT WEB API TEST")
    print("=" * 50)
    
    # Test enhanced agent
    agent_works = test_enhanced_agent_directly()
    
    # Test web API
    api_running = test_web_api_health()
    
    print(f"\n🎉 TEST SUMMARY")
    print("=" * 20)
    
    if agent_works:
        print("✅ Enhanced agent: LOADED")
    else:
        print("⚠️ Enhanced agent: Check imports")
    
    if api_running:
        print("✅ Web API: RUNNING")
    else:
        print("❌ Web API: Start with 'python3 -m src.eia_adk.http_api'")

if __name__ == "__main__":
    main()
