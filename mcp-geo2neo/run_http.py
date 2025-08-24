from fastapi import FastAPI
import uvicorn
from app import mcp

# Create FastAPI app that wraps the MCP server
api = FastAPI(title="mcp-geo2neo", version="0.1.0")

# Add a simple health check
@api.get("/health")
def health_check():
    return {"status": "healthy", "service": "mcp-geo2neo"}

# Run the MCP server via FastAPI
if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8766))
    uvicorn.run(api, host="0.0.0.0", port=port)
