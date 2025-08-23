from google.adk.agents.llm_agent import Agent
from google.adk.agents.sequential_agent import SequentialAgent
from .eia_adk.agents.ingest_agent import agent as ingest_agent
from .eia_adk.agents.geo_agent import agent as geo_agent
from .eia_adk.agents.synthesis_agent import agent as synthesis_agent
from .eia_adk.agents.summarizer_agent import agent as summarizer_agent
from .eia_adk.agents.legal_scope_agent import agent as legal_scope_agent
from .eia_adk.agents.legal_agent import agent as legal_agent
from .eia_adk.agents.report_agent import agent as report_agent
from .eia_adk.agents.tools import run_pipeline_tool


# Deterministic workflow runner that chains all specialists in order
workflow_agent = SequentialAgent(
    name='workflow',
    description='EIA pipeline: ingest → geo → synthesis → summarizer → legal_scope → legal → report',
    sub_agents=[
        ingest_agent,
        geo_agent,
        # synthesis_agent,
        # summarizer_agent,
        # legal_scope_agent,
        # legal_agent,
        # report_agent,
    ],
)

# LLM coordinator that can route or trigger the full pipeline tool
root_agent = Agent(
    model='gemini-2.5-flash',
    name='eia_coordinator',
    description='Coordinator/Dispatcher that routes to specialists and maintains shared state.',
    instruction=(
        'Eres el Coordinador EIA. Mantén un estado consistente en la sesión.\n'
        'Reglas de orquestación (en orden):\n'
        '- Si falta state.project -> transferir al agente workflow.\n'
        '- Si el usuario pide análisis completo, puedes llamar run_pipeline_tool(project_path, target_layers).\n'
        '- De lo contrario, transfiere al agente workflow para ejecutar la secuencia completa.\n'
        'Finaliza cuando exista un reporte listo (por ejemplo, out/report.md).\n'
        'Ejemplo: Analiza: project_path=data/sample_project/lines.geojson target_layers=["hydro.rivers","ecosystems","protected_areas"]\n'
    ),
    tools=[run_pipeline_tool],
    sub_agents=[workflow_agent],
)


