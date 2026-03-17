from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Security, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete

from app.database.session import async_session  # 🎯 Import your session factory
from app.models.upcoming_match import UpcomingMatch
from app.models.player_state import PlayerState
from app.services.data.llm_service import llmservice
from app.services.ml.inference_service import inference_service
from app.api.deps import get_api_key, get_db

router = APIRouter()

async def run_heavy_sync():
    async with async_session() as session:
        # Get matches from Gemini + ODDS api service
        featured_matches = await llmservice.sync_upcoming_matches(session)

        unique_ids = {m["p1_id"] for m in featured_matches if m["p1_id"]} | \
                     {m["p2_id"] for m in featured_matches if m["p2_id"]}
        
        # Pull all the associated player states
        result = await session.execute(select(PlayerState).where(PlayerState.player_id.in_(list(unique_ids))))
        player_map = {p.player_id: p for p in result.scalars().all()}

        # Predict & Build DB Objects
        db_matches = []
        now = datetime.now(timezone.utc)

        # building out each featured match entry
        for m in featured_matches:
            p1_row = player_map.get(m["p1_id"])
            p2_row = player_map.get(m["p2_id"])

            raw_time = m["commence_time"].replace("Z", "+00:00")
            dt_commence = datetime.fromisoformat(raw_time)

            if p1_row and p2_row:
                # We use inference service to predict the result of each game
                prediction = await inference_service.predict( 
                    session=session,
                    p1_row=p1_row,
                    p2_row=p2_row,
                    surface=m["surface"],
                    commence_time=m["commence_time"],
                )
                
                db_matches.append(UpcomingMatch(
                    p1_id=m["p1_id"],
                    p2_id=m["p2_id"],
                    p1_name=m["p1_name"],
                    p2_name=m["p2_name"],
                    commence_time=dt_commence,
                    tournament=m["tournament"],
                    surface=m["surface"],
                    pin_p1=m.get("pin_p1"),
                    pin_p2=m.get("pin_p2"),
                    p1_prob=prediction["p1_prob"],
                    p2_prob=prediction["p2_prob"],
                    synced_at=now
                ))

        if db_matches:
            # Deleting all existing match objects in the db
            await session.execute(delete(UpcomingMatch))

            # We use add all to easily insert a listr of Upcoming match objects
            session.add_all(db_matches)
            await session.commit()


# Returns the upcoming games for display on the dashboard
@router.get("/sync", dependencies=[Security(get_api_key)])
async def get_live_dashboard(background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_db)): # BackgroundTasks allows fire and forget functionality of a function
    
    #Fetch current cached matches
    stmt = select(UpcomingMatch).order_by(UpcomingMatch.commence_time.asc())
    result = await session.execute(stmt)
    cached_matches = result.scalars().all()

    now = datetime.now(timezone.utc)
    needs_sync = True # Default setting incase cache is empty

    if cached_matches:
        # Check if the last sync was within 12 hours
        last_sync = cached_matches[0].synced_at
        if now - last_sync < timedelta(hours=12):
            needs_sync = False

    # If stale or older than 12 hours since last sync, trigger the background task
    if needs_sync:
        background_tasks.add_task(run_heavy_sync)

    # we return the cached matches, status and last sync time, the frontend hits the endpoint every few seconds until it gets fresh as the status and the corresponding new set of games
    return {
        "matches": cached_matches, 
        "status": "fresh" if not needs_sync else "revalidating",
        "last_sync": cached_matches[0].synced_at if cached_matches else None
    }
