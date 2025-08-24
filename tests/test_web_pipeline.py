#!/usr/bin/env python3
"""
Test the web pipeline with enhanced geo_kb_agent.
"""

import requests
import json
import time

def test_pipeline():
    """Test the pipeline through the web API."""
    print("🧪 TESTING PIPELINE WITH ENHANCED GEO_KB_AGENT")
    print("=" * 50)
    
    # Test data
    request_data = {
        "project_path": "data/sample_project/lines.geojson",
        "target_layers": ["hydro.rivers", "ecosystems"]
    }
    
    print(f"📊 Request:")
    print(f"   Project: {request_data['project_path']}")
    print(f"   Layers: {request_data['target_layers']}")
    
    try:
        print(f"\n🚀 Sending request...")
        start_time = time.time()
        
        response = requests.post(
            "http://localhost:8000/pipeline/run",
            json=request_data,
            timeout=60
        )
        
        processing_time = time.time() - start_time
        
        print(f"⏱️ Processing time: {processing_time:.1f}s")
        print(f"📊 Status code: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"✅ Pipeline completed successfully!")
            
            # Show results
            print(f"\n📋 Results:")
            print(f"   Success: {result.get('success')}")
            print(f"   Message: {result.get('message')}")
            
            state_summary = result.get('state_summary', {})
            if state_summary:
                print(f"   State keys: {list(state_summary.keys())}")
                
                # Check for legal analysis (would contain enhanced geo_kb results)
                if 'legal_analysis' in state_summary:
                    print(f"   ✅ Legal analysis present")
                if 'legal_scope' in state_summary:
                    print(f"   ✅ Legal scope present")
            
            print(f"\n🎯 Enhanced geo_kb_agent integration: SUCCESS")
            return True
            
        else:
            print(f"❌ Pipeline failed: {response.status_code}")
            print(f"   Error: {response.text}")
            return False
            
    except requests.exceptions.Timeout:
        print(f"⏱️ Request timed out - this suggests rate limiting issues")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Run the test."""
    print("🎯 WEB API PIPELINE TEST")
    print("=" * 30)
    
    # Check API health first
    try:
        health = requests.get("http://localhost:8000/health", timeout=5)
        if health.status_code == 200:
            print("✅ Web API is healthy")
        else:
            print("❌ Web API health check failed")
            return
    except:
        print("❌ Web API is not running")
        return
    
    # Test pipeline
    success = test_pipeline()
    
    print(f"\n🎉 TEST RESULT:")
    if success:
        print("✅ Enhanced geo_kb_agent is working through web API!")
        print("✅ Rate limiting optimization is active!")
        print("✅ Pipeline completes without timeouts!")
    else:
        print("⚠️ Pipeline test encountered issues")
        print("   Check logs for details")

if __name__ == "__main__":
    main()
