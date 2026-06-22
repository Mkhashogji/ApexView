"""
Performance Insights Orchestrator Module (Phase 6)

Chains Phases 2-5 into a unified API endpoint that:
1. Fetches telemetry data from the API service
2. Runs scaled delta analysis (Phase 2)
3. Runs corner analysis (Phase 3)
4. Runs technique profiling (Phase 4)
5. Generates natural language insights (Phase 5)

This is the Backend-for-Frontend (BFF) pattern that reduces frontend
complexity from 4 API calls down to 1.

Usage:
    from services.performance_orchestrator import (
        orchestrate_performance_insights,
        PerformanceInsightsConfig
    )

    config = PerformanceInsightsConfig(
        session_id="2025_24_Qualifying",
        reference_driver="NOR",
        compare_drivers=["PIA", "VER"],
        corners=corners_list,
        mode="engineer"
    )

    result = await orchestrate_performance_insights(config, http_client)

Author: ApexView Engineering
Phase: 6 of 8 (Telemetry Analysis Pipeline)
"""

import logging
import time
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Tuple

import numpy as np
import httpx

from services.delta_analysis import calculate_scaled_delta, DeltaResult
from services.corner_analysis import (
    analyze_corners,
    analyze_corners_v2,
    CornerInput,
    CornerAnalysisResult,
    LapBreakdown,
    StraightSegment,
)
from services.technique_profiling import (
    profile_drivers,
    TechniqueProfile,
    SessionPercentiles,
)
from services.insight_generation import (
    generate_insights,
    InsightMode,
    NaturalLanguageInsight,
)

logger = logging.getLogger("analysis_service.performance_orchestrator")


# =============================================================================
# Constants
# =============================================================================

API_SERVICE_URL = "http://api:8000"
TELEMETRY_TIMEOUT_SECONDS = 30.0
DEFAULT_NUM_POINTS = 1000


# =============================================================================
# Data Classes
# =============================================================================

@dataclass
class PerformanceInsightsConfig:
    """
    Configuration for performance insights orchestration.

    Attributes:
        session_id: Session identifier (e.g., "2025_24_Qualifying")
        reference_driver: Reference driver code (e.g., "NOR")
        compare_drivers: List of driver codes to compare
        corners: List of CornerInput definitions
        mode: Insight mode ("engineer" or "driver")
        session_part: Qualifying session part filter (Q1, Q2, Q3)
        circuit_name: Circuit name for context
        include_telemetry: Whether to include delta arrays in response
        track_length: Track length in meters (for lap breakdown calculation)
        acquisition_mode: G0 — optional API acquisition override forwarded to
            the /telemetry fetch ("native" | "legacy"). None uses the API
            service's configured default. Set only by the A/B harness.
    """
    session_id: str
    reference_driver: str
    compare_drivers: List[str]
    corners: List[CornerInput]
    mode: str = "engineer"
    session_part: Optional[str] = None
    circuit_name: Optional[str] = None
    include_telemetry: bool = True
    track_length: Optional[float] = None
    acquisition_mode: Optional[str] = None


@dataclass
class PhaseTimingInfo:
    """Timing information for a single phase execution."""
    phase: str
    duration_ms: int
    success: bool
    error: Optional[str] = None


@dataclass
class DriverPerformanceResult:
    """
    Complete performance analysis for a single driver comparison.

    Aggregates results from all phases.
    """
    driver: str

    # Phase 2: Scaled Delta
    official_gap: float
    scaling_confidence: float
    delta: Optional[List[float]] = None
    distance: Optional[List[float]] = None
    telemetry_gap: Optional[float] = None
    scaling_factor: Optional[float] = None
    raw_delta: Optional[List[float]] = None

    # Phase 3: Corner Analysis
    corners_gaining: int = 0
    corners_losing: int = 0
    total_corner_delta: float = 0.0
    corner_results: List[Dict[str, Any]] = field(default_factory=list)
    # 5th Dimension: Lap Breakdown
    lap_breakdown: Optional[Dict[str, Any]] = None

    # Phase 4: Technique Profile
    technique_profile: Optional[Dict[str, Any]] = None

    # Phase 5: Natural Language Insight
    insight: Optional[Dict[str, Any]] = None


@dataclass
class PerformanceInsightsResult:
    """
    Complete result from performance insights orchestration.
    """
    session_id: str
    reference_driver: str
    circuit_name: Optional[str]
    mode: str

    # Driver results
    results: List[DriverPerformanceResult]

    # Session context
    session_percentiles: Optional[Dict[str, Any]] = None

    # Metrics
    total_drivers_requested: int = 0
    total_drivers_processed: int = 0
    total_corners: int = 0

    # Timing
    phase_timing: List[PhaseTimingInfo] = field(default_factory=list)
    total_duration_ms: int = 0

    # Errors/warnings
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


