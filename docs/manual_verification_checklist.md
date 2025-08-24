# 🔍 Manual State Flow Verification Checklist

## Current Workflow Status ✅
**Active Agents**: `ingest_agent → geo_agent → geo2neo_agent → geo_kb_agent`

## 🌐 ADK Web Interface Testing

**URL**: http://127.0.0.1:8000/dev-ui

### Test Command:
```
"Analiza: project_path=data/sample_project/lines.geojson target_layers=[\"soils\",\"biotic\",\"hidrology\"]"
```

## ✅ State Flow Verification Steps

### 1. **ingest_agent** Should Execute
**Look for**:
- ✅ Agent name: `ingest_agent`
- ✅ Tool call: `configure_project` or similar
- ✅ Success message indicating project configured

**Expected State Write**:
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

### 2. **geo_agent** Should Execute
**Look for**:
- ✅ Agent name: `geo_agent`
- ✅ Tool call: `structured_summary_via_mcp`
- ✅ MCP call: `get_structured_resource_summary`
- ✅ Success with resource count (should be ~21 resources)

**Expected State Write**:
```json
{
  "geo": {
    "structured_summary": {
      "count": 21,
      "rows": [
        {"recurso1": "Suelos", "tipo": "Suelos", "cantidad": 505, ...},
        {"recurso1": "Cuencas Hidrográficas", "tipo": "Hidrología", ...}
      ]
    }
  }
}
```

**Critical Check**: Verify that each row has a `tipo` field (needed for next agent)

### 3. **geo2neo_agent** Should Execute
**Look for**:
- ✅ Agent name: `geo2neo_agent`
- ✅ Tool call: `geo2neo_from_structured_summary`
- ✅ Reading: `state.geo.structured_summary.rows`
- ✅ Extracting unique `tipo` values
- ✅ MCP call: `map_by_aliases` with aliases like `["Suelos", "Hidrología", "Biótico"]`

**Expected State Write**:
```json
{
  "legal": {
    "geo2neo": {
      "alias_input": ["Suelos", "Hidrología", "Biótico", "Gestión de Riesgo", "Compensación"],
      "alias_mapping": {
        "ok": true,
        "count": 0-5,
        "results": [...]
      }
    }
  }
}
```

### 4. **geo_kb_agent** Should Execute
**Look for**:
- ✅ Agent name: `geo_kb_agent`
- ✅ Tool call: `geo_kb_search_from_state`
- ✅ Reading: `state.legal.geo2neo.alias_input`
- ✅ Reading: `state.legal.geo2neo.alias_mapping.results`
- ✅ Reading: `state.geo.structured_summary.rows`
- ✅ Deriving keywords from multiple sources
- ✅ MCP calls: `search_scraped_pages` for each keyword

**Expected State Write**:
```json
{
  "legal": {
    "kb": {
      "keywords": ["Suelos", "Hidrología", ...],
      "scraped_pages": {
        "count": 10-20,
        "rows": [
          {"url": "...", "content_md": "...", "title": "..."}
        ]
      }
    }
  }
}
```

## 🚨 Common Issues to Watch For

### ❌ **Agent Fails to Read State**
**Symptoms**: Agent says it can't find expected data
**Check**: Previous agent actually wrote the expected state keys

### ❌ **MCP Tool Not Found**
**Symptoms**: "Unknown tool: X" error
**Check**: MCP servers are running and tool is decorated with `@mcp.tool()`

### ❌ **Empty Results**
**Symptoms**: Agent succeeds but returns empty data
**Check**: Supabase credentials and data availability

### ❌ **State Key Mismatch**
**Symptoms**: Agent reads from wrong state path
**Check**: State reading code matches state writing code

## 🎯 Success Criteria

**All agents execute successfully AND**:

1. ✅ `ingest_agent` writes `state.project`
2. ✅ `geo_agent` reads `state.project.project_id` → writes `state.geo.structured_summary`
3. ✅ `geo2neo_agent` reads `state.geo.structured_summary.rows[].tipo` → writes `state.legal.geo2neo`
4. ✅ `geo_kb_agent` reads from both `state.legal.geo2neo.*` and `state.geo.structured_summary.*` → writes `state.legal.kb`

**Final State Should Contain**:
```json
{
  "project": {...},
  "geo": {"structured_summary": {...}},
  "legal": {
    "geo2neo": {...},
    "kb": {...}
  }
}
```

## 🔧 Debugging Tips

1. **Check Agent Logs**: Look for state reading/writing messages
2. **Verify MCP Connectivity**: Ensure both `geo-fetch-mcp` and `mcp-geo2neo` are accessible
3. **Check State Evolution**: Each agent should add to the state without breaking previous sections
4. **Validate Data Flow**: Each `tipo` from geo_agent should appear in geo2neo_agent aliases

## 🎉 Next Steps After Verification

Once all 4 agents execute successfully:
1. Enable additional agents (`synthesis_agent`, etc.)
2. Test full pipeline with `run_pipeline_tool`
3. Verify end-to-end report generation
