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
from copy import deepcopy
import threading
import json
from ..adapters.llm import LlmRunner, LlmConfig
import logging


logger = logging.getLogger("eia_adk.tools")


def _log_compact(label: str, data: Any, max_len: int = 1000) -> None:
    try:
        if isinstance(data, (dict, list)):
            text = json.dumps(data, ensure_ascii=False)
        else:
            text = str(data)
    except Exception:
        text = str(data)
    if len(text) > max_len:
        text = text[:max_len] + "...(truncated)"
    logger.info("%s: %s", label, text)


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


def enhanced_assemble_report(state_json: Dict[str, Any], out_path: str = "out/enhanced_report.md") -> Dict[str, Any]:
    """Generate a comprehensive EIA analysis report from all workflow results."""
    from datetime import datetime
    import os
    
    # Extract data from state
    project = state_json.get("project", {})
    geo = state_json.get("geo", {})
    legal = state_json.get("legal", {})
    
    # Project info
    project_name = project.get("project_name", "Proyecto Sin Nombre")
    project_id = project.get("project_id", "N/A")
    
    # Geo analysis results
    structured_summary = geo.get("structured_summary", {})
    geo_rows = structured_summary.get("rows", [])
    geo_count = structured_summary.get("count", 0)
    
    # Legal analysis results
    geo2neo = legal.get("geo2neo", {})
    alias_mapping = geo2neo.get("alias_mapping", {})
    kb_results = legal.get("kb", {}).get("scraped_pages", {})
    kb_rows = kb_results.get("rows", [])
    kb_count = kb_results.get("count", 0)
    
    # Generate report content
    report_content = []
    
    # Header
    report_content.extend([
        f"# Reporte de Análisis EIA - {project_name}",
        "",
        f"**Proyecto ID:** {project_id}",
        f"**Fecha de Generación:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "---",
        ""
    ])
    
    # Executive Summary
    report_content.extend([
        "## 📋 Resumen Ejecutivo",
        "",
        f"Este reporte presenta el análisis de impacto ambiental para el proyecto **{project_name}**. ",
        f"Se identificaron **{geo_count} recursos geoespaciales** afectados y se encontraron **{kb_count} documentos legales** relevantes.",
        "",
    ])
    
    # Project Details
    report_content.extend([
        "## 🏗️ Información del Proyecto",
        "",
        f"- **Nombre:** {project_name}",
        f"- **ID:** {project_id}",
    ])
    
    if project.get("project_shapefile_path"):
        report_content.append(f"- **Archivo Geoespacial:** {project.get('project_shapefile_path')}")
    
    config_layers = project.get("config", {}).get("layers", [])
    if config_layers:
        report_content.extend([
            "- **Capas Analizadas:**",
            *[f"  - {layer}" for layer in config_layers]
        ])
    
    report_content.append("")
    
    # Geospatial Analysis Results
    report_content.extend([
        "## 🌍 Análisis Geoespacial",
        "",
        f"**Total de recursos identificados:** {geo_count}",
        ""
    ])
    
    if geo_rows:
        # Group by category
        categories = {}
        for row in geo_rows:
            cat = row.get("categoria", "Sin Categoría")
            if cat not in categories:
                categories[cat] = []
            categories[cat].append(row)
        
        report_content.append("### Recursos por Categoría")
        report_content.append("")
        
        for category, resources in categories.items():
            report_content.extend([
                f"#### {category}",
                ""
            ])
            
            for resource in resources:
                recurso = resource.get("recurso", "N/A")
                cantidad = resource.get("cantidad", 0)
                tipo = resource.get("tipo", "N/A")
                report_content.append(f"- **{recurso}**: {cantidad} elementos (Tipo: {tipo})")
            
            report_content.append("")
    
    # Legal Framework Analysis
    report_content.extend([
        "## ⚖️ Marco Legal Aplicable",
        ""
    ])
    
    if alias_mapping:
        report_content.extend([
            "### Mapeo de Recursos a Marco Legal",
            ""
        ])
        
        for category, mapping_data in alias_mapping.items():
            if isinstance(mapping_data, dict) and mapping_data.get("results"):
                results = mapping_data["results"]
                report_content.extend([
                    f"#### {category}",
                    ""
                ])
                
                for result in results[:5]:  # Show first 5 results
                    instruments = result.get("instrumentsAndPermits", [])
                    if instruments:
                        report_content.append(f"**Categoría:** {result.get('category', 'N/A')}")
                        report_content.append("**Instrumentos y Permisos:**")
                        for instrument in instruments[:3]:  # Show first 3 instruments
                            name = instrument.get("name", "N/A")
                            entity = instrument.get("entity", "N/A")
                            report_content.append(f"- {name} ({entity})")
                        report_content.append("")
    else:
        report_content.extend([
            "No se encontraron mapeos específicos en el marco legal.",
            ""
        ])
    
    # Knowledge Base Results
    report_content.extend([
        "## 📚 Documentos Legales Relevantes",
        "",
        f"**Total de documentos encontrados:** {kb_count}",
        ""
    ])
    
    if kb_rows:
        report_content.extend([
            "### Documentos Identificados",
            ""
        ])
        
        for i, doc in enumerate(kb_rows[:10], 1):  # Show first 10 documents
            title = doc.get("title", "Sin Título")
            url = doc.get("url", "#")
            content_preview = doc.get("content_md", "")[:200] + "..." if doc.get("content_md") else "Sin contenido disponible"
            
            report_content.extend([
                f"#### {i}. {title}",
                f"**URL:** {url}",
                f"**Contenido:** {content_preview}",
                ""
            ])
    else:
        report_content.extend([
            "No se encontraron documentos legales específicos en la base de conocimiento.",
            ""
        ])
    
    # Requirements and Recommendations
    report_content.extend([
        "## 📋 Requerimientos y Recomendaciones",
        "",
        "### Requerimientos Identificados",
        ""
    ])
    
    # Extract requirements from legal documents
    requirements_found = []
    for doc in kb_rows[:5]:  # Check first 5 documents
        content = doc.get("content_md", "").lower()
        if any(keyword in content for keyword in ["permiso", "licencia", "autorización", "registro"]):
            requirements_found.append(f"- Revisar documento: {doc.get('title', 'Sin título')}")
    
    if requirements_found:
        report_content.extend(requirements_found)
    else:
        report_content.append("- Realizar análisis detallado de requerimientos legales específicos")
    
    report_content.extend([
        "",
        "### Próximos Pasos Recomendados",
        "",
        "1. **Análisis Legal Detallado:** Revisar en profundidad los documentos legales identificados",
        "2. **Consulta con Autoridades:** Contactar las entidades reguladoras pertinentes",
        "3. **Evaluación de Impactos:** Realizar estudios específicos para cada categoría de recurso",
        "4. **Preparación de Documentación:** Compilar la documentación necesaria para permisos",
        "5. **Seguimiento Regulatorio:** Establecer cronograma de cumplimiento normativo",
        "",
        "---",
        "",
        f"*Reporte generado automáticamente por EIA-ADK el {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*"
    ])
    
    # Write report to file
    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else "out", exist_ok=True)
    
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_content))
    
    # Update state
    state = _to_state(state_json)
    if not hasattr(state, 'artifacts') or state.artifacts is None:
        state.artifacts = []
    
    state.artifacts.append({
        "type": "enhanced_report_md", 
        "uri": out_path,
        "description": f"Reporte EIA completo para {project_name}"
    })
    
    result = _from_state(state)
    result["report_uri"] = out_path
    result["report_type"] = "enhanced_eia_analysis"
    
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
            # Initialize handshake before any requests
            await session.initialize()
            # Call ping directly; avoid list_tools to prevent version/protocol mismatches
            try:
                result = await session.call_tool("ping", {})
            except Exception as exc:
                # As a fallback, try to list tools for diagnostics
                try:
                    tools = await session.list_tools()
                    tool_names = [t.name for t in tools.tools]
                except Exception as exc2:
                    tool_names = [f"list_tools_failed: {exc2}"]
                return {"ok": False, "error": f"ping call failed: {exc}", "tools": tool_names}
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


