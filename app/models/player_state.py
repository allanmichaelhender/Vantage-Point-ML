from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Date, Float, ForeignKey, Integer
from sqlalchemy.dialects.postgresql import JSONB
from datetime import date
from app.models.base import Base


class PlayerState(Base):
    __tablename__ = "player_states"

    player_id: Mapped[str] = mapped_column(ForeignKey("players.id"), primary_key=True)
    player_name: Mapped[str] = mapped_column(String(150), index=True)

    current_elo: Mapped[float | None] = mapped_column(Float, default=1500.0)
    current_hard_elo: Mapped[float | None] = mapped_column(Float)
    current_clay_elo: Mapped[float | None] = mapped_column(Float)
    current_grass_elo: Mapped[float | None] = mapped_column(Float)

    last_match_date: Mapped[date | None] = mapped_column(Date)
    last_hard_match_date: Mapped[date | None] = mapped_column(Date)
    last_clay_match_date: Mapped[date | None] = mapped_column(Date)
    last_grass_match_date: Mapped[date | None] = mapped_column(Date)

    rolling_match_win_pct: Mapped[float | None] = mapped_column(Float)
    rolling_game_win_pct: Mapped[float | None] = mapped_column(Float)
    rolling_serve_won_pct: Mapped[float | None] = mapped_column(Float)
    rolling_ace_per_game: Mapped[float | None] = mapped_column(Float)
    rolling_df_per_pt: Mapped[float | None] = mapped_column(Float)
    rolling_bp_save_pct: Mapped[float | None] = mapped_column(Float)
    rolling_return_won_pct: Mapped[float | None] = mapped_column(Float)
    
    current_tournament_fatigue: Mapped[float | None] = mapped_column(Float, server_default="0.0", default=0.0)

    matches_played: Mapped[int | None] = mapped_column(Integer)