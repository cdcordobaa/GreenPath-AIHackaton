import os
from typing import Optional, Dict, Any

from dotenv import load_dotenv
from supabase import create_client, Client
from mcp.server.fastmcp import FastMCP
from models import LayerQueryInput, GenericLayerQueryInput, LayerQueryOutput
from supabase_io import fetch_layer_records


load_dotenv()

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY") or os.environ.get("SUPABASE_ANON_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # Allow starting without credentials; tools that need Supabase will raise if used
    supabase: Optional[Client] = None
else:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

mcp = FastMCP("geo-fetch-mcp")


@mcp.tool()
def get_layer_records(input: GenericLayerQueryInput) -> LayerQueryOutput:
    recs = fetch_layer_records(project_id=input.project_id, layer=input.layer)
    return LayerQueryOutput(layer=input.layer, count=len(recs), records=recs)


@mcp.tool()
def get_soils(input: LayerQueryInput) -> LayerQueryOutput:
    layer = "soils"
    recs = fetch_layer_records(project_id=input.project_id, layer=layer)
    return LayerQueryOutput(layer=layer, count=len(recs), records=recs)


@mcp.tool()
def get_protected_areas(input: LayerQueryInput) -> LayerQueryOutput:
    layer = "protected_areas"
    recs = fetch_layer_records(project_id=input.project_id, layer=layer)
    return LayerQueryOutput(layer=layer, count=len(recs), records=recs)


@mcp.tool()
def get_biotic(input: LayerQueryInput) -> LayerQueryOutput:
    layer = "biotic"
    recs = fetch_layer_records(project_id=input.project_id, layer=layer)
    return LayerQueryOutput(layer=layer, count=len(recs), records=recs)


@mcp.tool()
def get_hydrography(input: LayerQueryInput) -> LayerQueryOutput:
    layer = "hydrography"
    recs = fetch_layer_records(project_id=input.project_id, layer=layer)
    return LayerQueryOutput(layer=layer, count=len(recs), records=recs)


@mcp.tool()
def get_ecosystems(input: LayerQueryInput) -> LayerQueryOutput:
    layer = "ecosystems"
    recs = fetch_layer_records(project_id=input.project_id, layer=layer)
    return LayerQueryOutput(layer=layer, count=len(recs), records=recs)


@mcp.tool()
def get_species(input: LayerQueryInput) -> LayerQueryOutput:
    layer = "species"
    recs = fetch_layer_records(project_id=input.project_id, layer=layer)
    return LayerQueryOutput(layer=layer, count=len(recs), records=recs)


@mcp.tool()
def ping() -> dict:
    return {"ok": True, "service": "geo-fetch-mcp", "version": "0.1.0"}


@mcp.tool()
def capacidad_uso_tierra_query(limit: int = 10, eq: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    if supabase is None:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in environment")
    query = supabase.table("CapacidadUsoTierra").select("*")
    # Allow caller to pass filters with either uppercase or lowercase column names
    valid_cols = {
        "id",
        "EXPEDIENTE",
        "CLASE",
        "SUBCLASE",
        "G_MANEJO",
        "USO_PRIN_P",
        "AREA_HA",
        "DES_LIMI_U",
        "OBSERV",
        "TIPO",
        "CATEGORIA",
        "GEOMETRY",
    }
    if eq:
        for raw_col, val in eq.items():
            col = raw_col
            # Normalize simple lower-case keys to expected casing if needed
            if raw_col.lower() == "categoria":
                col = "CATEGORIA"
            elif raw_col.lower() == "clase":
                col = "CLASE"
            elif raw_col.lower() == "uso_prin_p":
                col = "USO_PRIN_P"
            elif raw_col.lower() == "area_ha":
                col = "AREA_HA"
            elif raw_col.lower() == "tipo":
                col = "TIPO"
            elif raw_col.lower() == "subclase":
                col = "SUBCLASE"
            elif raw_col.lower() == "g_manejo":
                col = "G_MANEJO"
            elif raw_col.lower() == "des_limi_u":
                col = "DES_LIMI_U"
            elif raw_col.lower() == "expediente":
                col = "EXPEDIENTE"
            elif raw_col.lower() == "geometry":
                col = "GEOMETRY"

            if col not in valid_cols:
                # Skip unknown columns rather than failing query
                continue
            query = query.eq(col, val)
    query = query.limit(limit)
    resp = query.execute()
    rows = getattr(resp, "data", []) or []
    err = getattr(resp, "error", None)
    return {"rows": rows, "count": len(rows), "error": err}


if __name__ == "__main__":
    mcp.run_stdio()


