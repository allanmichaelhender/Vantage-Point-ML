from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Optional

class UpcomingMatchBase(BaseModel):
    p1_name: str
    p2_name: str
    match_date: datetime
    tournament: str
    surface: str
    round: Optional[str] = None
    
    # Odds from our target bookies
    b365_p1: Optional[float] = None
    b365_p2: Optional[float] = None
    pin_p1: Optional[float] = None
    pin_p2: Optional[float] = None

class UpcomingMatchCreate(UpcomingMatchBase):
    """Schema for internal data creation (includes IDs)"""
    p1_id: str
    p2_id: str
    predicted_p1_prob: float
    predicted_p2_prob: float

class UpcomingMatchResponse(UpcomingMatchBase):
    """Schema for what the Frontend sees"""
    id: int
    p1_id: str
    p2_id: str
    predicted_p1_prob: float
    predicted_p2_prob: float
    synced_at: datetime

    class Config:
        from_attributes = True # Allows Pydantic to read SQLAlchemy objects

class SyncResponse(BaseModel):
    status: str
    count: int
    matches: List[UpcomingMatchResponse]
