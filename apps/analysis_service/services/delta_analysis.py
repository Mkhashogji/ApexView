"""
Delta Analysis Module

Provides accurate time delta calculations between drivers by:
1. Computing raw telemetry-based delta over distance
2. Scaling to match official timing differences
3. Generating distance-indexed delta traces for visualization

The scaling approach ensures that:
- Delta trace shape reflects WHERE time is gained/lost (from telemetry)
- Final delta magnitude matches OFFICIAL timing (ground truth)

This module is the foundation for corner analysis (Phase 3) which uses
get_delta_change_in_range() to determine time gained/lost at each corner.

Usage:
    from services.delta_analysis import calculate_scaled_delta, DeltaResult
    
    result = calculate_scaled_delta(
        ref_telemetry={'distance': [...], 'speed': [...]},
        comp_telemetry={'distance': [...], 'speed': [...]},
        ref_official_time=90.591,
        comp_official_time=90.791,
        ref_driver='VER',
        comp_driver='NOR'
    )
    
    # result.delta[-1] == 0.200 (matches official gap)
"""

import logging

import numpy as np
from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass

logger = logging.getLogger("analysis_service.delta_analysis")


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class DeltaResult:
    """
    Result of delta analysis between two drivers.
    
    Attributes:
        reference_driver: Driver code for reference lap (e.g., 'VER')
        compare_driver: Driver code for comparison lap (e.g., 'NOR')
        distance: Distance points in meters (common grid)
        delta: Scaled delta in seconds (positive = compare is slower)
        raw_delta: Unscaled telemetry delta before scaling
        official_gap: Official timing difference (ground truth)
        scaling_factor: Factor applied to raw delta (official_gap / telemetry_gap)
        telemetry_gap: Raw telemetry-derived gap before scaling
        confidence: Confidence score (0-1) based on scaling factor deviation
    """
    reference_driver: str
    compare_driver: str
    distance: List[float]
    delta: List[float]  # Scaled delta (positive = compare slower)
    raw_delta: List[float]  # Unscaled telemetry delta
    official_gap: float  # Official timing difference
    scaling_factor: float  # Factor applied to raw delta
    telemetry_gap: float  # Raw telemetry-derived gap
    confidence: float  # Confidence in the calculation (0-1)
    # --- G0 grid metadata (Honest Acquisition) ---------------------------
    # Bookkeeping for the alignment-vs-resolution distinction: the 1000-point
    # grid provides spatial co-location, NOT added temporal resolution. These
    # record how many real samples back the grid per driver. Consumed by
    # later gates; never serialized into API responses (main.py response
    # assembly is field-explicit and does not read them).
    ref_sample_count: Optional[int] = None
    comp_sample_count: Optional[int] = None
    ref_median_spacing_m: Optional[float] = None
    comp_median_spacing_m: Optional[float] = None


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


def _median_sample_spacing(distance: np.ndarray) -> Optional[float]:
    """
    Median spacing (metres) between consecutive real samples.

    G0 grid metadata: with the native acquisition path, `distance` contains
    only real car-data measurements, so this is the true granularity floor
    behind the 1000-point grid.
    """
    if distance is None or len(distance) < 2:
        return None
    diffs = np.diff(np.asarray(distance, dtype=float))
    diffs = diffs[diffs > 0]
    if len(diffs) == 0:
        return None
    return float(np.median(diffs))


def align_telemetry_to_distance(
    distance: np.ndarray,
    values: np.ndarray,
    target_distance: np.ndarray
) -> np.ndarray:
    """
    Interpolate telemetry values to target distance points.
    
    This allows comparing telemetry from two drivers on a common distance grid,
    even if their original sampling points differ.
    
    Args:
        distance: Original distance array (meters)
        values: Original value array (speed, throttle, etc.)
        target_distance: Target distance points for interpolation
        
    Returns:
        Interpolated values at target distance points
        
    Example:
        >>> ref_speed_aligned = align_telemetry_to_distance(
        ...     ref_distance, ref_speed, common_distance
        ... )
    """
    return np.interp(target_distance, distance, values)


