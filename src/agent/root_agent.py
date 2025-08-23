import os
from google.adk.agents import Agent  # type: ignore


root_agent = Agent(
    name="eia-root",
    model=os.getenv("EIA_MODEL_PRIMARY", "gemini-2.5-flash"),
    description="Root agent for EIA demo",
    instruction=(
        "Eres un asistente de evaluación ambiental. Responde de forma concisa en español."
    ),
)


