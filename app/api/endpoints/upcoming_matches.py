# app/api/endpoints/matches.py
from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Depends, Security, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, desc

from app.database.session import async_session  # 🎯 Import your session factory
from app.models.upcoming_match import UpcomingMatch
from app.models.player_state import PlayerState
from app.services.data import llm_service
from app.services.ml.inference_service import inference_service
from app.api.deps import get_api_key, get_db
from app.schemas.upcoming import SyncMatchesResponse

router = APIRouter()

async def run_heavy_sync():
    """
    The 'Heavy Lifter' that actually spends Gemini tokens and runs XGBoost.
    Runs in the background so the user doesn't have to wait.
    """
    async with async_session() as session:
        print("💎 Starting Heavy Sync: Calling Gemini & Model Inference...")
        
        # 1. Get matches from Gemini
        featured_matches = await llm_service.sync_upcoming_matches(session)

        # 2. Map Players (The 'Big Pluck')
        unique_ids = {m["p1_id"] for m in featured_matches if m["p1_id"]} | \
                     {m["p2_id"] for m in featured_matches if m["p2_id"]}
        
        result = await session.execute(select(PlayerState).where(PlayerState.player_id.in_(list(unique_ids))))
        player_map = {p.player_id: p for p in result.scalars().all()}

        # 3. Predict & Build DB Objects
        db_matches = []
        now = datetime.now(timezone.utc)

        for m in featured_matches:
            p1_row = player_map.get(m["p1_id"])
            p2_row = player_map.get(m["p2_id"])

            if p1_row and p2_row:
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
                    commence_time=m["commence_time"],
                    tournament=m["tournament"],
                    surface=m["surface"],
                    pin_p1=m.get("pin_p1"),
                    pin_p2=m.get("pin_p2"),
                    predicted_p1_prob=prediction["p1_prob"],
                    predicted_p2_prob=prediction["p2_prob"],
                    synced_at=now
                ))

        if db_matches:
            # 4. Atomic Swap: Clear old and insert new
            await session.execute(delete(UpcomingMatch))
            session.add_all(db_matches)
            await session.commit()
            print(f"✅ Heavy Sync Complete: {len(db_matches)} matches cached.")

@router.get("/sync", dependencies=[Security(get_api_key)])
async def get_live_dashboard(background_tasks: BackgroundTasks, session: AsyncSession = Depends(get_db)):
    """
    The 'Smart' Endpoint. 
    Returns cached data instantly. Triggers sync if data is > 12 hours old.
    """
    # 1. Fetch current cache
    stmt = select(UpcomingMatch).order_by(UpcomingMatch.synced_at.desc())
    result = await session.execute(stmt)
    cached_matches = result.scalars().all()

    now = datetime.now(timezone.utc)
    needs_sync = True

    if cached_matches:
        # Check if the last sync was within 12 hours
        last_sync = cached_matches[0].synced_at
        if now - last_sync < timedelta(hours=12):
            needs_sync = False

    # 2. If stale or empty, trigger the background task
    if needs_sync:
        print("🕒 Cache stale/empty. Dispatching background sync...")
        background_tasks.add_task(run_heavy_sync)

    return {
        "matches": cached_matches, 
        "status": "fresh" if not needs_sync else "revalidating",
        "last_sync": cached_matches[0].synced_at if cached_matches else None
    }
