## EIA multi-agent overview (ADK)

This project implements an Environmental Impact Assessment (EIA) workflow using ADK’s multi-agent hierarchy. A Coordinator agent orchestrates a sequence of specialist agents; shared session state lets every step read/write the same data.

### Architecture (Coordinator/Dispatcher + Hierarchy)

- **Root (Coordinator)**: `src/root_agent.py::eia_coordinator`
  - Routes requests, maintains session state, can trigger a full pipeline tool
  - Has a `SequentialAgent` child (`workflow`) that invokes specialists in order
- **Specialist agents** (`src/eia_adk/agents/`):
  - `ingest_agent`: Configures project; records target layers
  - `geo_agent`: Runs geospatial analysis over configured layers
  - `synthesis_agent`: Synthesizes intersections
  - `summarizer_agent`: Extracts legal triggers (LLM)
  - `legal_scope_agent`: Maps triggers to legal scope
  - `legal_agent`: Produces legal requirements (LLM)
  - `report_agent`: Assembles final report (`out/report.md`)

This mirrors ADK multi-agent guidance: a parent LLM routes to sub-agents, with shared session state and deterministic sequencing for reliability.

References:
- ADK Multi-agents and hierarchy: https://google.github.io/adk-docs/agents/multi-agents/
- Team tutorial: https://google.github.io/adk-docs/tutorials/agent-team/

### Session state (shared “blackboard”)

We use a single state key `state["eia"]` to keep all pipeline data consistent across steps.

Suggested shape (baseline seed):

```yaml
eia:
  project: {}
  geo: { intersections: [] }
  synthesis: { affected_features: [] }
  legal: { triggers: [], scope: [], requirements: [] }
  artifacts: []
```

Coordinator attaches callbacks so tools automatically receive the latest state and write results back:
- Seed on first run (ensure `state["eia"]` exists)
- Before tool: inject `state_json` from `state["eia"]` if missing
- After tool: replace `state["eia"]` with the returned dict

This guarantees all agents operate over the same evolving state without manual message passing.

### Tools (bridge to pipeline code)

Tools live in `src/eia_adk/agents/tools.py` and call your existing pipeline functions in `src/eia_adk/graph.py` and `src/eia_adk/nodes/*`:

- `configure_project(target_layers, project_path?, layer_type?) -> state`
- `run_geospatial_with_config(state_json, predicate?, buffer_m?) -> state`
- `synthesize_intersections(state_json) -> state`
- `summarize_impacts(state_json, model?) -> state` (LLM)
- `resolve_legal_scope(state_json) -> state`
- `legal_requirements(state_json, model?) -> state` (LLM)
- `assemble_report(state_json, out_path=out/report.md) -> state + report_uri`
- `run_pipeline_tool(project_path, target_layers) -> state + report_uri` (one-shot)

Each tool returns a full JSON-safe state dict. The Coordinator merges it back to `state["eia"]` via the after-tool callback.

### Agent responsibilities (inputs → outputs)

- **ingest_agent**
  - Asserts file exists; asks for missing inputs before proceeding
  - Requires `target_layers` (e.g., ["hydro.rivers","ecosystems","protected_areas"]) and optionally `project_path` (defaults to `data/sample_project/lines.geojson`) and `layer_type` (defaults to `lines`)
  - Calls `configure_project(...)` → updates `state.project.config_layers`

- **geo_agent**
  - Requires `state_json` (from ingest) and `predicate` (default "intersects"), optional `buffer_m`
  - Calls `run_geospatial_with_config(...)` → updates `state.geo.intersections`

- **synthesis_agent** → `synthesize_intersections` → `state.synthesis.affected_features`
- **summarizer_agent** → `summarize_impacts` (LLM JSON) → `state.legal.triggers`
- **legal_scope_agent** → `resolve_legal_scope` → `state.legal.scope`
- **legal_agent** → `legal_requirements` (LLM JSON) → `state.legal.requirements`
- **report_agent** → `assemble_report` → `state.artifacts` + `report_uri`

### How to run

- Dev UI server:
```bash
. .venv/bin/activate
adk web --host 127.0.0.1 --port 8000
# Open http://127.0.0.1:8000/dev-ui and select app "src"
```

- Try either path:
  - One-shot tool: `Analiza: project_path=data/sample_project/lines.geojson target_layers=["hydro.rivers","ecosystems","protected_areas"]`
  - Routed: “Configura proyecto con capas: [ ... ] y ejecuta análisis.”

Check `out/report.md` after a full run.

### Prompt guidance (LLM stability)

- Agents request missing inputs first; then call tools.
- LLM-only steps return JSON per schemas in `src/eia_adk/prompts/` to keep outputs parseable.
- Keep instructions concise, include examples for: configuring project, running geo analysis, and generating report.

### Notes

- Models default via `.env`: `EIA_MODEL_PRIMARY` (e.g., `gemini-2.5-pro`), `EIA_MODEL_FALLBACK` (e.g., `gemini-2.5-flash`).
- Coordinator sequential path is deterministic; you can still run the one-shot `run_pipeline_tool` for quick tests.


