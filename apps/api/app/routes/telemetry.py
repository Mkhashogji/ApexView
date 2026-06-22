from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional
from app.models.dto import TelemetryResponse, DeltaResponse, TelemetryMetaResponse
from app.services.data_service import get_data_service
from app.services.telemetry.native_acquisition import NativeAcquisitionError

router = APIRouter()

# G0: per-request acquisition override ("native" | "legacy"). None -> the
# service default (settings.ACQUISITION_MODE). Used by the A/B harness; the
# frontend never sends it. The legacy value is scheduled for removal at a
# later cleanup gate.
_ACQUISITION_PATTERN = "^(native|legacy)$"


@router.get("", response_model=list[TelemetryResponse])
async def get_telemetry(
    session: str = Query(..., description="Session ID or identifier"),
    drivers: List[str] = Query(..., description="Driver abbreviations"),
    lap_type: str = Query("fastest", description="Lap type: fastest, average, specific"),
    downsample: bool = Query(True, description="Downsample telemetry if too many points"),
    session_part: Optional[str] = Query(None, description="Qualifying session part: Q1, Q2, or Q3"),
    acquisition: Optional[str] = Query(
        None, pattern=_ACQUISITION_PATTERN,
        description="G0 acquisition override: native (dual-stream, real samples only) "
                    "or legacy (pre-G0 merged frame; A/B harness only)"),
):
    """
    Get telemetry data for specified drivers' laps.
    Returns speed, throttle, brake, gear, RPM, and DRS data as flat arrays.

    Optionally filter by qualifying session part (Q1, Q2, Q3).
    """
    service = get_data_service()
    try:
        telemetry = await service.get_telemetry(
            session, drivers, lap_type, session_part, acquisition=acquisition)
    except NativeAcquisitionError as e:
        # G0 ground rule: surface a structured error — never silently fall
        # back to the merged get_telemetry() path.
        raise HTTPException(status_code=502, detail=e.to_detail())
    return telemetry


@router.get("/delta", response_model=list[DeltaResponse])
async def get_delta_analysis(
    session: str = Query(..., description="Session ID"),
    reference_driver: str = Query(..., description="Reference driver"),
    compare_drivers: List[str] = Query(..., description="Drivers to compare"),
    session_part: Optional[str] = Query(None, description="Qualifying session part: Q1, Q2, or Q3"),
    acquisition: Optional[str] = Query(
        None, pattern=_ACQUISITION_PATTERN,
        description="G0 acquisition override (see /telemetry)"),
):
    """
    Calculate delta time between reference driver and comparison drivers.
    Returns distance-indexed delta arrays showing where time is gained/lost.

    Optionally filter by qualifying session part (Q1, Q2, Q3).
    """
    service = get_data_service()
    try:
        delta_data = await service.get_delta_analysis(
            session, reference_driver, compare_drivers, session_part,
            acquisition=acquisition)
    except NativeAcquisitionError as e:
        raise HTTPException(status_code=502, detail=e.to_detail())
    return delta_data


@router.get("/meta", response_model=list[TelemetryMetaResponse])
async def get_telemetry_meta(
    session: str = Query(..., description="Session ID or identifier"),
    drivers: List[str] = Query(..., description="Driver abbreviations"),
    session_part: Optional[str] = Query(None, description="Qualifying session part: Q1, Q2, or Q3"),
):
    """
    G0 — native acquisition metadata for each driver's fastest lap: gap
    inventory (intervals where car-sample dt exceeds 3x the lap median,
    strictly) and per-stream statistics (sample counts, median dt, schema
    version, library versions).

    New, additive endpoint: the existing /telemetry response schema is frozen
    against the golden contract, so gap/meta data lives here instead of new
    fields there. Consumed by the analysis-service orchestrator (corner
    gap_flag derivation) and the A/B harness — not by the frontend.
    """
    # G0 continuation review (L3-1/L4-5): when the service is env-configured
    # legacy, native acquisition must not run server-side at all — a legacy
    # rollback must fully isolate pre-G0 behaviour. Without this guard, an
    # orchestrator meta fetch would mix native-frame gap bounds with
    # merged-frame corner zones. The orchestrator degrades gracefully on 501.
    from app.core.config import settings
    if settings.ACQUISITION_MODE == "legacy":
        raise HTTPException(
            status_code=501,
            detail={"error": "native_meta_unavailable",
                    "reason": "service is running in legacy acquisition mode"})
    service = get_data_service()
    if not hasattr(service, "get_telemetry_meta"):
        # Mock data service has no native bundles.
        raise HTTPException(
            status_code=501,
            detail={"error": "native_meta_unavailable",
                    "reason": "data service does not support native acquisition (mock mode)"})
    try:
        return await service.get_telemetry_meta(session, drivers, session_part)
    except NativeAcquisitionError as e:
        raise HTTPException(status_code=502, detail=e.to_detail())
