from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routes import sessions, laps, telemetry, track, analysis, race, practice
from app.core.config import settings

app = FastAPI(
    title="F1 Engineering API",
    description="FastAPI backend for F1 telemetry and race analysis",
    version="0.1.0",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(sessions.router, prefix="/sessions", tags=["sessions"])
app.include_router(laps.router, prefix="/laps", tags=["laps"])
app.include_router(telemetry.router, prefix="/telemetry", tags=["telemetry"])
app.include_router(track.router, prefix="/track", tags=["track"])
app.include_router(analysis.router, prefix="/analysis", tags=["analysis"])
app.include_router(race.router, prefix="/race", tags=["race"])
app.include_router(practice.router, prefix="/practice", tags=["practice"])


@app.get("/")
async def root():
    return {
        "message": "F1 Engineering API",
        "version": "0.1.0",
        "docs": "/docs",
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)

