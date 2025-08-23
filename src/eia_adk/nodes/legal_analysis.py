from ..state import EIAState


# from ..adapters.doc_fetcher import fetch_text

def run(state: EIAState, model: str = "gemini-1.5-flash") -> EIAState:
    requirements = []
    for item in state.legal_scope:
        requirements.append(
            {
                "ref": item["legal_ref"],
                "action": f"Tramitar {item['permit_type']}",
                "when": "antes de obra",
                "docs": item.get("evidence", []),
                "risk": "alto" if "cauce" in item["permit_type"].lower() else "medio",
            }
        )
    state.compliance["requirements"] = requirements
    return state
