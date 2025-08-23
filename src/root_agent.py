from google.adk.agents.llm_agent import Agent


root_agent = Agent(
    model='gemini-2.5-flash',
    name='root_agent',
    description='EIA root agent for src app.',
    instruction='Responde de forma concisa en español.'
)


