from ..state import EIAState


def run(state: EIAState) -> EIAState:
    groups: dict[str, list[dict]] = {}
    for r in state.intersections:
        groups.setdefault(r["env_layer"], []).append(r)
    state.affected_features = [
        {
            "theme": "water" if "river" in k.lower() else "other",
            "feature": k,
            "n_records": len(v),
            "summary": f"{len(v)} intersecciones con {k}",
        }
        for k, v in groups.items()
    ]
    return state
