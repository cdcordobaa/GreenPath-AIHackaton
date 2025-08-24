from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field


class LayerRecord(BaseModel):
    record_id: str
    project_id: str
    layer: str
    feature_id: Optional[str] = None
    feature_name: Optional[str] = None
    predicate: Optional[str] = None
    buffer_m: Optional[float] = None
    area_m2: Optional[float] = None
    length_m: Optional[float] = None
    distance_m: Optional[float] = None
    attrs: Dict[str, Any] = Field(default_factory=dict)


class LayerQueryInput(BaseModel):
    project_id: str


class GenericLayerQueryInput(LayerQueryInput):
    layer: str


class LayerQueryOutput(BaseModel):
    layer: str
    count: int
    records: List[LayerRecord]


