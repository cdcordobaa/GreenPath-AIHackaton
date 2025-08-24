from typing import Any, Dict, List, Set

from fastmcp import FastMCP
from pydantic import BaseModel, Field

from neo4j_io import (
    lookup_tokens,
    inspect_taxonomy as _inspect_taxonomy,
    fetch_instrumento_paths,
    run_tx,
)


mcp = FastMCP(
    name="geo2neo-mcp",
    version="0.1.0",
)


# ---- Config: which columns to read per layer (add more as needed) ----
DEFAULT_LAYER_COLS: Dict[str, List[str]] = {
    # your sample layer
    "capacidad_uso_tierra": [
        "CATEGORIA",
        "TIPO",
        "DES_LIMI_U",
        "CLASE",
        "SUBCLASE",
        "G_MANEJO",
        "USO_PRIN_P",
    ],
    # typical others (safe guesses; adjust freely)
    "hydrography": ["NOMBRE", "TIPO", "CATEGORIA", "CLASE"],
    "soils": ["CATEGORIA", "CLASE", "SUBCLASE", "USO"],
    "protected_areas": ["NOMBRE", "CATEGORIA", "FIGURA", "TIPO"],
    "biotic": ["NOMBRE", "CATEGORIA", "TIPO"],
    "ecosystems": ["NOMBRE", "CATEGORIA", "TIPO", "BIOMA"],
    "species": ["SCIENTIFIC", "COMMON", "CATEGORIA", "IUCN"],
}


# ---- I/O models ----
class MapInput(BaseModel):
    geo: Dict[str, Any]  # full payload you posted
    # optional override: {"layer_name": ["COL1","COL2", ...]}
    layer_cols: Dict[str, List[str]] = Field(default_factory=dict)


class MapOutput(BaseModel):
    tokens: List[str]
    matches: List[Dict[str, Any]]  # [{token, laws[], permits[], authorities[]}]


# ---- Helpers ----
def _to_token(v: Any) -> str | None:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return str(v)
    if isinstance(v, str):
        s = v.strip()
        return s if s else None
    # ignore non-scalars
    return None


def extract_tokens(geo: Dict[str, Any], layer_cols: Dict[str, List[str]]) -> List[str]:
    unique: Set[str] = set()
    by_layer = (geo or {}).get("by_layer") or {}
    for layer, bucket in by_layer.items():
        rows = bucket.get("rows") or []
        cols = layer_cols.get(layer) or DEFAULT_LAYER_COLS.get(layer) or []
        if not cols:  # if we don't know the layer, try all stringy fields present in first row
            if rows:
                cols = [k for k in rows[0].keys() if k.upper() not in ("GEOMETRY",)]
        for r in rows:
            for c in cols:
                val = _to_token(r.get(c))
                if val:
                    unique.add(val)
    # also add summary keys like "capacidad_uso_tierra_count">0? add layer name
    summary = (geo or {}).get("summary") or {}
    for k, v in summary.items():
        if isinstance(v, (int, float)) and v > 0:
            layer_name = k.replace("_count", "")
            unique.add(layer_name)
    return sorted(unique)


# ---- Tool ----
def map_geo_to_legal(input: MapInput) -> MapOutput:
    tokens = extract_tokens(input.geo, input.layer_cols)
    hits = lookup_tokens(tokens)
    # Return exactly what’s needed: the token and the graph’s responses
    # Ensure every token appears once; include empty hits for transparency
    by_tok = {
        h["token"]: {
            "token": h["token"],
            "laws": h.get("laws", []),
            "permits": h.get("permits", []),
            "authorities": h.get("authorities", []),
        }
        for h in hits
    }
    matches = [
        by_tok.get(
            t, {"token": t, "laws": [], "permits": [], "authorities": []}
        )
        for t in tokens
    ]
    return MapOutput(tokens=tokens, matches=matches)


class InspectInput(BaseModel):
    count_limit: int | None = 100
    include_properties: bool = True
    include_indexes: bool = True
    include_constraints: bool = True


