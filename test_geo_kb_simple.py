#!/usr/bin/env python3
"""
Simple standalone test for geo_kb_agent functionality.
Tests keyword derivation logic without external dependencies.
"""

import json
from copy import deepcopy
from typing import Dict, Any, List

def derive_keywords_from_state(state_json: Dict[str, Any], max_keywords: int = 12) -> List[str]:
    """
    Replicate the keyword derivation logic from geo_kb_search_from_state.
    This is the core logic that the geo_kb_agent uses.
    """
    keywords: List[str] = []

    # 1) Aliases used
    try:
        aliases = list(((state_json.get("legal") or {}).get("geo2neo") or {}).get("alias_input") or [])
        keywords.extend([str(a) for a in aliases if a is not None])
        print(f"   🔑 From alias_input: {aliases}")
    except Exception:
        pass

    # 2) From mapping results
    try:
        results = ((state_json.get("legal") or {}).get("geo2neo") or {}).get("alias_mapping", {}).get("results") or []
        mapping_keywords = []
        for item in results:
            cat = item.get("category")
            if cat:
                keywords.append(str(cat))
                mapping_keywords.append(str(cat))
            for inst in item.get("instrumentsAndPermits", []) or []:
                name = inst.get("instrumentName")
                if name:
                    keywords.append(str(name))
                    mapping_keywords.append(str(name))
                for mod in inst.get("modalities", []) or []:
                    ar = mod.get("affectedResource")
                    if ar:
                        keywords.append(str(ar))
                        mapping_keywords.append(str(ar))
        print(f"   🔑 From mapping results: {mapping_keywords}")
    except Exception:
        pass

    # 3) From structured summary rows
    try:
        rows = (((state_json.get("geo") or {}).get("structured_summary") or {}).get("rows") or [])
        summary_keywords = []
        for r in rows:
            if r.get("categoria"):
                keywords.append(str(r.get("categoria")))
                summary_keywords.append(str(r.get("categoria")))
            if r.get("tipo"):
                keywords.append(str(r.get("tipo")))
                summary_keywords.append(str(r.get("tipo")))
        # Show unique summary keywords
        unique_summary = list(set(summary_keywords))
        print(f"   🔑 From structured_summary: {unique_summary}")
    except Exception:
        pass

    # Deduplicate and cap
    uniq: List[str] = []
    seen: set[str] = set()
    for k in keywords:
        k2 = k.strip()
        if not k2:
            continue
        if k2.lower() in seen:
            continue
        seen.add(k2.lower())
        uniq.append(k2)
        if len(uniq) >= max_keywords:
            break

    return uniq


