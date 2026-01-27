"""
Technique Profiling Module (Phase 4)

Provides session-relative driver technique classification by:
1. Aggregating corner results by cause type (braking/apex/exit)
2. Calculating session percentiles across all drivers
3. Classifying each driver's technique dimensions (STRONG/NEUTRAL/WEAK)
4. Generating style summaries for natural language output (Phase 5)

This module replaces the absolute threshold approach in clustering.py
with a relative, session-normalized profiling system that adapts to
different circuits and conditions.

Usage:
    from services.technique_profiling import profile_drivers, TechniqueProfile

    # corner_results_by_driver maps driver code to CornerAnalysisResult
    profiles, session_percentiles = profile_drivers(
        corner_results_by_driver={'PIA': pia_result, 'VER': ver_result},
        reference_driver='NOR'
    )

    for profile in profiles:
        print(f"{profile.driver}: {profile.style_summary}")
        print(f"  Braking: {profile.braking.level} (P{profile.braking.percentile:.0f})")
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional
from enum import Enum

import numpy as np

from services.corner_analysis import CornerResult, CornerAnalysisResult, LapBreakdown, StraightSegment

logger = logging.getLogger("ml_service.technique_profiling")


# ============================================================================
# Constants
# ============================================================================

# Classification boundaries (percentile-based)
STRONG_PERCENTILE_THRESHOLD = 30  # Top 30% = STRONG
WEAK_PERCENTILE_THRESHOLD = 70    # Bottom 30% = WEAK

# Confidence weights for aggregation
CONFIDENCE_WEIGHTS: Dict[str, float] = {
    "high": 1.0,
    "medium": 0.7,
    "low": 0.3
}

# Minimum corners required for reliable dimension calculation
MIN_CORNERS_FOR_DIMENSION = 2

# Neutral threshold (delta change < 5ms considered negligible)
NEUTRAL_THRESHOLD = 0.005


# ============================================================================
# Descriptors (for Phase 5 Natural Language Generation)
# ============================================================================

DIMENSION_DESCRIPTORS: Dict[str, Dict[str, str]] = {
    "braking": {
        "STRONG": "Strong under braking",
        "NEUTRAL": "Balanced braking",
        "WEAK": "Loses time under braking"
    },
    "apex": {
        "STRONG": "Excellent apex speed",
        "NEUTRAL": "Average apex performance",
        "WEAK": "Loses time at apex"
    },
    "exit": {
        "STRONG": "Excellent traction",
        "NEUTRAL": "Balanced exits",
        "WEAK": "Struggles on exits"
    },
    "consistency": {
        "STRONG": "Highly consistent",
        "NEUTRAL": "Moderate consistency",
        "WEAK": "Variable performance"
    },
    "straight_line": {
        "STRONG": "Excellent straight-line speed",
        "NEUTRAL": "Balanced straight-line performance",
        "WEAK": "Straight-line deficit"
    }
}

# Primary factor descriptions for straight-line performance (5th dimension)
STRAIGHT_LINE_FACTORS: Dict[str, str] = {
    "aero_efficiency": "Low-drag setup maximizing top speed",
    "exit_traction": "Excellent traction from corner exits",
    "high_drag": "High-downforce setup compromising straight-line speed",
    "poor_traction": "Traction deficit limiting acceleration",
    "balanced": "Balanced straight-line performance",
}

# Style summary templates based on (braking_level, exit_level) combinations
STYLE_TEMPLATES: Dict[Tuple[str, str], str] = {
    ("STRONG", "STRONG"): "Complete package — excels in all phases",
    ("STRONG", "NEUTRAL"): "Late braker with balanced exits",
    ("STRONG", "WEAK"): "Aggressive entry, struggles with traction",
    ("NEUTRAL", "STRONG"): "Balanced entry, excellent exit speed",
    ("NEUTRAL", "NEUTRAL"): "Well-rounded technique",
    ("NEUTRAL", "WEAK"): "Balanced entry, loses time on exits",
    ("WEAK", "STRONG"): "Conservative entry, aggressive exit",
    ("WEAK", "NEUTRAL"): "Early braker with balanced exits",
    ("WEAK", "WEAK"): "Conservative approach throughout",
}


# ============================================================================
# Data Classes
# ============================================================================

class TechniqueLevel(str, Enum):
    """Classification level for technique dimensions."""
    STRONG = "strong"
    NEUTRAL = "neutral"
    WEAK = "weak"


@dataclass
class TechniqueDimension:
    """
    Single dimension of driving technique.

    Attributes:
        level: Classification (STRONG/NEUTRAL/WEAK)
        descriptor: Human-readable description for Phase 5
        percentile: Where driver falls in session distribution (0-100)
        raw_value: Actual delta sum in seconds
        corner_count: Number of corners contributing to this dimension
        avg_confidence: Average confidence of contributing corners (0-1)
    """
    level: TechniqueLevel
    descriptor: str
    percentile: float
    raw_value: float
    corner_count: int
    avg_confidence: float


@dataclass
class StraightLineDimension:
    """
    5th Dimension: Straight-line performance analysis.

    Captures time gained/lost on straight sections between corners,
    providing insight into aero efficiency, traction, and setup choices.

    Note: For straight-line, negative delta = faster = better (gaining time).
    So STRONG = most negative (low percentile), WEAK = most positive (high percentile).

    Attributes:
        level: Classification (STRONG/NEUTRAL/WEAK)
        descriptor: Human-readable description for Phase 5
        percentile: Session-relative percentile (0-100)
        raw_delta: Total straight-line delta in seconds (from LapBreakdown.straight_total)
        primary_factor: Dominant cause ('aero_efficiency', 'exit_traction', 'high_drag', 'poor_traction', 'balanced')
        segment_count: Number of straight segments analyzed
        top_gaining_straights: Names of straights where time was gained (up to 3)
        top_losing_straights: Names of straights where time was lost (up to 3)
        avg_confidence: Average confidence across segments (0-1)
    """
    level: TechniqueLevel
    descriptor: str
    percentile: float
    raw_delta: float
    primary_factor: str
    segment_count: int = 0
    top_gaining_straights: List[str] = field(default_factory=list)
    top_losing_straights: List[str] = field(default_factory=list)
    avg_confidence: float = 0.0


@dataclass
class TechniqueProfile:
    """
    Complete technique profile for a driver.

    Now includes 5 dimensions: braking, apex, exit, consistency, and straight_line.

    Attributes:
        driver: Driver code (e.g., "PIA")
        reference_driver: Who this is compared against (e.g., "NOR")
        braking: Braking technique dimension
        apex: Apex technique dimension
        exit: Exit technique dimension
        consistency: Consistency dimension
        straight_line: Straight-line performance dimension (5th dimension)
        top_gaining_corners: Best 3 corners (names/numbers)
        top_losing_corners: Worst 3 corners (names/numbers)
        style_summary: One-line characterization
        overall_confidence: Aggregate confidence score (0-1)
        total_corners_analyzed: Number of corners in analysis
    """
    driver: str
    reference_driver: str
    braking: TechniqueDimension
    apex: TechniqueDimension
    exit: TechniqueDimension
    consistency: TechniqueDimension
    straight_line: Optional[StraightLineDimension] = None  # NEW: 5th dimension
    top_gaining_corners: List[str] = field(default_factory=list)
    top_losing_corners: List[str] = field(default_factory=list)
    style_summary: str = ""
    overall_confidence: float = 0.0
    total_corners_analyzed: int = 0


@dataclass
class SessionPercentiles:
    """
    Percentile boundaries calculated from all drivers in session.

    Used for session-relative classification. Stores both the P30/P70
    thresholds and the raw values for exact percentile calculation.

    Now includes straight-line percentiles for 5th dimension.
    """
    braking_p30: float
    braking_p70: float
    apex_p30: float
    apex_p70: float
    exit_p30: float
    exit_p70: float
    consistency_p30: float
    consistency_p70: float
    driver_count: int

    # Store all values for exact percentile calculation
    all_braking: List[float] = field(default_factory=list)
    all_apex: List[float] = field(default_factory=list)
    all_exit: List[float] = field(default_factory=list)
    all_consistency: List[float] = field(default_factory=list)

    # 5th dimension: straight-line percentiles
    straight_line_p30: float = 0.0
    straight_line_p70: float = 0.0
    all_straight_line: List[float] = field(default_factory=list)


@dataclass
class DriverAggregates:
    """
    Intermediate aggregated data for a single driver.

    This is an internal data structure used during profiling.
    """
    driver: str
    braking_total: float
    apex_total: float
    exit_total: float
    consistency: float
    braking_count: int
    apex_count: int
    exit_count: int
    total_corners: int
    avg_confidence: float
    top_gaining: List[str] = field(default_factory=list)
    top_losing: List[str] = field(default_factory=list)


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


# ============================================================================
# Aggregation Functions
# ============================================================================

def identify_key_corners(corner_results: List[CornerResult]) -> Tuple[List[str], List[str]]:
    """
    Identify the most impactful corners (gaining and losing).

    Args:
        corner_results: List of CornerResult from Phase 3

    Returns:
        Tuple of (top_gaining_corners, top_losing_corners) as formatted strings
    """
    if not corner_results:
        return [], []

    # Sort by absolute delta (most impactful first)
    sorted_corners = sorted(
        corner_results,
        key=lambda c: abs(c.delta_change),
        reverse=True
    )

    # Top gaining (negative delta = compare driver faster than reference)
    gaining = [c for c in sorted_corners if c.delta_change < -NEUTRAL_THRESHOLD]
    top_gaining = []
    for c in gaining[:3]:
        name = c.name if c.name else f"T{c.corner_number}"
        top_gaining.append(name)

    # Top losing (positive delta = compare driver slower than reference)
    losing = [c for c in sorted_corners if c.delta_change > NEUTRAL_THRESHOLD]
    top_losing = []
    for c in losing[:3]:
        name = c.name if c.name else f"T{c.corner_number}"
        top_losing.append(name)

    return top_gaining, top_losing


def aggregate_by_cause(
    corner_results: List[CornerResult],
    weight_by_confidence: bool = True
) -> DriverAggregates:
    """
    Aggregate corner deltas by cause type.

    Args:
        corner_results: List of CornerResult from Phase 3
        weight_by_confidence: Whether to apply confidence weighting

    Returns:
        DriverAggregates with totals for each dimension
    """
    if not corner_results:
        logger.warning("No corner results provided for aggregation")
        return DriverAggregates(
            driver="",
            braking_total=0.0,
            apex_total=0.0,
            exit_total=0.0,
            consistency=0.0,
            braking_count=0,
            apex_count=0,
            exit_count=0,
            total_corners=0,
            avg_confidence=0.0,
            top_gaining=[],
            top_losing=[]
        )

    # Group corners by cause
    braking_corners = [c for c in corner_results if c.cause == "braking"]
    apex_corners = [c for c in corner_results if c.cause == "apex"]
    exit_corners = [c for c in corner_results if c.cause == "exit"]

    def calc_weighted_total(corners: List[CornerResult]) -> Tuple[float, float]:
        """Calculate weighted total and average confidence for a cause group."""
        if not corners:
            return 0.0, 0.0

        if weight_by_confidence:
            weighted_sum = sum(
                c.delta_change * CONFIDENCE_WEIGHTS.get(c.confidence, 0.5)
                for c in corners
            )
            total_weight = sum(
                CONFIDENCE_WEIGHTS.get(c.confidence, 0.5)
                for c in corners
            )
            # Normalize back to corner count scale
            total = (weighted_sum / total_weight) * len(corners) if total_weight > 0 else 0.0
        else:
            total = sum(c.delta_change for c in corners)

        # Calculate average confidence
        confidences = [CONFIDENCE_WEIGHTS.get(c.confidence, 0.5) for c in corners]
        avg_conf = float(np.mean(confidences)) if confidences else 0.0

        return total, avg_conf

    braking_total, braking_conf = calc_weighted_total(braking_corners)
    apex_total, apex_conf = calc_weighted_total(apex_corners)
    exit_total, exit_conf = calc_weighted_total(exit_corners)

    # Consistency: standard deviation across ALL corners (including "multiple")
    all_deltas = [c.delta_change for c in corner_results]
    consistency = float(np.std(all_deltas)) if len(all_deltas) > 1 else 0.0

    # Overall average confidence across all corners
    all_confidences = [CONFIDENCE_WEIGHTS.get(c.confidence, 0.5) for c in corner_results]
    avg_confidence = float(np.mean(all_confidences)) if all_confidences else 0.0

    # Identify top corners
    top_gaining, top_losing = identify_key_corners(corner_results)

    logger.debug(
        f"Aggregated: braking={braking_total:+.3f}s ({len(braking_corners)} corners), "
        f"apex={apex_total:+.3f}s ({len(apex_corners)}), "
        f"exit={exit_total:+.3f}s ({len(exit_corners)}), "
        f"consistency={consistency:.3f}"
    )

    return DriverAggregates(
        driver="",  # Set by caller
        braking_total=braking_total,
        apex_total=apex_total,
        exit_total=exit_total,
        consistency=consistency,
        braking_count=len(braking_corners),
        apex_count=len(apex_corners),
        exit_count=len(exit_corners),
        total_corners=len(corner_results),
        avg_confidence=avg_confidence,
        top_gaining=top_gaining,
        top_losing=top_losing
    )


# ============================================================================
# Straight-Line Performance Aggregation (5th Dimension)
# ============================================================================

def determine_straight_line_primary_factor(
    straight_segments: List[StraightSegment],
    top_speed_delta: Optional[float] = None,
    avg_exit_delta: Optional[float] = None
) -> str:
    """
    Determine the primary factor explaining straight-line performance.

    Logic priority:
    1. If top_speed_delta > +2 km/h → aero_efficiency (low drag)
    2. If top_speed_delta < -2 km/h → high_drag (high downforce)
    3. If avg_exit_delta < -0.02s AND gaining on straights → exit_traction
    4. If avg_exit_delta > +0.02s AND losing on straights → poor_traction
    5. Otherwise → balanced (or most common segment factor)

    Args:
        straight_segments: List of StraightSegment from LapBreakdown
        top_speed_delta: Optional speed difference at top speed trap (km/h)
        avg_exit_delta: Optional average exit delta from corners

    Returns:
        Primary factor string: 'aero_efficiency', 'exit_traction', 'high_drag',
        'poor_traction', or 'balanced'
    """
    if not straight_segments:
        return "balanced"

    # Calculate aggregate performance
    total_delta = sum(s.delta_change for s in straight_segments)
    gaining_on_straights = total_delta < 0

    # Count factor occurrences from segments
    factor_counts: Dict[str, int] = {}
    for segment in straight_segments:
        factor = getattr(segment, 'primary_factor', 'balanced')
        factor_counts[factor] = factor_counts.get(factor, 0) + 1

    # Priority 1: Use top speed delta if available
    if top_speed_delta is not None:
        if top_speed_delta > 2.0:
            logger.debug(f"Primary factor: aero_efficiency (top_speed_delta={top_speed_delta:.1f} km/h)")
            return "aero_efficiency"
        elif top_speed_delta < -2.0:
            logger.debug(f"Primary factor: high_drag (top_speed_delta={top_speed_delta:.1f} km/h)")
            return "high_drag"

    # Priority 2: Use exit performance correlation
    if avg_exit_delta is not None:
        if avg_exit_delta < -0.02 and gaining_on_straights:
            logger.debug(f"Primary factor: exit_traction (avg_exit_delta={avg_exit_delta:+.3f}s, gaining)")
            return "exit_traction"
        elif avg_exit_delta > 0.02 and not gaining_on_straights:
            logger.debug(f"Primary factor: poor_traction (avg_exit_delta={avg_exit_delta:+.3f}s, losing)")
            return "poor_traction"

    # Priority 3: Fall back to most common segment factor
    if factor_counts:
        most_common = max(factor_counts, key=factor_counts.get)
        if most_common != "balanced":
            logger.debug(f"Primary factor: {most_common} (from segment analysis)")
            return most_common

    return "balanced"


def aggregate_straight_line_performance(
    lap_breakdown: Optional[LapBreakdown],
    exit_dimension: Optional[TechniqueDimension] = None
) -> Dict[str, any]:
    """
    Aggregate straight-line performance data from LapBreakdown.

    Extracts the straight_total, identifies top gaining/losing segments,
    and determines the primary performance factor.

    Args:
        lap_breakdown: LapBreakdown from corner analysis (Phase 3)
        exit_dimension: Exit TechniqueDimension for correlation analysis

    Returns:
        Dict containing:
        - straight_total: Total time delta on straights (seconds)
        - segment_count: Number of straight segments
        - primary_factor: Dominant performance factor
        - top_gaining_straights: Best 3 straights (names, e.g., "T4→T5")
        - top_losing_straights: Worst 3 straights (names)
        - avg_confidence: Average confidence (set to 0.8 as straights are derived)
    """
    if lap_breakdown is None or not lap_breakdown.straight_segments:
        logger.debug("No lap_breakdown or straight_segments, returning empty aggregation")
        return {
            'straight_total': 0.0,
            'segment_count': 0,
            'primary_factor': 'balanced',
            'top_gaining_straights': [],
            'top_losing_straights': [],
            'avg_confidence': 0.0,
        }

    straight_total = lap_breakdown.straight_total
    segments = lap_breakdown.straight_segments

    # Sort by delta_change (most negative first = most gain)
    sorted_segments = sorted(segments, key=lambda s: s.delta_change)

    # Gaining = negative delta (faster), Losing = positive delta (slower)
    gaining = [s for s in sorted_segments if s.delta_change < -NEUTRAL_THRESHOLD]
    losing = [s for s in sorted_segments if s.delta_change > NEUTRAL_THRESHOLD]

    # Take top 3 from each
    top_gaining = [s.name for s in gaining[:3]]
    top_losing = [s.name for s in list(reversed(losing))[:3]]

    # Determine primary factor using exit correlation if available
    avg_exit_delta = exit_dimension.raw_value if exit_dimension else None
    primary_factor = determine_straight_line_primary_factor(
        segments,
        top_speed_delta=None,  # Could be passed from telemetry if available
        avg_exit_delta=avg_exit_delta
    )

    logger.debug(
        f"Straight-line aggregated: total={straight_total:+.3f}s, "
        f"segments={len(segments)}, factor={primary_factor}, "
        f"gaining={len(gaining)}, losing={len(losing)}"
    )

    return {
        'straight_total': straight_total,
        'segment_count': len(segments),
        'primary_factor': primary_factor,
        'top_gaining_straights': top_gaining,
        'top_losing_straights': top_losing,
        'avg_confidence': 0.8,  # Derived from delta analysis which has known confidence
    }


def classify_straight_line_dimension(
    straight_total: float,
    all_straight_totals: List[float],
    primary_factor: str,
    segment_count: int,
    top_gaining: List[str],
    top_losing: List[str],
    avg_confidence: float = 0.8
) -> StraightLineDimension:
    """
    Classify straight-line performance into STRONG/NEUTRAL/WEAK.

    Note: For straight-line, negative delta = faster = better.
    So STRONG = low percentile (most negative), WEAK = high percentile (most positive).

    Args:
        straight_total: This driver's straight-line total delta (seconds)
        all_straight_totals: All drivers' straight-line totals in session
        primary_factor: Determined primary factor from aggregation
        segment_count: Number of segments analyzed
        top_gaining: Top 3 gaining straights (names)
        top_losing: Top 3 losing straights (names)
        avg_confidence: Average confidence (0-1)

    Returns:
        StraightLineDimension with classification
    """
    if not all_straight_totals or len(all_straight_totals) < 2:
        # Not enough data for percentile calculation
        logger.warning(
            f"Insufficient data for straight-line percentile: "
            f"{len(all_straight_totals) if all_straight_totals else 0} drivers"
        )
        return StraightLineDimension(
            level=TechniqueLevel.NEUTRAL,
            descriptor="Insufficient data for straight-line classification",
            percentile=50.0,
            raw_delta=straight_total,
            primary_factor=primary_factor,
            segment_count=segment_count,
            top_gaining_straights=top_gaining,
            top_losing_straights=top_losing,
            avg_confidence=avg_confidence,
        )

    # Calculate exact percentile
    percentile = calculate_exact_percentile(straight_total, all_straight_totals)

    # Calculate P30/P70 thresholds
    p30 = float(np.percentile(all_straight_totals, STRONG_PERCENTILE_THRESHOLD))
    p70 = float(np.percentile(all_straight_totals, WEAK_PERCENTILE_THRESHOLD))

    # Classify: lower (more negative) = better for straight-line
    if straight_total <= p30:
        level = TechniqueLevel.STRONG
    elif straight_total >= p70:
        level = TechniqueLevel.WEAK
    else:
        level = TechniqueLevel.NEUTRAL

    # Get descriptor with factor info
    base_descriptor = DIMENSION_DESCRIPTORS.get("straight_line", {}).get(
        level.name, f"{level.name.capitalize()} straight-line performance"
    )
    factor_text = STRAIGHT_LINE_FACTORS.get(primary_factor, "")
    if factor_text and level != TechniqueLevel.NEUTRAL:
        descriptor = f"{base_descriptor} — {factor_text}"
    else:
        descriptor = base_descriptor

    logger.debug(
        f"Straight-line classified: {level.value} (P{percentile:.0f}), "
        f"raw={straight_total:+.3f}s, factor={primary_factor}"
    )

    return StraightLineDimension(
        level=level,
        descriptor=descriptor,
        percentile=percentile,
        raw_delta=straight_total,
        primary_factor=primary_factor,
        segment_count=segment_count,
        top_gaining_straights=top_gaining,
        top_losing_straights=top_losing,
        avg_confidence=avg_confidence,
    )


# ============================================================================
# Session Percentile Calculation
# ============================================================================

def calculate_session_percentiles(
    all_aggregates: List[DriverAggregates]
) -> SessionPercentiles:
    """
    Calculate percentile boundaries from all drivers' aggregated data.

    Args:
        all_aggregates: List of DriverAggregates, one per driver

    Returns:
        SessionPercentiles with P30/P70 boundaries for each dimension
    """
    if len(all_aggregates) < 2:
        logger.warning(
            f"Only {len(all_aggregates)} drivers provided, "
            "percentiles may not be meaningful"
        )

    # Extract all dimension values
    all_braking = [a.braking_total for a in all_aggregates]
    all_apex = [a.apex_total for a in all_aggregates]
    all_exit = [a.exit_total for a in all_aggregates]
    all_consistency = [a.consistency for a in all_aggregates]

    # Handle edge case of single driver
    if len(all_aggregates) == 1:
        # Use the single value as both thresholds (will result in NEUTRAL)
        return SessionPercentiles(
            braking_p30=all_braking[0],
            braking_p70=all_braking[0],
            apex_p30=all_apex[0],
            apex_p70=all_apex[0],
            exit_p30=all_exit[0],
            exit_p70=all_exit[0],
            consistency_p30=all_consistency[0],
            consistency_p70=all_consistency[0],
            driver_count=1,
            all_braking=all_braking,
            all_apex=all_apex,
            all_exit=all_exit,
            all_consistency=all_consistency
        )

    return SessionPercentiles(
        braking_p30=float(np.percentile(all_braking, STRONG_PERCENTILE_THRESHOLD)),
        braking_p70=float(np.percentile(all_braking, WEAK_PERCENTILE_THRESHOLD)),
        apex_p30=float(np.percentile(all_apex, STRONG_PERCENTILE_THRESHOLD)),
        apex_p70=float(np.percentile(all_apex, WEAK_PERCENTILE_THRESHOLD)),
        exit_p30=float(np.percentile(all_exit, STRONG_PERCENTILE_THRESHOLD)),
        exit_p70=float(np.percentile(all_exit, WEAK_PERCENTILE_THRESHOLD)),
        consistency_p30=float(np.percentile(all_consistency, STRONG_PERCENTILE_THRESHOLD)),
        consistency_p70=float(np.percentile(all_consistency, WEAK_PERCENTILE_THRESHOLD)),
        driver_count=len(all_aggregates),
        all_braking=all_braking,
        all_apex=all_apex,
        all_exit=all_exit,
        all_consistency=all_consistency
    )


def calculate_exact_percentile(value: float, all_values: List[float]) -> float:
    """
    Calculate the exact percentile of a value within a distribution.

    Uses the formula: percentile = (count_below + 0.5 * count_equal) / total * 100

    Args:
        value: The value to find percentile for
        all_values: All values in the distribution

    Returns:
        Percentile (0-100)
    """
    if not all_values:
        return 50.0

    count_below = sum(1 for v in all_values if v < value)
    count_equal = sum(1 for v in all_values if v == value)

    # Percentile = (count below + 0.5 * count equal) / total * 100
    percentile = (count_below + 0.5 * count_equal) / len(all_values) * 100

    return float(percentile)


# ============================================================================
# Classification Functions
# ============================================================================

def classify_dimension(
    value: float,
    p30: float,
    p70: float,
    all_values: List[float],
    dimension_name: str,
    corner_count: int,
    avg_confidence: float
) -> TechniqueDimension:
    """
    Classify a driver's performance in a single dimension.

    Args:
        value: Driver's aggregated value for this dimension
        p30: 30th percentile threshold (STRONG boundary)
        p70: 70th percentile threshold (WEAK boundary)
        all_values: All drivers' values (for exact percentile calculation)
        dimension_name: Name of dimension for descriptor lookup
        corner_count: Number of corners contributing
        avg_confidence: Average confidence of contributing corners

    Returns:
        TechniqueDimension with classification
    """
    # Calculate exact percentile
    percentile = calculate_exact_percentile(value, all_values)

    # Classify based on thresholds
    # For performance dimensions: lower (more negative) = better
    # For consistency: lower std_dev = better
    if value <= p30:
        level = TechniqueLevel.STRONG
    elif value >= p70:
        level = TechniqueLevel.WEAK
    else:
        level = TechniqueLevel.NEUTRAL

    # Get descriptor from lookup table
    descriptor = DIMENSION_DESCRIPTORS.get(dimension_name, {}).get(
        level.name, f"{level.name.capitalize()} {dimension_name}"
    )

    return TechniqueDimension(
        level=level,
        descriptor=descriptor,
        percentile=percentile,
        raw_value=value,
        corner_count=corner_count,
        avg_confidence=avg_confidence
    )


def generate_style_summary(
    braking: TechniqueDimension,
    exit_dim: TechniqueDimension,
    apex: TechniqueDimension,
    consistency: TechniqueDimension
) -> str:
    """
    Generate a one-line style characterization.

    Primarily based on braking and exit dimensions, as these are
    the most actionable for driver coaching.

    Args:
        braking: Braking technique dimension
        exit_dim: Exit technique dimension
        apex: Apex technique dimension
        consistency: Consistency dimension

    Returns:
        Human-readable style summary string
    """
    key = (braking.level.name, exit_dim.level.name)

    if key in STYLE_TEMPLATES:
        return STYLE_TEMPLATES[key]

    # Fallback: generate from components
    parts = []

    if braking.level == TechniqueLevel.STRONG:
        parts.append("Late braker")
    elif braking.level == TechniqueLevel.WEAK:
        parts.append("Conservative entry")

    if exit_dim.level == TechniqueLevel.STRONG:
        parts.append("strong exit speed")
    elif exit_dim.level == TechniqueLevel.WEAK:
        parts.append("struggles with traction")

    if consistency.level == TechniqueLevel.STRONG:
        parts.append("highly consistent")
    elif consistency.level == TechniqueLevel.WEAK:
        parts.append("variable")

    return ", ".join(parts) if parts else "Balanced approach"


# ============================================================================
# Main Entry Point
# ============================================================================

def profile_drivers(
    corner_results_by_driver: Dict[str, CornerAnalysisResult],
    reference_driver: str,
    weight_by_confidence: bool = True
) -> Tuple[List[TechniqueProfile], SessionPercentiles]:
    """
    Profile all drivers in a session using session-relative classification.

    This is the main entry point for technique profiling. It:
    1. Aggregates each driver's corner results by cause type
    2. Collects straight-line totals for 5th dimension
    3. Calculates session-wide percentiles (including straight-line)
    4. Classifies each driver's technique dimensions
    5. Generates style summaries

    Args:
        corner_results_by_driver: Dict mapping driver code to CornerAnalysisResult
        reference_driver: The reference driver for comparisons
        weight_by_confidence: Whether to weight aggregations by corner confidence

    Returns:
        Tuple of (list of TechniqueProfile, SessionPercentiles)

    Example:
        >>> profiles, percentiles = profile_drivers(
        ...     corner_results_by_driver={'PIA': pia_result, 'VER': ver_result},
        ...     reference_driver='NOR'
        ... )
        >>> for p in profiles:
        ...     print(f"{p.driver}: {p.style_summary}")
    """
    logger.info(
        f"Profiling {len(corner_results_by_driver)} drivers "
        f"against reference {reference_driver}"
    )

    if not corner_results_by_driver:
        logger.warning("No drivers provided for profiling")
        return [], SessionPercentiles(
            braking_p30=0.0, braking_p70=0.0,
            apex_p30=0.0, apex_p70=0.0,
            exit_p30=0.0, exit_p70=0.0,
            consistency_p30=0.0, consistency_p70=0.0,
            driver_count=0
        )

    # Stage 1: Aggregate each driver's corner results
    all_aggregates: List[DriverAggregates] = []
    # NEW: Collect straight-line data for 5th dimension
    straight_line_data_by_driver: Dict[str, Dict[str, any]] = {}
    all_straight_totals: List[float] = []

    for driver, result in corner_results_by_driver.items():
        aggregates = aggregate_by_cause(
            result.corner_results,
            weight_by_confidence
        )
        aggregates.driver = driver
        all_aggregates.append(aggregates)

        # NEW: Aggregate straight-line performance if lap_breakdown exists
        if result.lap_breakdown is not None:
            straight_agg = aggregate_straight_line_performance(
                result.lap_breakdown,
                exit_dimension=None  # Will be set later after exit classification
            )
            straight_line_data_by_driver[driver] = straight_agg
            all_straight_totals.append(straight_agg['straight_total'])
            logger.debug(
                f"Aggregated {driver}: braking={aggregates.braking_total:+.3f}s, "
                f"exit={aggregates.exit_total:+.3f}s, consistency={aggregates.consistency:.3f}, "
                f"straight_line={straight_agg['straight_total']:+.3f}s"
            )
        else:
            logger.debug(
                f"Aggregated {driver}: braking={aggregates.braking_total:+.3f}s, "
                f"exit={aggregates.exit_total:+.3f}s, consistency={aggregates.consistency:.3f}"
            )

    # Stage 2: Calculate session percentiles (including straight-line)
    session_percentiles = calculate_session_percentiles(all_aggregates)

    # NEW: Add straight-line percentiles to session percentiles
    if all_straight_totals and len(all_straight_totals) >= 2:
        session_percentiles.straight_line_p30 = float(
            np.percentile(all_straight_totals, STRONG_PERCENTILE_THRESHOLD)
        )
        session_percentiles.straight_line_p70 = float(
            np.percentile(all_straight_totals, WEAK_PERCENTILE_THRESHOLD)
        )
        session_percentiles.all_straight_line = all_straight_totals
    elif all_straight_totals:
        # Single value case
        session_percentiles.straight_line_p30 = all_straight_totals[0]
        session_percentiles.straight_line_p70 = all_straight_totals[0]
        session_percentiles.all_straight_line = all_straight_totals

    logger.debug(
        f"Session percentiles (n={session_percentiles.driver_count}): "
        f"braking P30={session_percentiles.braking_p30:+.3f}s, "
        f"P70={session_percentiles.braking_p70:+.3f}s, "
        f"straight_line P30={session_percentiles.straight_line_p30:+.3f}s, "
        f"P70={session_percentiles.straight_line_p70:+.3f}s"
    )

    # Stage 3 & 4: Classify each driver and build profiles
    profiles: List[TechniqueProfile] = []

    for aggregates in all_aggregates:
        driver = aggregates.driver

        # Classify braking dimension
        braking = classify_dimension(
            value=aggregates.braking_total,
            p30=session_percentiles.braking_p30,
            p70=session_percentiles.braking_p70,
            all_values=session_percentiles.all_braking,
            dimension_name="braking",
            corner_count=aggregates.braking_count,
            avg_confidence=aggregates.avg_confidence
        )

        # Classify apex dimension
        apex = classify_dimension(
            value=aggregates.apex_total,
            p30=session_percentiles.apex_p30,
            p70=session_percentiles.apex_p70,
            all_values=session_percentiles.all_apex,
            dimension_name="apex",
            corner_count=aggregates.apex_count,
            avg_confidence=aggregates.avg_confidence
        )

        # Classify exit dimension
        exit_dim = classify_dimension(
            value=aggregates.exit_total,
            p30=session_percentiles.exit_p30,
            p70=session_percentiles.exit_p70,
            all_values=session_percentiles.all_exit,
            dimension_name="exit",
            corner_count=aggregates.exit_count,
            avg_confidence=aggregates.avg_confidence
        )

        # Classify consistency dimension
        consistency = classify_dimension(
            value=aggregates.consistency,
            p30=session_percentiles.consistency_p30,
            p70=session_percentiles.consistency_p70,
            all_values=session_percentiles.all_consistency,
            dimension_name="consistency",
            corner_count=aggregates.total_corners,
            avg_confidence=aggregates.avg_confidence
        )

        # NEW: Classify straight-line dimension (5th dimension)
        straight_line_dim = None
        if driver in straight_line_data_by_driver:
            straight_data = straight_line_data_by_driver[driver]

            # Re-aggregate with exit dimension for correlation analysis
            corner_result = corner_results_by_driver.get(driver)
            if corner_result and corner_result.lap_breakdown:
                straight_data = aggregate_straight_line_performance(
                    corner_result.lap_breakdown,
                    exit_dimension=exit_dim
                )

            straight_line_dim = classify_straight_line_dimension(
                straight_total=straight_data['straight_total'],
                all_straight_totals=all_straight_totals,
                primary_factor=straight_data['primary_factor'],
                segment_count=straight_data['segment_count'],
                top_gaining=straight_data['top_gaining_straights'],
                top_losing=straight_data['top_losing_straights'],
                avg_confidence=straight_data['avg_confidence'],
            )

        # Generate style summary
        style_summary = generate_style_summary(braking, exit_dim, apex, consistency)

        profile = TechniqueProfile(
            driver=driver,
            reference_driver=reference_driver,
            braking=braking,
            apex=apex,
            exit=exit_dim,
            consistency=consistency,
            straight_line=straight_line_dim,  # NEW: 5th dimension
            top_gaining_corners=aggregates.top_gaining,
            top_losing_corners=aggregates.top_losing,
            style_summary=style_summary,
            overall_confidence=aggregates.avg_confidence,
            total_corners_analyzed=aggregates.total_corners
        )

        profiles.append(profile)

        # Enhanced logging with straight-line
        if straight_line_dim:
            logger.info(
                f"Profile for {driver}: "
                f"braking={braking.level.value} (P{braking.percentile:.0f}), "
                f"exit={exit_dim.level.value} (P{exit_dim.percentile:.0f}), "
                f"straight_line={straight_line_dim.level.value} (P{straight_line_dim.percentile:.0f}), "
                f"style='{style_summary}'"
            )
        else:
            logger.info(
                f"Profile for {driver}: "
                f"braking={braking.level.value} (P{braking.percentile:.0f}), "
                f"exit={exit_dim.level.value} (P{exit_dim.percentile:.0f}), "
                f"style='{style_summary}'"
            )

    return profiles, session_percentiles


# ============================================================================
# Convenience Functions
# ============================================================================

def profile_single_driver(
    corner_result: CornerAnalysisResult,
    reference_driver: str,
    weight_by_confidence: bool = True
) -> TechniqueProfile:
    """
    Profile a single driver (no session percentiles, uses direct classification).

    When only one driver is available, percentile-based classification
    cannot be meaningfully applied. This function provides a simplified
    profile based on absolute performance.

    Args:
        corner_result: CornerAnalysisResult for the driver
        reference_driver: The reference driver for comparisons
        weight_by_confidence: Whether to weight by corner confidence

    Returns:
        TechniqueProfile for the single driver
    """
    profiles, _ = profile_drivers(
        corner_results_by_driver={corner_result.compare_driver: corner_result},
        reference_driver=reference_driver,
        weight_by_confidence=weight_by_confidence
    )

    if profiles:
        return profiles[0]

    # Return empty profile if no results
    empty_dimension = TechniqueDimension(
        level=TechniqueLevel.NEUTRAL,
        descriptor="Insufficient data",
        percentile=50.0,
        raw_value=0.0,
        corner_count=0,
        avg_confidence=0.0
    )

    return TechniqueProfile(
        driver=corner_result.compare_driver,
        reference_driver=reference_driver,
        braking=empty_dimension,
        apex=empty_dimension,
        exit=empty_dimension,
        consistency=empty_dimension,
        style_summary="Insufficient data for profile",
        overall_confidence=0.0,
        total_corners_analyzed=0
    )
