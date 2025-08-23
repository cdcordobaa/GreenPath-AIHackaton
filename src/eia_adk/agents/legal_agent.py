from google.adk.agents.llm_agent import Agent
from .tools import legal_requirements


agent = Agent(
    model='gemini-2.5-pro',
    name='legal_agent',
    description='Análisis legal y requerimientos',
    instruction='Usa legal_requirements(state_json) para producir requirements. Devuelve el estado.',
    tools=[legal_requirements],
)


