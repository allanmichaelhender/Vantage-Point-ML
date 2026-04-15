from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import lab, players, manual_predict, upcoming_matches
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from app.core.ratelimit import limiter
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import pytz

app = FastAPI(title="Tennis ML API")

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(players.router, prefix="/api/v1/players", tags=["players"])
app.include_router(manual_predict.router, prefix="/api/v1/predict", tags=["predict"])
app.include_router(
    upcoming_matches.router, prefix="/api/v1/upcoming", tags=["Live Sync"]
)
app.include_router(lab.router, prefix="/api/v1/lab", tags=["Lab"])

# Set up APScheduler
scheduler = AsyncIOScheduler(timezone=pytz.timezone("Europe/London"))


@app.on_event("startup")
async def startup_event():
    from app.api.endpoints.upcoming_matches import run_heavy_sync

    # Schedule daily sync at 00:01 AM London time
    scheduler.add_job(
        run_heavy_sync,
        trigger=CronTrigger(hour=0, minute=1),
        id="daily_sync",
        name="Daily Match Sync",
        replace_existing=True,
    )
    scheduler.start()
    print("🗓️  APScheduler started with Europe/London timezone")
    print("🗓️  Daily sync scheduled for 00:01 AM London time")


@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
    print("🗓️  APScheduler shutdown")


@app.get("/")
async def root():
    return {"status": "API Online", "version": "v1.0"}
