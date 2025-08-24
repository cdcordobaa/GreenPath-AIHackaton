#!/usr/bin/env python3
"""
Test the optimized geo_kb_search_from_state function with content filtering.
"""

import sys
import json
from pathlib import Path
from copy import deepcopy
from typing import Dict, Any, List

# Add src to path to import the tools
sys.path.insert(0, str(Path(__file__).parent / "src"))

def simulate_optimized_geo_kb_search(state_data: Dict[str, Any]) -> Dict[str, Any]:
    """Simulate the optimized geo_kb_search with token-aware filtering."""
    print("🔧 Testing Optimized geo_kb_search Function")
    print("=" * 50)
    
    # Extract keywords (same logic as original)
    keywords = []
    
    # From alias_input
    aliases = state_data.get("legal", {}).get("geo2neo", {}).get("alias_input", [])
    keywords.extend(str(a) for a in aliases if a)
    
    # From structured_summary  
    rows = state_data.get("geo", {}).get("structured_summary", {}).get("rows", [])
    for r in rows:
        if r.get("categoria"):
            keywords.append(str(r.get("categoria")))
        if r.get("tipo"):
            keywords.append(str(r.get("tipo")))
    
    # Deduplicate
    uniq_keywords = []
    seen = set()
    for k in keywords:
        k2 = k.strip()
        if k2 and k2.lower() not in seen:
            seen.add(k2.lower())
            uniq_keywords.append(k2)
            if len(uniq_keywords) >= 12:
                break
    
    print(f"📝 Keywords derived: {len(uniq_keywords)}")
    print(f"   {uniq_keywords[:6]}{'...' if len(uniq_keywords) > 6 else ''}")
    
    # Simulate MCP search results with different sizes
    mock_search_results = {
        'Biótico': [
            {'url': 'url1', 'title': 'Small doc', 'content_md': 'A' * 5000},  # 5K chars
            {'url': 'url2', 'title': 'Medium doc', 'content_md': 'B' * 25000}  # 25K chars
        ],
        'Compensación': [
            {'url': 'url3', 'title': 'Large doc', 'content_md': 'C' * 50000},  # 50K chars  
            {'url': 'url4', 'title': 'Huge doc', 'content_md': 'D' * 600000}  # 600K chars (will be skipped)
        ],
        'Gestión de Riesgo': [
            {'url': 'url5', 'title': 'Normal doc', 'content_md': 'E' * 12000},  # 12K chars
            {'url': 'url6', 'title': 'Big doc', 'content_md': 'F' * 80000}  # 80K chars
        ]
    }
    
    # Apply new filtering logic
    per_keyword_limit = 2
    max_chars_per_doc = 15000
    skip_docs_larger_than = 500000
    
    aggregated = {}
    stats = {'skipped': 0, 'truncated': 0, 'kept_as_is': 0}
    
    for keyword in uniq_keywords[:3]:  # Test first 3 keywords
        results = mock_search_results.get(keyword, [])[:per_keyword_limit]
        
        print(f"\n🔍 Processing keyword: '{keyword}'")
        
        for i, row in enumerate(results):
            content_md = row.get("content_md", "")
            content_length = len(content_md)
            
            print(f"   Doc {i+1}: {content_length:,} chars")
            
            if content_length > skip_docs_larger_than:
                print(f"      🚫 SKIPPED (>{skip_docs_larger_than:,} chars)")
                stats['skipped'] += 1
                continue
                
            if content_length > max_chars_per_doc:
                truncated_content = content_md[:max_chars_per_doc] + "\\n\\n[Content truncated...]"
                row = row.copy()
                row["content_md"] = truncated_content
                row["_original_length"] = content_length
                row["_truncated"] = True
                print(f"      ✂️ TRUNCATED ({content_length:,} → {len(truncated_content):,} chars)")
                stats['truncated'] += 1
            else:
                print(f"      ✅ KEPT AS-IS ({content_length:,} chars)")
                stats['kept_as_is'] += 1
            
            url = row.get("url", "")
            key = url or f"doc_{len(aggregated)}"
            if key not in aggregated:
                aggregated[key] = row
    
    # Calculate final stats
    docs = list(aggregated.values())
    total_chars = sum(len(doc.get("content_md", "")) for doc in docs)
    estimated_tokens = total_chars // 4
    
    print(f"\n📊 OPTIMIZATION RESULTS:")
    print(f"   Documents processed: {stats['kept_as_is'] + stats['truncated'] + stats['skipped']}")
    print(f"   ✅ Kept as-is: {stats['kept_as_is']}")
    print(f"   ✂️ Truncated: {stats['truncated']}")
    print(f"   🚫 Skipped (too large): {stats['skipped']}")
    print(f"   📄 Final docs in KB: {len(docs)}")
    print(f"   📏 Total chars: {total_chars:,}")
    print(f"   🎯 Estimated tokens: {estimated_tokens:,}")
    
    # Project to full 12 keywords
    projected_tokens = estimated_tokens * 4  # 12 keywords / 3 tested
    print(f"\n🔮 PROJECTION FOR ALL 12 KEYWORDS:")
    print(f"   Estimated total tokens: ~{projected_tokens:,}")
    
    if projected_tokens < 50000:
        status = "🎉 EXCELLENT"
    elif projected_tokens < 100000:
        status = "✅ GOOD"
    elif projected_tokens < 200000:
        status = "⚠️ MANAGEABLE"
    else:
        status = "🚨 STILL TOO LARGE"
    
    print(f"   Status: {status}")
    
    # Create final state structure
    updated_state = deepcopy(state_data)
    kb = updated_state.setdefault("legal", {}).setdefault("kb", {})
    
    kb["keywords"] = uniq_keywords
    kb["scraped_pages"] = {
        "count": len(docs),
        "rows": docs,
        "_metadata": {
            "truncated_docs": stats['truncated'],
            "skipped_docs": stats['skipped'],
            "total_chars": total_chars,
            "estimated_tokens": estimated_tokens,
            "per_keyword_limit": per_keyword_limit,
            "max_chars_per_doc": max_chars_per_doc
        }
    }
    
    return updated_state

