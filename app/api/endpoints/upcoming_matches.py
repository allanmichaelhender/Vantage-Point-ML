from fastapi import APIRouter, Security, Request
from app.api.deps import get_api_key
from app.services.llm_service import GeminiService
from app.core.ratelimit import limiter
from app.schemas.upcoming import SyncResponse

router = APIRouter()
llm_service = GeminiService()


@router.post("/sync", dependencies=[Security(get_api_key)])
# @limiter.limit("1/minute")
async def sync_upcoming(request: Request, response_model=SyncResponse):
    """
    Triggers Gemini to search the web and return the top 20 matches.
    (We aren't saving to DB yet, just testing the 'Ping')
    """
    try:
        data = await llm_service.sync_upcoming_matches()
        return data
    except Exception as e:
        return {"error": str(e)}
