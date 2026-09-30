"""Pydantic schemas for API requests/responses"""
from typing import Optional, List
from pydantic import BaseModel, Field


class RoomSpec(BaseModel):
    type: str
    area_sqft: Optional[float] = None
    attached_bath: bool = False
    vastu_zone: Optional[str] = None


class DesignSpec(BaseModel):
    """Structured spec generated from user prompt"""
    bhk: int = Field(..., ge=1, le=10)
    total_area_sqft: float = Field(..., gt=0)
    facing: str = "north"
    vastu_compliant: bool = True
    rooms: List[RoomSpec] = []
    floors: int = 1
    city: Optional[str] = None
    notes: Optional[str] = None


class PromptRequest(BaseModel):
    """User prompt input"""
    prompt: str = Field(..., min_length=5, max_length=500)


class GenerateResponse(BaseModel):
    """Full pipeline response"""
    success: bool
    spec: Optional[DesignSpec] = None
    image_2d_url: Optional[str] = None
    model_3d_url: Optional[str] = None
    model_3d_error: Optional[str] = None
    processing_time_sec: float
    message: str = ""
