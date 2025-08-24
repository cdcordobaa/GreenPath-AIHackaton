from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import uvicorn
from dotenv import load_dotenv

load_dotenv()

try:
    from .graph import run_pipeline
    from .state import EIAState
except ImportError:
    from eia_adk.graph import run_pipeline
    from eia_adk.state import EIAState

app = FastAPI(title="EIA-ADK Agent API", version="0.1.0")

class PipelineRequest(BaseModel):
    project_path: str
    target_layers: List[str] = ["hydro.rivers", "ecosystems", "protected_areas"]

class PipelineResponse(BaseModel):
    success: bool
    message: str
    artifacts: Optional[Dict[str, Any]] = None
    state_summary: Optional[Dict[str, Any]] = None

@app.get("/health")
def health_check():
    return {"status": "healthy", "service": "eia-adk-agent"}

@app.post("/pipeline/run", response_model=PipelineResponse)
def run_analysis_pipeline(request: PipelineRequest):
    """Run the complete EIA analysis pipeline"""
    try:
        state = run_pipeline(
            project_path=request.project_path,
            target_layers=request.target_layers
        )
        
        # Convert artifacts list to dict for API response
        artifacts_dict = {}
        if hasattr(state, 'artifacts') and state.artifacts:
            for i, artifact in enumerate(state.artifacts):
                artifacts_dict[f"artifact_{i}"] = artifact
        
        return PipelineResponse(
            success=True,
            message="Pipeline completed successfully with enhanced geo_kb_agent",
            artifacts=artifacts_dict,
            state_summary={
                "project": getattr(state, 'project', {}),
                "geo_summary": getattr(state, 'geo', {}).get('structured_summary', {}),
                "legal_analysis": getattr(state, 'legal', {}),
                "intersections": len(getattr(state, 'intersections', [])),
                "enhanced_optimization": "active"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Pipeline execution failed: {str(e)}")

@app.get("/pipeline/status")
def get_pipeline_status():
    """Get the status of the pipeline service"""
    return {
        "service": "eia-adk-agent",
        "status": "running",
        "available_endpoints": [
            "/health",
            "/pipeline/run",
            "/pipeline/status"
        ]
    }

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
