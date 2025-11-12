from fastapi import APIRouter, Query
from typing import List
from app.models.dto import LapResponse, SectorTime
from app.services.data_service import get_data_service

router = APIRouter()


@router.get("", response_model=list[LapResponse])
async def get_laps(
    session: str = Query(..., description="Session ID or identifier"),
    drivers: List[str] = Query(..., description="Driver abbreviations (e.g., VER, HAM)"),
):
    """
    Get lap data for specified drivers in a session.
    """
    service = get_data_service()
    laps = await service.get_laps(session, drivers)
    return laps


@router.get("/fastest")
async def get_fastest_laps(
    session: str = Query(..., description="Session ID or identifier"),
):
    """
    Get fastest laps for all drivers in a session.
    """
    service = get_data_service()
    fastest_laps = await service.get_fastest_laps(session)
    return fastest_laps


@router.get("/sectors", response_model=list[SectorTime])
async def get_sectors(
    session: str = Query(..., description="Session ID or identifier"),
    drivers: List[str] = Query(..., description="Driver abbreviations"),
):
    """
    Get sector times for specified drivers in a session.
    Returns sector 1, 2, 3 times and total lap time.
    """
    service = get_data_service()
    sectors = await service.get_sectors(session, drivers)
    return sectors

