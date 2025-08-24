from fastapi import FastAPI, Body
from typing import Dict, Any, Optional

from models import LayerQueryInput, GenericLayerQueryInput
import app as mcp_app


api = FastAPI(title="eia-geo-mcp", version="0.1.0")


@api.post("/tools/ping")
def http_ping() -> Dict[str, Any]:
    return mcp_app.ping()


@api.post("/tools/get_layer_records")
def http_get_layer_records(input: GenericLayerQueryInput):
    out = mcp_app.get_layer_records(input)
    return out.model_dump()


@api.post("/tools/get_ecosystems")
def http_get_ecosystems(input: LayerQueryInput):
    out = mcp_app.get_ecosystems(input)
    return out.model_dump()


@api.post("/tools/capacidad_uso_tierra_query")
def http_capacidad_uso_tierra_query(limit: int = 10, filters: Optional[Dict[str, Any]] = Body(default=None)):
    return mcp_app.capacidad_uso_tierra_query(limit=limit, eq=filters)


@api.post("/tools/hydrology")
def http_hydrology(project_id: str, limit: int = 10, filters: Optional[Dict[str, Any]] = Body(default=None)):
    return mcp_app.hydrology(project_id=project_id, limit=limit, filters=filters)


if __name__ == "__main__":
    import uvicorn
    import os
    port = int(os.environ.get("PORT", 8765))
    uvicorn.run(api, host="0.0.0.0", port=port)


