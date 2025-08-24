from google.adk.agents.llm_agent import Agent
import os
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, StdioServerParameters
from pathlib import Path
from typing import Any, Dict
from .tools import (
    mock_geo2neo_map,
    geo2neo_from_structured_summary,
    mock_geo2neo_from_structured_summary,
)


# Configure MCP stdio toolset for mcp-geo2neo
_repo_root = Path(__file__).resolve().parents[3]
_mcp_dir = _repo_root / 'mcp-geo2neo'
_mcp_entry = _mcp_dir / 'run_stdio.py'
# Prefer the mcp-geo2neo venv python if present, else current interpreter
_venv_python = _mcp_dir / '.venv' / 'bin' / 'python'
_python_cmd = str(_venv_python) if _venv_python.exists() else os.environ.get('PYTHON', os.sys.executable)

mcp_geo2neo_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=_python_cmd,
            args=[str(_mcp_entry)],
        ),
        timeout=30.0,  # Increase timeout from 5s to 30s
    ),
)


agent = Agent(
    model='gemini-2.5-flash',
    name='geo2neo_agent',
    description='Agent that calls the geo2neo MCP based on impacted resources.',
    instruction=(
        'Toma la salida previa (state.geo.structured_summary). Extrae valores únicos de la columna tipo y,\n'
        "para esos alias, llama la herramienta MCP 'map_by_aliases' en mcp-geo2neo. Guarda el resultado en state.legal.geo2neo.alias_mapping.\n"
        'En modo MOCK, usa mock_geo2neo_from_structured_summary.'
    ),
    tools=[
        mcp_geo2neo_toolset,
        mock_geo2neo_from_structured_summary if os.getenv('EIA_USE_MOCKS', '0') in ('1','true','True') else geo2neo_from_structured_summary,
    ],
)
