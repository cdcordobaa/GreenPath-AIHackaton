from google.adk.agents.llm_agent import Agent
from .tools import configure_project


agent = Agent(
    model='gemini-2.5-flash',
    name='ingest_agent',
    description='Configuración inicial del proyecto (asumiendo archivo existente) y definición de capas objetivo.',
    instruction=(
        'Asume que el archivo del proyecto ya existe. Antes de continuar, solicita la información faltante:\n'
        '- target_layers (obligatorio): lista de capas ambientales a evaluar.\n'
        '- project_path (opcional): si no se indica, usaré data/sample_project/lines.geojson y lo confirmaré.\n'
        '- layer_type (opcional): por defecto "lines".\n'
        'Cuando tengas target_layers (y opcionalmente project_path y layer_type), llama a\n'
        'configure_project(target_layers, project_path?, layer_type?) y devuelve el estado JSON resultante.'
    ),
    tools=[configure_project],
)


