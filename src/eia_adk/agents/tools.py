from __future__ import annotations

from typing import Any, Dict, List, Optional
from ..state import EIAState
from .. import graph
from ..nodes import (
    project_ingestion,
    geospatial_analysis,
    intersection_synthesis,
    llm_summarizer,
    legal_scope_resolution,
    legal_analysis,
    report_assembly,
)


def _to_state(state_json: Optional[Dict[str, Any]]) -> EIAState:
    if not state_json:
        return EIAState()
    return EIAState(**state_json)


def _from_state(state: EIAState) -> Dict[str, Any]:
    return state.model_dump()


def run_pipeline_tool(project_path: str, target_layers: List[str]) -> Dict[str, Any]:
    state = graph.run_pipeline(project_path=project_path, target_layers=target_layers)
    result = _from_state(state)
    report_uri = None
    for art in state.artifacts:
        if art.get("type") == "report_md":
            report_uri = art.get("uri")
            break
    result["report_uri"] = report_uri or "out/report.md"
    return result


def ingest_project(project_path: str, layer_type: str = "lines") -> Dict[str, Any]:
    state = EIAState()
    state = project_ingestion.run(state, project_path=project_path, layer_type=layer_type)
    return _from_state(state)


def configure_project(
    target_layers: List[str],
    project_path: str = "data/sample_project/lines.geojson",
    layer_type: str = "lines",
) -> Dict[str, Any]:
    """Initialize state with the project and record which env layers to test against.

    Assumes the project file already exists; input is the list of target layers.
    """
    state = EIAState()
    state = project_ingestion.run(state, project_path=project_path, layer_type=layer_type)
    state_dict = _from_state(state)
    state_dict.setdefault("project", {})
    state_dict["project"]["config_layers"] = list(target_layers)
    return state_dict


def run_geospatial(state_json: Dict[str, Any], target_layers: List[str], predicate: str = "intersects", buffer_m: Optional[float] = None) -> Dict[str, Any]:
    state = _to_state(state_json)
    state = geospatial_analysis.run(state, target_layers=target_layers, predicate=predicate, buffer_m=buffer_m)
    return _from_state(state)


def synthesize_intersections(state_json: Dict[str, Any]) -> Dict[str, Any]:
    state = _to_state(state_json)
    state = intersection_synthesis.run(state)
    return _from_state(state)


def summarize_impacts(state_json: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
    state = _to_state(state_json)
    state = llm_summarizer.run(state, model=model)
    return _from_state(state)


def resolve_legal_scope(state_json: Dict[str, Any]) -> Dict[str, Any]:
    state = _to_state(state_json)
    state = legal_scope_resolution.run(state)
    return _from_state(state)


def legal_requirements(state_json: Dict[str, Any], model: Optional[str] = None) -> Dict[str, Any]:
    state = _to_state(state_json)
    state = legal_analysis.run(state, model=model)
    return _from_state(state)


def assemble_report(state_json: Dict[str, Any], out_path: str = "out/report.md") -> Dict[str, Any]:
    state = _to_state(state_json)
    state = report_assembly.run(state, out_path=out_path)
    result = _from_state(state)
    result["report_uri"] = out_path
    return result


def run_geospatial_with_config(state_json: Dict[str, Any], predicate: str = "intersects", buffer_m: Optional[float] = None) -> Dict[str, Any]:
    """Runs geospatial analysis using layers configured in project.config_layers."""
    target_layers = []
    try:
        target_layers = list((state_json.get("project", {}) or {}).get("config_layers", []))
    except Exception:
        target_layers = []
    if not target_layers:
        # No configured layers; return state unchanged
        return state_json
    state = _to_state(state_json)
    state = geospatial_analysis.run(state, target_layers=target_layers, predicate=predicate, buffer_m=buffer_m)
    return _from_state(state)


