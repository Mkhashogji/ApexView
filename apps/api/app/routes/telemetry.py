from fastapi import APIRouter, Query
from typing import List
from app.models.dto import TelemetryResponse, DeltaResponse
from app.services.data_service import get_data_service

router = APIRouter()


@router.get("", response_model=list[TelemetryResponse])
async def get_telemetry(
    session: str = Query(..., description="Session ID or identifier"),
    drivers: List[str] = Query(..., description="Driver abbreviations"),
    lap_type: str = Query("fastest", description="Lap type: fastest, average, specific"),
    downsample: bool = Query(True, description="Downsample telemetry if too many points"),
):
    """
    Get telemetry data for specified drivers' laps.
    Returns speed, throttle, brake, gear, RPM, and DRS data as flat arrays.
    """
    service = get_data_service()
    telemetry = await service.get_telemetry(session, drivers, lap_type)
    return telemetry


@router.get("/delta", response_model=list[DeltaResponse])
async def get_delta_analysis(
    session: str = Query(..., description="Session ID"),
    reference_driver: str = Query(..., description="Reference driver"),
    compare_drivers: List[str] = Query(..., description="Drivers to compare"),
):
    """
    Calculate delta time between reference driver and comparison drivers.
    Returns distance-indexed delta arrays showing where time is gained/lost.
    """
    service = get_data_service()
    delta_data = await service.get_delta_analysis(session, reference_driver, compare_drivers)
    return delta_data

