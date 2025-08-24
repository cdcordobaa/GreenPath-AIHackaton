from typing import Optional, List, Dict
import os

from ..adapters.supabase_client import fetch_layer_intersections


class GeoMCP:
    def __init__(self, project_id_env: str = "EIA_PROJECT_ID") -> None:
        self.project_id = os.getenv(project_id_env, "demo-project")

    def get_layer(self, layer_key: str, bbox: Optional[dict] = None) -> dict:
        return {"layer_key": layer_key, "crs": "EPSG:3116", "features": []}

    def spatial_join(
        self,
        project_layer: dict,
        env_layer: dict,
        predicate: str = "intersects",
        buffer_m: Optional[float] = None,
    ) -> List[Dict]:
        layer = env_layer["layer_key"]
        project_id = self.project_id
        try:
            rows = fetch_layer_intersections(project_id=project_id, layer=layer)
        except Exception:
            rows = []
        return rows

    def summarize_intersections(self, rows: List[Dict], by: str = "feature_type") -> dict:
        return {"count": len(rows), "by": by}
