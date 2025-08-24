# EIA-ADK State Flow Verification

## Current Active Workflow
```
ingest_agent → geo_agent → geo2neo_agent → geo_kb_agent
```

## Detailed State Flow Analysis

### 1. 🔧 **ingest_agent** 
**Tool**: `configure_project()`

**Input**: 
- `target_layers`: List of layers to analyze
- `project_path`: Path to GeoJSON file  
- `layer_type`: Type of layer (default: "lines")

**State Write**:
```json
{
  "project": {
    "project_id": "proj_001",
    "project_name": "Linea_110kV_Z", 
    "config": {
      "layers": ["soils", "biotic", "hidrology"]
    }
  }
}
```

### 2. 🌍 **geo_agent**
**Tool**: `structured_summary_via_mcp()`

**State Read**:
```python
project_ref = (current.get("project") or {})
args["project_id"] = project_ref.get("project_id") or project_ref.get("project_name")
```

**MCP Call**: `get_structured_resource_summary(project_id)`

**State Write**:
```json
{
  "geo": {
    "structured_summary": {
      "count": 21,
      "rows": [
        {
          "recurso1": "Suelos",
          "recurso": "Suelos", 
          "cantidad": 505,
          "tipo": "Suelos",
          "categoria": "SOILS"
        },
        {
          "recurso1": "Cuencas Hidrográficas",
          "recurso": "Cuencas Hidrográficas",
          "cantidad": 19, 
          "tipo": "Hidrología",
          "categoria": "HYDROLOGY"
        }
        // ... more rows
      ]
    }
  }
}
```

### 3. 🔗 **geo2neo_agent**
**Tool**: `geo2neo_from_structured_summary()`

**State Read**:
```python
rows = (((current.get("geo") or {}).get("structured_summary") or {}).get("rows") or [])
aliases = sorted({str(r.get("tipo")) for r in rows if r.get("tipo") is not None})
```

**MCP Call**: `map_by_aliases({"input": {"aliases": aliases}})`

**State Write**:
```json
{
  "legal": {
    "geo2neo": {
      "alias_input": ["Suelos", "Hidrología", "Biótico", "Gestión de Riesgo", "Compensación"],
      "alias_mapping": {
        "ok": true,
        "count": 2,
        "results": [
          {
            "category": "Suelos",
            "instrumentsAndPermits": [...],
            "associatedNorms": [...]
          }
        ]
      }
    }
  }
}
```

### 4. 📚 **geo_kb_agent**
**Tool**: `geo_kb_search_from_state()`

**State Read** (Multiple Sources):
```python
# 1) From geo2neo aliases
aliases = list(((current.get("legal") or {}).get("geo2neo") or {}).get("alias_input") or [])

# 2) From mapping results  
results = ((current.get("legal") or {}).get("geo2neo") or {}).get("alias_mapping", {}).get("results") or []

# 3) From structured summary
rows = (((current.get("geo") or {}).get("structured_summary") or {}).get("rows") or [])
```

**MCP Call**: `search_scraped_pages(text_contains=keyword, limit=per_keyword_limit)`

**State Write**:
```json
{
  "legal": {
    "kb": {
      "keywords": ["Suelos", "Hidrología", "Biótico"],
      "scraped_pages": {
        "count": 15,
        "rows": [
          {
            "url": "https://example.com/ley-99",
            "content_md": "Ley 99 de 1993...",
            "title": "Ley General Ambiental"
          }
        ]
      }
    }
  }
}
```

## ✅ State Dependencies Verification

### Flow 1: ingest_agent → geo_agent
- ✅ **Write**: `state.project.project_id` 
- ✅ **Read**: `project_ref.get("project_id")`
- **Status**: ✅ CONNECTED

### Flow 2: geo_agent → geo2neo_agent  
- ✅ **Write**: `state.geo.structured_summary.rows`
- ✅ **Read**: `((current.get("geo") or {}).get("structured_summary") or {}).get("rows")`
- **Status**: ✅ CONNECTED

### Flow 3: geo_agent + geo2neo_agent → geo_kb_agent
- ✅ **Write**: `state.legal.geo2neo.alias_input` + `state.geo.structured_summary.rows`
- ✅ **Read**: Multiple reads from both sections
- **Status**: ✅ CONNECTED

## 🔍 Critical State Keys

| Agent | Key State Reads | Key State Writes |
|-------|----------------|------------------|
| **ingest_agent** | None | `project.{project_id, project_name, config.layers}` |
| **geo_agent** | `project.project_id` | `geo.structured_summary.{count, rows}` |
| **geo2neo_agent** | `geo.structured_summary.rows[].tipo` | `legal.geo2neo.{alias_input, alias_mapping}` |
| **geo_kb_agent** | `legal.geo2neo.*` + `geo.structured_summary.rows` | `legal.kb.{keywords, scraped_pages}` |

## 🎯 Verification Commands

Test the complete flow:
```bash
# In ADK web interface:
"Analiza: project_path=data/sample_project/lines.geojson target_layers=[\"soils\",\"biotic\",\"hidrology\"]"
```

Expected final state structure:
```json
{
  "project": { "project_id": "...", "project_name": "...", "config": {...} },
  "geo": { "structured_summary": { "count": N, "rows": [...] } },
  "legal": {
    "geo2neo": { "alias_input": [...], "alias_mapping": {...} },
    "kb": { "keywords": [...], "scraped_pages": {...} }
  }
}
```
