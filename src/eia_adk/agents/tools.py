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
import asyncio
import sys
from pathlib import Path


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


# --- MCP integration helpers ---

async def _async_ping_geo_mcp() -> Dict[str, Any]:
    """Call the geo-fetch-mcp stdio server's ping tool via MCP stdio.

    This function spawns the server as a subprocess over stdio, lists tools, then calls 'ping'.
    """
    try:
        from mcp.client.session import ClientSession  # type: ignore
        from mcp.client.stdio import stdio_client, StdioServerParameters  # type: ignore
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "error": f"Missing mcp client dependency: {exc}"}

    repo_root = Path(__file__).resolve().parents[3]
    server_path = repo_root / "geo-fetch-mcp" / "run_stdio.py"
    if not server_path.exists():
        return {"ok": False, "error": f"MCP server entry not found: {server_path}"}

    params = StdioServerParameters(command=sys.executable, args=[str(server_path)])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            # Ensure tools available and call ping
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            if "ping" not in tool_names:
                return {"ok": False, "error": f"'ping' tool not exposed. Available: {tool_names}"}
            result = await session.call_tool("ping", {})
            # result.content is a list of content blocks; normalize
            # Try to return first JSON-like block if present
            payload: Dict[str, Any] = {"ok": True}
            try:
                blocks = getattr(result, "content", [])
                if blocks:
                    block0 = blocks[0]
                    # FastMCP usually returns a JSON block with .type == 'json'
                    data = getattr(block0, "data", None) or getattr(block0, "text", None)
                    if isinstance(data, dict):
                        payload.update(data)
                    elif isinstance(data, str):
                        payload["message"] = data
            except Exception:
                pass
            return payload


def ping_geo_mcp() -> Dict[str, Any]:
    """Synchronous wrapper to ping geo-fetch-mcp via stdio MCP.

    Returns a JSON-serializable dict, e.g. {"ok": True, ...} or error info.
    """
    try:
        return asyncio.run(_async_ping_geo_mcp())
    except RuntimeError:
        # If already in an event loop (e.g., certain runtimes), create a new loop
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_async_ping_geo_mcp())
        finally:
            loop.close()


async def _async_hydrology_geo_mcp(project_id: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        from mcp.client.session import ClientSession  # type: ignore
        from mcp.client.stdio import stdio_client, StdioServerParameters  # type: ignore
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "error": f"Missing mcp client dependency: {exc}"}

    repo_root = Path(__file__).resolve().parents[3]
    server_path = repo_root / "geo-fetch-mcp" / "run_stdio.py"
    if not server_path.exists():
        return {"ok": False, "error": f"MCP server entry not found: {server_path}"}

    params = StdioServerParameters(command=sys.executable, args=[str(server_path)])

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            tools = await session.list_tools()
            tool_names = [t.name for t in tools.tools]
            if "hydrology" not in tool_names:
                return {"ok": False, "error": f"'hydrology' tool not exposed. Available: {tool_names}"}
            result = await session.call_tool("hydrology", {"project_id": project_id, "limit": limit, "filters": filters})
            payload: Dict[str, Any] = {"ok": True}
            try:
                blocks = getattr(result, "content", [])
                if blocks:
                    block0 = blocks[0]
                    data = getattr(block0, "data", None) or getattr(block0, "text", None)
                    if isinstance(data, dict):
                        payload.update(data)
                    elif isinstance(data, str):
                        payload["message"] = data
            except Exception:
                pass
            return payload


def hydrology_geo_mcp(project_id: str, limit: int = 10, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    try:
        return asyncio.run(_async_hydrology_geo_mcp(project_id=project_id, limit=limit, filters=filters))
    except RuntimeError:
        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(_async_hydrology_geo_mcp(project_id=project_id, limit=limit, filters=filters))
        finally:
            loop.close()


