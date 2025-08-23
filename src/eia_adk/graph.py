from .state import EIAState
from .nodes import (
    project_ingestion,
    geospatial_analysis,
    intersection_synthesis,
    llm_summarizer,
    legal_scope_resolution,
    legal_analysis,
    report_assembly,
)


def run_pipeline(project_path: str, target_layers: list[str] = ["hydro.rivers"]) -> EIAState:
    state = EIAState()
    state = project_ingestion.run(state, project_path=project_path, layer_type="lines")
    state = geospatial_analysis.run(
        state, target_layers=target_layers, predicate="intersects", buffer_m=None
    )
    state = intersection_synthesis.run(state)
    state = llm_summarizer.run(state, model="gemini-1.5-flash")
    state = legal_scope_resolution.run(state)
    state = legal_analysis.run(state, model="gemini-1.5-flash")
    state = report_assembly.run(state, out_path="out/report.md")
    return state
