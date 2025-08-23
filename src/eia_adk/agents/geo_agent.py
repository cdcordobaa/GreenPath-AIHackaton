from google.adk.agents.llm_agent import Agent
from .tools import run_geospatial


agent = Agent(
    model='gemini-2.5-flash',
    name='geo_agent',
    description='Análisis geoespacial e intersecciones',
    instruction='Usa run_geospatial(state_json, target_layers, predicate, buffer_m) y devuelve el estado.',
    tools=[run_geospatial],
)


