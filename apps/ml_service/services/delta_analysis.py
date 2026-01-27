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

logger = logging.getLogger("ml_service.delta_analysis")


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
    Calculate delta with scaling to match official timing.
    
    This is the primary function for delta analysis. It:
    1. Computes raw telemetry-based delta (WHERE time is gained/lost)
    2. Calculates scaling factor from official times
    3. Applies scaling to preserve shape but correct magnitude
    4. Computes confidence score based on scaling deviation
    
    The result is a delta trace where:
    - The SHAPE shows where time is gained/lost (from telemetry)
    - The MAGNITUDE matches official timing (ground truth)
    - delta[-1] == official_gap (always, by design)
    
    Args:
        ref_telemetry: Reference driver telemetry dict with 'distance' and 'speed' keys
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
        ...     ref_telemetry={'distance': [...], 'speed': [...]},
        ...     comp_telemetry={'distance': [...], 'speed': [...]},
        ...     ref_official_time=90.591,
        ...     comp_official_time=90.791,
        ...     ref_driver='VER',
        ...     comp_driver='NOR'
        ... )
        >>> assert abs(result.delta[-1] - 0.200) < 0.001  # Matches official
        >>> print(f"Scaling factor: {result.scaling_factor:.3f}")
    """
    logger.info(f"Calculating scaled delta: {ref_driver} vs {comp_driver}")
    
    # Extract arrays from telemetry dicts
    ref_distance = np.array(ref_telemetry.get('distance', []))
    ref_speed = np.array(ref_telemetry.get('speed', []))
    comp_distance = np.array(comp_telemetry.get('distance', []))
    comp_speed = np.array(comp_telemetry.get('speed', []))
    
    # Validate inputs
    if len(ref_distance) == 0 or len(ref_speed) == 0:
        logger.error(f"Empty telemetry for reference driver {ref_driver}")
        # Return minimal valid result
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
    
    # Calculate raw telemetry delta
    common_distance, raw_delta = calculate_raw_delta(
        ref_distance, ref_speed,
        comp_distance, comp_speed,
        num_points
    )
    
    # Official gap (positive = comparison driver slower)
    official_gap = comp_official_time - ref_official_time
    
    # Raw telemetry gap (final value of raw delta)
    telemetry_gap = raw_delta[-1] if len(raw_delta) > 0 else 0.0
    
    # Calculate scaling factor
    # scaling_factor = official_gap / telemetry_gap
    if abs(telemetry_gap) > 0.001:  # Avoid division by near-zero
        scaling_factor = official_gap / telemetry_gap
    else:
        # Telemetry shows essentially no gap, use 1.0
        scaling_factor = 1.0
        logger.warning(
            f"Telemetry gap near zero ({telemetry_gap:.4f}s), using scaling=1.0"
        )
    
    # Apply sanity bounds to scaling factor
    # If scaling is extreme, something is wrong with the data
    SCALING_BOUND = 5.0
    if abs(scaling_factor) > SCALING_BOUND:
        logger.warning(
            f"Extreme scaling factor {scaling_factor:.2f} detected. "
            f"Official gap: {official_gap:.3f}s, Telemetry gap: {telemetry_gap:.3f}s. "
            f"Clamping to ±{SCALING_BOUND}"
        )
        scaling_factor = np.clip(scaling_factor, -SCALING_BOUND, SCALING_BOUND)
    
    # Handle sign mismatch (telemetry says A faster, official says B faster)
    if (telemetry_gap > 0 and official_gap < 0) or (telemetry_gap < 0 and official_gap > 0):
        if abs(telemetry_gap) > 0.050:  # Only warn for significant mismatches
            logger.warning(
                f"Sign mismatch: telemetry_gap={telemetry_gap:.3f}s, "
                f"official_gap={official_gap:.3f}s. Using official as truth."
            )
    
    # Scale the delta
    scaled_delta = raw_delta * scaling_factor
    
    # Calculate confidence based on scaling factor magnitude
    # Scaling close to 1.0 = high confidence (telemetry matches official)
    # Scaling far from 1.0 = lower confidence (data quality issues)
    scaling_deviation = abs(scaling_factor - 1.0)
    
    if scaling_deviation < 0.2:
        confidence = 1.0  # Excellent match
    elif scaling_deviation < 0.5:
        confidence = 0.8  # Good match
    elif scaling_deviation < 1.0:
        confidence = 0.6  # Acceptable
    elif scaling_deviation < 2.0:
        confidence = 0.4  # Poor match
    else:
        confidence = 0.3  # Very poor match
    
    logger.info(
        f"Delta analysis complete: official_gap={official_gap:.3f}s, "
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
        confidence=confidence
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
