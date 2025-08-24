from google.adk.agents.llm_agent import Agent
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, StdioServerParameters
from pathlib import Path
import os
from .tools import search_scraped_pages_via_mcp


# Configure MCP stdio toolset for mcp-geo2neo
_repo_root = Path(__file__).resolve().parents[3]
_mcp_dir = _repo_root / 'mcp-geo2neo'
_mcp_entry = _mcp_dir / 'run_stdio.py'
_venv_python = _mcp_dir / '.venv' / 'bin' / 'python'
_python_cmd = str(_venv_python) if _venv_python.exists() else os.environ.get('PYTHON', os.sys.executable)

mcp_geo2neo_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=_python_cmd,
            args=[str(_mcp_entry)],
        ),
    ),
)


agent = Agent(
    model='gemini-2.5-flash',
    name='geo_kb_agent',
    description='Interprets geo2neo results and queries the knowledge base via MCP.',
    instruction=(
        'Use prior state (e.g., legal.geo2neo.summary.category) to decide what to search.\n'
        "First ensure connectivity by pinging MCP; then call the search tool to fetch matching scraped_pages rows."
    ),
    tools=[
        mcp_geo2neo_toolset,
        search_scraped_pages_via_mcp,
    ],
)


