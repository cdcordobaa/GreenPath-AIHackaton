from pydantic import BaseModel, Field
from typing import List, Dict, Any


class EIAState(BaseModel):
    project: Dict[str, Any] = Field(default_factory=dict)
    intersections: List[Dict[str, Any]] = Field(default_factory=list)
    affected_features: List[Dict[str, Any]] = Field(default_factory=list)
    legal_triggers: List[Dict[str, Any]] = Field(default_factory=list)
    legal_scope: List[Dict[str, Any]] = Field(default_factory=list)
    compliance: Dict[str, Any] = Field(default_factory=lambda: {"requirements": []})
    artifacts: List[Dict[str, Any]] = Field(default_factory=list)
