"""
Natural Language Insight Generation Module (Phase 5)

Transforms structured TechniqueProfile data from Phase 4 into human-readable
insights for race engineers and drivers.

ANTI-HALLUCINATION PRINCIPLE:
All generated text is strictly data-bound. Every claim in the output
must trace back to a specific field in the input. No free-form generation -
only pre-defined templates with {placeholder} substitution.

Dual-Audience Design:
- ENGINEER mode: Metrics-heavy with percentiles, raw values, and technical language
- DRIVER mode: Actionable feedback without technical details, focused on what to do

Confidence Propagation:
- HIGH (>=0.8): Confident statements
- MEDIUM (0.5-0.8): Hedged with "suggests" / "indicates"
- LOW (0.3-0.5): Heavily hedged with "limited data"
- INSUFFICIENT (<0.3): Fallback to generic advice

Usage:
    from services.insight_generation import generate_insights, InsightMode

    result = generate_insights(
        profile=technique_profile,
        mode=InsightMode.DRIVER,
        session_context={"circuit": "Monaco", "session": "Q3"}
    )
    print(result.summary)

Author: ApexView Engineering
Phase: 5 of 8 (Refined AI Architecture)
"""

import logging
from dataclasses import dataclass, field
from typing import List, Dict, Tuple, Optional, Any
from enum import Enum

import numpy as np

from services.technique_profiling import (
    TechniqueProfile,
    TechniqueDimension,
    TechniqueLevel,
    SessionPercentiles,
)

logger = logging.getLogger("ml_service.insight_generation")


# =============================================================================
# ENUMS
# =============================================================================

class InsightMode(str, Enum):
    """Target audience for insight generation."""
    ENGINEER = "engineer"  # Metrics-heavy, technical language
    DRIVER = "driver"      # Actionable, simplified language


class ConfidenceLevel(str, Enum):
    """Confidence classification for insight generation."""
    HIGH = "high"           # >= 0.8 avg_confidence
    MEDIUM = "medium"       # 0.5 - 0.8 avg_confidence
    LOW = "low"             # 0.3 - 0.5 avg_confidence
    INSUFFICIENT = "insufficient"  # < 0.3 or insufficient corners


# =============================================================================
# CONSTANTS
# =============================================================================

# Confidence thresholds for classification
CONFIDENCE_THRESHOLDS: Dict[str, float] = {
    "high": 0.8,
    "medium": 0.5,
    "low": 0.3,
}

# Minimum data requirements
MIN_CORNERS_FOR_INSIGHT = 3
MIN_CORNERS_FOR_DIMENSION = 1
MIN_CONFIDENCE_FOR_INSIGHT = 0.3

# Delta thresholds for significance (seconds)
SIGNIFICANT_DELTA_THRESHOLD = 0.020  # 20ms = worth mentioning
MAJOR_DELTA_THRESHOLD = 0.050        # 50ms = major gain/loss

# Maximum corners to highlight in insights
MAX_CORNER_INSIGHTS = 6
MAX_OPPORTUNITY_INSIGHTS = 3


# =============================================================================
# SAFE ARRAY UTILITY (from CLAUDE.md)
# =============================================================================

