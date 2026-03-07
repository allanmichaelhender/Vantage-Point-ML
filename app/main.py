from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.endpoints import players, manual_predict, upcoming_matches
from slowapi import _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from app.core.ratelimit import limiter

# 1. Setup the limiter (Tracks by IP address)
app = FastAPI(title="Tennis ML API")

# 2. Add to app state so endpoints can access it
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# 1. ENABLE CORS (Required for React)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Your Vite Frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 2. REGISTER ROUTERS
# This makes the endpoint: GET http://localhost:8000/api/v1/players/search
app.include_router(players.router, prefix="/api/v1/players", tags=["players"])
app.include_router(manual_predict.router, prefix="/api/v1/predict", tags=["predict"])
app.include_router(upcoming_matches.router, prefix="/api/v1/upcoming", tags=["Live Sync"])


@app.get("/")
async def root():
    return {"status": "Tennis ML API Online", "version": "v1.0"}
