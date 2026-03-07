from fastapi import APIRouter, Depends, Security
from sqlalchemy.ext.asyncio import AsyncSession
from app.api.deps import get_db, get_api_key
from app.services.llm_service import LLMService
from app.services.inference_service import inference_service
from app.core.ratelimit import limiter
from app.schemas.upcoming import SyncMatchesResponse
from app.models.player_state import PlayerState
from sqlalchemy import select


router = APIRouter()
llm_service = LLMService()


@router.post("/sync", dependencies=[Security(get_api_key)], response_model=SyncMatchesResponse)
# @limiter.limit("1/minute")
async def sync_live_matches(session: AsyncSession = Depends(get_db)):
    featured_matches = await llm_service.sync_upcoming_matches(session)

    unique_ids = set()
    for match in featured_matches:
        if match["p1_id"]:
            unique_ids.add(match["p1_id"])
        if match["p2_id"]:
            unique_ids.add(match["p2_id"])

    # 2. THE BIG PLUCK: One query for all 40 players
    stmt = select(PlayerState).where(PlayerState.player_id.in_(list(unique_ids)))
    result = await session.execute(stmt)

    # 3. THE MAP: Instant lookup dictionary
    # We map the ID string to the actual DB Row Object
    player_map = {p.player_id: p for p in result.scalars().all()}

    for match in featured_matches:
        # Grab the pre-loaded DB rows
        p1_row = player_map.get(match["p1_id"])
        p2_row = player_map.get(match["p2_id"])

        if p1_row and p2_row:
            # Pass the ROWS directly to the service
            prediction = await inference_service.predict(
                session=session,
                p1_row=p1_row,
                p2_row=p2_row,
                surface=match["surface"],
                commence_time=match["commence_time"],
            )
            match["p1_prob"] = prediction["p1_prob"]
            match["p2_prob"] = prediction["p2_prob"]

    return {"matches": featured_matches}