# --- Async utilities ---
def _run_coro_blocking(coro):
    """Run a coroutine from sync context even if an event loop is already running.

    If no loop is running, uses asyncio.run. Otherwise, spins up a dedicated
    thread with its own loop to execute the coroutine and returns the result.
    """
    try:
        asyncio.get_running_loop()
        loop_running = True
    except RuntimeError:
        loop_running = False

    if not loop_running:
        return asyncio.run(coro)

    result_holder: Dict[str, Any] = {}
    error_holder: Dict[str, BaseException] = {}

    def _thread_runner():
        new_loop = asyncio.new_event_loop()
        try:
            asyncio.set_event_loop(new_loop)
            result_holder["value"] = new_loop.run_until_complete(coro)
        except BaseException as exc:  # capture and re-raise in caller thread
            error_holder["exc"] = exc
        finally:
            try:
                new_loop.close()
            except Exception:
                pass

    t = threading.Thread(target=_thread_runner, daemon=True)
    t.start()
    t.join()
    if "exc" in error_holder:
        raise error_holder["exc"]
    return result_holder.get("value")

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



# =====================
# N1: Intake (thin)
# =====================
def intake_project(
    project_name: str,
    layers: List[str],
    project_id: Optional[str] = None,
    project_shapefile_path: Optional[str] = None,
) -> Dict[str, Any]:
    """Initialize state with project metadata and target layers (no I/O).

    Produces the canonical state skeleton requested for the simple workflow.
    """
    state: Dict[str, Any] = {
        "project": {"project_name": project_name},
        "config": {"layers": list(layers)},
        "geo": {"summary": {}, "by_layer": {}, "intersections": {}},
        "impacts": {"categories": [], "entities": []},
        "legal": {"candidates": [], "requirements": []},
    }
    if project_id:
        state["project"]["project_id"] = project_id
    if project_shapefile_path:
        state["project"]["project_shapefile_path"] = project_shapefile_path
    return state


