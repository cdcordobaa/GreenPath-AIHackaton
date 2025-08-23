from ..state import EIAState


def run(state: EIAState, project_path: str, layer_type: str = "lines") -> EIAState:
    state.project = {
        "name": "Demo Project",
        "crs": "EPSG:3116",
        "layers": {layer_type: {"path": project_path, "count": 1}},
        "metadata": {"owner": "EcoLegalHack", "date": "2025-08-23"},
    }
    return state
