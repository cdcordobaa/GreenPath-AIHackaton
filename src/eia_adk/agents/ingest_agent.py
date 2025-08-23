from google.adk.agents.llm_agent import Agent
from .tools import ingest_project


agent = Agent(
    model='gemini-2.5-flash',
    name='ingest_agent',
    description='Ingesta de proyecto GIS',
    instruction='Usa la herramienta ingest_project(project_path, layer_type) y devuelve el estado JSON.',
    tools=[ingest_project],
)


