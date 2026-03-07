from fastapi import APIRouter, HTTPException, Security
from datetime import datetime, timedelta
from app.api.deps import get_api_key
from app.database.session import async_session
from app.schemas.predict import ManualPredictRequest, ManualPredictResponse
from app.services.inference_service import inference_service
from sqlalchemy import select
from app.models.player_state import PlayerState

router = APIRouter()


@router.post(
    "/manual-predict",
    dependencies=[Security(get_api_key)],
    response_model=ManualPredictResponse,
)
async def manual_predict(data: ManualPredictRequest):
    async with async_session() as session:
        # 1. Fetch exactly the two players requested
        stmt = select(PlayerState).where(
            PlayerState.player_id.in_([data.p1_id, data.p2_id])
        )
        result = await session.execute(stmt)

        # 2. Map them into a small local dict for easy access
        player_rows = {p.player_id: p for p in result.scalars().all()}

        p1_row = player_rows.get(data.p1_id)
        p2_row = player_rows.get(data.p2_id)

        if not p1_row or not p2_row:
            raise HTTPException(status_code=404, detail="Player data missing from DB")

        # 3. Parse these two ROWS into your inference logic
        # We use datetime.now() because it's a "Manual" check for right now
        prediction = await inference_service.predict(
            session=session,
            p1_row=p1_row,
            p2_row=p2_row,
            surface=data.surface,
            commence_time=datetime.now().isoformat(),
        )

        return {
            "p1_prob": prediction["p1_prob"],
            "p2_prob": prediction["p2_prob"],
            "p1_stats": p1_row,
            "p2_stats": p2_row,
        }
