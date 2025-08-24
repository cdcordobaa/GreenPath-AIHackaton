from google.adk.agents.llm_agent import Agent
import os
from .tools import (
    structured_summary_via_mcp,
    mock_structured_summary,
)
from google.adk.tools.mcp_tool.mcp_toolset import MCPToolset, StdioConnectionParams, StdioServerParameters
from pathlib import Path
import os


# Configure MCP stdio toolset for geo-fetch-mcp
_repo_root = Path(__file__).resolve().parents[3]
_mcp_dir = _repo_root / 'geo-fetch-mcp'
_mcp_entry = _mcp_dir / 'run_stdio.py'
# Prefer the geo-fetch-mcp venv python if present, else current interpreter
_venv_python = _mcp_dir / '.venv' / 'bin' / 'python'
_python_cmd = str(_venv_python) if _venv_python.exists() else os.environ.get('PYTHON', os.sys.executable)
mcp_geo_fetch_toolset = MCPToolset(
    connection_params=StdioConnectionParams(
        server_params=StdioServerParameters(
            command=_python_cmd,
            args=[str(_mcp_entry)],
        ),
        timeout=30.0,  # Increase timeout from 5s to 30s
    ),
)

USE_MOCKS = os.getenv('EIA_USE_MOCKS', '0') in ('1', 'true', 'True')

agent = Agent(
    model='gemini-2.5-flash',
    name='geo_agent',
    description='Análisis geoespacial e intersecciones',
    instruction=(
        'Recibe el estado del intake con project y config.layers.\n'
        '1) Llama structured_summary_via_mcp (vía MCP) para obtener filas agregadas con campos {recurso1,recurso,cantidad,tipo,categoria}.\n'
        '2) Guarda el resultado en state.geo.structured_summary.\n'
        'Soporta modo MOCK via EIA_USE_MOCKS=1.\n'
    ),
    tools=[
        mcp_geo_fetch_toolset,
        mock_structured_summary if USE_MOCKS else structured_summary_via_mcp,
    ],
)


