# EIA-ADK

Minimal multi-agent pipeline for Environmental Impact Assessment using Google's ADK (Gemini).

## Quickstart

```bash
cd eia-adk
uv venv && source .venv/bin/activate
uv add adk google-genai pydantic python-dotenv rich
# later: uv add geopandas shapely pandas supabase

# run
PYTHONPATH=src python src/eia_adk/app.py
```

## Layout

```
src/
  eia_adk/
    app.py
    state.py
    graph.py
    nodes/
    mcp/
    adapters/
    prompts/
```

The pipeline executes stubbed nodes end-to-end and writes `out/report.md`.
