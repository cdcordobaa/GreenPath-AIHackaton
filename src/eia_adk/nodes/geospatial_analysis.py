from typing import Optional, List

from ..state import EIAState
from ..mcp.geo_mcp import GeoMCP


def run(
    state: EIAState,
    target_layers: List[str],
    predicate: str = "intersects",
    buffer_m: Optional[float] = None,
) -> EIAState:
    geo = GeoMCP()
    for key in target_layers:
        env = geo.get_layer(key)
        proj = state.project.get("layers", {}).get("lines", {})
        hits = geo.spatial_join(
            project_layer=proj, env_layer=env, predicate=predicate, buffer_m=buffer_m
        )
        state.intersections.extend(hits)
    return state
