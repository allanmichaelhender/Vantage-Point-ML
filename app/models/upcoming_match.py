from sqlalchemy import String, Float, Integer, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from datetime import datetime, timezone
from app.models.base import Base


class UpcomingMatch(Base):
    __tablename__ = "upcoming_matches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    
    # 1. Identity & Schedule
    p1_id: Mapped[str] = mapped_column(String, ForeignKey("players.id"))
    p2_id: Mapped[str] = mapped_column(String, ForeignKey("players.id"))
    p1_name: Mapped[str] = mapped_column(String)
    p2_name: Mapped[str] = mapped_column(String)
    commence_time: Mapped[datetime] = mapped_column(DateTime) # Explicit date from LLM

    # 2. Context
    tournament: Mapped[str] = mapped_column(String)
    surface: Mapped[str] = mapped_column(String)

    # 3. Market Data (Specific Bookie Targets)
    pin_p1: Mapped[float | None] = mapped_column(Float)
    pin_p2: Mapped[float | None] = mapped_column(Float)
    bf_p1: Mapped[float | None] = mapped_column(Float) # Pinnacle
    bf_p2: Mapped[float | None] = mapped_column(Float)

    # 4. Model Output (The "Brain")
    predicted_p1_prob: Mapped[float] = mapped_column(Float)
    predicted_p2_prob: Mapped[float] = mapped_column(Float)
    
    # 5. Metadata
    synced_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), 
    default=lambda: datetime.now(timezone.utc)
)
