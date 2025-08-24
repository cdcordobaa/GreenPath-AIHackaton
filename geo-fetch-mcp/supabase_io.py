import os
from typing import List
from supabase import create_client, Client
from dotenv import load_dotenv
from models import LayerRecord


load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY") or os.getenv("SUPABASE_ANON_KEY")


def get_client() -> Client:
    if not SUPABASE_URL or not SUPABASE_KEY:
        raise RuntimeError("Missing SUPABASE_URL or SUPABASE_KEY in environment")
    return create_client(SUPABASE_URL, SUPABASE_KEY)


LAYER_TABLES = {
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


def fetch_layer_records(project_id: str, layer: str) -> List[LayerRecord]:
    table = LAYER_TABLES.get(layer)
    if not table:
        raise ValueError(f"Unknown layer: {layer}")

    supa = get_client()
    resp = supa.table(table).select(",".join(BASIC_COLUMNS)).eq("project_id", project_id).execute()
    rows = resp.data or []

    out: List[LayerRecord] = []
    for r in rows:
        out.append(
            LayerRecord(
                record_id=str(r.get("record_id") or r.get("id")),
                project_id=str(r["project_id"]),
                layer=layer,
                feature_id=str(r.get("feature_id")) if r.get("feature_id") is not None else None,
                feature_name=r.get("feature_name"),
                predicate=r.get("predicate"),
                buffer_m=r.get("buffer_m"),
                area_m2=r.get("area_m2"),
                length_m=r.get("length_m"),
                distance_m=r.get("distance_m"),
                attrs=r.get("attrs") or {},
            )
        )
    return out