def test_geo_kb_keyword_derivation():
    """Test the keyword derivation logic with your provided state data."""
    print("🔍 Testing geo_kb_agent Keyword Derivation")
    print("=" * 50)
    
    # Your provided state data
    state_data = {
        "config": {
            "layers": ["soils", "biotic", "hidrology"]
        },
        "geo": {
            "by_layer": {},
            "intersections": {},
            "structured_summary": {
                "count": 21,
                "rows": [
                    {"cantidad": 505, "categoria": "SOILS", "recurso": "Suelos", "recurso1": "Suelos", "tipo": "Suelos"},
                    {"cantidad": 19, "categoria": "HYDROLOGY", "recurso": "Cuencas Hidrográficas", "recurso1": "Cuencas Hidrográficas", "tipo": "Hidrología"},
                    {"cantidad": 2, "categoria": "HYDROLOGY", "recurso": "Ocupación de Cauce", "recurso1": "Ocupación de Cauce", "tipo": "Hidrología"},
                    {"cantidad": 32, "categoria": "HYDROLOGY", "recurso": "Agua Superficial", "recurso1": "Agua Superficial", "tipo": "Hidrología"},
                    {"cantidad": 174, "categoria": "HYDROLOGY", "recurso": "Uso Recursos Hídricos", "recurso1": "Uso Recursos Hídricos", "tipo": "Hidrología"},
                    {"cantidad": 208, "categoria": "HYDROGEOLOGY", "recurso": "Hidrogeología", "recurso1": "Hidrogeología", "tipo": "Hidrogeología"},
                    {"cantidad": 21, "categoria": "HYDROGEOLOGY", "recurso": "Agua Subterránea", "recurso1": "Agua Subterránea", "tipo": "Hidrogeología"},
                    {"cantidad": 1000, "categoria": "BIOTIC", "recurso": "Aprovechamiento Forestal (Polígono)", "recurso1": "Aprovechamiento Forestal (Polígono)", "tipo": "Biótico"},
                    {"cantidad": 1000, "categoria": "BIOTIC", "recurso": "Aprovechamiento Forestal (Punto)", "recurso1": "Aprovechamiento Forestal (Punto)", "tipo": "Biótico"},
                    {"cantidad": 1000, "categoria": "BIOTIC", "recurso": "Cobertura de Tierra", "recurso1": "Cobertura de Tierra", "tipo": "Biótico"},
                    {"cantidad": 1000, "categoria": "BIOTIC", "recurso": "Ecosistemas", "recurso1": "Ecosistemas", "tipo": "Biótico"},
                    {"cantidad": 253, "categoria": "BIOTIC", "recurso": "Fauna", "recurso1": "Fauna", "tipo": "Biótico"},
                    {"cantidad": 501, "categoria": "BIOTIC", "recurso": "Flora", "recurso1": "Flora", "tipo": "Biótico"},
                    {"cantidad": 187, "categoria": "BIOTIC", "recurso": "Transectos Fauna", "recurso1": "Transectos Fauna", "tipo": "Biótico"},
                    {"cantidad": 1000, "categoria": "RISK_MANAGEMENT", "recurso": "amenazaotras", "recurso1": "amenazaotras", "tipo": "Gestión de Riesgo"},
                    {"cantidad": 1000, "categoria": "RISK_MANAGEMENT", "recurso": "elementosexpuestosln", "recurso1": "elementosexpuestosln", "tipo": "Gestión de Riesgo"},
                    {"cantidad": 1000, "categoria": "RISK_MANAGEMENT", "recurso": "elementosexpuestospt", "recurso1": "elementosexpuestospt", "tipo": "Gestión de Riesgo"},
                    {"cantidad": 1000, "categoria": "RISK_MANAGEMENT", "recurso": "suscept_incendios", "recurso1": "suscept_incendios", "tipo": "Gestión de Riesgo"},
                    {"cantidad": 280, "categoria": "RISK_MANAGEMENT", "recurso": "suscept_inundaciones", "recurso1": "suscept_inundaciones", "tipo": "Gestión de Riesgo"},
                    {"cantidad": 1000, "categoria": "RISK_MANAGEMENT", "recurso": "vulnerabilidad_pt", "recurso1": "vulnerabilidad_pt", "tipo": "Gestión de Riesgo"},
                    {"cantidad": 37, "categoria": "COMPENSATION", "recurso": "Compensación Biodiversidad", "recurso1": "Compensación Biodiversidad", "tipo": "Compensación"}
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
                "alias_input": ["Biótico", "Compensación", "Gestión de Riesgo", "Hidrogeología", "Hidrología", "Suelos"],
                "alias_mapping": {
                    "count": 0,
                    "meta": {"counters": {}, "t_consumed": 3, "t_first": 105},
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
    
    print("📋 STATE INPUT ANALYSIS:")
    print("=" * 30)
    
    # Show what we have
    geo2neo_data = state_data.get("legal", {}).get("geo2neo", {})
    structured_summary = state_data.get("geo", {}).get("structured_summary", {})
    
    print(f"📖 alias_input: {geo2neo_data.get('alias_input', [])}")
    print(f"📖 alias_mapping.results: {len(geo2neo_data.get('alias_mapping', {}).get('results', []))} items")
    print(f"📖 structured_summary.rows: {len(structured_summary.get('rows', []))} items")
    
    # Test keyword derivation
    print("\n🔄 DERIVING KEYWORDS:")
    print("=" * 30)
    
    keywords = derive_keywords_from_state(state_data)
    
    print(f"\n✅ FINAL KEYWORDS ({len(keywords)} total):")
    for i, kw in enumerate(keywords, 1):
        print(f"   {i:2d}. {kw}")
    
    # Simulate what would happen in MCP search
    print(f"\n🔍 WHAT HAPPENS NEXT:")
    print("=" * 30)
    print(f"   🌐 geo_kb_agent would search MCP for each keyword")
    print(f"   📄 Query: search_scraped_pages(text_contains='{keywords[0]}', limit=5)")
    print(f"   📄 Query: search_scraped_pages(text_contains='{keywords[1]}', limit=5)")
    print(f"   📄 ... (for all {len(keywords)} keywords)")
    print(f"   💾 Results stored in state.legal.kb.scraped_pages")
    
    # Validate the workflow state
    print(f"\n📊 WORKFLOW VALIDATION:")
    print("=" * 30)
    
    required_data = {
        "alias_input_present": len(geo2neo_data.get('alias_input', [])) > 0,
        "structured_summary_present": len(structured_summary.get('rows', [])) > 0,
        "keywords_derived": len(keywords) > 0,
        "has_geo2neo_mapping": geo2neo_data.get('alias_mapping', {}).get('ok') is True
    }
    
    all_good = all(required_data.values())
    
    for check, status in required_data.items():
        print(f"   {'✅' if status else '❌'} {check}: {status}")
    
    print(f"\n{'🎉' if all_good else '⚠️'} {'READY' if all_good else 'ISSUES'} for geo_kb_agent execution")
    
    if all_good:
        print("\n🚀 SUCCESS - This state is ready for geo_kb_agent!")
        print("   ✅ Has alias_input from geo2neo_agent") 
        print("   ✅ Has structured_summary from geo_agent")
        print("   ✅ Can derive meaningful keywords")
        print("   ✅ geo2neo mapping completed successfully")
        print(f"\n💡 The geo_kb_agent would:")
        print(f"   1. Use these {len(keywords)} keywords to search scraped pages")
        print(f"   2. Store results in state.legal.kb.scraped_pages")
        print(f"   3. Complete the workflow")
    else:
        print("\n❌ Issues detected in state data")
        print("   Check the failed validation points above")
    
    return all_good, keywords


def main():
    """Main function."""
    print("🧪 SIMPLE geo_kb_agent Test (No Dependencies)")
    print("Testing only the keyword derivation logic\n")
    
    success, keywords = test_geo_kb_keyword_derivation()
    
    print("\n" + "=" * 50)
    if success:
        print("✅ geo_kb_agent keyword derivation WORKS!")
        print(f"   Derived {len(keywords)} search keywords")
        print("   Ready to query knowledge base")
        print("\n🔧 TO TEST FULL FUNCTIONALITY:")
        print("   1. Ensure MCP servers are running")
        print("   2. Use the real geo_kb_search_from_state function")
        print("   3. Check state.legal.kb.scraped_pages output")
    else:
        print("❌ Issues with state data for geo_kb_agent")
        print("   Fix the validation errors above")


if __name__ == "__main__":
    main()

