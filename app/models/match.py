from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, DateTime, ForeignKey, Integer
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
    
    winner_id: Mapped[str] = mapped_column(ForeignKey("players.id"), index=True)
    loser_id: Mapped[str] = mapped_column(ForeignKey("players.id"), index=True)
    
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