# ============================================================================
# Core Delta Calculation Functions
# ============================================================================

def calculate_raw_delta(
    ref_distance: np.ndarray,
    ref_speed: np.ndarray,
    comp_distance: np.ndarray,
    comp_speed: np.ndarray,
    num_points: int = 1000
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate raw time delta from telemetry speed traces.
    
    Uses the physics relationship: time = distance / speed
    Integrates small distance segments to compute cumulative time.
    
    This produces a delta trace that shows WHERE time is gained/lost,
    but the magnitude may not match official timing due to interpolation errors.
    
    Args:
        ref_distance: Reference driver distance array (meters)
        ref_speed: Reference driver speed array (km/h)
        comp_distance: Comparison driver distance array (meters)
        comp_speed: Comparison driver speed array (km/h)
        num_points: Number of interpolation points (default 1000)
        
    Returns:
        Tuple of (common_distance, raw_delta_seconds)
        - common_distance: Shared distance grid
        - raw_delta_seconds: Time delta at each point (positive = compare slower)
        
    Example:
        >>> common_dist, delta = calculate_raw_delta(
        ...     ref_distance, ref_speed, comp_distance, comp_speed
        ... )
        >>> print(f"Final raw delta: {delta[-1]:.3f}s")
    """
    # Safely convert inputs
    ref_distance = _safe_array(ref_distance)
    ref_speed = _safe_array(ref_speed, default_value=100.0)
    comp_distance = _safe_array(comp_distance)
    comp_speed = _safe_array(comp_speed, default_value=100.0)
    
    # Find common distance range (overlap between both laps)
    min_dist = max(ref_distance.min(), comp_distance.min())
    max_dist = min(ref_distance.max(), comp_distance.max())
    
    # Handle edge case where laps don't overlap
    if max_dist <= min_dist:
        logger.warning("No distance overlap between laps, using reference range")
        min_dist = ref_distance.min()
        max_dist = ref_distance.max()
    
    # Create common distance grid
    common_distance = np.linspace(min_dist, max_dist, num_points)
    
    # Interpolate speeds to common distance grid
    ref_speed_interp = align_telemetry_to_distance(ref_distance, ref_speed, common_distance)
    comp_speed_interp = align_telemetry_to_distance(comp_distance, comp_speed, common_distance)
    
    # Convert km/h to m/s for physics calculation
    ref_speed_ms = ref_speed_interp / 3.6
    comp_speed_ms = comp_speed_interp / 3.6
    
    # Avoid division by zero (minimum speed of 0.1 m/s ≈ 0.36 km/h)
    ref_speed_ms = np.maximum(ref_speed_ms, 0.1)
    comp_speed_ms = np.maximum(comp_speed_ms, 0.1)
    
    # Calculate time for each distance segment
    # time = distance / speed
    distance_segments = np.diff(common_distance, prepend=common_distance[0])
    
    # Cumulative time for each driver
    ref_times = np.cumsum(distance_segments / ref_speed_ms)
    comp_times = np.cumsum(distance_segments / comp_speed_ms)
    
    # Delta is comparison minus reference
    # Positive = compare is slower (behind reference)
    # Negative = compare is faster (ahead of reference)
    raw_delta = comp_times - ref_times
    
    logger.debug(
        f"Raw delta calculation: {len(common_distance)} points, "
        f"range {min_dist:.0f}-{max_dist:.0f}m, "
        f"final delta {raw_delta[-1]:.3f}s"
    )
    
    return common_distance, raw_delta


# ============================================================================
# Three-Tier Delta Calculation Methods
# ============================================================================

def _calculate_with_relative_distance(
    ref_relative_distance: np.ndarray,
    ref_time: np.ndarray,
    comp_relative_distance: np.ndarray,
    comp_time: np.ndarray,
    ref_official_time: float,
    comp_official_time: float,
    ref_distance: np.ndarray,
    num_points: int = 1000
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Tier 1 (PREFERRED): Calculate delta using RelativeDistance + Time scaling.

    This method:
    1. Uses RelativeDistance (0-1) for position alignment
    2. Scales time to match official lap time BEFORE delta calculation
    3. Results in scale_factor = 1.0 and confidence >= 0.9

    Key insight: By pre-scaling time to official lap time, the final delta
    automatically equals the official gap - no post-scaling needed!

    Args:
        ref_relative_distance: Reference driver RelativeDistance (0-1)
        ref_time: Reference driver elapsed time (seconds)
        comp_relative_distance: Comparison driver RelativeDistance (0-1)
        comp_time: Comparison driver elapsed time (seconds)
        ref_official_time: Reference driver official lap time
        comp_official_time: Comparison driver official lap time
        ref_distance: Reference driver absolute distance (for output conversion)
        num_points: Number of interpolation points

    Returns:
        Tuple of (common_distance, delta, confidence)
    """
    logger.info("Using PREFERRED method: RelativeDistance + Time scaling (Tier 1)")

    # Normalize time to start at 0
    ref_lap_relative = ref_time - ref_time[0]
    comp_lap_relative = comp_time - comp_time[0]

    # Scale time to EXACTLY match official lap time
    ref_telemetry_span = ref_lap_relative[-1]
    comp_telemetry_span = comp_lap_relative[-1]

    if ref_telemetry_span > 0:
        ref_time_scale = ref_official_time / ref_telemetry_span
    else:
        ref_time_scale = 1.0
        logger.warning("Reference telemetry span is zero, using scale=1.0")

    if comp_telemetry_span > 0:
        comp_time_scale = comp_official_time / comp_telemetry_span
    else:
        comp_time_scale = 1.0
        logger.warning("Comparison telemetry span is zero, using scale=1.0")

    ref_time_scaled = ref_lap_relative * ref_time_scale
    comp_time_scaled = comp_lap_relative * comp_time_scale

    # Create common RelativeDistance grid (0 to 1, full lap)
    common_rel_dist = np.linspace(0, 1, num_points)

    # Interpolate scaled times to common RelativeDistance grid
    ref_time_at_pos = np.interp(common_rel_dist, ref_relative_distance, ref_time_scaled)
    comp_time_at_pos = np.interp(common_rel_dist, comp_relative_distance, comp_time_scaled)

    # Calculate delta - delta[-1] now EXACTLY equals official_gap
    delta = comp_time_at_pos - ref_time_at_pos

    # Convert RelativeDistance back to meters for display
    track_length = ref_distance[-1] - ref_distance[0]
    common_distance = common_rel_dist * track_length

    # Calculate confidence based on time scale factors
    # Scale should be close to 1.0 if telemetry quality is good
    avg_scale = (ref_time_scale + comp_time_scale) / 2
    scale_deviation = abs(avg_scale - 1.0)

    if scale_deviation < 0.1:
        confidence = 1.0  # Excellent telemetry quality
    elif scale_deviation < 0.2:
        confidence = 0.95
    elif scale_deviation < 0.3:
        confidence = 0.9
    else:
        confidence = 0.85

    logger.info(
        f"Tier 1 complete: ref_scale={ref_time_scale:.4f}, comp_scale={comp_time_scale:.4f}, "
        f"confidence={confidence:.2f}"
    )

    return common_distance, delta, confidence


def _calculate_with_time_only(
    ref_distance: np.ndarray,
    ref_time: np.ndarray,
    comp_distance: np.ndarray,
    comp_time: np.ndarray,
    ref_official_time: float,
    comp_official_time: float,
    num_points: int = 1000
) -> Tuple[np.ndarray, np.ndarray, float]:
    """
    Tier 2 (FALLBACK): Calculate delta using Time column with distance alignment.

    Less accurate than Tier 1 due to distance sampling differences, but
    still better than speed integration because it uses direct time data.

    Args:
        ref_distance: Reference driver distance array (meters)
        ref_time: Reference driver elapsed time (seconds)
        comp_distance: Comparison driver distance array (meters)
        comp_time: Comparison driver elapsed time (seconds)
        ref_official_time: Reference driver official lap time
        comp_official_time: Comparison driver official lap time
        num_points: Number of interpolation points

    Returns:
        Tuple of (common_distance, delta, confidence)
    """
    logger.info("Using FALLBACK method: Time with distance alignment (Tier 2)")

    # Normalize time to start at 0
    ref_lap_relative = ref_time - ref_time[0]
    comp_lap_relative = comp_time - comp_time[0]

    # Scale time to match official
    ref_time_scale = ref_official_time / ref_lap_relative[-1] if ref_lap_relative[-1] > 0 else 1.0
    comp_time_scale = comp_official_time / comp_lap_relative[-1] if comp_lap_relative[-1] > 0 else 1.0

    ref_time_scaled = ref_lap_relative * ref_time_scale
    comp_time_scaled = comp_lap_relative * comp_time_scale

    # Find common distance range
    min_dist = max(ref_distance.min(), comp_distance.min())
    max_dist = min(ref_distance.max(), comp_distance.max())

    if max_dist <= min_dist:
        min_dist = ref_distance.min()
        max_dist = ref_distance.max()

    common_distance = np.linspace(min_dist, max_dist, num_points)

    # Interpolate times to common distance grid
    ref_time_at_dist = np.interp(common_distance, ref_distance, ref_time_scaled)
    comp_time_at_dist = np.interp(common_distance, comp_distance, comp_time_scaled)

    delta = comp_time_at_dist - ref_time_at_dist

    # Lower confidence than Tier 1 due to distance alignment issues
    confidence = 0.8

    logger.info(f"Tier 2 complete: confidence={confidence:.2f}")

    return common_distance, delta, confidence


def calculate_scaled_delta(
    ref_telemetry: Dict[str, List[float]],
    comp_telemetry: Dict[str, List[float]],
    ref_official_time: float,
    comp_official_time: float,
    ref_driver: str,
    comp_driver: str,
    num_points: int = 1000
) -> DeltaResult:
    """
    Calculate delta with three-tier algorithm for maximum accuracy.

    Three-Tier Algorithm:
    - Tier 1 (PREFERRED): RelativeDistance + Time scaling
        * Uses RelativeDistance (0-1) for position alignment
        * Pre-scales time to match official lap time
        * Result: scaling_factor = 1.0, confidence >= 0.9

    - Tier 2 (FALLBACK): Time column with distance alignment
        * Uses Time column but distance-based alignment
        * Result: scaling_factor = 1.0, confidence ~ 0.8

    - Tier 3 (FALLBACK): Speed integration (legacy)
        * Uses speed to derive time
        * Result: scaling_factor varies, confidence <= 0.6

    The result is a delta trace where:
    - The SHAPE shows where time is gained/lost (from telemetry)
    - The MAGNITUDE matches official timing (ground truth)
    - delta[-1] == official_gap (always, by design)

    Args:
        ref_telemetry: Reference driver telemetry dict with keys:
            - 'distance': List[float] (required)
            - 'speed': List[float] (required)
            - 'relative_distance': List[float] (optional, enables Tier 1)
            - 'time': List[float] (optional, enables Tier 1/2)
        comp_telemetry: Comparison driver telemetry dict with same keys
        ref_official_time: Reference driver official lap time (seconds)
        comp_official_time: Comparison driver official lap time (seconds)
        ref_driver: Reference driver code (e.g., 'VER')
        comp_driver: Comparison driver code (e.g., 'NOR')
        num_points: Number of points for delta trace (default 1000)

    Returns:
        DeltaResult with scaled delta and metadata

    Example:
        >>> result = calculate_scaled_delta(
        ...     ref_telemetry={'distance': [...], 'speed': [...], 'relative_distance': [...], 'time': [...]},
        ...     comp_telemetry={'distance': [...], 'speed': [...], 'relative_distance': [...], 'time': [...]},
        ...     ref_official_time=90.591,
        ...     comp_official_time=90.791,
        ...     ref_driver='VER',
        ...     comp_driver='NOR'
        ... )
        >>> assert result.scaling_factor == 1.0  # Tier 1 guarantees this
        >>> print(f"Confidence: {result.confidence:.2f}")  # Should be >= 0.9
    """
    logger.info(f"Calculating scaled delta: {ref_driver} vs {comp_driver}")

    # Extract required arrays from telemetry dicts
    ref_distance = np.array(ref_telemetry.get('distance', []))
    ref_speed = np.array(ref_telemetry.get('speed', []))
    comp_distance = np.array(comp_telemetry.get('distance', []))
    comp_speed = np.array(comp_telemetry.get('speed', []))

    # Extract optional Tier 1/2 fields
    ref_relative_distance = ref_telemetry.get('relative_distance')
    ref_time = ref_telemetry.get('time')
    comp_relative_distance = comp_telemetry.get('relative_distance')
    comp_time = comp_telemetry.get('time')

    # Convert to numpy arrays if present
    if ref_relative_distance is not None:
        ref_relative_distance = np.array(ref_relative_distance)
    if ref_time is not None:
        ref_time = np.array(ref_time)
    if comp_relative_distance is not None:
        comp_relative_distance = np.array(comp_relative_distance)
    if comp_time is not None:
        comp_time = np.array(comp_time)

    # Validate basic inputs
    if len(ref_distance) == 0 or len(ref_speed) == 0:
        logger.error(f"Empty telemetry for reference driver {ref_driver}")
        return DeltaResult(
            reference_driver=ref_driver,
            compare_driver=comp_driver,
            distance=[0.0],
            delta=[comp_official_time - ref_official_time],
            raw_delta=[0.0],
            official_gap=comp_official_time - ref_official_time,
            scaling_factor=1.0,
            telemetry_gap=0.0,
            confidence=0.0
        )

    official_gap = comp_official_time - ref_official_time

    # G0 grid metadata — real-sample counts and spacing behind the grid
    # (see DeltaResult docstring; internal, not serialized).
    _grid_meta = dict(
        ref_sample_count=int(len(ref_distance)),
        comp_sample_count=int(len(comp_distance)),
        ref_median_spacing_m=_median_sample_spacing(ref_distance),
        comp_median_spacing_m=_median_sample_spacing(comp_distance),
    )

    # Determine which tier to use
    can_use_tier1 = (
        ref_relative_distance is not None and len(ref_relative_distance) > 0 and
        ref_time is not None and len(ref_time) > 0 and
        comp_relative_distance is not None and len(comp_relative_distance) > 0 and
        comp_time is not None and len(comp_time) > 0
    )

    can_use_tier2 = (
        ref_time is not None and len(ref_time) > 0 and
        comp_time is not None and len(comp_time) > 0
    )

    # =========================================================================
    # TIER 1: RelativeDistance + Time (PREFERRED)
    # =========================================================================
    if can_use_tier1:
        common_distance, delta, confidence = _calculate_with_relative_distance(
            ref_relative_distance, ref_time,
            comp_relative_distance, comp_time,
            ref_official_time, comp_official_time,
            ref_distance,
            num_points
        )

        return DeltaResult(
            reference_driver=ref_driver,
            compare_driver=comp_driver,
            distance=common_distance.tolist(),
            delta=delta.tolist(),
            raw_delta=delta.tolist(),  # No scaling needed, so raw = scaled
            official_gap=official_gap,
            scaling_factor=1.0,  # Always 1.0 with Tier 1
            telemetry_gap=delta[-1],  # Should match official_gap
            confidence=confidence,
            **_grid_meta
        )

    # =========================================================================
    # TIER 2: Time with distance alignment (FALLBACK)
    # =========================================================================
    elif can_use_tier2:
        common_distance, delta, confidence = _calculate_with_time_only(
            ref_distance, ref_time,
            comp_distance, comp_time,
            ref_official_time, comp_official_time,
            num_points
        )

        return DeltaResult(
            reference_driver=ref_driver,
            compare_driver=comp_driver,
            distance=common_distance.tolist(),
            delta=delta.tolist(),
            raw_delta=delta.tolist(),
            official_gap=official_gap,
            scaling_factor=1.0,
            telemetry_gap=delta[-1],
            confidence=confidence,
            **_grid_meta
        )

    # =========================================================================
    # TIER 3: Speed integration (LEGACY FALLBACK)
    # =========================================================================
    else:
        logger.warning("Using FALLBACK method: Speed integration (Tier 3)")

        # Use existing calculate_raw_delta function
        common_distance, raw_delta = calculate_raw_delta(
            ref_distance, ref_speed,
            comp_distance, comp_speed,
            num_points
        )

        # Raw telemetry gap (final value of raw delta)
        telemetry_gap = raw_delta[-1] if len(raw_delta) > 0 else 0.0

        # Calculate scaling factor
        if abs(telemetry_gap) > 0.001:
            scaling_factor = official_gap / telemetry_gap
        else:
            scaling_factor = 1.0
            logger.warning(f"Telemetry gap near zero ({telemetry_gap:.4f}s), using scaling=1.0")

        # Apply sanity bounds
        SCALING_BOUND = 5.0
        if abs(scaling_factor) > SCALING_BOUND:
            logger.warning(
                f"Extreme scaling factor {scaling_factor:.2f} detected. "
                f"Official gap: {official_gap:.3f}s, Telemetry gap: {telemetry_gap:.3f}s. "
                f"Clamping to +/-{SCALING_BOUND}"
            )
            scaling_factor = np.clip(scaling_factor, -SCALING_BOUND, SCALING_BOUND)

        # Handle sign mismatch
        if (telemetry_gap > 0 and official_gap < 0) or (telemetry_gap < 0 and official_gap > 0):
            if abs(telemetry_gap) > 0.050:
                logger.warning(
                    f"Sign mismatch: telemetry_gap={telemetry_gap:.3f}s, "
                    f"official_gap={official_gap:.3f}s. Using official as truth."
                )

        # Scale the delta
        scaled_delta = raw_delta * scaling_factor

        # Calculate confidence (lower for Tier 3)
        scaling_deviation = abs(scaling_factor - 1.0)
        if scaling_deviation < 0.2:
            confidence = 0.6  # Cap at 0.6 for Tier 3
        elif scaling_deviation < 0.5:
            confidence = 0.5
        elif scaling_deviation < 1.0:
            confidence = 0.4
        elif scaling_deviation < 2.0:
            confidence = 0.35
        else:
            confidence = 0.3

        logger.info(
            f"Tier 3 complete: official_gap={official_gap:.3f}s, "
            f"telemetry_gap={telemetry_gap:.3f}s, scaling={scaling_factor:.3f}, "
            f"confidence={confidence:.2f}"
        )

        return DeltaResult(
            reference_driver=ref_driver,
            compare_driver=comp_driver,
            distance=common_distance.tolist(),
            delta=scaled_delta.tolist(),
            raw_delta=raw_delta.tolist(),
            official_gap=official_gap,
            scaling_factor=scaling_factor,
            telemetry_gap=telemetry_gap,
            confidence=confidence,
            **_grid_meta
        )


# ============================================================================
# Query Functions (Used by Phase 3: Corner Analysis)
# ============================================================================

def get_delta_at_distance(delta_result: DeltaResult, target_distance: float) -> float:
    """
    Get the delta value at a specific track distance.
    
    Useful for finding delta at corner entry/exit points.
    Uses linear interpolation if target_distance falls between grid points.
    
    Args:
        delta_result: DeltaResult from calculate_scaled_delta
        target_distance: Distance in meters to query
        
    Returns:
        Delta in seconds at the target distance
        
    Example:
        >>> # Get delta at Turn 3 entry (2500m)
        >>> delta_at_t3 = get_delta_at_distance(result, 2500.0)
        >>> print(f"Delta at Turn 3: {delta_at_t3:+.3f}s")
    """
    distance = np.array(delta_result.distance)
    delta = np.array(delta_result.delta)
    
    # Handle edge cases
    if len(distance) == 0 or len(delta) == 0:
        logger.warning("Empty delta result, returning 0")
        return 0.0
    
    # Clamp to valid range
    target_distance = np.clip(target_distance, distance.min(), distance.max())
    
    # Interpolate to find delta at target distance
    return float(np.interp(target_distance, distance, delta))


def get_delta_change_in_range(
    delta_result: DeltaResult,
    start_distance: float,
    end_distance: float
) -> float:
    """
    Get the delta change (time gained/lost) within a distance range.
    
    This is the key function for Phase 3: Corner Analysis.
    It calculates how much time was gained or lost between two track positions,
    which corresponds to performance through a specific corner or sector.
    
    Args:
        delta_result: DeltaResult from calculate_scaled_delta
        start_distance: Start of range in meters
        end_distance: End of range in meters
        
    Returns:
        Delta change in seconds
        - Positive = compare driver lost time in this range
        - Negative = compare driver gained time in this range
        
    Example:
        >>> # Calculate time lost through Turn 3 (2400m to 2800m)
        >>> time_lost = get_delta_change_in_range(result, 2400.0, 2800.0)
        >>> print(f"Time {'lost' if time_lost > 0 else 'gained'}: {abs(time_lost):.3f}s")
    """
    delta_at_start = get_delta_at_distance(delta_result, start_distance)
    delta_at_end = get_delta_at_distance(delta_result, end_distance)
    
    delta_change = delta_at_end - delta_at_start
    
    logger.debug(
        f"Delta change {start_distance:.0f}m-{end_distance:.0f}m: "
        f"{delta_at_start:.3f}s -> {delta_at_end:.3f}s = {delta_change:+.3f}s"
    )
    
    return delta_change


def get_max_delta_point(delta_result: DeltaResult) -> Tuple[float, float]:
    """
    Find the track position where the maximum delta occurs.
    
    Useful for identifying the most significant point of difference.
    
    Args:
        delta_result: DeltaResult from calculate_scaled_delta
        
    Returns:
        Tuple of (distance_meters, delta_seconds) at max delta
    """
    distance = np.array(delta_result.distance)
    delta = np.array(delta_result.delta)
    
    if len(delta) == 0:
        return 0.0, 0.0
    
    # Find maximum absolute delta
    max_idx = np.argmax(np.abs(delta))
    
    return float(distance[max_idx]), float(delta[max_idx])


def get_min_delta_point(delta_result: DeltaResult) -> Tuple[float, float]:
    """
    Find the track position where the minimum (most negative) delta occurs.
    
    This is where the comparison driver was closest to (or ahead of) reference.
    
    Args:
        delta_result: DeltaResult from calculate_scaled_delta
        
    Returns:
        Tuple of (distance_meters, delta_seconds) at min delta
    """
    distance = np.array(delta_result.distance)
    delta = np.array(delta_result.delta)
    
    if len(delta) == 0:
        return 0.0, 0.0
    
    min_idx = np.argmin(delta)
    
    return float(distance[min_idx]), float(delta[min_idx])
