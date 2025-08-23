from typing import Optional, List, Dict


class GeoMCP:
    def get_layer(self, layer_key: str, bbox: Optional[dict] = None) -> dict:
        return {"layer_key": layer_key, "crs": "EPSG:3116", "features": []}

    def spatial_join(
        self,
        project_layer: dict,
        env_layer: dict,
        predicate: str = "intersects",
        buffer_m: Optional[float] = None,
    ) -> List[Dict]:
        return [
            {
                "project_id": "L-001",
                "env_layer": env_layer["layer_key"],
                "env_id": "RIVER-123",
                "predicate": predicate,
                "buffer_m": buffer_m or 0,
                "area_m2": 0,
                "length_m": 42.0,
                "distance_m": 0.0,
                "attrs": {"name": "Río Demostración"},
            }
        ]

    def summarize_intersections(self, rows: List[Dict], by: str = "feature_type") -> dict:
        return {"count": len(rows), "by": by}
