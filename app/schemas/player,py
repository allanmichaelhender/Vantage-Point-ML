from pydantic import BaseModel, Field
from typing import Optional, List

class PlayerBase(BaseModel):
    id: str = Field(..., example="104925")
    name: str = Field(..., example="Novak Djokovic")
    country: Optional[str] = None
    hand: Optional[str] = Field(None, example="R") # R, L, U

class PlayerSearchResponse(PlayerBase):
    """Minimal schema for the fast Autocomplete dropdown"""
    current_rank: Optional[int] = None
    
    class Config:
        from_attributes = True

class PlayerDetailResponse(PlayerSearchResponse):
    """Full schema for the 'Battle' page profile"""
    elo: float
    surface_elo: float
    height: Optional[int] = None
    birth_date: Optional[str] = None

class PlayerListResponse(BaseModel):
    count: int
    players: List[PlayerSearchResponse]