# =============================================================================
# Utility Functions
# =============================================================================

def _safe_array(arr, default_value: float = 0.0) -> np.ndarray:
    """
    Safely convert input to numpy array, handling None/empty/NaN cases.

    This utility is defined in CLAUDE.md as a standard for all new modules.
    """
    if arr is None or (hasattr(arr, '__len__') and len(arr) == 0):
        logger.warning(f"Empty/None array received, using default [{default_value}]")
        return np.array([default_value])

    result = np.array(arr, dtype=float)

    if np.any(np.isnan(result)):
        nan_count = np.sum(np.isnan(result))
        logger.warning(f"Array contains {nan_count} NaN values, interpolating")
        mask = np.isnan(result)
        if np.any(~mask):
            result[mask] = np.interp(
                np.flatnonzero(mask),
                np.flatnonzero(~mask),
                result[~mask]
            )
        else:
            result = np.full_like(result, default_value)

    return result


def _technique_profile_to_dict(profile: TechniqueProfile) -> Dict[str, Any]:
    """Convert TechniqueProfile dataclass to serializable dict."""
    result = {
        "driver": profile.driver,
        "reference_driver": profile.reference_driver,
        "braking": {
            "level": profile.braking.level.value,
            "descriptor": profile.braking.descriptor,
            "percentile": profile.braking.percentile,
            "raw_value": profile.braking.raw_value,
            "corner_count": profile.braking.corner_count,
            "avg_confidence": profile.braking.avg_confidence,
        },
        "apex": {
            "level": profile.apex.level.value,
            "descriptor": profile.apex.descriptor,
            "percentile": profile.apex.percentile,
            "raw_value": profile.apex.raw_value,
            "corner_count": profile.apex.corner_count,
            "avg_confidence": profile.apex.avg_confidence,
        },
        "exit": {
            "level": profile.exit.level.value,
            "descriptor": profile.exit.descriptor,
            "percentile": profile.exit.percentile,
            "raw_value": profile.exit.raw_value,
            "corner_count": profile.exit.corner_count,
            "avg_confidence": profile.exit.avg_confidence,
        },
        "consistency": {
            "level": profile.consistency.level.value,
            "descriptor": profile.consistency.descriptor,
            "percentile": profile.consistency.percentile,
            "raw_value": profile.consistency.raw_value,
            "corner_count": profile.consistency.corner_count,
            "avg_confidence": profile.consistency.avg_confidence,
        },
        "top_gaining_corners": profile.top_gaining_corners,
        "top_losing_corners": profile.top_losing_corners,
        "style_summary": profile.style_summary,
        "overall_confidence": profile.overall_confidence,
        "total_corners_analyzed": profile.total_corners_analyzed,
    }

    # NEW: Include 5th dimension (straight-line) if present
    if profile.straight_line is not None:
        result["straight_line"] = {
            "level": profile.straight_line.level.value,
            "descriptor": profile.straight_line.descriptor,
            "percentile": profile.straight_line.percentile,
            "raw_delta": profile.straight_line.raw_delta,
            "primary_factor": profile.straight_line.primary_factor,
            "segment_count": profile.straight_line.segment_count,
            "top_gaining_straights": profile.straight_line.top_gaining_straights,
            "top_losing_straights": profile.straight_line.top_losing_straights,
            "avg_confidence": profile.straight_line.avg_confidence,
        }

    return result


def _session_percentiles_to_dict(percentiles: SessionPercentiles) -> Dict[str, Any]:
    """Convert SessionPercentiles dataclass to serializable dict."""
    result = {
        "braking_p30": percentiles.braking_p30,
        "braking_p70": percentiles.braking_p70,
        "apex_p30": percentiles.apex_p30,
        "apex_p70": percentiles.apex_p70,
        "exit_p30": percentiles.exit_p30,
        "exit_p70": percentiles.exit_p70,
        "consistency_p30": percentiles.consistency_p30,
        "consistency_p70": percentiles.consistency_p70,
        "driver_count": percentiles.driver_count,
    }

    # NEW: Include straight-line percentiles for 5th dimension
    if hasattr(percentiles, 'straight_line_p30'):
        result["straight_line_p30"] = percentiles.straight_line_p30
        result["straight_line_p70"] = percentiles.straight_line_p70

    return result