def inspect_taxonomy(input: InspectInput) -> Dict[str, Any]:
    return _inspect_taxonomy(
        count_limit=input.count_limit,
        include_properties=input.include_properties,
        include_indexes=input.include_indexes,
        include_constraints=input.include_constraints,
    )


class InstrumentoInput(BaseModel):
    limit: int = 25


def get_instrumento_paths(input: InstrumentoInput) -> Dict[str, Any]:
    items = fetch_instrumento_paths(limit=input.limit)
    return {"count": len(items), "paths": items}


# ---------- New: Map by aliases (Categoria-driven) ----------
class MapByAliasesInput(BaseModel):
    aliases: List[str] = Field(default_factory=list)


MAP_BY_ALIASES_CYPHER = """
UNWIND $aliases AS alias
WITH DISTINCT alias
MATCH (c:Category)
WHERE alias IN c.aliases
WITH DISTINCT c
MATCH (c)<-[:BELONGS_TO_CATEGORY]-(i:Instrument)
MATCH (i)<-[:IS_MODALITY_OF]-(sub:Subcategory)-[:APPLIES_TO]->(r:Resource)
OPTIONAL MATCH (sub)<-[:IS_CRITERION_FOR]-(mc:ManagementCriterion)
WITH c, i, sub, r, collect(DISTINCT mc.description) AS managementCriteria
OPTIONAL MATCH (sub)<-[:IS_CRITERION_FOR]-(cc:CompensationCriterion)
WITH c, i, sub, r, managementCriteria, collect(DISTINCT cc.description) AS compensationCriteria
WITH c, i, {
  subcategoryName: sub.name,
  affectedResource: r.name,
  managementCriteria: managementCriteria,
  compensationCriteria: compensationCriteria
} AS subcategoryDetails
ORDER BY subcategoryDetails.subcategoryName
WITH c, i, collect(subcategoryDetails) AS instrumentModalities
WITH c, {
  instrumentName: i.name,
  modalities: instrumentModalities
} AS instrumentDetails
ORDER BY instrumentDetails.instrumentName
WITH c, collect(instrumentDetails) AS detailedInstruments
OPTIONAL MATCH (c)-[:INCLUDES_NORM]->(norm:NormativeInstrument)
OPTIONAL MATCH (norm)-[reg:REGULATED_BY]->(childNorm:NormativeInstrument)
WITH c, detailedInstruments, norm, {
  childNormName: childNorm.name,
  relationType: reg.type
} AS childNormDetails
ORDER BY childNormDetails.childNormName
WITH c, detailedInstruments, norm, collect(childNormDetails) AS childNorms
WITH c, detailedInstruments, norm,
     CASE WHEN size(childNorms) > 0 AND childNorms[0].childNormName IS NOT NULL THEN childNorms ELSE [] END AS cleanedChildNorms
ORDER BY norm.name
WITH c, detailedInstruments, {
  normName: norm.name,
  type: norm.type,
  issuer: norm.issuer,
  year: norm.year,
  component: norm.component,
  obligations: norm.obligations,
  requiredData: norm.required_data,
  childNorms: cleanedChildNorms
} AS normDetails
WITH c, detailedInstruments, collect(DISTINCT normDetails) AS associatedNorms
RETURN c.name AS category, detailedInstruments AS instrumentsAndPermits, associatedNorms AS associatedNorms
"""


@mcp.tool()
def map_by_aliases(input: MapByAliasesInput) -> Dict[str, Any]:
    aliases = [a for a in (input.aliases or []) if isinstance(a, str) and a.strip()]
    if not aliases:
        return {"ok": False, "error": "empty aliases"}
    records, meta = run_tx(MAP_BY_ALIASES_CYPHER, {"aliases": aliases})
    return {"ok": True, "count": len(records), "results": records, "meta": meta}


@mcp.tool()
def ping() -> Dict[str, Any]:
    return {"ok": True}


if __name__ == "__main__":
    mcp.run(host="0.0.0.0", port=8795)


