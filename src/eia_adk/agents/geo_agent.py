from google.adk.agents.llm_agent import Agent
from .tools import run_geospatial_with_config
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
    ),
)

agent = Agent(
    model='gemini-2.5-flash',
    name='geo_agent',
    description='Análisis geoespacial e intersecciones',
    instruction=(
        'Primero verifica conectividad con el servicio geo-fetch-mcp llamando el tool MCP "ping".\n'
        'Luego llama al tool "hydrology" con project_id (por defecto "demo-project") para obtener un resumen.\n'
        'Si falla, informa el error y solicita continuar o reintentar.\n'
        # 'Si falta state_json o no hay project.config_layers definidos, solicita:\n'
        # '- state_json (estado actual devuelto por ingest_agent).\n'
        # '- predicate (por defecto "intersects"): indica el tipo de análisis.\n'
        # '- buffer_m (opcional).\n'
        # 'Cuando estén listos, llama run_geospatial_with_config(state_json, predicate?, buffer_m?) y devuelve el estado.'
    ),
    tools=[mcp_geo_fetch_toolset],
)