def main():
    """Test the optimized function."""
    print("🚀 Testing Optimized geo_kb_agent with Token Management")
    print("This simulates the improved content filtering\\n")
    
    # Your state data
    state_data = {
        "config": {"layers": ["soils", "biotic", "hidrology"]},
        "geo": {
            "structured_summary": {
                "count": 21,
                "rows": [
                    {"cantidad": 505, "categoria": "SOILS", "tipo": "Suelos"},
                    {"cantidad": 19, "categoria": "HYDROLOGY", "tipo": "Hidrología"},
                ]
            }
        },
        "legal": {
            "geo2neo": {
                "alias_input": ["Biótico", "Compensación", "Gestión de Riesgo", "Hidrogeología", "Hidrología", "Suelos"],
                "alias_mapping": {"ok": True, "results": []}
            }
        },
        "project": {"project_id": "proj_001", "project_name": "Linea_110kV_Z"}
    }
    
    result = simulate_optimized_geo_kb_search(state_data)
    
    print("\\n" + "=" * 60)
    
    metadata = result["legal"]["kb"]["scraped_pages"]["_metadata"]
    tokens = metadata["estimated_tokens"]
    
    if tokens < 30000:
        print("🎉 OPTIMIZATION SUCCESS!")
        print(f"   ✅ Reduced to {tokens:,} tokens")
        print("   ✅ Well within LLM context limits")
        print("   ✅ Should prevent rate limiting issues")
    else:
        print("⚠️ Still needs more optimization")
        print(f"   Current: {tokens:,} tokens")
        print("   Consider further reducing max_chars_per_doc")
    
    print(f"\\n🔧 Configuration used:")
    print(f"   per_keyword_limit: {metadata['per_keyword_limit']}")
    print(f"   max_chars_per_doc: {metadata['max_chars_per_doc']:,}")
    print(f"   Truncated docs: {metadata['truncated_docs']}")
    print(f"   Skipped docs: {metadata['skipped_docs']}")

if __name__ == "__main__":
    main()

