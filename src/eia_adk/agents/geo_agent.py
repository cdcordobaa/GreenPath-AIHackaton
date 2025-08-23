from google.adk.agents.llm_agent import Agent
from .tools import run_geospatial_with_config


agent = Agent(
    model='gemini-2.5-flash',
    name='geo_agent',
    description='Análisis geoespacial e intersecciones',
    instruction=(
        'Si falta state_json o no hay project.config_layers definidos, solicita:\n'
        '- state_json (estado actual devuelto por ingest_agent).\n'
        '- predicate (por defecto "intersects"): indica el tipo de análisis.\n'
        '- buffer_m (opcional).\n'
        'Cuando estén listos, llama run_geospatial_with_config(state_json, predicate?, buffer_m?) y devuelve el estado.'
    ),
    tools=[run_geospatial_with_config],
)


