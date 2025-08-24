from google.adk.agents.llm_agent import Agent
from .tools import enhanced_assemble_report


agent = Agent(
    model='gemini-2.5-flash',
    name='enhanced_report_agent',
    description='Generación de reporte de análisis EIA completo y detallado',
    instruction=(
        'Genera un reporte de análisis EIA completo basado en todos los resultados del workflow:\n'
        '1. Información del proyecto (state.project)\n'
        '2. Análisis geoespacial (state.geo.structured_summary)\n'
        '3. Mapeo de recursos legales (state.legal.geo2neo.alias_mapping)\n'
        '4. Búsqueda en base de conocimiento legal (state.legal.kb.scraped_pages)\n'
        '5. Usa enhanced_assemble_report(state_json, out_path) para generar un documento estructurado.\n'
        'El reporte debe incluir:\n'
        '- Resumen ejecutivo del proyecto\n'
        '- Recursos geoespaciales identificados\n'
        '- Marco legal aplicable\n'
        '- Requerimientos y permisos identificados\n'
        '- Recomendaciones y próximos pasos\n'
        'Devuelve el estado actualizado con el reporte.'
    ),
    tools=[enhanced_assemble_report],
)
