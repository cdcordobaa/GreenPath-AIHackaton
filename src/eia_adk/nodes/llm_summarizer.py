from ..state import EIAState

# from adk.agents import LlmAgent  # enable later when configuring ADK


def run(state: EIAState, model: str = "gemini-1.5-flash") -> EIAState:
    # agent = LlmAgent(model=model)
    # prompt = (
    #     "Eres un analista ambiental. Dado el JSON de 'affected_features', "
    #     "devuelve: (1) resumen por tema, (2) lista de 'legal_triggers' con "
    #     "trigger, contexto, prioridad.\n"
    #     f"AFFECTED_FEATURES:\n{state.affected_features}"
    # )
    # response = agent.run(prompt)
    # state.legal_triggers = parse(response)
    state.legal_triggers = [
        {"trigger": "cruce de cauce", "context": "river crossing", "priority": "alta"}
    ]
    return state
