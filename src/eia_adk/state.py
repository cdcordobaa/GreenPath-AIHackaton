from pydantic import BaseModel, Field
from typing import List, Dict, Any


class EIAState(BaseModel):
    """EIA State model that matches the actual nested structure used by agents."""
    
    # Project metadata (written by ingest_agent)
    project: Dict[str, Any] = Field(default_factory=dict, description="Project metadata: project_name, project_id, project_shapefile_path")
    
    # Configuration (written by ingest_agent)
    config: Dict[str, Any] = Field(default_factory=lambda: {"layers": []}, description="Configuration: target layers for analysis")
    
    # Geospatial analysis results (written by geo_agent, read by geo2neo_agent and geo_kb_agent)
    geo: Dict[str, Any] = Field(
        default_factory=lambda: {
            "summary": {},
            "by_layer": {},
            "intersections": {},
            "structured_summary": {"count": 0, "rows": []}
        },
        description="Geospatial data: structured_summary with {recurso1, recurso, cantidad, tipo, categoria}"
    )
    
    # Impact analysis results
    impacts: Dict[str, Any] = Field(
        default_factory=lambda: {"categories": [], "entities": []},
        description="Impact analysis: affected categories and entities"
    )
    
    # Legal analysis results (written by geo2neo_agent and geo_kb_agent)
    legal: Dict[str, Any] = Field(
        default_factory=lambda: {
            "candidates": [],
            "requirements": [],
            "geo2neo": {"alias_input": [], "alias_mapping": {}},
            "kb": {"keywords": [], "scraped_pages": {"count": 0, "rows": []}}
        },
        description="Legal analysis: geo2neo mappings and knowledge base search results"
    )
    
    # Legacy fields for backward compatibility (if needed)
    intersections: List[Dict[str, Any]] = Field(default_factory=list, description="Legacy: use geo.intersections instead")
    affected_features: List[Dict[str, Any]] = Field(default_factory=list, description="Legacy: use impacts.entities instead")
    legal_triggers: List[Dict[str, Any]] = Field(default_factory=list, description="Legacy: use legal.candidates instead")
    legal_scope: List[Dict[str, Any]] = Field(default_factory=list, description="Legacy: use legal.requirements instead")
    compliance: Dict[str, Any] = Field(default_factory=lambda: {"requirements": []}, description="Legacy: use legal.requirements instead")
    artifacts: List[Dict[str, Any]] = Field(default_factory=list, description="Workflow artifacts and outputs")
