"""
Corner Analysis Module

Analyzes WHERE and WHY time is gained or lost at each corner by:
1. Detecting braking zones using telemetry
2. Defining corner zones (brake start to apex + exit)
3. Computing delta change within each zone
4. Attributing cause (braking, apex, exit, multiple)

This module builds on Phase 2's delta_analysis module, using
get_delta_change_in_range() as the foundation for corner-by-corner analysis.

Usage:
    from services.corner_analysis import analyze_corners, CornerInput

    corners = [
        CornerInput(corner_number=1, name="Turn 1", apex_distance=180, corner_type="left"),
        CornerInput(corner_number=5, name="Turn 5", apex_distance=700, corner_type="right"),
    ]

    result = analyze_corners(
        delta_result=delta_result,  # From calculate_scaled_delta()
        ref_brake=ref_telemetry['brake'],
        comp_brake=comp_telemetry['brake'],
        ref_distance=ref_telemetry['distance'],
        comp_distance=comp_telemetry['distance'],
        corners=corners
    )

    for corner in result.corner_results:
        print(f"T{corner.corner_number}: {corner.delta_change:+.3f}s ({corner.cause})")
"""

import logging
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Literal

import numpy as np

from services.delta_analysis import DeltaResult, get_delta_change_in_range
from core.corner_config import CornerAnalysisConfig, get_config_for_circuit

logger = logging.getLogger("ml_service.corner_analysis")


# ============================================================================
# Constants
# ============================================================================

# Default zone offsets from apex (meters)
DEFAULT_BRAKE_SEARCH_START = 250  # Search for braking starts apex - 250m
DEFAULT_BRAKE_SEARCH_END = 50     # Search for braking ends apex - 50m
DEFAULT_ZONE_BEFORE_APEX = 150    # Fallback: zone starts apex - 150m (reduced from 200)
DEFAULT_ZONE_AFTER_APEX = 80      # Zone ends apex + 80m (reduced from 100)
APPROACH_MARGIN_METERS = 20       # Distance before earliest braking point for zone start

# Zone overlap prevention
MIN_ZONE_LENGTH = 50              # Minimum zone length after clamping (meters)

# Braking detection thresholds
BRAKE_THRESHOLD_PERCENT = 20.0    # Minimum brake % to consider "braking"
BRAKE_GRADIENT_THRESHOLD = 5.0   # Minimum gradient (%/10m) for "real" braking

# Cause determination thresholds
PHASE_SPLIT_RATIO = 0.33          # Split zone into thirds for cause attribution
MULTIPLE_CAUSE_THRESHOLD = 0.3    # If second-largest phase > 30% of total, it's "multiple"
NEUTRAL_THRESHOLD = 0.005         # Delta change < 5ms considered neutral


# ============================================================================
# Data Classes
# ============================================================================

CauseType = Literal["braking", "apex", "exit", "multiple", "unknown"]
ConfidenceLevel = Literal["high", "medium", "low"]


@dataclass
class CornerInput:
    """
    Input definition for a corner to analyze.

    Attributes:
        corner_number: Sequential corner number (1-indexed)
        apex_distance: Distance from start/finish to corner apex (meters)
        corner_type: Left or right turn direction
        name: Optional corner name (e.g., "Turn 1", "Parabolica")
    """
    corner_number: int
    apex_distance: float
    corner_type: str  # "left" or "right"
    name: Optional[str] = None


@dataclass
class CornerResult:
    """
    Result of analyzing a single corner.

    Attributes:
        corner_number: Sequential corner number
        name: Corner name (if provided)
        apex_distance: Distance to corner apex (meters)
        brake_distance: Detected braking start distance (meters)
        zone_start: Analysis zone start distance (meters)
        zone_end: Analysis zone end distance (meters)
        delta_change: Time gained/lost (positive = compare driver slower)
        cause: Primary cause of time difference
        confidence: Confidence level in the analysis
    """
    corner_number: int
    name: Optional[str]
    apex_distance: float
    brake_distance: float
    zone_start: float
    zone_end: float
    delta_change: float  # seconds, positive = compare driver slower
    cause: CauseType
    confidence: ConfidenceLevel


@dataclass
class StraightSegment:
    """
    Delta information for a straight section between corners.

    Attributes:
        segment_number: Sequential segment number (1-indexed)
        name: Human-readable segment name (e.g., "T6 → T10")
        start_distance: Start distance in meters
        end_distance: End distance in meters
        delta_change: Time delta in this segment (seconds, positive = comp slower)
        length: Segment length in meters
        primary_factor: Primary driver of straight-line performance
    """
    segment_number: int
    name: str
    start_distance: float
    end_distance: float
    delta_change: float
    length: float
    primary_factor: str  # 'aero_efficiency', 'traction', 'balanced', 'drag'


@dataclass
class LapBreakdown:
    """
    Complete breakdown of lap time delta into corners and straights.

    This provides mathematical closure: corner_total + straight_total = official_gap
    (within reconciliation tolerance).

    Attributes:
        corner_total: Sum of all corner deltas (seconds)
        straight_total: Sum of all straight deltas (seconds)
        official_gap: Official timing gap from Phase 2 (seconds)
        track_coverage: Fraction of track covered by corners (0-1)
        straight_segments: List of individual straight segment analyses
        reconciliation_valid: Whether corners + straights ≈ official_gap
        reconciliation_error: Absolute difference from expected sum
        insight_text: Educational text explaining the breakdown
    """
    corner_total: float
    straight_total: float
    official_gap: float
    track_coverage: float
    straight_segments: List[StraightSegment] = field(default_factory=list)
    reconciliation_valid: bool = True
    reconciliation_error: float = 0.0
    insight_text: str = ""


@dataclass
class CornerAnalysisResult:
    """
    Complete result of corner analysis for a driver comparison.

    Attributes:
        reference_driver: Reference driver code
        compare_driver: Comparison driver code
        corner_results: List of results for each corner
        total_delta_change: Sum of all corner delta changes
        corners_gaining: Count of corners where compare driver gained time
        corners_losing: Count of corners where compare driver lost time
        lap_breakdown: Complete breakdown showing corners + straights = official
    """
    reference_driver: str
    compare_driver: str
    corner_results: List[CornerResult] = field(default_factory=list)
    total_delta_change: float = 0.0
    corners_gaining: int = 0
    corners_losing: int = 0
    lap_breakdown: Optional[LapBreakdown] = None


# ============================================================================
# Utility Functions
# ============================================================================

