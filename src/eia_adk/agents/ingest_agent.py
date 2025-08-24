from google.adk.agents.llm_agent import Agent
from .tools import intake_project


agent = Agent(
    model='gemini-2.5-flash',
    name='ingest_agent',
    description='Intake del proyecto: project_name, project_id? y layers[].',
    instruction=(
        'Solicita y valida: project_name (obligatorio), project_id (opcional) y layers[] (obligatorio).\n'
        'Cuando estén listos, llama:\n'
        'intake_project(project_name, layers, project_id?, project_shapefile_path?)\n'
        'Devuelve el estado JSON tal como lo entrega la herramienta.'
    ),
    tools=[intake_project],
)


