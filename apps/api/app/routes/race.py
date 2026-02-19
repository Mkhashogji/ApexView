"""Race analysis endpoints."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import logging
from app.models.dto import (
    RacePaceResponse,
    TyreDegradationResponse,
    PitStopAnalysisResponse,
    TeamPerformanceResponse,
)
from app.services.race.race_data_service import (
    get_processed_race_data,
    compute_race_pace_stats,
)
from app.services.race.tyre_degradation import compute_tyre_degradation
from app.services.race.pit_stop_analysis import analyse_pit_stops
from app.services.race.team_performance import compute_team_performance

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/pace", response_model=RacePaceResponse)
async def get_race_pace(
    session: str = Query(..., description="Session ID, e.g. 2025_17_Race"),
    fuel_effect: float = Query(0.032, description="Fuel effect per kg in seconds"),
):
    """
    Get pre-computed race pace statistics for box plot visualization.
    Returns per-driver: min, Q1, median, mean, Q3, max, outliers, gap,
    strategy, consistency, traffic count.
    """
    race_data = await get_processed_race_data(session, fuel_effect)
    return compute_race_pace_stats(race_data)


@router.get("/tyre-degradation", response_model=TyreDegradationResponse)
async def get_tyre_degradation(
    session: str = Query(..., description="Session ID, e.g. 2025_17_Race"),
    fuel_effect: float = Query(0.032, description="Fuel effect per kg in seconds"),
    mode: str = Query("driver", description="Analysis mode: 'driver' or 'team'"),
):
    """
    Phase 3: Tyre degradation analysis with fuel-adjusted scatter data
    and linear regression per driver/team per compound.
    """
    if mode not in ('driver', 'team'):
        raise HTTPException(status_code=400, detail="mode must be 'driver' or 'team'")

    return await compute_tyre_degradation(session, fuel_effect, mode)


@router.get("/pit-stops", response_model=PitStopAnalysisResponse)
async def get_pit_stops(
    session: str = Query(..., description="Session ID, e.g. 2025_17_Race"),
):
    """
    Phase 4: Pit stop analysis with team/driver aggregates, gap to fastest,
    tiered consistency metrics, and template-based insight data.
    """
    try:
        race_data = await get_processed_race_data(session)
        pit_stops = race_data.get('pit_stops', [])
        return analyse_pit_stops(pit_stops)
    except Exception as e:
        logger.error(f"Pit stop analysis failed for {session}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/team-performance", response_model=TeamPerformanceResponse)
async def get_team_performance(
    session: str = Query(..., description="Session ID, e.g. 2025_17_Race"),
    fuel_effect: float = Query(0.032, description="Fuel effect per kg in seconds"),
):
    """
    Phase 5: Team performance quadrant — per-team top speed and mean speed
    with field-average deltas and deterministic insight data.
    """
    try:
        race_data = await get_processed_race_data(session, fuel_effect)

        # Resolve circuit length server-side from static track JSON
        parts = session.split('_')
        season = int(parts[0])
        round_num = int(parts[1])

        from app.services.data_service import get_data_service
        track_info = await get_data_service().get_track_info(season, round_num)
        circuit_length_m = track_info.length

        return compute_team_performance(race_data['laps'], circuit_length_m, session)
    except Exception as e:
        logger.error(f"Team performance analysis failed for {session}: {e}")
        raise HTTPException(status_code=500, detail=str(e))
