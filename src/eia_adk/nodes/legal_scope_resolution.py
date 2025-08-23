from ..state import EIAState
from ..mcp.legal_kb_mcp import LegalKBMCP


def run(state: EIAState) -> EIAState:
    kb = LegalKBMCP()
    scope = kb.map_triggers_to_rules(state.legal_triggers)
    state.legal_scope = scope
    return state