def _safe_array(arr, default_value: float = 0.0) -> np.ndarray:
    """
    Safely convert input to numpy array, handling None/empty/NaN cases.

    This utility is defined in CLAUDE.md as a standard for all new modules.

    Args:
        arr: Input (list, np.ndarray, None, or empty)
        default_value: Fallback for empty/invalid arrays

    Returns:
        np.ndarray with at least one valid element
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


def _interpolate_to_distance(
    source_distance: np.ndarray,
    source_values: np.ndarray,
    target_distance: np.ndarray
) -> np.ndarray:
    """
    Interpolate values to a target distance grid.

    Args:
        source_distance: Original distance array
        source_values: Values at original distances
        target_distance: Target distance grid

    Returns:
        Interpolated values at target distances
    """
    return np.interp(target_distance, source_distance, source_values)


def _combine_confidence(
    conf_a: ConfidenceLevel,
    conf_b: ConfidenceLevel
) -> ConfidenceLevel:
    """
    Combine two confidence levels, returning the lower of the two.

    Used when both reference and comparison driver braking points are detected
    to provide a conservative overall confidence for the corner analysis.

    Args:
        conf_a: First confidence level
        conf_b: Second confidence level

    Returns:
        The lower confidence level of the two inputs
    """
    confidence_rank = {"high": 3, "medium": 2, "low": 1}
    rank_to_conf: Dict[int, ConfidenceLevel] = {3: "high", 2: "medium", 1: "low"}
    min_rank = min(confidence_rank[conf_a], confidence_rank[conf_b])
    return rank_to_conf[min_rank]


def _boost_confidence_from_delta_accuracy(
    corner_confidence: ConfidenceLevel,
    delta_confidence: float
) -> ConfidenceLevel:
    """
    Boost corner confidence based on delta analysis accuracy.

    When delta analysis has high confidence (scale factor ~1.0), it means
    the underlying time calculations are accurate. This external validation
    can boost corner confidence by one level.

    The rationale is that even if mechanical brake detection is uncertain,
    we can trust the delta values more if the overall lap time calculation
    is highly accurate (matches official timing).

    Args:
        corner_confidence: Current confidence from brake detection
        delta_confidence: Confidence from delta analysis (0-1 scale)

    Returns:
        Potentially boosted confidence level

    Boosting Rules:
        - delta_confidence >= 0.9: Boost by 1 level (low->medium, medium->high)
        - delta_confidence >= 0.8: Boost low->medium only
        - delta_confidence < 0.8: No boost

    Examples:
        >>> _boost_confidence_from_delta_accuracy("low", 0.95)
        "medium"
        >>> _boost_confidence_from_delta_accuracy("medium", 0.95)
        "high"
        >>> _boost_confidence_from_delta_accuracy("low", 0.85)
        "medium"
        >>> _boost_confidence_from_delta_accuracy("medium", 0.85)
        "medium"
        >>> _boost_confidence_from_delta_accuracy("low", 0.70)
        "low"
    """
    if delta_confidence >= 0.9:
        # High delta accuracy - boost by one level
        if corner_confidence == "low":
            logger.debug(f"Boosting confidence low->medium (delta_conf={delta_confidence:.2f})")
            return "medium"
        elif corner_confidence == "medium":
            logger.debug(f"Boosting confidence medium->high (delta_conf={delta_confidence:.2f})")
            return "high"
        return corner_confidence  # Already high

    elif delta_confidence >= 0.8:
        # Good delta accuracy - boost low to medium only
        if corner_confidence == "low":
            logger.debug(f"Boosting confidence low->medium (delta_conf={delta_confidence:.2f})")
            return "medium"
        return corner_confidence

    return corner_confidence  # No boost


# ============================================================================
# Braking Zone Detection
# ============================================================================

def detect_braking_zone(
    distance: np.ndarray,
    brake: np.ndarray,
    apex_distance: float,
    search_start_offset: float = DEFAULT_BRAKE_SEARCH_START,
    search_end_offset: float = DEFAULT_BRAKE_SEARCH_END
) -> Tuple[float, ConfidenceLevel]:
    """
    Detect the braking point for a corner using telemetry.

    Uses a hybrid approach:
    1. Define a search zone (apex - search_start to apex - search_end)
    2. Find first point where brake > threshold AND gradient > threshold
    3. If not found, fall back to fixed offset (apex - DEFAULT_ZONE_BEFORE_APEX)

    Args:
        distance: Distance array from telemetry (meters)
        brake: Brake percentage array (0-100)
        apex_distance: Corner apex distance (meters)
        search_start_offset: Search zone starts apex - this value
        search_end_offset: Search zone ends apex - this value

    Returns:
        Tuple of (brake_start_distance, confidence_level)
        - HIGH: Clear braking point detected
        - MEDIUM: Fallback to default offset
        - LOW: No valid data in search zone

    Example:
        >>> brake_dist, conf = detect_braking_zone(distance, brake, apex_distance=500)
        >>> print(f"Braking at {brake_dist:.0f}m (confidence: {conf})")
    """
    distance = _safe_array(distance)
    brake = _safe_array(brake)

    # Define search zone
    search_start = apex_distance - search_start_offset
    search_end = apex_distance - search_end_offset

    # Ensure valid bounds
    search_start = max(search_start, distance.min())
    search_end = min(search_end, distance.max())

    if search_start >= search_end:
        logger.warning(
            f"Invalid search zone for apex {apex_distance}m: "
            f"{search_start:.0f}m to {search_end:.0f}m"
        )
        # Return fallback with LOW confidence
        fallback = max(apex_distance - DEFAULT_ZONE_BEFORE_APEX, distance.min())
        return fallback, "low"

    # Find indices within search zone
    mask = (distance >= search_start) & (distance <= search_end)
    zone_indices = np.where(mask)[0]

    if len(zone_indices) < 2:
        logger.debug(f"Not enough points in search zone for apex {apex_distance}m")
        fallback = max(apex_distance - DEFAULT_ZONE_BEFORE_APEX, distance.min())
        return fallback, "low"

    # Get distance and brake values in search zone
    zone_distance = distance[zone_indices]
    zone_brake = brake[zone_indices]

    # Calculate brake gradient (change per 10 meters)
    # gradient[i] = (brake[i+1] - brake[i]) / (distance[i+1] - distance[i]) * 10
    # This means gradient[i] represents the change LEADING INTO index i+1
    distance_diff = np.diff(zone_distance)
    brake_diff = np.diff(zone_brake)

    # Avoid division by zero
    distance_diff = np.maximum(distance_diff, 0.1)
    gradient = (brake_diff / distance_diff) * 10.0  # per 10 meters

    # Find first point meeting both criteria:
    # 1. Brake > threshold at index i+1 (the target point)
    # 2. Gradient > threshold leading INTO that point
    # Note: gradient[i] is the change from zone_brake[i] to zone_brake[i+1]
    # So we check zone_brake[i+1] >= threshold AND gradient[i] >= threshold
    for i in range(len(gradient)):
        if zone_brake[i + 1] >= BRAKE_THRESHOLD_PERCENT and gradient[i] >= BRAKE_GRADIENT_THRESHOLD:
            # Return the point where braking reaches threshold
            brake_start = float(zone_distance[i + 1])
            logger.debug(
                f"Braking detected at {brake_start:.0f}m for apex {apex_distance}m "
                f"(brake={zone_brake[i + 1]:.1f}%, gradient={gradient[i]:.1f}%/10m)"
            )
            return brake_start, "high"

    # Check for sustained braking without sharp gradient
    # (driver already on brakes at search zone start)
    if zone_brake[0] >= BRAKE_THRESHOLD_PERCENT:
        logger.debug(
            f"Driver already braking at search zone start for apex {apex_distance}m"
        )
        # Return search zone start with MEDIUM confidence
        return float(zone_distance[0]), "medium"

    # No clear braking point found, use fallback
    logger.debug(
        f"No braking detected in search zone for apex {apex_distance}m, using fallback"
    )
    fallback = max(apex_distance - DEFAULT_ZONE_BEFORE_APEX, distance.min())
    return fallback, "medium"


# ============================================================================
# Cause Attribution
# ============================================================================

def determine_cause(
    delta_result: DeltaResult,
    zone_start: float,
    zone_end: float,
    apex_distance: float
) -> CauseType:
    """
    Determine the primary cause of time gain/loss in a corner zone.

    Splits the zone into three phases:
    - Braking: zone_start to (apex - 30% of zone)
    - Apex: around apex (middle 34% of zone)
    - Exit: (apex + 30% of zone) to zone_end

    Returns the phase with the largest absolute delta change,
    or "multiple" if secondary phase is significant.

    Args:
        delta_result: DeltaResult from calculate_scaled_delta
        zone_start: Zone start distance (meters)
        zone_end: Zone end distance (meters)
        apex_distance: Corner apex distance (meters)

    Returns:
        CauseType indicating where time was primarily gained/lost

    Example:
        >>> cause = determine_cause(result, zone_start=300, zone_end=600, apex=500)
        >>> print(f"Primary cause: {cause}")
    """
    zone_length = zone_end - zone_start
    if zone_length <= 0:
        return "unknown"

    # Define phase boundaries
    # Braking phase: zone_start to apex - 20m (or 1/3 into zone, whichever is closer to apex)
    # Apex phase: around apex ± some margin
    # Exit phase: apex + margin to zone_end

    braking_end = min(apex_distance - 20, zone_start + zone_length * PHASE_SPLIT_RATIO)
    exit_start = max(apex_distance + 20, zone_end - zone_length * PHASE_SPLIT_RATIO)

    # Ensure valid boundaries
    braking_end = max(braking_end, zone_start)
    exit_start = min(exit_start, zone_end)

    # Calculate delta change in each phase
    braking_delta = get_delta_change_in_range(delta_result, zone_start, braking_end)
    apex_delta = get_delta_change_in_range(delta_result, braking_end, exit_start)
    exit_delta = get_delta_change_in_range(delta_result, exit_start, zone_end)

    # Find absolute values
    abs_changes = {
        "braking": abs(braking_delta),
        "apex": abs(apex_delta),
        "exit": abs(exit_delta)
    }

    total_abs = sum(abs_changes.values())

    if total_abs < NEUTRAL_THRESHOLD:
        return "unknown"  # Essentially no change

    # Sort by absolute magnitude
    sorted_causes = sorted(abs_changes.items(), key=lambda x: x[1], reverse=True)
    primary_cause, primary_value = sorted_causes[0]
    secondary_value = sorted_causes[1][1]

    # Check if it's "multiple" (secondary phase is significant)
    if primary_value > 0 and secondary_value / primary_value > MULTIPLE_CAUSE_THRESHOLD:
        return "multiple"

    return primary_cause  # type: ignore


# ============================================================================
# Single Corner Analysis
# ============================================================================

def analyze_single_corner(
    delta_result: DeltaResult,
    ref_distance: np.ndarray,
    ref_brake: np.ndarray,
    comp_distance: np.ndarray,
    comp_brake: np.ndarray,
    corner: CornerInput,
    delta_confidence: float = 0.0
) -> CornerResult:
    """
    Analyze time gained/lost at a single corner.

    Process:
    1. Detect braking zones for BOTH reference and comparison drivers
    2. Use the earlier braking point (with margin) as zone start
    3. Calculate delta change within zone
    4. Determine primary cause
    5. Boost confidence based on delta analysis accuracy

    This dual-driver braking detection eliminates phase artifacts that occur
    when comparing late-braking drivers. If we only used the reference driver's
    brake point, a late-braking comparison driver would appear to "lose time"
    in the braking phase (because they're still accelerating when measured).

    Args:
        delta_result: DeltaResult from calculate_scaled_delta
        ref_distance: Reference driver distance array
        ref_brake: Reference driver brake array
        comp_distance: Comparison driver distance array
        comp_brake: Comparison driver brake array
        corner: CornerInput defining the corner
        delta_confidence: Confidence from delta analysis (0-1), used to boost
                         corner confidence when delta accuracy is high

    Returns:
        CornerResult with analysis details

    Example:
        >>> result = analyze_single_corner(
        ...     delta_result, ref_distance, ref_brake,
        ...     comp_distance, comp_brake,
        ...     CornerInput(corner_number=1, apex_distance=500, corner_type="left"),
        ...     delta_confidence=0.95
        ... )
        >>> print(f"T{result.corner_number}: {result.delta_change:+.3f}s")
    """
    # Detect braking zones for BOTH drivers
    ref_brake_dist, ref_conf = detect_braking_zone(
        distance=ref_distance,
        brake=ref_brake,
        apex_distance=corner.apex_distance
    )

    comp_brake_dist, comp_conf = detect_braking_zone(
        distance=comp_distance,
        brake=comp_brake,
        apex_distance=corner.apex_distance
    )

    # Use EARLIER braking point to capture both drivers' complete phases
    earliest_brake = min(ref_brake_dist, comp_brake_dist)

    # Add approach margin for clean baseline
    zone_start = earliest_brake - APPROACH_MARGIN_METERS
    zone_start = max(zone_start, 0)  # Don't go negative

    zone_end = corner.apex_distance + DEFAULT_ZONE_AFTER_APEX

    # Combined confidence reflects less confident detection
    confidence = _combine_confidence(ref_conf, comp_conf)

    # Boost confidence if delta analysis is highly accurate
    confidence = _boost_confidence_from_delta_accuracy(confidence, delta_confidence)

    # Store reference brake distance for reporting
    brake_distance = ref_brake_dist

    logger.debug(
        f"Corner {corner.corner_number}: ref_brake={ref_brake_dist:.0f}m, "
        f"comp_brake={comp_brake_dist:.0f}m, zone_start={zone_start:.0f}m"
    )

    # Clamp to valid distance range
    delta_distance = np.array(delta_result.distance)
    zone_start = max(zone_start, delta_distance.min())
    zone_end = min(zone_end, delta_distance.max())

    if zone_start >= zone_end:
        logger.warning(
            f"Invalid zone for corner {corner.corner_number}: "
            f"{zone_start:.0f}m to {zone_end:.0f}m"
        )
        return CornerResult(
            corner_number=corner.corner_number,
            name=corner.name,
            apex_distance=corner.apex_distance,
            brake_distance=brake_distance,
            zone_start=zone_start,
            zone_end=zone_end,
            delta_change=0.0,
            cause="unknown",
            confidence="low"
        )

    # Calculate delta change in corner zone
    delta_change = get_delta_change_in_range(delta_result, zone_start, zone_end)

    # Determine cause
    cause = determine_cause(delta_result, zone_start, zone_end, corner.apex_distance)

    logger.debug(
        f"Corner {corner.corner_number} ({corner.name or 'unnamed'}): "
        f"brake={brake_distance:.0f}m, zone={zone_start:.0f}-{zone_end:.0f}m, "
        f"delta={delta_change:+.3f}s, cause={cause}, confidence={confidence}"
    )

    return CornerResult(
        corner_number=corner.corner_number,
        name=corner.name,
        apex_distance=corner.apex_distance,
        brake_distance=brake_distance,
        zone_start=zone_start,
        zone_end=zone_end,
        delta_change=delta_change,
        cause=cause,
        confidence=confidence
    )


# ============================================================================
# Main Entry Point
# ============================================================================

def analyze_corners(
    delta_result: DeltaResult,
    ref_distance: List[float],
    ref_brake: List[float],
    comp_distance: List[float],
    comp_brake: List[float],
    corners: List[CornerInput]
) -> CornerAnalysisResult:
    """
    Analyze time gained/lost at all corners.

    This is the main entry point for corner analysis. It processes each corner
    and aggregates the results, using both reference and comparison driver
    telemetry for accurate braking zone detection.

    Args:
        delta_result: DeltaResult from calculate_scaled_delta
        ref_distance: Reference driver distance array
        ref_brake: Reference driver brake array (0-100%)
        comp_distance: Comparison driver distance array
        comp_brake: Comparison driver brake array (0-100%)
        corners: List of CornerInput definitions

    Returns:
        CornerAnalysisResult with all corner analyses

    Example:
        >>> corners = [
        ...     CornerInput(1, 180, "left", "Turn 1"),
        ...     CornerInput(5, 700, "right", "Turn 5")
        ... ]
        >>> result = analyze_corners(
        ...     delta_result, ref_dist, ref_brake,
        ...     comp_dist, comp_brake, corners
        ... )
        >>> print(f"Total delta change: {result.total_delta_change:+.3f}s")
        >>> print(f"Corners gaining: {result.corners_gaining}")
        >>> print(f"Corners losing: {result.corners_losing}")
    """
    logger.info(
        f"Analyzing {len(corners)} corners for "
        f"{delta_result.reference_driver} vs {delta_result.compare_driver}"
    )

    # Convert to numpy arrays
    ref_distance_arr = _safe_array(ref_distance)
    ref_brake_arr = _safe_array(ref_brake)
    comp_distance_arr = _safe_array(comp_distance)
    comp_brake_arr = _safe_array(comp_brake)

    # FastF1/API returns brake as 0-1 (boolean converted to float)
    # Convert to 0-100 percentage scale if needed
    if ref_brake_arr.max() <= 1.0:
        logger.debug("Converting ref brake data from 0-1 to 0-100 scale")
        ref_brake_arr = ref_brake_arr * 100.0

    if comp_brake_arr.max() <= 1.0:
        logger.debug("Converting comp brake data from 0-1 to 0-100 scale")
        comp_brake_arr = comp_brake_arr * 100.0

    # Analyze each corner
    corner_results: List[CornerResult] = []
    total_delta = 0.0
    gaining = 0
    losing = 0

    for corner in corners:
        result = analyze_single_corner(
            delta_result=delta_result,
            ref_distance=ref_distance_arr,
            ref_brake=ref_brake_arr,
            comp_distance=comp_distance_arr,
            comp_brake=comp_brake_arr,
            corner=corner,
            delta_confidence=delta_result.confidence
        )
        corner_results.append(result)

        total_delta += result.delta_change

        # Positive delta = compare driver lost time (reference gained)
        # Negative delta = compare driver gained time
        if result.delta_change > NEUTRAL_THRESHOLD:
            losing += 1  # Compare driver losing time
        elif result.delta_change < -NEUTRAL_THRESHOLD:
            gaining += 1  # Compare driver gaining time

    logger.info(
        f"Corner analysis complete: "
        f"total_delta={total_delta:+.3f}s, "
        f"gaining={gaining}, losing={losing}"
    )

    return CornerAnalysisResult(
        reference_driver=delta_result.reference_driver,
        compare_driver=delta_result.compare_driver,
        corner_results=corner_results,
        total_delta_change=total_delta,
        corners_gaining=gaining,
        corners_losing=losing,
        lap_breakdown=None  # V1 doesn't calculate lap breakdown
    )


# ============================================================================
# V2 Functions - Deceleration-Based Corner Analysis
# ============================================================================

@dataclass
class SectorValidation:
    """
    Result of validating corner deltas against official sector times.

    Attributes:
        sector_number: Sector number (1, 2, or 3)
        corner_delta_sum: Sum of corner delta changes in this sector
        official_delta: Official sector time delta (comp - ref)
        difference: Difference between corner sum and official
        is_valid: Whether the difference is within tolerance
    """
    sector_number: int
    corner_delta_sum: float
    official_delta: float
    difference: float
    is_valid: bool


@dataclass
class CornerResultV2(CornerResult):
    """
    Extended corner result for v2 analysis with additional metadata.

    Inherits all fields from CornerResult and adds:
        detected_apex: Dynamically detected apex distance
        entry_speed: Speed at zone entry (km/h)
        apex_speed: Speed at apex (km/h)
        exit_distance: Dynamically detected exit distance
        detection_metadata: Additional detection information
    """
    detected_apex: float = 0.0
    entry_speed: float = 0.0
    apex_speed: float = 0.0
    exit_distance: float = 0.0
    detection_metadata: Dict = field(default_factory=dict)


def compute_deceleration(
    distance: np.ndarray,
    speed: np.ndarray,
    smoothing_window: int = 5
) -> np.ndarray:
    """
    Compute longitudinal deceleration from speed and distance.

    Uses the kinematic equation: a = (v₂² - v₁²) / (2 × Δd)
    This is distance-based, not time-based, which is more accurate
    for telemetry that may have variable sampling rates.

    Args:
        distance: Distance array (meters)
        speed: Speed array (km/h)
        smoothing_window: Window size for moving average filter

    Returns:
        Deceleration array (m/s²) - negative values indicate braking
        Note: Array is one element shorter than input due to diff operation

    Example:
        >>> decel = compute_deceleration(distance, speed)
        >>> heavy_braking_mask = decel < -5.0  # < -5 m/s²
    """
    distance = _safe_array(distance)
    speed = _safe_array(speed)

    # Handle edge case of single-element arrays
    if len(distance) < 2 or len(speed) < 2:
        logger.warning("Insufficient data for deceleration calculation")
        return np.array([0.0])

    # Convert speed from km/h to m/s
    speed_ms = speed / 3.6

    # Calculate distance deltas
    delta_distance = np.diff(distance)
    # Avoid division by zero (replace 0 with small value)
    delta_distance = np.where(delta_distance == 0, 0.001, delta_distance)

    # Calculate deceleration using kinematic equation
    # a = (v2² - v1²) / (2 × Δd)
    v1_sq = speed_ms[:-1] ** 2
    v2_sq = speed_ms[1:] ** 2
    decel = (v2_sq - v1_sq) / (2 * delta_distance)

    # Apply smoothing to reduce noise from ~5 Hz sampling
    if smoothing_window > 1 and len(decel) >= smoothing_window:
        kernel = np.ones(smoothing_window) / smoothing_window
        decel = np.convolve(decel, kernel, mode="same")

    if len(decel) > 0:
        logger.debug(
            f"Computed deceleration: min={decel.min():.1f} m/s², "
            f"max={decel.max():.1f} m/s², mean={decel.mean():.1f} m/s²"
        )

    return decel


def detect_apex_from_speed_v2(
    distance: np.ndarray,
    speed: np.ndarray,
    nominal_apex: float,
    search_margin: float = 50.0
) -> Tuple[float, float, ConfidenceLevel]:
    """
    Detect the actual apex position as the speed minimum within a search window.

    The nominal apex (from track JSON) is approximate. The true apex is where
    the driver reaches minimum speed, which varies by driver line choice.

    Args:
        distance: Distance array (meters)
        speed: Speed array (km/h)
        nominal_apex: Nominal apex distance from track data (meters)
        search_margin: Search window ± this value (meters)

    Returns:
        Tuple of (apex_distance, apex_speed, confidence)
        - apex_distance: Detected apex position (meters)
        - apex_speed: Speed at apex (km/h)
        - confidence: Detection confidence level

    Example:
        >>> apex_dist, apex_speed, conf = detect_apex_from_speed_v2(
        ...     distance, speed, nominal_apex=500, search_margin=50
        ... )
    """
    distance = _safe_array(distance)
    speed = _safe_array(speed)

    window_start = nominal_apex - search_margin
    window_end = nominal_apex + search_margin

    # Find indices within search window
    mask = (distance >= window_start) & (distance <= window_end)

    if not mask.any():
        # No data in search window, return nominal apex
        idx = np.searchsorted(distance, nominal_apex)
        idx = min(idx, len(speed) - 1)
        logger.debug(
            f"No data in apex search window [{window_start:.0f}-{window_end:.0f}m], "
            f"using nominal apex {nominal_apex:.0f}m"
        )
        return nominal_apex, float(speed[idx]), "low"

    window_idx = np.where(mask)[0]
    # Find index of minimum speed within window
    min_local_idx = np.argmin(speed[mask])
    min_idx = window_idx[min_local_idx]

    apex_dist = float(distance[min_idx])
    apex_speed = float(speed[min_idx])

    # Determine confidence based on distance from nominal apex
    deviation = abs(apex_dist - nominal_apex)
    if deviation < 20:
        confidence: ConfidenceLevel = "high"
    elif deviation < 40:
        confidence = "medium"
    else:
        confidence = "low"

    logger.debug(
        f"Apex detected at {apex_dist:.0f}m (nominal: {nominal_apex:.0f}m, "
        f"deviation: {deviation:.0f}m), speed={apex_speed:.0f} km/h, "
        f"confidence={confidence}"
    )

    return apex_dist, apex_speed, confidence


def detect_braking_zone_v2(
    distance: np.ndarray,
    brake: np.ndarray,
    speed: np.ndarray,
    decel: np.ndarray,
    apex_distance: float,
    config: CornerAnalysisConfig
) -> Tuple[float, ConfidenceLevel, Dict]:
    """
    Two-stage braking detection using boolean brake signal and deceleration.

    Stage 1: Find initial candidate using boolean brake signal (fast)
    Stage 2: Refine using deceleration threshold (accurate)

    This hybrid approach combines the speed of boolean detection with
    the accuracy of physics-based deceleration analysis.

    Args:
        distance: Distance array (meters)
        brake: Brake array (0-100 or 0-1)
        speed: Speed array (km/h)
        decel: Deceleration array (m/s²) from compute_deceleration
        apex_distance: Corner apex distance (meters)
        config: Configuration with threshold parameters

    Returns:
        Tuple of (brake_distance, confidence, metadata)
        - brake_distance: Detected braking point (meters)
        - confidence: Detection confidence level
        - metadata: Dict with detection details (stage, boolean_dist, refined_dist)

    Example:
        >>> brake_dist, conf, meta = detect_braking_zone_v2(
        ...     distance, brake, speed, decel, apex_distance=500, config=config
        ... )
        >>> print(f"Braking at {brake_dist:.0f}m via {meta['stage']}")
    """
    distance = _safe_array(distance)
    brake = _safe_array(brake)
    speed = _safe_array(speed)

    # Define search zone (300m before apex to 30m before apex)
    search_start = apex_distance - 300
    search_end = apex_distance - 30

    # Clamp to valid distance range
    search_start = max(search_start, distance.min())
    search_end = min(search_end, distance.max())

    zone_mask = (distance >= search_start) & (distance <= search_end)
    zone_idx = np.where(zone_mask)[0]

    if len(zone_idx) == 0:
        logger.debug(f"No data in braking search zone for apex {apex_distance:.0f}m")
        return search_start, "low", {"stage": "fallback", "reason": "no_data"}

    # Normalize brake if needed (0-100 to 0-1)
    brake_normalized = brake / 100.0 if brake.max() > 1.0 else brake

    # Stage 1: Boolean brake candidate
    # Find first point where brake > 0.5 (50%)
    brake_candidates = zone_idx[brake_normalized[zone_idx] >= 0.5]

    if len(brake_candidates) == 0:
        # No boolean brake signal, use deceleration only
        for idx in zone_idx:
            if idx < len(decel) and decel[idx] <= config.braking_decel_threshold:
                logger.debug(
                    f"Decel-only detection at {distance[idx]:.0f}m "
                    f"(decel={decel[idx]:.1f} m/s²)"
                )
                return float(distance[idx]), "medium", {"stage": "decel_only"}

        # Fallback to zone start
        logger.debug(f"No braking detected, using zone start {distance[zone_idx[0]]:.0f}m")
        return float(distance[zone_idx[0]]), "low", {"stage": "fallback", "reason": "no_brake"}

    boolean_brake_idx = brake_candidates[0]
    boolean_brake_dist = float(distance[boolean_brake_idx])

    # Stage 2: Refine using deceleration
    # Look backward from boolean point to find where decel starts
    refined_idx = boolean_brake_idx
    while refined_idx > zone_idx[0]:
        decel_idx = min(refined_idx - 1, len(decel) - 1)
        if decel_idx >= 0 and decel[decel_idx] > config.braking_decel_threshold:
            # Found point where decel is not yet heavy
            break
        refined_idx -= 1

    refined_dist = float(distance[max(0, refined_idx)])

    # Calculate alignment difference
    alignment_diff = abs(boolean_brake_dist - refined_dist)

    # Determine confidence based on alignment
    if alignment_diff <= config.braking_point_tolerance:
        confidence: ConfidenceLevel = "high"
    elif alignment_diff <= config.braking_point_tolerance * 2:
        confidence = "medium"
    else:
        confidence = "low"

    logger.debug(
        f"Two-stage braking detection: boolean={boolean_brake_dist:.0f}m, "
        f"refined={refined_dist:.0f}m, alignment={alignment_diff:.0f}m, "
        f"confidence={confidence}"
    )

    return refined_dist, confidence, {
        "stage": "two_stage",
        "boolean_dist": boolean_brake_dist,
        "refined_dist": refined_dist,
        "alignment_diff": alignment_diff
    }


def detect_exit_zone_v2(
    distance: np.ndarray,
    speed: np.ndarray,
    decel: np.ndarray,
    apex_idx: int,
    entry_speed: float,
    config: CornerAnalysisConfig
) -> Tuple[float, ConfidenceLevel]:
    """
    Detect corner exit via sustained acceleration OR speed recovery.

    Exit is detected when either:
    1. Sustained acceleration above threshold for N consecutive points
    2. Speed recovers to >= 85% of pre-braking speed

    This is more accurate than a fixed offset from apex.

    Args:
        distance: Distance array (meters)
        speed: Speed array (km/h)
        decel: Deceleration array (m/s²)
        apex_idx: Index of apex point in arrays
        entry_speed: Speed at corner entry (km/h)
        config: Configuration with threshold parameters

    Returns:
        Tuple of (exit_distance, confidence)

    Example:
        >>> exit_dist, conf = detect_exit_zone_v2(
        ...     distance, speed, decel, apex_idx=100, entry_speed=300, config=config
        ... )
    """
    distance = _safe_array(distance)
    speed = _safe_array(speed)

    max_search = distance[apex_idx] + config.max_exit_search_distance
    speed_target = entry_speed * config.exit_speed_recovery_pct

    sustained_count = 0
    exit_idx = apex_idx

    while exit_idx < len(distance) - 1:
        if distance[exit_idx] > max_search:
            # Reached max search distance
            logger.debug(
                f"Exit search reached max distance {max_search:.0f}m"
            )
            return float(distance[exit_idx]), "medium"

        # Condition 1: Sustained acceleration
        if exit_idx < len(decel) and decel[exit_idx] >= config.acceleration_threshold:
            sustained_count += 1
            if sustained_count >= config.exit_sustained_points:
                logger.debug(
                    f"Exit detected via sustained acceleration at "
                    f"{distance[exit_idx]:.0f}m (accel={decel[exit_idx]:.1f} m/s²)"
                )
                return float(distance[exit_idx]), "high"
        else:
            sustained_count = 0

        # Condition 2: Speed recovery
        if speed[exit_idx] >= speed_target:
            logger.debug(
                f"Exit detected via speed recovery at {distance[exit_idx]:.0f}m "
                f"(speed={speed[exit_idx]:.0f} km/h, target={speed_target:.0f} km/h)"
            )
            return float(distance[exit_idx]), "high"

        exit_idx += 1

    # Reached end of data
    final_idx = min(exit_idx, len(distance) - 1)
    logger.debug(f"Exit detection reached end of data at {distance[final_idx]:.0f}m")
    return float(distance[final_idx]), "low"


def validate_against_sectors(
    corner_results: List[CornerResult],
    sector_boundaries: Tuple[float, float],
    ref_sectors: Tuple[float, float, float],
    comp_sectors: Tuple[float, float, float],
    tolerance: float = 0.100
) -> Tuple[List[SectorValidation], float]:
    """
    Validate corner delta sums against official sector time differences.

    This provides external validation that corner analysis aligns with
    official timing data, catching systematic errors in corner detection.

    Args:
        corner_results: List of CornerResult from corner analysis
        sector_boundaries: (sector1_end, sector2_end) distances in meters
        ref_sectors: Reference driver sector times (s1, s2, s3) in seconds
        comp_sectors: Comparison driver sector times (s1, s2, s3) in seconds
        tolerance: Maximum acceptable difference (seconds)

    Returns:
        Tuple of (validations, confidence_adjustment)
        - validations: List of SectorValidation for each sector
        - confidence_adjustment: 0.5-1.0 multiplier based on validation pass rate

    Example:
        >>> validations, conf_adj = validate_against_sectors(
        ...     corner_results,
        ...     sector_boundaries=(1500, 3000),
        ...     ref_sectors=(25.5, 30.2, 22.8),
        ...     comp_sectors=(25.7, 30.0, 23.1)
        ... )
        >>> for v in validations:
        ...     status = "PASS" if v.is_valid else "FAIL"
        ...     print(f"S{v.sector_number}: {status} (diff={v.difference:+.3f}s)")
    """
    s1_end, s2_end = sector_boundaries

    # Calculate official sector deltas (comp - ref)
    official_deltas = [
        comp_sectors[0] - ref_sectors[0],
        comp_sectors[1] - ref_sectors[1],
        comp_sectors[2] - ref_sectors[2],
    ]

    # Group corners by sector
    sectors: List[List[CornerResult]] = [[], [], []]
    for cr in corner_results:
        apex = cr.apex_distance
        if apex < s1_end:
            sectors[0].append(cr)
        elif apex < s2_end:
            sectors[1].append(cr)
        else:
            sectors[2].append(cr)

    # Validate each sector
    validations: List[SectorValidation] = []
    valid_count = 0

    for i in range(3):
        corner_sum = sum(cr.delta_change for cr in sectors[i])
        diff = corner_sum - official_deltas[i]
        is_valid = abs(diff) <= tolerance

        if is_valid:
            valid_count += 1

        validations.append(SectorValidation(
            sector_number=i + 1,
            corner_delta_sum=corner_sum,
            official_delta=official_deltas[i],
            difference=diff,
            is_valid=is_valid
        ))

        logger.debug(
            f"Sector {i + 1}: corner_sum={corner_sum:+.3f}s, "
            f"official={official_deltas[i]:+.3f}s, "
            f"diff={diff:+.3f}s, valid={is_valid}"
        )

    # Calculate confidence adjustment (0.5 to 1.0)
    confidence_adj = 0.5 + (valid_count / 3) * 0.5

    logger.info(
        f"Sector validation: {valid_count}/3 passed, "
        f"confidence adjustment: {confidence_adj:.2f}"
    )

    return validations, confidence_adj


def analyze_single_corner_v2(
    delta_result: DeltaResult,
    ref_distance: np.ndarray,
    ref_brake: np.ndarray,
    ref_speed: np.ndarray,
    comp_distance: np.ndarray,
    comp_brake: np.ndarray,
    comp_speed: np.ndarray,
    corner: CornerInput,
    config: CornerAnalysisConfig,
    delta_confidence: float = 0.0
) -> CornerResultV2:
    """
    Analyze a single corner using v2 deceleration-based detection.

    Process:
    1. Compute deceleration for both drivers
    2. Detect apex from speed minimum
    3. Two-stage braking detection
    4. Dynamic exit detection
    5. Calculate delta change within clamped zone
    6. Boost confidence based on delta analysis accuracy

    Args:
        delta_result: DeltaResult from calculate_scaled_delta
        ref_distance: Reference driver distance array
        ref_brake: Reference driver brake array
        ref_speed: Reference driver speed array
        comp_distance: Comparison driver distance array
        comp_brake: Comparison driver brake array
        comp_speed: Comparison driver speed array
        corner: CornerInput defining the corner
        config: CornerAnalysisConfig with tuning parameters
        delta_confidence: Confidence from delta analysis (0-1), used to boost
                         corner confidence when delta accuracy is high

    Returns:
        CornerResultV2 with analysis details and v2-specific metadata
    """
    # Ensure arrays are numpy arrays
    ref_distance = _safe_array(ref_distance)
    ref_brake = _safe_array(ref_brake)
    ref_speed = _safe_array(ref_speed)
    comp_distance = _safe_array(comp_distance)
    comp_brake = _safe_array(comp_brake)
    comp_speed = _safe_array(comp_speed)

    # Convert brake if needed (0-100 scale)
    if ref_brake.max() <= 1.0:
        ref_brake = ref_brake * 100.0
    if comp_brake.max() <= 1.0:
        comp_brake = comp_brake * 100.0

    # Step 1: Compute deceleration for both drivers
    ref_decel = compute_deceleration(
        ref_distance, ref_speed, config.decel_smoothing_window
    )
    comp_decel = compute_deceleration(
        comp_distance, comp_speed, config.decel_smoothing_window
    )

    # Step 2: Detect apex from speed minimum (use reference driver)
    detected_apex, apex_speed, apex_confidence = detect_apex_from_speed_v2(
        ref_distance, ref_speed,
        corner.apex_distance, config.apex_search_margin
    )

    # Step 3: Two-stage braking detection for both drivers
    ref_brake_dist, ref_brake_conf, ref_meta = detect_braking_zone_v2(
        ref_distance, ref_brake, ref_speed, ref_decel,
        detected_apex, config
    )
    comp_brake_dist, comp_brake_conf, comp_meta = detect_braking_zone_v2(
        comp_distance, comp_brake, comp_speed, comp_decel,
        detected_apex, config
    )

    # Use earlier braking point with margin
    earliest_brake = min(ref_brake_dist, comp_brake_dist)
    zone_start = earliest_brake - APPROACH_MARGIN_METERS
    zone_start = max(zone_start, 0)

    # Get entry speed (speed at zone start for reference driver)
    entry_idx = np.searchsorted(ref_distance, zone_start)
    entry_idx = min(entry_idx, len(ref_speed) - 1)
    entry_speed = float(ref_speed[entry_idx])

    # Step 4: Dynamic exit detection
    apex_idx = np.searchsorted(ref_distance, detected_apex)
    apex_idx = min(apex_idx, len(ref_speed) - 1)

    exit_dist, exit_confidence = detect_exit_zone_v2(
        ref_distance, ref_speed, ref_decel,
        apex_idx, entry_speed, config
    )

    zone_end = exit_dist

    # Clamp to valid distance range
    delta_distance = np.array(delta_result.distance)
    zone_start = max(zone_start, delta_distance.min())
    zone_end = min(zone_end, delta_distance.max())

    # Combine confidence levels
    confidence = _combine_confidence(
        _combine_confidence(apex_confidence, ref_brake_conf),
        _combine_confidence(comp_brake_conf, exit_confidence)
    )

    # Boost confidence if delta analysis is highly accurate
    confidence = _boost_confidence_from_delta_accuracy(confidence, delta_confidence)

    if zone_start >= zone_end:
        logger.warning(
            f"Invalid zone for corner {corner.corner_number}: "
            f"{zone_start:.0f}m to {zone_end:.0f}m"
        )
        return CornerResultV2(
            corner_number=corner.corner_number,
            name=corner.name,
            apex_distance=corner.apex_distance,
            brake_distance=ref_brake_dist,
            zone_start=zone_start,
            zone_end=zone_end,
            delta_change=0.0,
            cause="unknown",
            confidence="low",
            detected_apex=detected_apex,
            entry_speed=entry_speed,
            apex_speed=apex_speed,
            exit_distance=exit_dist,
            detection_metadata={
                "ref_brake_meta": ref_meta,
                "comp_brake_meta": comp_meta,
                "error": "invalid_zone"
            }
        )

    # Calculate delta change in corner zone
    delta_change = get_delta_change_in_range(delta_result, zone_start, zone_end)

    # Determine cause
    cause = determine_cause(delta_result, zone_start, zone_end, detected_apex)

    logger.debug(
        f"Corner {corner.corner_number} (v2): "
        f"apex={detected_apex:.0f}m (nominal: {corner.apex_distance:.0f}m), "
        f"zone={zone_start:.0f}-{zone_end:.0f}m, "
        f"delta={delta_change:+.3f}s, cause={cause}, confidence={confidence}"
    )

    return CornerResultV2(
        corner_number=corner.corner_number,
        name=corner.name,
        apex_distance=corner.apex_distance,
        brake_distance=ref_brake_dist,
        zone_start=zone_start,
        zone_end=zone_end,
        delta_change=delta_change,
        cause=cause,
        confidence=confidence,
        detected_apex=detected_apex,
        entry_speed=entry_speed,
        apex_speed=apex_speed,
        exit_distance=exit_dist,
        detection_metadata={
            "ref_brake_meta": ref_meta,
            "comp_brake_meta": comp_meta,
            "apex_deviation": detected_apex - corner.apex_distance
        }
    )


def _clamp_zones_to_prevent_overlap(
    corner_results: List[CornerResultV2],
    delta_result: DeltaResult
) -> List[CornerResultV2]:
    """
    Post-process corner zones to prevent overlap between adjacent corners.

    When fallback zones are used (due to brake detection failure), they can
    extend 320m before apex and 200m after, causing massive overlap when
    corners are closer than 520m apart. This was causing 92% of track to be
    double-counted on circuits like Mexico.

    This function adjusts zone boundaries so that:
    1. Adjacent zone_end never exceeds next zone_start
    2. The split point is the midpoint between apexes
    3. Delta is recalculated for the adjusted zones

    Args:
        corner_results: List of CornerResultV2 from initial analysis
        delta_result: DeltaResult for recalculating delta changes

    Returns:
        List of CornerResultV2 with adjusted zone boundaries
    """
    if len(corner_results) < 2:
        return corner_results

    # Sort by apex distance to ensure correct ordering
    sorted_results = sorted(corner_results, key=lambda x: x.apex_distance)

    adjusted_results: List[CornerResultV2] = []

    for i, current in enumerate(sorted_results):
        # Create a copy with updated values
        adjusted = CornerResultV2(
            corner_number=current.corner_number,
            name=current.name,
            apex_distance=current.apex_distance,
            brake_distance=current.brake_distance,
            zone_start=current.zone_start,
            zone_end=current.zone_end,
            delta_change=current.delta_change,
            cause=current.cause,
            confidence=current.confidence,
            detected_apex=current.detected_apex,
            entry_speed=current.entry_speed,
            apex_speed=current.apex_speed,
            exit_distance=current.exit_distance,
            detection_metadata=dict(current.detection_metadata) if current.detection_metadata else {}
        )

        # Clamp zone_end to not exceed next corner's zone_start
        if i < len(sorted_results) - 1:
            next_corner = sorted_results[i + 1]

            # Calculate midpoint between apexes
            midpoint = (current.apex_distance + next_corner.apex_distance) / 2

            # Clamp zone_end to midpoint if it exceeds
            if adjusted.zone_end > midpoint:
                original_end = adjusted.zone_end
                adjusted.zone_end = midpoint
                adjusted.detection_metadata["zone_clamped"] = True
                adjusted.detection_metadata["original_zone_end"] = original_end
                adjusted.detection_metadata["clamped_to"] = midpoint

                logger.debug(
                    f"Corner {adjusted.corner_number}: clamped zone_end "
                    f"from {original_end:.0f}m to {midpoint:.0f}m"
                )

        # Clamp zone_start to not go below previous corner's zone_end
        if i > 0:
            prev_adjusted = adjusted_results[-1]

            if adjusted.zone_start < prev_adjusted.zone_end:
                original_start = adjusted.zone_start
                adjusted.zone_start = prev_adjusted.zone_end
                adjusted.detection_metadata["zone_start_clamped"] = True
                adjusted.detection_metadata["original_zone_start"] = original_start

                logger.debug(
                    f"Corner {adjusted.corner_number}: clamped zone_start "
                    f"from {original_start:.0f}m to {prev_adjusted.zone_end:.0f}m"
                )

        # Recalculate delta_change for adjusted zone if zone is valid
        if adjusted.zone_end - adjusted.zone_start >= MIN_ZONE_LENGTH:
            adjusted.delta_change = get_delta_change_in_range(
                delta_result, adjusted.zone_start, adjusted.zone_end
            )
            # Recalculate cause with new boundaries
            adjusted.cause = determine_cause(
                delta_result, adjusted.zone_start, adjusted.zone_end, adjusted.detected_apex
            )
        else:
            # Zone is too small after clamping, keep original delta but mark as low confidence
            adjusted.confidence = "low"
            adjusted.detection_metadata["zone_too_small"] = True
            logger.warning(
                f"Corner {adjusted.corner_number}: zone too small after clamping "
                f"({adjusted.zone_end - adjusted.zone_start:.0f}m < {MIN_ZONE_LENGTH}m)"
            )

        adjusted_results.append(adjusted)

    # Restore original corner order
    adjusted_results.sort(key=lambda x: x.corner_number)

    return adjusted_results


def analyze_corners_v2(
    delta_result: DeltaResult,
    ref_distance: List[float],
    ref_brake: List[float],
    ref_speed: List[float],
    comp_distance: List[float],
    comp_brake: List[float],
    comp_speed: List[float],
    corners: List[CornerInput],
    circuit_id: str = "",
    track_length: Optional[float] = None
) -> CornerAnalysisResult:
    """
    Analyze all corners using v2 deceleration-based detection.

    This is the v2 entry point that provides more accurate corner analysis
    by using speed and deceleration data instead of relying solely on
    boolean brake signals.

    Args:
        delta_result: DeltaResult from calculate_scaled_delta
        ref_distance: Reference driver distance array
        ref_brake: Reference driver brake array
        ref_speed: Reference driver speed array
        comp_distance: Comparison driver distance array
        comp_brake: Comparison driver brake array
        comp_speed: Comparison driver speed array
        corners: List of CornerInput definitions
        circuit_id: Circuit identifier for config lookup
        track_length: Track length in meters (for lap breakdown calculation)

    Returns:
        CornerAnalysisResult with v2 corner analyses (including lap_breakdown if track_length provided)
    """
    logger.info(
        f"Analyzing {len(corners)} corners (v2) for "
        f"{delta_result.reference_driver} vs {delta_result.compare_driver}"
    )

    # Get circuit-specific configuration
    config = get_config_for_circuit(circuit_id)

    # Convert to numpy arrays
    ref_distance_arr = _safe_array(ref_distance)
    ref_brake_arr = _safe_array(ref_brake)
    ref_speed_arr = _safe_array(ref_speed)
    comp_distance_arr = _safe_array(comp_distance)
    comp_brake_arr = _safe_array(comp_brake)
    comp_speed_arr = _safe_array(comp_speed)

    # Analyze each corner (initial pass)
    corner_results: List[CornerResultV2] = []

    for corner in corners:
        result = analyze_single_corner_v2(
            delta_result=delta_result,
            ref_distance=ref_distance_arr,
            ref_brake=ref_brake_arr,
            ref_speed=ref_speed_arr,
            comp_distance=comp_distance_arr,
            comp_brake=comp_brake_arr,
            comp_speed=comp_speed_arr,
            corner=corner,
            config=config,
            delta_confidence=delta_result.confidence
        )
        corner_results.append(result)

    # Apply zone overlap prevention
    corner_results = _clamp_zones_to_prevent_overlap(corner_results, delta_result)

    # Log if any zones were clamped
    clamped_count = sum(
        1 for cr in corner_results
        if cr.detection_metadata.get("zone_clamped") or cr.detection_metadata.get("zone_start_clamped")
    )
    if clamped_count > 0:
        logger.info(f"Zone overlap prevention: {clamped_count} corners had zones adjusted")

    # Calculate totals
    total_delta = 0.0
    gaining = 0
    losing = 0

    for result in corner_results:
        total_delta += result.delta_change

        if result.delta_change > NEUTRAL_THRESHOLD:
            losing += 1
        elif result.delta_change < -NEUTRAL_THRESHOLD:
            gaining += 1

    # Validate corner delta sum against official gap
    official_gap = delta_result.official_gap
    if abs(total_delta) > abs(official_gap) * 2.5 and abs(official_gap) > 0.01:
        logger.warning(
            f"ANOMALY: Corner delta sum ({total_delta:+.3f}s) exceeds "
            f"2.5x official gap ({official_gap:+.3f}s). "
            f"Possible detection issues."
        )

    # Check for sign inversion
    if abs(official_gap) > 0.05:
        if (official_gap < 0 and total_delta > 0.1) or (official_gap > 0 and total_delta < -0.1):
            logger.warning(
                f"SIGN MISMATCH: Official gap is {official_gap:+.3f}s "
                f"but corner delta is {total_delta:+.3f}s"
            )

    logger.info(
        f"Corner analysis (v2) complete: "
        f"total_delta={total_delta:+.3f}s, "
        f"gaining={gaining}, losing={losing}"
    )

    # Calculate lap breakdown if track_length is provided
    lap_breakdown = None
    if track_length is not None and track_length > 0:
        try:
            lap_breakdown = calculate_lap_breakdown(
                delta_result=delta_result,
                corner_results=corner_results,
                track_length=track_length,
                comp_driver=delta_result.compare_driver
            )
            logger.info(
                f"Lap breakdown calculated: "
                f"corners={lap_breakdown.corner_total:+.3f}s, "
                f"straights={lap_breakdown.straight_total:+.3f}s, "
                f"reconciled={'✓' if lap_breakdown.reconciliation_valid else '✗'}"
            )
        except Exception as e:
            logger.warning(f"Failed to calculate lap breakdown: {e}")
            lap_breakdown = None

    return CornerAnalysisResult(
        reference_driver=delta_result.reference_driver,
        compare_driver=delta_result.compare_driver,
        corner_results=corner_results,
        total_delta_change=total_delta,
        corners_gaining=gaining,
        corners_losing=losing,
        lap_breakdown=lap_breakdown
    )


# ============================================================================
# Straight-Line Performance Integration (5th Dimension)
# ============================================================================

def _determine_straight_primary_factor(delta: float, length: float) -> str:
    """
    Determine primary factor for straight-line delta.

    Uses heuristics based on segment length and delta direction:
    - Long straights (>300m): aero/drag dependent
    - Short straights (<300m): traction dependent
    - Small deltas: balanced

    Args:
        delta: Delta change in seconds (negative = gaining time)
        length: Segment length in meters

    Returns:
        Primary factor string: 'aero_efficiency', 'traction', 'balanced', 'drag'
    """
    if length <= 0:
        return "balanced"

    delta_per_100m = abs(delta / length) * 100

    if delta_per_100m < 0.005:
        return "balanced"
    elif delta < 0:  # Gaining time
        return "aero_efficiency" if length > 300 else "traction"
    else:  # Losing time
        return "drag" if length > 300 else "traction"


def calculate_straight_segments(
    delta_result: DeltaResult,
    corner_results: List[CornerResult],
    track_length: float
) -> Tuple[List[StraightSegment], float]:
    """
    Calculate delta changes on straight sections between corners.

    Identifies track segments NOT covered by corner zones and calculates
    the delta change in each segment using the Phase 2 delta curve.

    Strategy:
    1. Sort corners by zone_start position
    2. Identify gaps between consecutive corner zones
    3. Calculate delta change in each gap using get_delta_change_in_range()
    4. Sum all gap deltas = straight_total

    Args:
        delta_result: Phase 2 delta analysis result
        corner_results: List of corner analysis results with zone boundaries
        track_length: Total track length in meters

    Returns:
        Tuple of (list of straight segments, total straight delta)

    Example:
        >>> segments, straight_total = calculate_straight_segments(
        ...     delta_result, corner_results, track_length=5543
        ... )
        >>> print(f"Straight total: {straight_total:+.3f}s")
    """
    if track_length <= 0:
        logger.warning("Invalid track_length, returning empty segments")
        return [], 0.0

    if not corner_results:
        # No corners = entire track is "straight"
        total_delta = get_delta_change_in_range(delta_result, 0, track_length)
        return [StraightSegment(
            segment_number=1,
            name="Full Track",
            start_distance=0,
            end_distance=track_length,
            delta_change=total_delta,
            length=track_length,
            primary_factor="balanced"
        )], total_delta

    # Sort corners by track position
    sorted_corners = sorted(corner_results, key=lambda c: c.zone_start)
    straight_segments = []
    segment_num = 1

    MIN_SEGMENT_LENGTH = 10  # Minimum 10m to count as a straight segment

    # Gap before first corner (start/finish to T1)
    first_corner = sorted_corners[0]
    if first_corner.zone_start > MIN_SEGMENT_LENGTH:
        seg_start = 0
        seg_end = first_corner.zone_start
        delta = get_delta_change_in_range(delta_result, seg_start, seg_end)
        straight_segments.append(StraightSegment(
            segment_number=segment_num,
            name=f"Start -> T{first_corner.corner_number}",
            start_distance=seg_start,
            end_distance=seg_end,
            delta_change=delta,
            length=seg_end - seg_start,
            primary_factor=_determine_straight_primary_factor(delta, seg_end - seg_start)
        ))
        segment_num += 1

    # Gaps between consecutive corners
    for i in range(len(sorted_corners) - 1):
        current = sorted_corners[i]
        next_corner = sorted_corners[i + 1]

        seg_start = current.zone_end
        seg_end = next_corner.zone_start

        if seg_end > seg_start + MIN_SEGMENT_LENGTH:
            delta = get_delta_change_in_range(delta_result, seg_start, seg_end)
            straight_segments.append(StraightSegment(
                segment_number=segment_num,
                name=f"T{current.corner_number} -> T{next_corner.corner_number}",
                start_distance=seg_start,
                end_distance=seg_end,
                delta_change=delta,
                length=seg_end - seg_start,
                primary_factor=_determine_straight_primary_factor(delta, seg_end - seg_start)
            ))
            segment_num += 1

    # Gap after last corner (final corner to finish)
    last_corner = sorted_corners[-1]
    if last_corner.zone_end < track_length - MIN_SEGMENT_LENGTH:
        seg_start = last_corner.zone_end
        seg_end = track_length
        delta = get_delta_change_in_range(delta_result, seg_start, seg_end)
        straight_segments.append(StraightSegment(
            segment_number=segment_num,
            name=f"T{last_corner.corner_number} -> Finish",
            start_distance=seg_start,
            end_distance=seg_end,
            delta_change=delta,
            length=seg_end - seg_start,
            primary_factor=_determine_straight_primary_factor(delta, seg_end - seg_start)
        ))

    # Calculate total
    straight_total = sum(seg.delta_change for seg in straight_segments)

    logger.debug(
        f"Calculated {len(straight_segments)} straight segments, "
        f"total_delta={straight_total:+.3f}s"
    )

    return straight_segments, straight_total


def _generate_lap_breakdown_insight(
    corner_total: float,
    straight_total: float,
    official_gap: float,
    track_coverage: float,
    comp_driver: str
) -> str:
    """
    Generate educational insight text explaining the lap breakdown.

    Uses template-based generation (anti-hallucination pattern) to create
    human-readable text that explains why corner totals don't match official gaps.

    Args:
        corner_total: Sum of corner deltas (seconds)
        straight_total: Sum of straight deltas (seconds)
        official_gap: Official timing gap (seconds)
        track_coverage: Fraction of track covered by corners (0-1)
        comp_driver: Comparison driver code

    Returns:
        Educational insight text
    """
    coverage_pct = track_coverage * 100
    straight_pct = 100 - coverage_pct
    driver = comp_driver or "Driver"

    if corner_total > 0 and straight_total < 0:
        # Lost in corners, gained on straights
        if abs(corner_total) > abs(straight_total):
            return (
                f"Corner zones cover {coverage_pct:.1f}% of the circuit. "
                f"{driver} lost {corner_total:+.3f}s in corners but recovered "
                f"{abs(straight_total):.3f}s on straights. The cornering deficit "
                f"was larger, resulting in a net gap of {official_gap:+.3f}s."
            )
        else:
            return (
                f"Corner zones cover {coverage_pct:.1f}% of the circuit. "
                f"{driver} lost {corner_total:+.3f}s in corners but nearly "
                f"compensated with {abs(straight_total):.3f}s gained on straights. "
                f"Net gap: {official_gap:+.3f}s."
            )
    elif corner_total < 0 and straight_total > 0:
        # Gained in corners, lost on straights
        return (
            f"Corner zones cover {coverage_pct:.1f}% of the circuit. "
            f"{driver} gained {abs(corner_total):.3f}s in corners but lost "
            f"{straight_total:+.3f}s on straights. Net result: {official_gap:+.3f}s."
        )
    elif corner_total > 0 and straight_total > 0:
        # Lost everywhere
        dominant = "corners" if corner_total > straight_total else "straights"
        return (
            f"Corner zones cover {coverage_pct:.1f}% of the circuit. "
            f"{driver} lost time in both corners ({corner_total:+.3f}s) and "
            f"straights ({straight_total:+.3f}s), with {dominant} being the larger deficit. "
            f"Total: {official_gap:+.3f}s."
        )
    elif corner_total < 0 and straight_total < 0:
        # Gained everywhere
        dominant = "corners" if abs(corner_total) > abs(straight_total) else "straights"
        return (
            f"Corner zones cover {coverage_pct:.1f}% of the circuit. "
            f"{driver} gained time in both corners ({corner_total:+.3f}s) and "
            f"straights ({straight_total:+.3f}s), with {dominant} contributing more. "
            f"Total advantage: {official_gap:+.3f}s."
        )
    else:
        # Edge case: one of them is zero
        return (
            f"Corner zones cover {coverage_pct:.1f}% of the circuit. "
            f"Corner delta: {corner_total:+.3f}s, Straight delta: {straight_total:+.3f}s. "
            f"Net result: {official_gap:+.3f}s."
        )


def calculate_lap_breakdown(
    delta_result: DeltaResult,
    corner_results: List[CornerResult],
    track_length: float,
    comp_driver: str = ""
) -> LapBreakdown:
    """
    Calculate complete lap breakdown showing corner and straight contributions.

    This is the key function for straight-line integration. It ensures mathematical
    closure: corner_total + straight_total = official_gap (within 5ms tolerance).

    The breakdown transforms user confusion ("why don't these numbers match?")
    into user understanding ("corners + straights = official gap").

    Args:
        delta_result: Phase 2 delta analysis result
        corner_results: List of corner analysis results
        track_length: Total track length in meters
        comp_driver: Comparison driver code (for insight text)

    Returns:
        LapBreakdown with corner total, straight total, and reconciliation check

    Example:
        >>> breakdown = calculate_lap_breakdown(delta_result, corners, 5543, "LEC")
        >>> print(f"Corners: {breakdown.corner_total:+.3f}s")
        >>> print(f"Straights: {breakdown.straight_total:+.3f}s")
        >>> print(f"Official: {breakdown.official_gap:+.3f}s")
        >>> print(f"Valid: {breakdown.reconciliation_valid}")
    """
    if track_length <= 0:
        logger.warning("Invalid track_length for lap breakdown")
        return LapBreakdown(
            corner_total=0.0,
            straight_total=0.0,
            official_gap=delta_result.official_gap,
            track_coverage=0.0,
            straight_segments=[],
            reconciliation_valid=False,
            reconciliation_error=abs(delta_result.official_gap),
            insight_text="Unable to calculate lap breakdown (invalid track length)."
        )

    # Calculate corner total
    corner_total = sum(cr.delta_change for cr in corner_results)

    # Calculate corner distance coverage
    corner_distance = sum(cr.zone_end - cr.zone_start for cr in corner_results)
    track_coverage = corner_distance / track_length

    # Calculate straight segments
    straight_segments, straight_total = calculate_straight_segments(
        delta_result, corner_results, track_length
    )

    # Reconciliation check
    calculated_total = corner_total + straight_total
    reconciliation_error = abs(calculated_total - delta_result.official_gap)
    reconciliation_valid = reconciliation_error < 0.005  # 5ms tolerance

    if not reconciliation_valid:
        logger.warning(
            f"Lap breakdown reconciliation failed: "
            f"corners ({corner_total:+.3f}s) + straights ({straight_total:+.3f}s) = "
            f"{calculated_total:+.3f}s, but official gap is {delta_result.official_gap:+.3f}s "
            f"(error: {reconciliation_error:.3f}s)"
        )

    # Generate insight text
    insight_text = _generate_lap_breakdown_insight(
        corner_total=corner_total,
        straight_total=straight_total,
        official_gap=delta_result.official_gap,
        track_coverage=track_coverage,
        comp_driver=comp_driver
    )

    logger.info(
        f"Lap breakdown: corners={corner_total:+.3f}s, straights={straight_total:+.3f}s, "
        f"official={delta_result.official_gap:+.3f}s, coverage={track_coverage:.1%}, "
        f"reconciled={reconciliation_valid}"
    )

    return LapBreakdown(
        corner_total=corner_total,
        straight_total=straight_total,
        official_gap=delta_result.official_gap,
        track_coverage=track_coverage,
        straight_segments=straight_segments,
        reconciliation_valid=reconciliation_valid,
        reconciliation_error=reconciliation_error,
        insight_text=insight_text
    )
