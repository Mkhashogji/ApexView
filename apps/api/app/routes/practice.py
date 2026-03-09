"""
Practice session analysis endpoints.

Provides long run pace data, short run / best lap ranking, sector
analysis, and session availability for FP1/FP2/FP3 practice sessions.
"""

from fastapi import APIRouter, Query
import logging

from app.models.dto import (
    PracticeLongRunResponse,
    PracticeProgressionEntry,
    PracticeProgressionDriver,
    PracticeProgressionResponse,
    PracticeSectorAnalysisResponse,
    PracticeSectorDriver,
    PracticeSectorSummary,
    PracticeSessionsResponse,
    PracticeShortRunDriver,
    PracticeShortRunResponse,
    PracticeSpeedTrapDriver,
)
from app.services.practice.practice_data_service import (
    get_processed_practice_data,
    compute_long_run_stats,
    compute_short_run_stats,
    compute_sector_analysis,
    compute_progression_stats,
    get_available_sessions,
)

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/sessions", response_model=PracticeSessionsResponse)
async def practice_sessions(
    year: int = Query(..., description="Season year (e.g. 2025)"),
    round_num: int = Query(..., description="Round number (e.g. 1)"),
):
    """Return available practice sessions for a race weekend."""
    try:
        return await get_available_sessions(year, round_num)
    except Exception as e:
        logger.error(f"Error getting practice sessions: {e}", exc_info=True)
        return PracticeSessionsResponse(
            year=year,
            round_num=round_num,
            sessions=['FP1', 'FP2', 'FP3'],  # Fallback
        )


@router.get("/long-runs", response_model=PracticeLongRunResponse)
async def practice_long_runs(
    session: str = Query(..., description="Session ID, e.g. 2025_1_FP2"),
    fuel_effect: float = Query(0.0, description="Fuel effect per kg in seconds (0 = no correction)"),
):
    """
    Return long run stint analysis for a practice session.

    Each stint with >= 4 valid laps is classified as a long run and
    returned with box plot statistics, degradation hint, and clean-air
    percentage. Stints are sorted by average pace (fastest first).
    """
    try:
        data = await get_processed_practice_data(session, fuel_effect)
        return compute_long_run_stats(data)
    except Exception as e:
        logger.error(f"Error computing long runs for {session}: {e}", exc_info=True)
        return PracticeLongRunResponse(
            session_id=session,
            fuel_corrected=(fuel_effect > 0),
            stints=[],
            session_best_average=None,
        )


@router.get("/short-runs", response_model=PracticeShortRunResponse)
async def practice_short_runs(
    session: str = Query(..., description="Session ID, e.g. 2025_1_FP2"),
    fuel_effect: float = Query(0.0, description="Fuel effect per kg in seconds (0 = no correction)"),
):
    """
    Return session best-lap ranking for a practice session.

    Uses official session-best lap data per driver (raw LapTime from
    FastF1/FIA timing) for accurate ranking, times, and gaps.  Falls
    back to short-run stint extraction when official data is unavailable.
    Hits the same cached practice data pipeline as the long-runs endpoint.
    """
    try:
        data = await get_processed_practice_data(session, fuel_effect)
        short_run_stints = data.get('short_run_stints', [])
        session_best_laps = data.get('session_best_laps', {})

        driver_results = compute_short_run_stats(short_run_stints, session_best_laps)

        session_best = driver_results[0]['best_lap_time'] if driver_results else None
        verification_available = any(
            r.get('session_best_time') is not None for r in driver_results
        )

        drivers = [
            PracticeShortRunDriver(**result)
            for result in driver_results
        ]

        return PracticeShortRunResponse(
            session_id=session,
            fuel_corrected=(fuel_effect > 0),
            drivers=drivers,
            session_best_lap=session_best,
            total_drivers=len(drivers),
            verification_available=verification_available,
        )
    except Exception as e:
        logger.error(f"Error computing short runs for {session}: {e}", exc_info=True)
        return PracticeShortRunResponse(
            session_id=session,
            fuel_corrected=(fuel_effect > 0),
            drivers=[],
            session_best_lap=None,
            total_drivers=0,
        )


@router.get("/sector-analysis", response_model=PracticeSectorAnalysisResponse)
async def practice_sector_analysis(
    session: str = Query(..., description="Session ID, e.g. 2025_1_FP2"),
    fuel_effect: float = Query(0.0, description="Fuel effect (for pipeline cache reuse only)"),
):
    """
    Return sector-level analysis for a practice session.

    Shows each driver's session-best lap broken into S1/S2/S3,
    best individual sector times, theoretical best laps, and
    maximum speed trap readings.  All times are raw (not fuel-corrected).
    Reuses the same cached practice data pipeline.
    """
    try:
        data = await get_processed_practice_data(session, fuel_effect)
        enriched_laps = data.get('laps', [])
        session_best_laps = data.get('session_best_laps', {})

        result = compute_sector_analysis(enriched_laps, session_best_laps)

        drivers = [
            PracticeSectorDriver(**dr) for dr in result['drivers']
        ]
        summary = PracticeSectorSummary(**result['summary'])
        speed_traps = [
            PracticeSpeedTrapDriver(**st) for st in result['speed_traps']
        ]

        return PracticeSectorAnalysisResponse(
            session_id=session,
            drivers=drivers,
            summary=summary,
            speed_traps=speed_traps,
            total_drivers=result['total_drivers'],
        )
    except Exception as e:
        logger.error(f"Error computing sector analysis for {session}: {e}", exc_info=True)
        return PracticeSectorAnalysisResponse(
            session_id=session,
            drivers=[],
            summary=PracticeSectorSummary(),
            speed_traps=[],
            total_drivers=0,
        )


@router.get("/progression", response_model=PracticeProgressionResponse)
async def get_practice_progression(
    year: int = Query(..., description="Championship year e.g. 2025"),
    round_num: int = Query(..., description="Round number e.g. 1"),
):
    """Cross-session progression: per-driver gap-to-session-best across FP1/FP2/FP3.

    Weekend-level endpoint — does not accept a session parameter.
    Always uses raw lap times (fuel_effect=0.0) for comparable gaps.
    """
    try:
        result = await compute_progression_stats(year, round_num)

        drivers = [
            PracticeProgressionDriver(
                driver=d['driver'],
                team=d['team'],
                sessions=[
                    PracticeProgressionEntry(**entry)
                    for entry in d['sessions']
                ],
            )
            for d in result['drivers']
        ]

        return PracticeProgressionResponse(
            year=result['year'],
            round_num=result['round_num'],
            available_sessions=result['available_sessions'],
            is_sprint_weekend=result['is_sprint_weekend'],
            drivers=drivers,
            total_drivers=result['total_drivers'],
        )
    except Exception as e:
        logger.error(f"Error computing progression for {year} round {round_num}: {e}", exc_info=True)
        return PracticeProgressionResponse(
            year=year,
            round_num=round_num,
            available_sessions=[],
            is_sprint_weekend=False,
            drivers=[],
            total_drivers=0,
        )