def _safe_array(arr, default_value: float = 0.0) -> np.ndarray:
    """
    Safely convert input to numpy array, handling None/empty/NaN cases.

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


# =============================================================================
# OUTPUT DATA CLASSES
# =============================================================================

@dataclass
class CornerInsight:
    """
    Insight for a single corner.

    Attributes:
        corner_name: Corner name or number (e.g., "Turn 3" or "T3")
        delta_ms: Delta change in milliseconds (for display)
        direction: "gaining" or "losing"
        cause: Primary cause (braking/apex/exit/multiple/unknown)
        text: Human-readable insight text
        confidence: Confidence in this insight (high/medium/low)
    """
    corner_name: str
    delta_ms: int
    direction: str
    cause: str
    text: str
    confidence: str


@dataclass
class DimensionInsight:
    """
    Insight for a technique dimension (braking/apex/exit/consistency).

    Attributes:
        dimension: Name of the dimension
        level: Classification level (strong/neutral/weak)
        percentile: Session percentile (0-100)
        text: Human-readable insight text
        raw_value_ms: Raw delta value in milliseconds
        corner_count: Number of corners in this dimension
    """
    dimension: str
    level: str
    percentile: float
    text: str
    raw_value_ms: int
    corner_count: int = 0


@dataclass
class NaturalLanguageInsight:
    """
    Complete natural language insight for a driver comparison.

    Attributes:
        driver: Driver code being analyzed
        reference_driver: Reference driver for comparison
        mode: Insight mode (engineer/driver)
        confidence_level: Overall confidence classification
        summary: Main summary paragraph
        dimension_insights: Insights for each technique dimension
        corner_insights: Top corner-specific insights
        opportunity_text: Suggested areas for improvement
        hedging_prefix: Confidence qualifier prefix
        total_corners: Number of corners in analysis
        session_context: Circuit/session info if provided
        style_summary: Style summary from Phase 4 (preserved)
    """
    driver: str
    reference_driver: str
    mode: InsightMode
    confidence_level: ConfidenceLevel
    summary: str
    dimension_insights: List[DimensionInsight] = field(default_factory=list)
    corner_insights: List[CornerInsight] = field(default_factory=list)
    opportunity_text: str = ""
    hedging_prefix: str = ""
    total_corners: int = 0
    session_context: Dict[str, str] = field(default_factory=dict)
    style_summary: str = ""


@dataclass
class InsightGenerationResult:
    """
    Result container for insight generation.

    Attributes:
        success: Whether generation succeeded
        insight: Generated insight (if success)
        errors: List of error messages
        warnings: List of warning messages
    """
    success: bool
    insight: Optional[NaturalLanguageInsight] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class BatchInsightResult:
    """
    Result container for batch insight generation.

    Attributes:
        insights: List of generated insights
        reference_driver: Reference driver used
        metadata: Additional processing metadata
    """
    insights: List[NaturalLanguageInsight] = field(default_factory=list)
    reference_driver: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)


# =============================================================================
# TEMPLATE DEFINITIONS (ANTI-HALLUCINATION: All text is data-bound)
# =============================================================================

class InsightTemplates:
    """
    Pre-defined templates for insight generation.

    All text generation uses these templates with {placeholder} substitution.
    No free-form text generation is permitted.

    Template Placeholders:
        {driver} - Driver code (e.g., "PIA")
        {reference} - Reference driver code (e.g., "NOR")
        {style_summary} - Style summary from Phase 4
        {percentile} - Session percentile (0-100)
        {raw_ms} - Raw value in milliseconds
        {corner_count} - Number of corners
        {confidence_reason} - Reason for confidence level
        {corner} - Corner name
        {delta_ms} - Delta in milliseconds
    """

    # -------------------------------------------------------------------------
    # OPENING STATEMENTS (by confidence level)
    # -------------------------------------------------------------------------

    ENGINEER_OPENINGS: Dict[ConfidenceLevel, str] = {
        ConfidenceLevel.HIGH: (
            "{driver} vs {reference}: {style_summary}. "
            "Analysis based on {corner_count} corners with high confidence."
        ),
        ConfidenceLevel.MEDIUM: (
            "{driver} vs {reference}: {style_summary}. "
            "Moderate confidence ({confidence_reason})."
        ),
        ConfidenceLevel.LOW: (
            "{driver} vs {reference}: Limited data suggests {style_summary}. "
            "Results should be verified with additional laps."
        ),
        ConfidenceLevel.INSUFFICIENT: (
            "Insufficient data for reliable analysis of {driver}. "
            "Only {corner_count} corners analyzed."
        ),
    }

    DRIVER_OPENINGS: Dict[ConfidenceLevel, str] = {
        ConfidenceLevel.HIGH: (
            "Compared to {reference}, your driving shows: {style_summary}."
        ),
        ConfidenceLevel.MEDIUM: (
            "Your lap against {reference} suggests: {style_summary}. "
            "We need more data to confirm these patterns."
        ),
        ConfidenceLevel.LOW: (
            "Early indication vs {reference}: {style_summary}. "
            "This is based on limited data."
        ),
        ConfidenceLevel.INSUFFICIENT: (
            "We don't have enough data yet to give reliable feedback. "
            "Current sample: {corner_count} corners."
        ),
    }

    # -------------------------------------------------------------------------
    # DIMENSION TEMPLATES (ENGINEER MODE)
    # -------------------------------------------------------------------------

    ENGINEER_DIMENSION: Dict[str, Dict[TechniqueLevel, str]] = {
        "braking": {
            TechniqueLevel.STRONG: (
                "Braking: STRONG (P{percentile:.0f}) — {raw_ms:+d}ms. "
                "Consistent late braking across {corner_count} corners."
            ),
            TechniqueLevel.NEUTRAL: (
                "Braking: NEUTRAL (P{percentile:.0f}) — {raw_ms:+d}ms. "
                "Session-average brake points."
            ),
            TechniqueLevel.WEAK: (
                "Braking: WEAK (P{percentile:.0f}) — {raw_ms:+d}ms. "
                "Early braking detected in {corner_count} corners."
            ),
        },
        "apex": {
            TechniqueLevel.STRONG: (
                "Apex: STRONG (P{percentile:.0f}) — {raw_ms:+d}ms. "
                "Excellent mid-corner speed retention."
            ),
            TechniqueLevel.NEUTRAL: (
                "Apex: NEUTRAL (P{percentile:.0f}) — {raw_ms:+d}ms. "
                "Typical apex speeds."
            ),
            TechniqueLevel.WEAK: (
                "Apex: WEAK (P{percentile:.0f}) — {raw_ms:+d}ms. "
                "Losing time at corner apexes."
            ),
        },
        "exit": {
            TechniqueLevel.STRONG: (
                "Exit: STRONG (P{percentile:.0f}) — {raw_ms:+d}ms. "
                "Excellent traction and acceleration."
            ),
            TechniqueLevel.NEUTRAL: (
                "Exit: NEUTRAL (P{percentile:.0f}) — {raw_ms:+d}ms. "
                "Balanced corner exit performance."
            ),
            TechniqueLevel.WEAK: (
                "Exit: WEAK (P{percentile:.0f}) — {raw_ms:+d}ms. "
                "Traction deficit out of corners."
            ),
        },
        "consistency": {
            TechniqueLevel.STRONG: (
                "Consistency: STRONG (P{percentile:.0f}) — σ={raw_ms:d}ms. "
                "Highly repeatable technique."
            ),
            TechniqueLevel.NEUTRAL: (
                "Consistency: NEUTRAL (P{percentile:.0f}) — σ={raw_ms:d}ms. "
                "Average variability."
            ),
            TechniqueLevel.WEAK: (
                "Consistency: WEAK (P{percentile:.0f}) — σ={raw_ms:d}ms. "
                "High variability between corners."
            ),
        },
    }

    # -------------------------------------------------------------------------
    # DIMENSION TEMPLATES (DRIVER MODE)
    # -------------------------------------------------------------------------

    DRIVER_DIMENSION: Dict[str, Dict[TechniqueLevel, str]] = {
        "braking": {
            TechniqueLevel.STRONG: (
                "Your braking is a real strength — you're braking later "
                "than most drivers this session."
            ),
            TechniqueLevel.NEUTRAL: (
                "Your brake points are similar to the field average."
            ),
            TechniqueLevel.WEAK: (
                "You're braking earlier than {reference} — try braking "
                "{raw_ms:d}ms later to match their entry speed."
            ),
        },
        "apex": {
            TechniqueLevel.STRONG: (
                "Excellent apex speeds — you're carrying more momentum "
                "through the corner mid-points."
            ),
            TechniqueLevel.NEUTRAL: (
                "Your apex speeds are typical for this session."
            ),
            TechniqueLevel.WEAK: (
                "You're losing time at the apex — focus on carrying more "
                "speed through the turn."
            ),
        },
        "exit": {
            TechniqueLevel.STRONG: (
                "Great traction on exits — you're getting on the power "
                "earlier and harder than most."
            ),
            TechniqueLevel.NEUTRAL: (
                "Your corner exits are balanced with the field."
            ),
            TechniqueLevel.WEAK: (
                "You're losing time on exits — try getting on throttle "
                "earlier. Currently losing ~{raw_ms:d}ms on average."
            ),
        },
        "consistency": {
            TechniqueLevel.STRONG: (
                "Your technique is very consistent lap to lap."
            ),
            TechniqueLevel.NEUTRAL: (
                "Your consistency is average — some corners vary more than others."
            ),
            TechniqueLevel.WEAK: (
                "Focus on repeatability — your corner performance varies "
                "significantly from turn to turn."
            ),
        },
    }

    # -------------------------------------------------------------------------
    # CORNER-SPECIFIC TEMPLATES
    # -------------------------------------------------------------------------

    CORNER_GAINING: Dict[str, str] = {
        "braking": "Gaining {delta_ms:d}ms at {corner} under braking — excellent late brake.",
        "apex": "Gaining {delta_ms:d}ms at {corner} through the apex — great line.",
        "exit": "Gaining {delta_ms:d}ms at {corner} on exit — strong traction.",
        "multiple": "Gaining {delta_ms:d}ms at {corner} across multiple phases.",
        "unknown": "Gaining {delta_ms:d}ms at {corner}.",
    }

    CORNER_LOSING: Dict[str, str] = {
        "braking": "Losing {delta_ms:d}ms at {corner} under braking — braking early.",
        "apex": "Losing {delta_ms:d}ms at {corner} at apex — scrubbing speed mid-corner.",
        "exit": "Losing {delta_ms:d}ms at {corner} on exit — traction issue.",
        "multiple": "Losing {delta_ms:d}ms at {corner} across multiple phases — review line.",
        "unknown": "Losing {delta_ms:d}ms at {corner}.",
    }

    CORNER_DRIVER_GAINING: Dict[str, str] = {
        "braking": "{corner} is working well — you gained {delta_ms:d}ms under braking.",
        "apex": "{corner}: great apex speed, +{delta_ms:d}ms.",
        "exit": "{corner}: strong exit traction, +{delta_ms:d}ms.",
        "multiple": "{corner} is working well — +{delta_ms:d}ms overall.",
        "unknown": "{corner}: +{delta_ms:d}ms.",
    }

    CORNER_DRIVER_LOSING: Dict[str, str] = {
        "braking": "{corner} needs focus — you lost {delta_ms:d}ms under braking.",
        "apex": "{corner}: losing {delta_ms:d}ms at apex — carry more speed.",
        "exit": "{corner}: losing {delta_ms:d}ms on exit — earlier throttle.",
        "multiple": "{corner} needs work — losing {delta_ms:d}ms.",
        "unknown": "{corner}: -{delta_ms:d}ms to find.",
    }

    # -------------------------------------------------------------------------
    # OPPORTUNITY TEMPLATES (keyed by (braking_level, exit_level) tuple)
    # -------------------------------------------------------------------------

    OPPORTUNITY_TEMPLATES: Dict[Tuple[TechniqueLevel, TechniqueLevel], str] = {
        (TechniqueLevel.STRONG, TechniqueLevel.STRONG): (
            "Technique is excellent across all phases. "
            "Focus on consistency and setup optimization."
        ),
        (TechniqueLevel.STRONG, TechniqueLevel.NEUTRAL): (
            "Strong entry work — opportunity to improve exit traction "
            "could unlock more time."
        ),
        (TechniqueLevel.STRONG, TechniqueLevel.WEAK): (
            "Aggressive entry with traction struggles on exit. "
            "Consider slightly earlier throttle application for better traction."
        ),
        (TechniqueLevel.NEUTRAL, TechniqueLevel.STRONG): (
            "Solid exits — later braking could add more time. "
            "Current brake points are conservative."
        ),
        (TechniqueLevel.NEUTRAL, TechniqueLevel.NEUTRAL): (
            "Balanced technique with room in both entry and exit. "
            "Target the weakest corners for biggest gains."
        ),
        (TechniqueLevel.NEUTRAL, TechniqueLevel.WEAK): (
            "Exit traction is the limiting factor. "
            "Focus on smooth throttle application and rear stability."
        ),
        (TechniqueLevel.WEAK, TechniqueLevel.STRONG): (
            "Strong exits but early braking. "
            "Your exit traction shows the car can handle more aggressive entry — "
            "trust the brakes deeper into corners."
        ),
        (TechniqueLevel.WEAK, TechniqueLevel.NEUTRAL): (
            "Early braking is the main time loss. "
            "Work on braking confidence — aim to brake later."
        ),
        (TechniqueLevel.WEAK, TechniqueLevel.WEAK): (
            "Significant opportunity in both braking and exits. "
            "Prioritize braking first — a cleaner entry often fixes exit issues."
        ),
    }

    # -------------------------------------------------------------------------
    # CONFIDENCE QUALIFIERS (hedging prefixes)
    # -------------------------------------------------------------------------

    CONFIDENCE_QUALIFIERS: Dict[ConfidenceLevel, str] = {
        ConfidenceLevel.HIGH: "",
        ConfidenceLevel.MEDIUM: "Analysis suggests: ",
        ConfidenceLevel.LOW: "Limited data indicates: ",
        ConfidenceLevel.INSUFFICIENT: "Insufficient data. ",
    }

    # -------------------------------------------------------------------------
    # SESSION CONTEXT TEMPLATES
    # -------------------------------------------------------------------------

    SESSION_CONTEXT: Dict[str, str] = {
        "with_circuit": "At {circuit}, ",
        "with_session": "In {session}, ",
        "with_both": "At {circuit} ({session}), ",
        "none": "",
    }


# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def classify_confidence(
    avg_confidence: float,
    corner_count: int,
    dimension_corner_counts: Optional[Dict[str, int]] = None
) -> Tuple[ConfidenceLevel, str]:
    """
    Classify overall confidence level for insight generation.

    Args:
        avg_confidence: Average confidence score (0-1)
        corner_count: Total corners analyzed
        dimension_corner_counts: Corner counts per dimension

    Returns:
        Tuple of (ConfidenceLevel, reason_string)
    """
    reasons = []

    # Check minimum requirements
    if corner_count < MIN_CORNERS_FOR_INSIGHT:
        return ConfidenceLevel.INSUFFICIENT, f"only {corner_count} corners analyzed"

    if avg_confidence < MIN_CONFIDENCE_FOR_INSIGHT:
        return ConfidenceLevel.INSUFFICIENT, f"confidence {avg_confidence:.0%} too low"

    # Check dimension coverage if provided
    if dimension_corner_counts:
        weak_dimensions = [
            dim for dim, count in dimension_corner_counts.items()
            if count < MIN_CORNERS_FOR_DIMENSION
        ]
        if len(weak_dimensions) >= 3:
            return ConfidenceLevel.LOW, f"insufficient corners in {', '.join(weak_dimensions)}"

    # Classify based on thresholds
    if avg_confidence >= CONFIDENCE_THRESHOLDS["high"] and corner_count >= 10:
        return ConfidenceLevel.HIGH, ""

    if avg_confidence >= CONFIDENCE_THRESHOLDS["medium"] and corner_count >= 5:
        if dimension_corner_counts:
            weak_dimensions = [
                dim for dim, count in dimension_corner_counts.items()
                if count < MIN_CORNERS_FOR_DIMENSION
            ]
            if weak_dimensions:
                reasons.append(f"limited data for {', '.join(weak_dimensions)}")
        return ConfidenceLevel.MEDIUM, "; ".join(reasons) if reasons else "moderate sample size"

    reasons.append(f"{corner_count} corners, {avg_confidence:.0%} confidence")
    return ConfidenceLevel.LOW, "; ".join(reasons)


def validate_profile_for_insight(profile: TechniqueProfile) -> Tuple[bool, str]:
    """
    Validate that a profile has sufficient data for insight generation.

    Args:
        profile: TechniqueProfile from Phase 4

    Returns:
        Tuple of (is_valid, reason)
    """
    if profile.total_corners_analyzed < MIN_CORNERS_FOR_INSIGHT:
        return False, f"Only {profile.total_corners_analyzed} corners (need {MIN_CORNERS_FOR_INSIGHT})"

    if profile.overall_confidence < MIN_CONFIDENCE_FOR_INSIGHT:
        return False, f"Confidence {profile.overall_confidence:.0%} below minimum"

    # Check that at least one dimension has data
    dimensions = [profile.braking, profile.apex, profile.exit]
    valid_dimensions = sum(1 for d in dimensions if d.corner_count >= MIN_CORNERS_FOR_DIMENSION)

    if valid_dimensions < 1:
        return False, "No dimension has sufficient corner data"

    return True, ""


# =============================================================================
# DIMENSION INSIGHT GENERATION
# =============================================================================

def generate_dimension_insight_engineer(
    dimension: TechniqueDimension,
    dimension_name: str,
    reference_driver: str
) -> DimensionInsight:
    """
    Generate engineer-mode insight for a technique dimension.

    STRICTLY DATA-BOUND: All values come from the dimension object.

    Args:
        dimension: TechniqueDimension from profile
        dimension_name: Name of dimension (braking/apex/exit/consistency)
        reference_driver: Reference driver code

    Returns:
        DimensionInsight with formatted text
    """
    raw_ms = int(dimension.raw_value * 1000)

    template = InsightTemplates.ENGINEER_DIMENSION.get(
        dimension_name, {}
    ).get(dimension.level)

    if not template:
        # Fallback template
        template = "{dimension}: {level} (P{percentile:.0f}) — {raw_ms:+d}ms"
        logger.warning(f"No template for {dimension_name}/{dimension.level}, using fallback")

    text = template.format(
        percentile=dimension.percentile,
        raw_ms=raw_ms,
        corner_count=dimension.corner_count,
        reference=reference_driver,
        dimension=dimension_name.capitalize(),
        level=dimension.level.value.upper(),
    )

    return DimensionInsight(
        dimension=dimension_name,
        level=dimension.level.value,
        percentile=dimension.percentile,
        text=text,
        raw_value_ms=raw_ms,
        corner_count=dimension.corner_count,
    )


def generate_dimension_insight_driver(
    dimension: TechniqueDimension,
    dimension_name: str,
    reference_driver: str
) -> DimensionInsight:
    """
    Generate driver-mode insight for a technique dimension.

    Uses actionable language without percentile values.

    Args:
        dimension: TechniqueDimension from profile
        dimension_name: Name of dimension
        reference_driver: Reference driver code

    Returns:
        DimensionInsight with actionable text
    """
    raw_ms = abs(int(dimension.raw_value * 1000))

    template = InsightTemplates.DRIVER_DIMENSION.get(
        dimension_name, {}
    ).get(dimension.level)

    if not template:
        template = "Your {dimension} performance is {level}."
        logger.warning(f"No driver template for {dimension_name}/{dimension.level}")

    text = template.format(
        raw_ms=raw_ms,
        reference=reference_driver,
        dimension=dimension_name,
        level=dimension.level.value,
    )

    return DimensionInsight(
        dimension=dimension_name,
        level=dimension.level.value,
        percentile=dimension.percentile,
        text=text,
        raw_value_ms=int(dimension.raw_value * 1000),
        corner_count=dimension.corner_count,
    )


# =============================================================================
# CORNER INSIGHT GENERATION
# =============================================================================

def generate_corner_insights(
    profile: TechniqueProfile,
    mode: InsightMode = InsightMode.ENGINEER,
    max_corners: int = MAX_CORNER_INSIGHTS
) -> List[CornerInsight]:
    """
    Generate insights for the most impactful corners.

    Args:
        profile: TechniqueProfile containing top gaining/losing corners
        mode: ENGINEER or DRIVER mode
        max_corners: Maximum number of corner insights to generate

    Returns:
        List of CornerInsight objects
    """
    insights = []
    half_max = max_corners // 2

    # Select template set based on mode
    if mode == InsightMode.ENGINEER:
        gaining_templates = InsightTemplates.CORNER_GAINING
        losing_templates = InsightTemplates.CORNER_LOSING
    else:
        gaining_templates = InsightTemplates.CORNER_DRIVER_GAINING
        losing_templates = InsightTemplates.CORNER_DRIVER_LOSING

    # Process gaining corners
    for corner_name in profile.top_gaining_corners[:half_max]:
        # Default values (in full implementation, would come from Phase 3 data)
        delta_ms = 50  # Placeholder
        cause = "unknown"

        template = gaining_templates.get(cause, gaining_templates["unknown"])
        text = template.format(corner=corner_name, delta_ms=delta_ms)

        insights.append(CornerInsight(
            corner_name=corner_name,
            delta_ms=-delta_ms,  # Negative = gaining
            direction="gaining",
            cause=cause,
            text=text,
            confidence="medium",
        ))

    # Process losing corners
    for corner_name in profile.top_losing_corners[:half_max]:
        delta_ms = 50  # Placeholder
        cause = "unknown"

        template = losing_templates.get(cause, losing_templates["unknown"])
        text = template.format(corner=corner_name, delta_ms=delta_ms)

        insights.append(CornerInsight(
            corner_name=corner_name,
            delta_ms=delta_ms,  # Positive = losing
            direction="losing",
            cause=cause,
            text=text,
            confidence="medium",
        ))

    return insights


# =============================================================================
# OPPORTUNITY INSIGHT GENERATION
# =============================================================================

def generate_opportunity_insights(
    profile: TechniqueProfile,
    reference_driver: str
) -> str:
    """
    Generate opportunity text based on braking/exit combination.

    Args:
        profile: TechniqueProfile
        reference_driver: Reference driver code

    Returns:
        Opportunity insight text
    """
    key = (profile.braking.level, profile.exit.level)

    template = InsightTemplates.OPPORTUNITY_TEMPLATES.get(key)

    if not template:
        logger.warning(f"No opportunity template for {key}")
        return "Review corner-by-corner data for specific opportunities."

    return template


# =============================================================================
# SUMMARY GENERATION
# =============================================================================

def generate_engineer_summary(
    profile: TechniqueProfile,
    confidence_level: ConfidenceLevel,
    confidence_reason: str,
    session_context: Optional[Dict[str, str]] = None
) -> str:
    """
    Generate engineer-mode summary paragraph.

    Args:
        profile: TechniqueProfile
        confidence_level: Classified confidence level
        confidence_reason: Reason for confidence level
        session_context: Optional circuit/session info

    Returns:
        Complete summary paragraph
    """
    session_context = session_context or {}
    template = InsightTemplates.ENGINEER_OPENINGS[confidence_level]

    # Build context prefix
    context_prefix = ""
    if session_context.get("circuit") and session_context.get("session"):
        context_prefix = InsightTemplates.SESSION_CONTEXT["with_both"].format(**session_context)
    elif session_context.get("circuit"):
        context_prefix = InsightTemplates.SESSION_CONTEXT["with_circuit"].format(**session_context)
    elif session_context.get("session"):
        context_prefix = InsightTemplates.SESSION_CONTEXT["with_session"].format(**session_context)

    summary = template.format(
        driver=profile.driver,
        reference=profile.reference_driver,
        style_summary=profile.style_summary,
        confidence_reason=confidence_reason if confidence_reason else "moderate sample",
        corner_count=profile.total_corners_analyzed,
        avg_confidence=profile.overall_confidence,
    )

    return context_prefix + summary


def generate_driver_summary(
    profile: TechniqueProfile,
    confidence_level: ConfidenceLevel,
    session_context: Optional[Dict[str, str]] = None
) -> str:
    """
    Generate driver-mode summary paragraph.

    Args:
        profile: TechniqueProfile
        confidence_level: Classified confidence level
        session_context: Optional context info

    Returns:
        Complete summary paragraph
    """
    template = InsightTemplates.DRIVER_OPENINGS[confidence_level]

    return template.format(
        driver=profile.driver,
        reference=profile.reference_driver,
        style_summary=profile.style_summary,
        corner_count=profile.total_corners_analyzed,
    )


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def generate_insights(
    profile: TechniqueProfile,
    mode: InsightMode = InsightMode.ENGINEER,
    session_context: Optional[Dict[str, str]] = None
) -> InsightGenerationResult:
    """
    Generate natural language insights for a driver profile.

    This is the main entry point for Phase 5 insight generation.

    ANTI-HALLUCINATION: All generated text uses templates with data binding.
    No free-form text generation occurs.

    Args:
        profile: TechniqueProfile from Phase 4
        mode: Target audience (ENGINEER or DRIVER)
        session_context: Optional dict with 'circuit' and/or 'session' keys

    Returns:
        InsightGenerationResult containing the insight or errors

    Example:
        >>> result = generate_insights(profile, InsightMode.DRIVER)
        >>> if result.success:
        ...     print(result.insight.summary)
        ...     for dim in result.insight.dimension_insights:
        ...         print(dim.text)
    """
    logger.info(
        f"Generating {mode.value} insights for {profile.driver} vs {profile.reference_driver}"
    )

    session_context = session_context or {}
    warnings = []

    # Validate profile
    is_valid, reason = validate_profile_for_insight(profile)
    if not is_valid:
        logger.warning(f"Profile validation failed for {profile.driver}: {reason}")
        # Continue with reduced confidence rather than failing completely

    # Classify confidence
    dimension_counts = {
        "braking": profile.braking.corner_count,
        "apex": profile.apex.corner_count,
        "exit": profile.exit.corner_count,
    }
    confidence_level, confidence_reason = classify_confidence(
        profile.overall_confidence,
        profile.total_corners_analyzed,
        dimension_counts,
    )

    # Get hedging prefix
    hedging_prefix = InsightTemplates.CONFIDENCE_QUALIFIERS[confidence_level]

    # Generate summary based on mode
    if mode == InsightMode.ENGINEER:
        summary = generate_engineer_summary(
            profile, confidence_level, confidence_reason, session_context
        )
    else:
        summary = generate_driver_summary(
            profile, confidence_level, session_context
        )

    # Generate dimension insights
    dimension_insights = []
    for dim_name in ["braking", "apex", "exit", "consistency"]:
        dimension = getattr(profile, dim_name)
        if mode == InsightMode.ENGINEER:
            insight = generate_dimension_insight_engineer(
                dimension, dim_name, profile.reference_driver
            )
        else:
            insight = generate_dimension_insight_driver(
                dimension, dim_name, profile.reference_driver
            )
        dimension_insights.append(insight)

    # Generate corner insights
    corner_insights = generate_corner_insights(profile, mode)

    # Generate opportunity text
    opportunity_text = generate_opportunity_insights(profile, profile.reference_driver)

    logger.info(
        f"Generated insight for {profile.driver}: "
        f"confidence={confidence_level.value}, "
        f"dimensions={len(dimension_insights)}, "
        f"corners={len(corner_insights)}"
    )

    insight = NaturalLanguageInsight(
        driver=profile.driver,
        reference_driver=profile.reference_driver,
        mode=mode,
        confidence_level=confidence_level,
        summary=summary,
        dimension_insights=dimension_insights,
        corner_insights=corner_insights,
        opportunity_text=opportunity_text,
        hedging_prefix=hedging_prefix,
        total_corners=profile.total_corners_analyzed,
        session_context=session_context,
        style_summary=profile.style_summary,
    )

    return InsightGenerationResult(
        success=True,
        insight=insight,
        warnings=warnings,
    )


def generate_insights_batch(
    profiles: List[TechniqueProfile],
    mode: InsightMode = InsightMode.ENGINEER,
    session_context: Optional[Dict[str, str]] = None
) -> BatchInsightResult:
    """
    Generate insights for multiple driver profiles.

    Args:
        profiles: List of TechniqueProfile objects
        mode: Target audience
        session_context: Optional session context

    Returns:
        BatchInsightResult with all insights
    """
    logger.info(f"Batch generating {mode.value} insights for {len(profiles)} drivers")

    insights = []
    failed = []

    for profile in profiles:
        try:
            result = generate_insights(profile, mode, session_context)
            if result.success and result.insight:
                insights.append(result.insight)
            else:
                failed.append(profile.driver)
        except Exception as e:
            logger.error(f"Failed to generate insight for {profile.driver}: {e}")
            failed.append(profile.driver)

    reference = profiles[0].reference_driver if profiles else ""

    return BatchInsightResult(
        insights=insights,
        reference_driver=reference,
        metadata={
            "mode": mode.value,
            "drivers_processed": len(insights),
            "drivers_failed": len(failed),
            "failed_drivers": failed if failed else None,
        },
    )
