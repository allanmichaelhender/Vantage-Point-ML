from pydantic import BaseModel, Field, ConfigDict
from typing import Optional,Any

class ManualPredictRequest(BaseModel):
    p1_id: str = Field(..., example="A0E2")
    p2_id: str = Field(..., example="AG37")
    surface: str = Field(..., example="Hard")

class PlayerStateSchema(BaseModel):
    player_id: str
    player_name: str  # 🎯 Added
    current_elo: float
    current_hard_elo: Optional[float]
    current_clay_elo: Optional[float]
    current_grass_elo: Optional[float]
    last_match_date: Optional[Any]
    last_hard_match_date: Optional[Any]   # 🎯 Added
    last_clay_match_date: Optional[Any]   # 🎯 Added
    last_grass_match_date: Optional[Any]  # 🎯 Added
    rolling_match_win_pct: float
    rolling_game_win_pct: float           # 🎯 Added
    rolling_serve_won_pct: float          # 🎯 Added
    rolling_ace_per_game: float
    rolling_df_per_pt: float              # 🎯 Added
    rolling_bp_save_pct: float
    rolling_return_won_pct: float         # 🎯 Added
    current_tournament_fatigue: float

    model_config = ConfigDict(from_attributes=True)

class ManualPredictResponse(BaseModel):
    p1_prob: float  # 🎯 Switched from str to float
    p2_prob: float  # 🎯 Switched from str to float
    p1_stats: PlayerStateSchema
    p2_stats: PlayerStateSchema
