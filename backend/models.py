from pydantic import BaseModel
from typing import Optional, List, Dict


class AlarmConfig(BaseModel):
    id: Optional[int] = None
    tag_id: int
    operator: str  # '>', '<', etc.
    threshold: float
    priority: str
    enabled: bool = True
    message: str


class SensorMetadata(BaseModel):
    tag: str
    description: Optional[str] = None
    process_role: Optional[str] = None
    normal_range_min: Optional[float] = None
    normal_range_max: Optional[float] = None
    critical_range_min: Optional[float] = None
    critical_range_max: Optional[float] = None
    physical_location: Optional[str] = None
    related_system: Optional[str] = None
    failure_impact: Optional[str] = None
    operating_notes: Optional[str] = None


class ChatRequest(BaseModel):
    message: str
    history: Optional[List[Dict]] = []


class AIAskRequest(BaseModel):
    tag: Optional[str] = None
    question: str
