from fastapi import APIRouter, Query
from sqlalchemy import select
from app.database.session import async_session
from app.models.player import Player
from app.schemas.player import PlayerListResponse


router = APIRouter()

@router.get("/search", response_model=PlayerListResponse)
async def search_players(q: str = Query(..., min_length=2)):
    """
    Fuzzy search for players by name for the React Autocomplete.
    Returns: List of players with IDs and current ranks.
    """
    async with async_session() as session:
        # 'ilike' performs a case-insensitive search in Postgres
        stmt = select(Player).where(Player.name.ilike(f"%{q}%")).limit(10)
        result = await session.execute(stmt)
        players = result.scalars().all()
        
        return [
            {"id": p.id, "name": p.name, "rank": p.rank, "country": p.country} 
            for p in players
        ]
