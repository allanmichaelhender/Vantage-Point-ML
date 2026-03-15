from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

# Models
from app.models.player import Player

async def get_elite_players(session: AsyncSession):
    # Get Top 100 by Elo    
    stmt = (
        select(Player.id, Player.name, Player.elo)
        .order_by(Player.elo.desc())
        .limit(100)
    )
    result = await session.execute(stmt)
    return result.all()
