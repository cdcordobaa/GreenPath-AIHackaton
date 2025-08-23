from google.adk.agents.llm_agent import Agent
from .tools import summarize_impacts


agent = Agent(
    model='gemini-2.5-pro',
    name='summarizer_agent',
    description='Resumen de impactos y disparadores legales',
    instruction='Usa summarize_impacts(state_json) para producir legal_triggers. Devuelve el estado.',
    tools=[summarize_impacts],
)