# =====================
# N2: GeoFetch (MCP loop)
# =====================
async def _async_get_layer_records_via_mcp(project_ref: Dict[str, Any], layer: str) -> Dict[str, Any]:
    """Call the geo-fetch-mcp to get records for a given layer using the generic tool if available.

    Falls back to a per-layer tool name `get_<layer>` if `get_layer_records` is not exposed.
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

    project_id = project_ref.get("project_id")
    project_name = project_ref.get("project_name")

    args: Dict[str, Any] = {"project_id": project_id or "", "layer": layer}
    # If no id, pass name so server can handle either
    if not project_id and project_name:
        args["project_name"] = project_name

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            # Prefer generic first; on failure, fallback to get_<layer>
            call_names = ["get_layer_records", f"get_{layer}"]
            last_err: Optional[Exception] = None
            result = None
            for call_name in call_names:
                try:
                    result = await session.call_tool(call_name, args)
                    break
                except Exception as exc:
                    last_err = exc
                    continue
            if result is None:
                # As a last resort, try listing tools for visibility
                try:
                    tools = await session.list_tools()
                    tool_names = [t.name for t in tools.tools]
                except Exception as exc2:
                    tool_names = [f"list_tools_failed: {exc2}"]
                return {"ok": False, "error": f"No layer tool succeeded for '{layer}': {last_err}", "available": tool_names}
            payload: Dict[str, Any] = {"ok": True}
            try:
                blocks = getattr(result, "content", [])
                if blocks:
                    block0 = blocks[0]
                    data = getattr(block0, "data", None) or getattr(block0, "text", None)
                    if isinstance(data, dict):
                        payload.update(data)
                    elif isinstance(data, str):
                        # best-effort passthrough
                        payload["message"] = data
            except Exception:
                pass
            return payload


def geo_fetch_layers(state_json: Dict[str, Any]) -> Dict[str, Any]:
    """Iterate over config.layers and fetch per-layer records via MCP, merging into state.geo.

    - Writes geo.by_layer[layer] = {rows, count}
    - Updates geo.summary with count per layer
    - Optionally mirrors into geo.intersections[layer] with structure {layer, count, records}
    """
    current = deepcopy(state_json or {})
    project_ref = (current.get("project") or {})
    config = (current.get("config") or {})
    layers = list(config.get("layers") or [])

    # Ensure geo skeleton exists
    geo = current.setdefault("geo", {})
    by_layer: Dict[str, Any] = geo.setdefault("by_layer", {})
    summary: Dict[str, Any] = geo.setdefault("summary", {})
    intersections: Dict[str, Any] = geo.setdefault("intersections", {})

    if not layers:
        return current

    # Per-layer fetch
    for layer in layers:
        try:
            res = _run_coro_blocking(_async_get_layer_records_via_mcp(project_ref, layer))
            _log_compact(f"geo.layer.{layer}.result", {"ok": res.get("ok", True), "count": res.get("count"), "keys": list(res.keys())})

            if not res.get("ok", True):
                # Record error summary and continue
                summary[layer] = 0
                by_layer[layer] = {"rows": [], "count": 0, "error": res.get("error")}
                intersections[layer] = {"layer": layer, "count": 0, "records": []}
                continue

            # Normalize outputs
            count = int(res.get("count", 0))
            records = list(res.get("records", []))
            summary[layer] = count
            by_layer[layer] = {"rows": records, "count": count}
            intersections[layer] = {"layer": layer, "count": count, "records": records}
        except Exception as exc:  # Defensive: do not break the loop
            summary[layer] = 0
            by_layer[layer] = {"rows": [], "count": 0, "error": str(exc)}
            intersections[layer] = {"layer": layer, "count": 0, "records": []}
            logger.exception("geo.layer.%s.exception", layer)

    return current


def geo_kb_search_from_state(
    state_json: Dict[str, Any], 
    per_keyword_limit: int = 2,  # Reduced from 5 to 2
    max_keywords: int = 12,
    max_chars_per_doc: int = 15000,  # Truncate docs to 15K chars (~3.7K tokens)
    skip_docs_larger_than: int = 500000,  # Skip docs larger than 500K chars
    optimization_mode: str = "balanced"  # New: "fast", "balanced", "comprehensive", "adaptive"
) -> Dict[str, Any]:
    """Derive search keywords from state and query geo-fetch-mcp.scraped_pages for matching docs.

    Sources of keywords (in order):
    - legal.geo2neo.alias_input (the aliases used to map categories)
    - legal.geo2neo.alias_mapping.results[*].category
    - instrument names and affected resources in alias_mapping results
    - geo.structured_summary.rows[*].categoria and tipo
    """
    current = deepcopy(state_json or {})
    keywords: List[str] = []

    # 1) Aliases used
    try:
        aliases = list(((current.get("legal") or {}).get("geo2neo") or {}).get("alias_input") or [])
        keywords.extend([str(a) for a in aliases if a is not None])
    except Exception:
        pass

    # 2) From mapping results
    try:
        results = ((current.get("legal") or {}).get("geo2neo") or {}).get("alias_mapping", {}).get("results") or []
        for item in results:
            cat = item.get("category")
            if cat:
                keywords.append(str(cat))
            for inst in item.get("instrumentsAndPermits", []) or []:
                name = inst.get("instrumentName")
                if name:
                    keywords.append(str(name))
                for mod in inst.get("modalities", []) or []:
                    ar = mod.get("affectedResource")
                    if ar:
                        keywords.append(str(ar))
    except Exception:
        pass

    # 3) From structured summary rows
    try:
        rows = (((current.get("geo") or {}).get("structured_summary") or {}).get("rows") or [])
        for r in rows:
            if r.get("categoria"):
                keywords.append(str(r.get("categoria")))
            if r.get("tipo"):
                keywords.append(str(r.get("tipo")))
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

    # Query MCP search for each keyword
    aggregated: Dict[str, Dict[str, Any]] = {}
    for kw in uniq:
        args: Dict[str, Any] = {"text_contains": kw, "limit": per_keyword_limit}
        try:
            result = _run_coro_blocking(_async_call_mcp_server("geo-fetch-mcp", "search_scraped_pages", args))
        except Exception as exc:
            result = {"ok": False, "error": str(exc)}
        rows = result.get("rows") or []
        for row in rows:
            # Filter out documents that are too large
            content_md = row.get("content_md", "") or ""
            content_length = len(content_md)
            
            if content_length > skip_docs_larger_than:
                # Skip extremely large documents to prevent token overflow
                continue
                
            # Truncate content if it's too long
            if content_length > max_chars_per_doc:
                truncated_content = content_md[:max_chars_per_doc] + "\n\n[Content truncated...]"
                row = row.copy()  # Don't modify original
                row["content_md"] = truncated_content
                row["_original_length"] = content_length
                row["_truncated"] = True
            
            url = str(row.get("url") or "")
            key = url or row.get("id") or str(len(aggregated))
            if key not in aggregated:
                aggregated[key] = row

    # Save into state with content filtering stats
    kb = ((current.setdefault("legal", {})).setdefault("kb", {}))
    kb["keywords"] = uniq
    docs = list(aggregated.values())
    
    # Add metadata about content processing
    truncated_count = sum(1 for doc in docs if doc.get("_truncated", False))
    total_chars = sum(len(doc.get("content_md", "")) for doc in docs)
    
    kb["scraped_pages"] = {
        "count": len(docs), 
        "rows": docs,
        "_metadata": {
            "truncated_docs": truncated_count,
            "total_chars": total_chars,
            "estimated_tokens": total_chars // 4,
            "per_keyword_limit": per_keyword_limit,
            "max_chars_per_doc": max_chars_per_doc
        }
    }
    return current


def mock_geo_kb_search_from_state(state_json: Dict[str, Any]) -> Dict[str, Any]:
    current = deepcopy(state_json or {})
    kb = ((current.setdefault("legal", {})).setdefault("kb", {}))
    kb["keywords"] = ["aprovechamiento forestal", "recurso hídrico"]
    kb["scraped_pages"] = {
        "count": 2,
        "rows": [
            {"url": "https://example.org/mads/permiso-forestal", "title": "Permiso de Aprovechamiento Forestal", "content_md": "Requisitos y normativa..."},
            {"url": "https://example.org/anh/uso-agua", "title": "Usos y Usuarios del Recurso Hídrico", "content_md": "Procedimientos y autoridades..."},
        ],
    }
    return current

# =====================
# Geo: Fetch all *compendium tools
# =====================
async def _async_list_tools_and_call_compendia(project_ref: Dict[str, Any]) -> Dict[str, Any]:
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
    project_id = project_ref.get("project_id")
    project_name = project_ref.get("project_name")
    base_args: Dict[str, Any] = {"project_id": project_id or ""}
    if not project_id and project_name:
        base_args["project_name"] = project_name

    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            names: List[str]
            compendia: List[str]
            try:
                tools = await session.list_tools()
                names = [t.name for t in tools.tools]
                compendia = [n for n in names if n.endswith("_compendium") or (n.startswith("get_") and n.endswith("_compendium"))]
            except Exception:
                # Fallback to known compendium tool names if listing is unsupported
                names = []
                compendia = [
                    "get_soils_compendium",
                    "get_hydrology_compendium",
                    "get_hydrogeology_compendium",
                    "get_biotic_compendium",
                    "get_risk_management_compendium",
                    "get_compensation_compendium",
                ]
            results: Dict[str, Any] = {}
            for name in compendia:
                try:
                    res = await session.call_tool(name, base_args)
                    payload: Dict[str, Any] = {"ok": True}
                    blocks = getattr(res, "content", [])
                    if blocks:
                        blk0 = blocks[0]
                        data = getattr(blk0, "data", None) or getattr(blk0, "text", None)
                        if isinstance(data, dict):
                            payload.update(data)
                        elif isinstance(data, str):
                            try:
                                parsed = json.loads(data)
                                if isinstance(parsed, dict):
                                    payload.update(parsed)
                                else:
                                    payload["raw"] = data
                            except Exception:
                                payload["raw"] = data
                    results[name] = payload
                except Exception as exc:
                    results[name] = {"ok": False, "error": str(exc)}
            return {"ok": True, "compendia": results}


def geo_fetch_all_compendia(state_json: Dict[str, Any]) -> Dict[str, Any]:
    current = deepcopy(state_json or {})
    project_ref = (current.get("project") or {})
    geo = current.setdefault("geo", {})
    geo.setdefault("compendia", {})

    try:
        out = _run_coro_blocking(_async_list_tools_and_call_compendia(project_ref))
    except Exception as exc:
        current.setdefault("temp:geo:last_error", f"compendia failed: {exc}")
        return current
    if not out.get("ok"):
        current.setdefault("temp:geo:last_error", str(out))
        return current

    compendia_results: Dict[str, Any] = out.get("compendia", {})
    # Store raw compendia results
    geo["compendia"] = compendia_results
    _log_compact("geo.compendia.names", list(compendia_results.keys()))

    # Optional: roll up totals per compendium into geo.summary under a nested key
    summary = geo.setdefault("summary", {})
    for name, payload in compendia_results.items():
        comp_summary = payload.get("summary")
        if isinstance(comp_summary, dict):
            total = 0
            try:
                total = sum(int(v) for v in comp_summary.values())
            except Exception:
                pass
            summary_key = f"{name}:total"
            summary[summary_key] = total
        _log_compact(f"geo.compendia.{name}.summary", comp_summary if isinstance(comp_summary, dict) else {"summary": None})
    return current


# =====================
# Note: derive_impacts_from_compendia was removed as it's no longer needed
# The structured_summary_via_mcp provides the necessary impact analysis
# =====================


# =====================
# MOCK tools (no external calls)
# =====================
def mock_geo_fetch_all_compendia(state_json: Dict[str, Any]) -> Dict[str, Any]:
    current = deepcopy(state_json or {})
    geo = current.setdefault("geo", {})
    comp = {
        "get_soils_compendium": {
            "summary": {"CapacidadUsoTierra": 2},
            "datasets": {"CapacidadUsoTierra": {"count": 2, "rows": [{"id": 1}, {"id": 2}]}}
        },
        "get_hydrology_compendium": {
            "summary": {"CuencaHidrografica": 1, "ocupacioncauce": 0, "puntomuestreoaguasuper": 1, "usosyusuariosrecursohidrico": 0},
            "datasets": {}
        },
        "get_biotic_compendium": {
            "summary": {"ecosistema": 1, "coberturatierra": 1},
            "datasets": {}
        },
        "get_risk_management_compendium": {
            "summary": {"escenriesgoincendio": 0, "suscept_inundaciones": 1},
            "datasets": {}
        },
        "get_compensation_compendium": {
            "summary": {"compensacionbiodiversidad": 0},
            "datasets": {}
        },
    }
    geo["compendia"] = comp
    # Also write summary rollups
    summary = geo.setdefault("summary", {})
    for name, payload in comp.items():
        s = payload.get("summary") or {}
        try:
            summary[f"{name}:total"] = sum(int(v) for v in s.values())
        except Exception:
            summary[f"{name}:total"] = 0
    return current


# Note: mock_derive_impacts_from_compendia was removed as it's no longer needed


def mock_geo2neo_map(state_json: Dict[str, Any]) -> Dict[str, Any]:
    """Mock geo2neo mapping tool: saves mocked category/instruments/norms into state."""
    current = deepcopy(state_json or {})
    legal = current.setdefault("legal", {})
    geo2neo: Dict[str, Any] = legal.setdefault("geo2neo", {})

    payload = [
        {
            "keys": ["category", "instrumentsAndPermits", "associatedNorms"],
            "length": 3,
            "_fields": [
                "Gestión Integral de Flora y Bosques",
                [
                    {
                        "modalities": [
                            {
                                "subcategoryName": "Aprovechamiento Forestal Único (Desmonte)",
                                "compensationCriteria": [
                                    "*Compensación por Pérdida de Biodiversidad (Resolución 256 de 2018 - Manual de Compensaciones del Componente Biótico):* Obligación de restaurar ecológicamente o preservar un área de ecosistema ecológicamente equivalente a la afectada. El cálculo del área a compensar es mandatorio y se basa en fórmulas que consideran el tipo de ecosistema, su estado de amenaza, el área del impacto y un factor de compensación regional."
                                ],
                                "affectedResource": "Flora y Bosques",
                                "managementCriteria": [
                                    "Realización de un inventario forestal al 100% que identifique y georreferencie todos los individuos, especialmente los de especies vedadas o amenazadas.",
                                    "Implementación de un Plan de Rescate, Ahuyentamiento y Reubicación de Fauna Silvestre, ejecutado por biólogos antes y durante las actividades.",
                                    "Manejo de la biomasa vegetal mediante técnicas de chipeado y reincorporación al suelo para protegerlo de la erosión, prohibiendo explícitamente las quemas abiertas.",
                                    "Implementación inmediata de medidas de control de erosión como revegetalización temporal con especies nativas, instalación de barreras de sedimento (trinchos) y manejo de aguas de escorrentía.",
                                    "Elaboración e implementación del Plan de Gestión Integral de Residuos Peligrosos (RESPEL) para los residuos de la maquinaria (aceites, filtros, combustibles)."
                                ],
                            }
                        ],
                        "instrumentName": "Permiso de Aprovechamiento Forestal",
                    }
                ],
                [
                    {
                        "childNorms": [
                            {"relationType": "Reglamenta / condiciona", "childNormName": "Decreto 1791 de 1996"}
                        ],
                        "issuer": "MADS / CAR",
                        "component": "Biótica / Forestal",
                        "normName": "Aprovechamiento Forestal (Dec. 1791/1996) - ejecución",
                        "requiredData": "Inventarios, planes, talas autorizadas, trazabilidad.",
                        "year": "1996",
                        "obligations": "Cumplir autorizaciones, salvoconductos y medidas de compensación; registrar movilización autorizada.",
                        "type": "Instrumento ambiental (decreto)",
                    }
                ],
                {
                    "category": 0,
                    "instrumentsAndPermits": 1,
                    "associatedNorms": 2,
                },
            ],
            "_fieldLookup": {
                "category": 0,
                "instrumentsAndPermits": 1,
                "associatedNorms": 2,
            },
        }
    ]

    try:
        first = payload[0]
        fields = first.get("_fields", [])
        lookup = first.get("_fieldLookup", {})
        def _at(key: str):
            try:
                idx = lookup.get(key)
                if isinstance(idx, int) and 0 <= idx < len(fields):
                    return fields[idx]
            except Exception:
                pass
            return None
        category = _at("category")
        instruments = _at("instrumentsAndPermits") or []
        norms = _at("associatedNorms") or []
        geo2neo["raw"] = first
        geo2neo["normalized"] = {
            "category": category,
            "instrumentsAndPermits": instruments,
            "associatedNorms": norms,
        }
        geo2neo["summary"] = {
            "category": category,
            "instrument_count": len(instruments) if isinstance(instruments, list) else 0,
            "norm_count": len(norms) if isinstance(norms, list) else 0,
        }
    except Exception as exc:
        geo2neo["error"] = f"mock parse failed: {exc}"
    return current


async def _async_call_mcp_server(server_subdir: str, tool: str, args: Dict[str, Any]) -> Dict[str, Any]:
    try:
        from mcp.client.session import ClientSession  # type: ignore
        from mcp.client.stdio import stdio_client, StdioServerParameters  # type: ignore
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "error": f"Missing mcp client dependency: {exc}"}

    repo_root = Path(__file__).resolve().parents[3]
    server_path = repo_root / server_subdir / "run_stdio.py"
    if not server_path.exists():
        return {"ok": False, "error": f"MCP server entry not found: {server_path}"}

    # Prefer that server's venv python if present; else fall back to current interpreter
    venv_python = (repo_root / server_subdir / ".venv" / "bin" / "python")
    python_cmd = str(venv_python) if venv_python.exists() else sys.executable

    params = StdioServerParameters(command=python_cmd, args=[str(server_path)])
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            try:
                res = await session.call_tool(tool, args)
                blocks = getattr(res, "content", [])
                for blk in blocks:
                    data = getattr(blk, "data", None) or getattr(blk, "text", None)
                    if isinstance(data, dict):
                        return {"ok": True, **data}
                    if isinstance(data, str):
                        try:
                            parsed = json.loads(data)
                            if isinstance(parsed, dict):
                                return {"ok": True, **parsed}
                        except Exception:
                            pass
                return {"ok": True, "raw": str(blocks[0].text) if blocks else None}
            except Exception as exc:
                return {"ok": False, "error": str(exc)}


def search_scraped_pages_via_mcp(state_json: Dict[str, Any], url_contains: Optional[str] = None, text_contains: Optional[str] = None, limit: int = 10) -> Dict[str, Any]:
    """Ping geo2neo MCP and search scraped pages; write to state."""
    current = deepcopy(state_json or {})
    # Ping first
    try:
        # use geo-fetch-mcp for both ping and search since the search tool lives there
        ping_out = _run_coro_blocking(_async_call_mcp_server("geo-fetch-mcp", "ping", {}))
    except Exception as exc:
        ping_out = {"ok": False, "error": str(exc)}

    # Build args
    args: Dict[str, Any] = {"limit": limit}
    if url_contains:
        args["url_contains"] = url_contains
    if text_contains:
        args["text_contains"] = text_contains

    try:
        search_out = _run_coro_blocking(_async_call_mcp_server("geo-fetch-mcp", "search_scraped_pages", args))
    except Exception as exc:
        search_out = {"ok": False, "error": str(exc)}

    legal = current.setdefault("legal", {})
    geo2neo: Dict[str, Any] = legal.setdefault("geo2neo", {})
    geo2neo["ping"] = ping_out
    geo2neo["scraped_pages"] = search_out
    return current



def structured_summary_via_mcp(state_json: Dict[str, Any]) -> Dict[str, Any]:
    """Call geo-fetch-mcp.get_structured_resource_summary and write into state.geo.summary_rows.

    Expects state.project.project_id or project_name to be present (optional), but the MCP server
    reads from Supabase; we pass project_id if available.
    """
    current = deepcopy(state_json or {})
    project_ref = (current.get("project") or {})
    args: Dict[str, Any] = {}
    if project_ref.get("project_id"):
        args["project_id"] = project_ref.get("project_id")
    elif project_ref.get("project_name"):
        args["project_id"] = project_ref.get("project_name")
    else:
        # fall back to env var PROJECT_ID or demo-project
        args["project_id"] = os.getenv("PROJECT_ID", "demo-project")

    try:
        out = _run_coro_blocking(_async_call_mcp_server("geo-fetch-mcp", "get_structured_resource_summary", args))
    except Exception as exc:
        out = {"ok": False, "error": str(exc)}

    geo = current.setdefault("geo", {})
    if out.get("ok") and isinstance(out.get("rows"), list):
        geo["structured_summary"] = {"count": out.get("count", len(out.get("rows", []))), "rows": out.get("rows")}
    else:
        # propagate error or raw message for visibility
        err = out.get("error") or out.get("raw") or "structured summary failed"
        geo["structured_summary"] = {"error": err}
    return current


def mock_structured_summary(state_json: Dict[str, Any]) -> Dict[str, Any]:
    current = deepcopy(state_json or {})
    geo = current.setdefault("geo", {})
    # Minimal deterministic mock rows
    rows = [
        {"recurso1": "Ecosistema X", "recurso": "Bosque Húmedo", "cantidad": 3, "tipo": "aprovechaforestalpg", "categoria": "Bosque Húmedo"},
        {"recurso1": "Río Demo", "recurso": None, "cantidad": 2, "tipo": "puntomuestreoaguasuper", "categoria": "Río Demo"},
    ]
    geo["structured_summary"] = {"count": len(rows), "rows": rows, "mock": True}
    return current


def geo2neo_from_structured_summary(state_json: Dict[str, Any]) -> Dict[str, Any]:
    """Extract unique 'tipo' from state.geo.structured_summary and call geo2neo map_by_aliases.

    Writes results into state.legal.geo2neo.alias_mapping.
    """
    current = deepcopy(state_json or {})
    rows = (((current.get("geo") or {}).get("structured_summary") or {}).get("rows") or [])
    aliases: List[str] = sorted({str(r.get("tipo")) for r in rows if r.get("tipo") is not None})
    try:
        out = _run_coro_blocking(_async_call_mcp_server("mcp-geo2neo", "map_by_aliases", {"input": {"aliases": aliases}}))
    except Exception as exc:
        out = {"ok": False, "error": str(exc)}

    legal = current.setdefault("legal", {})
    g2n = legal.setdefault("geo2neo", {})
    g2n["alias_input"] = aliases
    g2n["alias_mapping"] = out
    return current


def mock_geo2neo_from_structured_summary(state_json: Dict[str, Any]) -> Dict[str, Any]:
    current = deepcopy(state_json or {})
    rows = (((current.get("geo") or {}).get("structured_summary") or {}).get("rows") or [])
    aliases: List[str] = sorted({str(r.get("tipo")) for r in rows if r.get("tipo") is not None})
    legal = current.setdefault("legal", {})
    g2n = legal.setdefault("geo2neo", {})
    g2n["alias_input"] = aliases
    g2n["alias_mapping"] = {
        "ok": True,
        "count": 1,
        "results": [
            {
                "category": "Demo Category",
                "instrumentsAndPermits": [{"instrumentName": "Permiso Demo", "modalities": []}],
                "associatedNorms": [],
            }
        ],
    }
    return current
