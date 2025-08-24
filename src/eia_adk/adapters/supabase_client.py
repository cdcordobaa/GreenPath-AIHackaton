import os
from typing import List, Dict, Any

from dotenv import load_dotenv
from supabase import create_client, Client


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")


_client: Client | None = None


def get_client() -> Client:
    global _client
    if _client is not None:
        return _client
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in environment")
    _client = create_client(SUPABASE_URL, SUPABASE_KEY)
    return _client


LAYER_TABLES: Dict[str, str] = {
    "soils": "intersections_soils",
    "protected_areas": "intersections_protected_areas",
    "biotic": "intersections_biotic",
    "hydrography": "intersections_hydro",
    "ecosystems": "intersections_ecosystems",
    "species": "intersections_species",
}


BASIC_COLUMNS = [
    "record_id",
    "project_id",
    "feature_id",
    "feature_name",
    "predicate",
    "buffer_m",
    "area_m2",
    "length_m",
    "distance_m",
    "attrs",
]


def fetch_layer_intersections(project_id: str, layer: str) -> List[Dict[str, Any]]:
    table = LAYER_TABLES.get(layer)
    if not table:
        raise ValueError(f"Unknown layer: {layer}")
    supa = get_client()
    resp = (
        supa.table(table)
        .select(",".join(BASIC_COLUMNS))
        .eq("project_id", project_id)
        .execute()
    )
    rows = getattr(resp, "data", []) or []

    out: List[Dict[str, Any]] = []
    for r in rows:
        out.append(
            {
                "project_id": str(r.get("project_id")),
                "env_layer": layer,
                "env_id": str(r.get("feature_id") or r.get("record_id") or r.get("id")),
                "predicate": r.get("predicate"),
                "buffer_m": r.get("buffer_m"),
                "area_m2": r.get("area_m2"),
                "length_m": r.get("length_m"),
                "distance_m": r.get("distance_m"),
                "attrs": r.get("attrs") or {"feature_name": r.get("feature_name")},
            }
        )
    return out
