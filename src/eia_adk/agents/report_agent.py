from google.adk.agents.llm_agent import Agent
from .tools import assemble_report


agent = Agent(
    model='gemini-2.5-flash',
    name='report_agent',
    description='Generación de reporte final',
    instruction='Usa assemble_report(state_json, out_path) y devuelve el estado con report_uri.',
    tools=[assemble_report],
)


