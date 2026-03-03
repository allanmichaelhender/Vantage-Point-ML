from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Date
from datetime import date
from app.models.base import Base

class Player(Base):
    __tablename__ = "players"
    
    # Primary Key is the ATP ID from your CSV
    id: Mapped[str] = mapped_column(String(50),primary_key=True) 
    
    # Core Bio Data
    player: Mapped[str] = mapped_column(String(150), index=True) # Full Name
    atpname: Mapped[str | None] = mapped_column(String(100))
    birthdate: Mapped[date | None] = mapped_column(Date)
    
    # Physical Attributes (Essential for XGBoost features)
    weight: Mapped[int | None] = mapped_column(Integer) # In kg
    height: Mapped[int | None] = mapped_column(Integer) # In cm
    
    # Career Details
    turnedpro: Mapped[int | None] = mapped_column(Integer) # Year
    birthplace: Mapped[str | None] = mapped_column(String(150))
    coaches: Mapped[str | None] = mapped_column(String(255))
    
    # Technical Style
    hand: Mapped[str | None] = mapped_column(String(20)) # 'Right', 'Left'
    backhand: Mapped[str | None] = mapped_column(String(20)) # 'One-handed', 'Two-handed'
    
    # Nationality
    ioc: Mapped[str | None] = mapped_column(String(3)) # e.g., 'ESP', 'SRB'


    def __repr__(self) -> str:
        return f"<Player(name={self.player}, id={self.id})>"
