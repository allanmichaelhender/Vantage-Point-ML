from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, ForeignKey, Integer, Boolean, Float
from sqlalchemy.dialects.postgresql import JSONB
from datetime import datetime
from app.models.base import Base


class Match(Base):
    __tablename__ = "matches"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    tourney_id: Mapped[str] = mapped_column(String(50), index=True)
    tourney_name: Mapped[str] = mapped_column(String(100))
    surface: Mapped[str] = mapped_column(String(20))
    tourney_level: Mapped[str] = mapped_column(String(10))
    tourney_date: Mapped[datetime] = mapped_column(DateTime)
    match_num: Mapped[int | None] = mapped_column(Integer)

    winner_id: Mapped[str] = mapped_column(ForeignKey("players.id"), index=True)
    loser_id: Mapped[str] = mapped_column(ForeignKey("players.id"), index=True)
    winner_name: Mapped[str | None] = mapped_column(String)
    loser_name: Mapped[str | None] = mapped_column(String)

    score: Mapped[str] = mapped_column(String(100))
    best_of: Mapped[int] = mapped_column(Integer)
    round: Mapped[str] = mapped_column(String(10))
    minutes: Mapped[int | None] = mapped_column(Integer)

    # Winner Stats
    w_ace: Mapped[int | None] = mapped_column(Integer)
    w_df: Mapped[int | None] = mapped_column(Integer)
    w_svpt: Mapped[int | None] = mapped_column(Integer)
    w_1stIn: Mapped[int | None] = mapped_column(Integer)
    w_1stWon: Mapped[int | None] = mapped_column(Integer)
    w_2ndWon: Mapped[int | None] = mapped_column(Integer)
    w_SvGms: Mapped[int | None] = mapped_column(Integer)
    w_bpSaved: Mapped[int | None] = mapped_column(Integer)
    w_bpFaced: Mapped[int | None] = mapped_column(Integer)
    winner_rank: Mapped[int | None] = mapped_column(Integer)
    winner_ranking_points: Mapped[int | None] = mapped_column(Integer)

    # Loser Stats
    l_ace: Mapped[int | None] = mapped_column(Integer)
    l_df: Mapped[int | None] = mapped_column(Integer)
    l_svpt: Mapped[int | None] = mapped_column(Integer)
    l_1stIn: Mapped[int | None] = mapped_column(Integer)
    l_1stWon: Mapped[int | None] = mapped_column(Integer)
    l_2ndWon: Mapped[int | None] = mapped_column(Integer)
    l_SvGms: Mapped[int | None] = mapped_column(Integer)
    l_bpSaved: Mapped[int | None] = mapped_column(Integer)
    l_bpFaced: Mapped[int | None] = mapped_column(Integer)
    loser_rank: Mapped[int | None] = mapped_column(Integer)
    loser_ranking_points: Mapped[int | None] = mapped_column(Integer)

    # New Score-Derived Metrics
    is_retirement: Mapped[bool] = mapped_column(Boolean, default=False)
    total_games: Mapped[int | None] = mapped_column(Integer)
    games_diff: Mapped[int | None] = mapped_column(Integer)
    game_win_percentage: Mapped[float | None] = mapped_column(Float)
    tiebreaks_played: Mapped[int | None] = mapped_column(Integer)
    tiebreaks_won: Mapped[int | None] = mapped_column(Integer)

    # Snapshots: State of the player BEFORE this match started
    w_elo_before: Mapped[float | None] = mapped_column(Float)
    l_elo_before: Mapped[float | None] = mapped_column(Float)

    w_surface_elo_before: Mapped[float | None] = mapped_column(Float)
    l_surface_elo_before: Mapped[float | None] = mapped_column(Float)

    w_days_off: Mapped[int | None] = mapped_column(Integer)
    l_days_off: Mapped[int | None] = mapped_column(Integer)

    # Surface-specific timing (Days since last match on THIS surface)
    w_surface_days_off: Mapped[int | None] = mapped_column(Integer)
    l_surface_days_off: Mapped[int | None] = mapped_column(Integer)

    w_rolling_match_win_pct: Mapped[float | None] = mapped_column(Float)
    l_rolling_match_win_pct: Mapped[float | None] = mapped_column(Float)

    w_rolling_game_win_pct: Mapped[float | None] = mapped_column(Float)
    l_rolling_game_win_pct: Mapped[float | None] = mapped_column(Float)

    # Efficiency Snapshots (State BEFORE this match)
    w_rolling_serve_won_pct: Mapped[float | None] = mapped_column(Float)
    w_rolling_ace_per_game: Mapped[float | None] = mapped_column(Float)
    w_rolling_df_per_pt: Mapped[float | None] = mapped_column(Float)
    w_rolling_bp_save_pct: Mapped[float | None] = mapped_column(Float)
    w_rolling_return_won_pct: Mapped[float | None] = mapped_column(Float)

    # Check your Match class for these specific missing columns:
    l_rolling_serve_won_pct: Mapped[float | None] = mapped_column(Float)
    l_rolling_ace_per_game: Mapped[float | None] = mapped_column(Float)
    l_rolling_df_per_pt: Mapped[float | None] = mapped_column(Float)
    l_rolling_bp_save_pct: Mapped[float | None] = mapped_column(Float)
    l_rolling_return_won_pct: Mapped[float | None] = mapped_column(Float)

    # Tournament Fatigue (Minutes in last 14 days)
    w_tournament_fatigue: Mapped[int | None] = mapped_column(Integer)
    l_tournament_fatigue: Mapped[int | None] = mapped_column(Integer)

    # Matches Played (not including current game)
    w_matches_played: Mapped[int | None] = mapped_column(Integer)
    l_matches_played: Mapped[int | None] = mapped_column(Integer)

    # Betting Odds (Closing Market)
    b365_w: Mapped[float | None] = mapped_column(Float)
    b365_l: Mapped[float | None] = mapped_column(Float)
    ps_w: Mapped[float | None] = mapped_column(Float)
    ps_l: Mapped[float | None] = mapped_column(Float)

    w_embedding: Mapped[list[float] | None] = mapped_column(JSONB)
    l_embedding: Mapped[list[float] | None] = mapped_column(JSONB)
