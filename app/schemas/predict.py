from pydantic import BaseModel, Field
from typing import Optional

class ManualPredictRequest(BaseModel):
    p1_id: str = Field(..., example="104925")
    p2_id: str = Field(..., example="106401")
    surface: str = Field(..., example="Hard")

class PlayerSnapshot(BaseModel):
    """The 'Right Now' state of the player"""
    elo: float
    surf_elo: float
    days_off: int
    surf_days_off: int
    fatigue: int
    m_win: float # Rolling match win %
    sv_won: float # Rolling serve won %
    ace: float
    df: float

class ManualPredictResponse(BaseModel):
    p1_prob: str = Field(..., example="65.45%")
    p2_prob: str = Field(..., example="34.55%")
    p1_stats: PlayerSnapshot
    p2_stats: PlayerSnapshot
    surface: str
