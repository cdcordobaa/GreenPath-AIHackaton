from google.adk.agents.llm_agent import Agent
from .tools import resolve_legal_scope


agent = Agent(
    model='gemini-2.5-flash',
    name='legal_scope_agent',
    description='Mapeo de disparadores a reglas legales',
    instruction='Usa resolve_legal_scope(state_json) y devuelve el estado con legal_scope.',
    tools=[resolve_legal_scope],
)