def _insight_to_dict(insight: NaturalLanguageInsight) -> Dict[str, Any]:
    """Convert NaturalLanguageInsight dataclass to serializable dict."""
    return {
        "driver": insight.driver,
        "reference_driver": insight.reference_driver,
        "mode": insight.mode.value,
        "confidence_level": insight.confidence_level.value,
        "summary": insight.summary,
        "dimension_insights": [
            {
                "dimension": d.dimension,
                "level": d.level,
                "percentile": d.percentile,
                "text": d.text,
                "raw_value_ms": d.raw_value_ms,
                "corner_count": d.corner_count,
            }
            for d in insight.dimension_insights
        ],
        "corner_insights": [
            {
                "corner_name": c.corner_name,
                "delta_ms": c.delta_ms,
                "direction": c.direction,
                "cause": c.cause,
                "text": c.text,
                "confidence": c.confidence,
            }
            for c in insight.corner_insights
        ],
        "opportunity_text": insight.opportunity_text,
        "hedging_prefix": insight.hedging_prefix,
        "total_corners": insight.total_corners,
        "session_context": insight.session_context,
        "style_summary": insight.style_summary,
    }


def _corner_result_to_dict(corner_result) -> Dict[str, Any]:
    """Convert CornerResult dataclass to serializable dict."""
    return {
        "corner_number": corner_result.corner_number,
        "name": corner_result.name,
        "apex_distance": corner_result.apex_distance,
        "brake_distance": corner_result.brake_distance,
        "zone_start": corner_result.zone_start,
        "zone_end": corner_result.zone_end,
        "delta_change": corner_result.delta_change,
        "cause": corner_result.cause,
        "confidence": corner_result.confidence,
    }


def _straight_segment_to_dict(segment) -> Dict[str, Any]:
    """Convert StraightSegment dataclass to serializable dict."""
    return {
        "segment_number": segment.segment_number,
        "name": segment.name,
        "start_distance": segment.start_distance,
        "end_distance": segment.end_distance,
        "delta_change": segment.delta_change,
        "length": segment.length,
        "primary_factor": segment.primary_factor,
    }


def _lap_breakdown_to_dict(lap_breakdown) -> Dict[str, Any]:
    """Convert LapBreakdown dataclass to serializable dict."""
    return {
        "corner_total": lap_breakdown.corner_total,
        "straight_total": lap_breakdown.straight_total,
        "official_gap": lap_breakdown.official_gap,
        "track_coverage": lap_breakdown.track_coverage,
        "straight_segments": [
            _straight_segment_to_dict(seg)
            for seg in lap_breakdown.straight_segments
        ],
        "reconciliation_valid": lap_breakdown.reconciliation_valid,
        "reconciliation_error": lap_breakdown.reconciliation_error,
        "insight_text": lap_breakdown.insight_text,
    }


# =============================================================================
# Telemetry Fetching
# =============================================================================

