from fastapi import APIRouter, Query, Security
from sqlalchemy import select
from app.database.session import async_session
from app.models.player_state import PlayerState
from sqlalchemy import desc
from app.api.deps import get_api_key
from app.schemas.player import Players
from typing import List

router = APIRouter(dependencies=[Security(get_api_key)])

# Endpoint to give the frontend a list of players
@router.get("/search", response_model=List[Players])
async def search_players(q: str = Query(..., min_length=2)): # We define a query parameter "q", the ... means required
    async with async_session() as session:
        stmt = (
            select(PlayerState)
            .where(PlayerState.player_name.ilike(f"%{q}%")) #ilike is a case insensite search, f"%{q}%" means anything can be eitherside of q
            .order_by(desc(PlayerState.current_elo))
            .limit(10)
        )
        result = await session.execute(stmt)
        players = result.scalars().all()

        # FastAPI handles the conversion to json/dict from response model
        return players
