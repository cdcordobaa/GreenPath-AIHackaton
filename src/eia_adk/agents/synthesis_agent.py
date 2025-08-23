from google.adk.agents.llm_agent import Agent
from .tools import synthesize_intersections


agent = Agent(
    model='gemini-2.5-flash',
    name='synthesis_agent',
    description='Síntesis de intersecciones',
    instruction='Usa synthesize_intersections(state_json) y devuelve el estado.',
    tools=[synthesize_intersections],
)


