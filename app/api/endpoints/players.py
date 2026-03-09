from fastapi import APIRouter, Query
from sqlalchemy import select
from app.database.session import async_session
from app.models.player_state import PlayerState
from app.schemas.player import PlayerListResponse
from sqlalchemy import desc

router = APIRouter()


@router.get("/search")
async def search_players(q: str = Query(..., min_length=2)):
    """
    Fuzzy search for players by name for the React Autocomplete.
    Returns: List of players with IDs and current ranks.
    """
    async with async_session() as session:
        # 'ilike' performs a case-insensitive search in Postgres
        stmt = (
            select(PlayerState)
            .where(PlayerState.player_name.ilike(f"%{q}%"))
            .order_by(desc(PlayerState.current_elo))
            .limit(10)
        )
        result = await session.execute(stmt)
        players = result.scalars().all()

        return [{"id": p.player_id, "name": p.player_name} for p in players]
