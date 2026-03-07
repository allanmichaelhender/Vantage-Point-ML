from pydantic import BaseModel
from typing import List, Optional

class MatchPrediction(BaseModel):
    p1_name: str
    p1_id: Optional[str]
    p2_name: str
    p2_id: Optional[str]
    pin_p1: Optional[float]
    pin_p2: Optional[float]
    bf_p1: Optional[float]
    bf_p2: Optional[float]
    tournament: str
    commence_time: str
    surface: str
    p1_prob: float
    p2_prob: float

class SyncMatchesResponse(BaseModel):
    matches: List[MatchPrediction]