async def fetch_driver_telemetry(
    client: httpx.AsyncClient,
    session_id: str,
    driver: str,
    session_part: Optional[str] = None,
    acquisition_mode: Optional[str] = None
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Fetch telemetry data for a driver from the API service.

    Args:
        client: Async HTTP client
        session_id: Session identifier
        driver: Driver code
        session_part: Optional session part filter
        acquisition_mode: G0 — optional per-request acquisition override
            forwarded to the API ("native" | "legacy"); None = API default

    Returns:
        Tuple of (telemetry_dict, error_message)
        - telemetry_dict contains 'distance', 'speed', 'brake', 'throttle'
        - error_message is None on success
    """
    try:
        params = {
            "session": session_id,
            "drivers": driver,
        }
        if session_part:
            params["session_part"] = session_part
        if acquisition_mode:
            params["acquisition"] = acquisition_mode

        url = f"{API_SERVICE_URL}/telemetry"

        response = await client.get(
            url,
            params=params,
            timeout=TELEMETRY_TIMEOUT_SECONDS
        )

        if response.status_code != 200:
            error = f"API returned {response.status_code} for {driver}"
            logger.warning(error)
            return None, error

        data = response.json()

        # API returns a list - extract the driver's telemetry
        if isinstance(data, list):
            if not data:
                error = f"Empty telemetry response for {driver}"
                logger.warning(error)
                return None, error
            data = data[0]  # Get first (and only) item for this driver

        # Validate required fields
        required = ["distance", "speed"]
        for field in required:
            if field not in data or not data[field]:
                error = f"Missing {field} in telemetry for {driver}"
                logger.warning(error)
                return None, error

        # Get official lap time if available
        # Include relative_distance and time for Tier 1 delta algorithm
        telemetry = {
            "distance": data["distance"],
            "speed": data["speed"],
            "brake": data.get("brake", [0] * len(data["distance"])),
            "throttle": data.get("throttle", [100] * len(data["distance"])),
            "lap_time": data.get("lapTime"),  # camelCase from API response
            "relative_distance": data.get("relativeDistance"),  # camelCase from API
            "time": data.get("time"),
        }

        return telemetry, None

    except httpx.TimeoutException:
        error = f"Timeout fetching telemetry for {driver}"
        logger.error(error)
        return None, error
    except Exception as e:
        error = f"Error fetching telemetry for {driver}: {str(e)}"
        logger.error(error)
        return None, error


async def fetch_all_telemetry(
    client: httpx.AsyncClient,
    session_id: str,
    reference_driver: str,
    compare_drivers: List[str],
    session_part: Optional[str] = None,
    acquisition_mode: Optional[str] = None
) -> Tuple[Dict[str, Dict[str, Any]], List[str]]:
    """
    Fetch telemetry for reference and all comparison drivers.

    Args:
        client: Async HTTP client
        session_id: Session identifier
        reference_driver: Reference driver code
        compare_drivers: List of comparison driver codes
        session_part: Optional session part filter
        acquisition_mode: G0 — optional acquisition override (see
            fetch_driver_telemetry)

    Returns:
        Tuple of (telemetry_by_driver, errors)
    """
    import asyncio

    all_drivers = [reference_driver] + compare_drivers
    errors = []
    telemetry_by_driver = {}

    # Fetch all telemetry concurrently
    tasks = [
        fetch_driver_telemetry(client, session_id, driver, session_part, acquisition_mode)
        for driver in all_drivers
    ]

    results = await asyncio.gather(*tasks)

    for driver, (telemetry, error) in zip(all_drivers, results):
        if error:
            errors.append(error)
        elif telemetry:
            telemetry_by_driver[driver] = telemetry

    return telemetry_by_driver, errors


# =============================================================================
# G0 — Native acquisition gap metadata (Honest Acquisition)
# =============================================================================

async def fetch_all_native_meta(
    client: httpx.AsyncClient,
    session_id: str,
    drivers: List[str],
    session_part: Optional[str] = None,
) -> Dict[str, List[Dict[str, Any]]]:
    """
    Fetch native-acquisition gap inventories from GET /telemetry/meta.

    Returns {driver: [gap, ...]} where each gap dict carries camelCase keys
    (dStart/dEnd in metres) from the API.

    Graceful degradation — and why it does not violate the no-silent-fallback
    rule: the telemetry arrays themselves are NEVER fallback-fetched; only
    this gap METADATA degrades (corners simply keep gap_flag=False), it is
    logged at WARNING, and the A/B harness computes the gap inventory
    independently from /telemetry/meta, so a degraded fetch here cannot hide
    gaps from the G0 evidence. Legacy-mode runs (A/B) skip this call entirely.
    The response shape is validated before use because test harnesses mock
    the HTTP client with a single canned payload for every URL.
    """
    try:
        params: Dict[str, Any] = {"session": session_id, "drivers": drivers}
        if session_part:
            params["session_part"] = session_part

        response = await client.get(
            f"{API_SERVICE_URL}/telemetry/meta",
            params=params,
            timeout=TELEMETRY_TIMEOUT_SECONDS,
        )
        if response.status_code != 200:
            logger.warning(
                "native meta fetch returned %s — corners will carry gap_flag=False",
                response.status_code)
            return {}

        data = response.json()
        # Shape validation: a list of items each holding 'driver' and 'gaps'.
        if not isinstance(data, list):
            logger.warning("native meta response is not a list — ignoring")
            return {}
        gaps_by_driver: Dict[str, List[Dict[str, Any]]] = {}
        for item in data:
            if not isinstance(item, dict) or "driver" not in item or "gaps" not in item:
                logger.warning("native meta item lacks driver/gaps keys — ignoring payload")
                return {}
            gaps_by_driver[item["driver"]] = item["gaps"] or []
        return gaps_by_driver

    except Exception as e:
        logger.warning("native meta fetch failed (%s) — corners will carry gap_flag=False", e)
        return {}


def _gap_overlaps_zone(gap: Dict[str, Any], zone_start: float, zone_end: float) -> bool:
    """True when a gap's distance interval intersects [zone_start, zone_end]."""
    d_start = gap.get("dStart", gap.get("d_start"))
    d_end = gap.get("dEnd", gap.get("d_end"))
    if d_start is None or d_end is None:
        return False
    return float(d_start) <= zone_end and float(d_end) >= zone_start


def apply_gap_flags(
    corner_results,
    ref_gaps: List[Dict[str, Any]],
    comp_gaps: List[Dict[str, Any]],
) -> int:
    """
    G0 gap law: FLAG (do not modify) corners whose analysis zone overlaps a
    native-acquisition gap on either driver's car stream.

    Design decision (documented per the G0 spec): the Phase-2 delta grid keeps
    interpolating end-to-end across gaps. Severing or down-weighting the grid
    inside gaps would break the closure invariant (delta[-1] == official gap);
    modelling uncertainty growth through gaps belongs to the fusion track at a
    later gate. At G0 the flag is internal bookkeeping only — it is NOT
    serialized into the API response (the response schema is frozen against
    the golden contract) and does not feed detection or confidence logic.

    Returns the number of corners flagged.
    """
    all_gaps = list(ref_gaps or []) + list(comp_gaps or [])
    if not all_gaps:
        return 0
    flagged = 0
    for cr in corner_results.corner_results:
        if any(_gap_overlaps_zone(g, cr.zone_start, cr.zone_end) for g in all_gaps):
            cr.gap_flag = True
            flagged += 1
    if flagged:
        logger.info("gap law: %d corner zone(s) overlap acquisition gaps "
                    "(internal gap_flag set; analysis values unchanged)", flagged)
    return flagged


# =============================================================================
# Phase Execution Functions
# =============================================================================

def _estimate_lap_time_from_telemetry(telemetry: Dict[str, Any]) -> float:
    """
    Estimate lap time from telemetry distance and speed arrays.
    Uses physics: time = sum(distance_segment / speed_segment).
    
    Returns estimated lap time in seconds, or 90.0 as fallback.
    """
    try:
        distance = np.array(telemetry.get("distance", []))
        speed = np.array(telemetry.get("speed", []))
        
        if len(distance) < 2 or len(speed) < 2:
            return 90.0
        
        # Convert speed from km/h to m/s
        speed_ms = speed / 3.6
        speed_ms = np.maximum(speed_ms, 0.1)  # Avoid division by zero
        
        # Calculate time for each segment
        distance_segments = np.diff(distance)
        avg_speeds = (speed_ms[:-1] + speed_ms[1:]) / 2
        
        segment_times = distance_segments / avg_speeds
        total_time = np.sum(segment_times)
        
        # Sanity check: F1 lap times are typically 60-120s
        if 50.0 <= total_time <= 150.0:
            return float(total_time)
        
        logger.warning(f"Estimated lap time {total_time:.3f}s outside expected range")
        return 90.0
        
    except Exception as e:
        logger.warning(f"Failed to estimate lap time: {e}")
        return 90.0


def run_phase2_delta(
    ref_telemetry: Dict[str, Any],
    comp_telemetry: Dict[str, Any],
    reference_driver: str,
    compare_driver: str
) -> Tuple[Optional[DeltaResult], Optional[str]]:
    """
    Run Phase 2: Scaled Delta Analysis.

    Args:
        ref_telemetry: Reference driver telemetry
        comp_telemetry: Comparison driver telemetry
        reference_driver: Reference driver code
        compare_driver: Comparison driver code

    Returns:
        Tuple of (DeltaResult, error_message)
    """
    try:
        # Extract official lap times, estimate from telemetry if not available
        ref_time = ref_telemetry.get("lap_time")
        comp_time = comp_telemetry.get("lap_time")
        
        if ref_time is None:
            ref_time = _estimate_lap_time_from_telemetry(ref_telemetry)
            logger.info(f"Estimated ref lap time for {reference_driver}: {ref_time:.3f}s")
        
        if comp_time is None:
            comp_time = _estimate_lap_time_from_telemetry(comp_telemetry)
            logger.info(f"Estimated comp lap time for {compare_driver}: {comp_time:.3f}s")

        result = calculate_scaled_delta(
            ref_telemetry=ref_telemetry,
            comp_telemetry=comp_telemetry,
            ref_official_time=ref_time,
            comp_official_time=comp_time,
            ref_driver=reference_driver,
            comp_driver=compare_driver,
            num_points=DEFAULT_NUM_POINTS
        )

        return result, None

    except Exception as e:
        error = f"Phase 2 error for {compare_driver}: {str(e)}"
        logger.error(error, exc_info=True)
        return None, error


def run_phase3_corner(
    delta_result: DeltaResult,
    ref_telemetry: Dict[str, Any],
    comp_telemetry: Dict[str, Any],
    corners: List[CornerInput],
    track_length: Optional[float] = None
) -> Tuple[Optional[CornerAnalysisResult], Optional[str]]:
    """
    Run Phase 3: Corner Analysis.

    Uses both reference and comparison driver telemetry for accurate
    braking zone detection, eliminating phase artifacts for late-braking
    drivers.

    Prefers V2 analysis (with speed-based zone detection and overlap prevention)
    when speed data is available, falls back to V1 otherwise.

    Args:
        delta_result: Result from Phase 2
        ref_telemetry: Reference driver telemetry
        comp_telemetry: Comparison driver telemetry
        corners: List of corner definitions
        track_length: Track length in meters (for lap breakdown calculation)

    Returns:
        Tuple of (CornerAnalysisResult, error_message)
    """
    try:
        # Check if speed data is available for V2 analysis
        ref_has_speed = ref_telemetry.get("speed") and len(ref_telemetry["speed"]) > 0
        comp_has_speed = comp_telemetry.get("speed") and len(comp_telemetry["speed"]) > 0

        if ref_has_speed and comp_has_speed:
            # Use V2 analysis with speed-based zone detection and overlap prevention
            logger.info("Using V2 corner analysis with zone overlap prevention")
            result = analyze_corners_v2(
                delta_result=delta_result,
                ref_distance=ref_telemetry["distance"],
                ref_brake=ref_telemetry["brake"],
                ref_speed=ref_telemetry["speed"],
                comp_distance=comp_telemetry["distance"],
                comp_brake=comp_telemetry["brake"],
                comp_speed=comp_telemetry["speed"],
                corners=corners,
                track_length=track_length
            )
        else:
            # Fall back to V1 analysis
            logger.info("Using V1 corner analysis (no speed data available)")
            result = analyze_corners(
                delta_result=delta_result,
                ref_distance=ref_telemetry["distance"],
                ref_brake=ref_telemetry["brake"],
                comp_distance=comp_telemetry["distance"],
                comp_brake=comp_telemetry["brake"],
                corners=corners
            )

        return result, None

    except Exception as e:
        error = f"Phase 3 error: {str(e)}"
        logger.error(error, exc_info=True)
        return None, error


def run_phase4_technique(
    corner_results_by_driver: Dict[str, CornerAnalysisResult],
    reference_driver: str
) -> Tuple[List[TechniqueProfile], Optional[SessionPercentiles], Optional[str]]:
    """
    Run Phase 4: Technique Profiling.

    Args:
        corner_results_by_driver: Map of driver code to CornerAnalysisResult
        reference_driver: Reference driver code

    Returns:
        Tuple of (profiles, session_percentiles, error_message)
    """
    try:
        profiles, percentiles = profile_drivers(
            corner_results_by_driver=corner_results_by_driver,
            reference_driver=reference_driver,
            weight_by_confidence=True
        )

        return profiles, percentiles, None

    except Exception as e:
        error = f"Phase 4 error: {str(e)}"
        logger.error(error, exc_info=True)
        return [], None, error


def run_phase5_insight(
    profile: TechniqueProfile,
    mode: InsightMode,
    session_context: Optional[Dict[str, str]] = None
) -> Tuple[Optional[NaturalLanguageInsight], Optional[str]]:
    """
    Run Phase 5: Natural Language Insight Generation.

    Args:
        profile: TechniqueProfile from Phase 4
        mode: Insight mode (ENGINEER or DRIVER)
        session_context: Optional circuit/session context

    Returns:
        Tuple of (NaturalLanguageInsight, error_message)
    """
    try:
        result = generate_insights(
            profile=profile,
            mode=mode,
            session_context=session_context
        )

        if result.success and result.insight:
            return result.insight, None
        else:
            error = f"Phase 5 failed for {profile.driver}: {result.errors}"
            return None, error

    except Exception as e:
        error = f"Phase 5 error for {profile.driver}: {str(e)}"
        logger.error(error, exc_info=True)
        return None, error


# =============================================================================
# Main Orchestration Function
# =============================================================================

async def orchestrate_performance_insights(
    config: PerformanceInsightsConfig,
    client: Optional[httpx.AsyncClient] = None
) -> PerformanceInsightsResult:
    """
    Orchestrate the complete performance insights pipeline.

    This is the main entry point for Phase 6. It:
    1. Fetches telemetry for all drivers
    2. Runs Phase 2 (delta) for each comparison driver
    3. Runs Phase 3 (corner) for each comparison driver
    4. Runs Phase 4 (technique) across all drivers
    5. Runs Phase 5 (insight) for each driver

    Args:
        config: PerformanceInsightsConfig with all parameters
        client: Optional httpx.AsyncClient (created if not provided)

    Returns:
        PerformanceInsightsResult with complete analysis
    """
    start_time = time.time()

    logger.info(
        f"Orchestrating performance insights: session={config.session_id}, "
        f"ref={config.reference_driver}, compare={config.compare_drivers}"
    )

    # Initialize result
    result = PerformanceInsightsResult(
        session_id=config.session_id,
        reference_driver=config.reference_driver,
        circuit_name=config.circuit_name,
        mode=config.mode,
        results=[],
        total_drivers_requested=len(config.compare_drivers),
        total_corners=len(config.corners),
    )

    # Create client if not provided
    own_client = client is None
    if own_client:
        client = httpx.AsyncClient()

    try:
        # =====================================================================
        # Stage 1: Fetch Telemetry
        # =====================================================================
        telemetry_start = time.time()

        telemetry_by_driver, fetch_errors = await fetch_all_telemetry(
            client,
            config.session_id,
            config.reference_driver,
            config.compare_drivers,
            config.session_part,
            config.acquisition_mode
        )

        result.errors.extend(fetch_errors)

        # G0: native acquisition gap inventories (metadata only — see
        # fetch_all_native_meta for the degradation rationale). Skipped for
        # explicit legacy-mode runs, which have no native bundles.
        gaps_by_driver: Dict[str, List[Dict[str, Any]]] = {}
        if config.acquisition_mode != "legacy":
            gaps_by_driver = await fetch_all_native_meta(
                client,
                config.session_id,
                [config.reference_driver] + config.compare_drivers,
                config.session_part,
            )

        telemetry_duration = int((time.time() - telemetry_start) * 1000)
        result.phase_timing.append(PhaseTimingInfo(
            phase="telemetry_fetch",
            duration_ms=telemetry_duration,
            success=config.reference_driver in telemetry_by_driver,
            error=fetch_errors[0] if fetch_errors and config.reference_driver not in telemetry_by_driver else None
        ))

        # Check if reference driver telemetry is available
        if config.reference_driver not in telemetry_by_driver:
            error = f"No telemetry for reference driver {config.reference_driver}"
            result.errors.append(error)
            result.total_duration_ms = int((time.time() - start_time) * 1000)
            logger.error(error)
            return result

        ref_telemetry = telemetry_by_driver[config.reference_driver]

        # =====================================================================
        # Stage 2: Phase 2 - Scaled Delta (per driver)
        # =====================================================================
        phase2_start = time.time()
        delta_results: Dict[str, DeltaResult] = {}
        phase2_errors = []

        for driver in config.compare_drivers:
            if driver not in telemetry_by_driver:
                phase2_errors.append(f"No telemetry for {driver}")
                continue

            delta_result, error = run_phase2_delta(
                ref_telemetry,
                telemetry_by_driver[driver],
                config.reference_driver,
                driver
            )

            if error:
                phase2_errors.append(error)
            elif delta_result:
                delta_results[driver] = delta_result

        phase2_duration = int((time.time() - phase2_start) * 1000)
        result.phase_timing.append(PhaseTimingInfo(
            phase="delta_analysis",
            duration_ms=phase2_duration,
            success=len(delta_results) > 0,
            error=phase2_errors[0] if phase2_errors else None
        ))
        result.errors.extend(phase2_errors)

        # =====================================================================
        # Stage 3: Phase 3 - Corner Analysis (per driver)
        # =====================================================================
        phase3_start = time.time()
        corner_results: Dict[str, CornerAnalysisResult] = {}
        phase3_errors = []

        for driver, delta_result in delta_results.items():
            comp_telemetry = telemetry_by_driver.get(driver)
            if not comp_telemetry:
                phase3_errors.append(f"Missing telemetry for {driver} in Phase 3")
                continue

            corner_result, error = run_phase3_corner(
                delta_result,
                ref_telemetry,
                comp_telemetry,
                config.corners,
                track_length=config.track_length
            )

            if error:
                phase3_errors.append(error)
            elif corner_result:
                # G0: flag corners whose zones overlap acquisition gaps
                # (internal bookkeeping; values and confidence unchanged).
                # Cross-domain approximation (review L3-6): comparison-driver
                # gap distances are integrated on that driver's car frame while
                # zones live on the reference/delta-grid axis; measured
                # inter-frame drift is a constant <1 m (diagnostics/g0), far
                # below zone scale, so no tolerance padding is applied at G0.
                apply_gap_flags(
                    corner_result,
                    gaps_by_driver.get(config.reference_driver, []),
                    gaps_by_driver.get(driver, []),
                )
                corner_results[driver] = corner_result

        phase3_duration = int((time.time() - phase3_start) * 1000)
        result.phase_timing.append(PhaseTimingInfo(
            phase="corner_analysis",
            duration_ms=phase3_duration,
            success=len(corner_results) > 0,
            error=phase3_errors[0] if phase3_errors else None
        ))
        result.errors.extend(phase3_errors)

        # =====================================================================
        # Stage 4: Phase 4 - Technique Profiling (all drivers)
        # =====================================================================
        phase4_start = time.time()
        profiles: Dict[str, TechniqueProfile] = {}
        session_percentiles: Optional[SessionPercentiles] = None

        if corner_results:
            profile_list, percentiles, error = run_phase4_technique(
                corner_results,
                config.reference_driver
            )

            if error:
                result.errors.append(error)
            else:
                session_percentiles = percentiles
                for profile in profile_list:
                    profiles[profile.driver] = profile

        phase4_duration = int((time.time() - phase4_start) * 1000)
        result.phase_timing.append(PhaseTimingInfo(
            phase="technique_profiling",
            duration_ms=phase4_duration,
            success=len(profiles) > 0,
            error=None if profiles else "No profiles generated"
        ))

        # =====================================================================
        # Stage 5: Phase 5 - Natural Language Insights (per driver)
        # =====================================================================
        phase5_start = time.time()
        insights: Dict[str, NaturalLanguageInsight] = {}

        insight_mode = InsightMode.ENGINEER if config.mode == "engineer" else InsightMode.DRIVER
        session_context = {}
        if config.circuit_name:
            session_context["circuit"] = config.circuit_name
        if config.session_part:
            session_context["session"] = config.session_part

        for driver, profile in profiles.items():
            insight, error = run_phase5_insight(profile, insight_mode, session_context)

            if error:
                result.warnings.append(error)
            elif insight:
                insights[driver] = insight

        phase5_duration = int((time.time() - phase5_start) * 1000)
        result.phase_timing.append(PhaseTimingInfo(
            phase="insight_generation",
            duration_ms=phase5_duration,
            success=len(insights) > 0,
            error=None if insights else "No insights generated"
        ))

        # =====================================================================
        # Stage 6: Assemble Results
        # =====================================================================
        for driver in config.compare_drivers:
            driver_result = DriverPerformanceResult(
                driver=driver,
                official_gap=0.0,
                scaling_confidence=0.0,
            )

            # Add Phase 2 data
            if driver in delta_results:
                delta = delta_results[driver]
                driver_result.official_gap = delta.official_gap
                driver_result.scaling_confidence = delta.confidence
                driver_result.telemetry_gap = delta.telemetry_gap
                driver_result.scaling_factor = delta.scaling_factor
                driver_result.raw_delta = list(delta.raw_delta) if delta.raw_delta is not None else None

                if config.include_telemetry:
                    driver_result.delta = delta.delta
                    driver_result.distance = delta.distance

            # Add Phase 3 data
            if driver in corner_results:
                corner = corner_results[driver]
                driver_result.corners_gaining = corner.corners_gaining
                driver_result.corners_losing = corner.corners_losing
                driver_result.total_corner_delta = corner.total_delta_change
                driver_result.corner_results = [
                    _corner_result_to_dict(cr)
                    for cr in corner.corner_results
                ]
                # Add lap breakdown (5th Dimension)
                if corner.lap_breakdown:
                    driver_result.lap_breakdown = _lap_breakdown_to_dict(
                        corner.lap_breakdown
                    )

            # Add Phase 4 data
            if driver in profiles:
                driver_result.technique_profile = _technique_profile_to_dict(
                    profiles[driver]
                )

            # Add Phase 5 data
            if driver in insights:
                driver_result.insight = _insight_to_dict(insights[driver])

            result.results.append(driver_result)

        # Add session percentiles
        if session_percentiles:
            result.session_percentiles = _session_percentiles_to_dict(
                session_percentiles
            )

        result.total_drivers_processed = len([
            r for r in result.results
            if r.technique_profile is not None
        ])

    finally:
        if own_client:
            await client.aclose()

    result.total_duration_ms = int((time.time() - start_time) * 1000)

    logger.info(
        f"Orchestration complete: {result.total_drivers_processed}/{result.total_drivers_requested} "
        f"drivers processed in {result.total_duration_ms}ms"
    )

    return result
