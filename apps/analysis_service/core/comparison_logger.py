"""
Comparison Logger Module

Provides logging utilities for comparing v1 and v2 corner analysis results
during the transition period. This helps validate that v2 produces better
results before fully switching over.

Usage:
    from core.comparison_logger import log_v1_v2_comparison, log_v2_metrics

    # Log comparison between v1 and v2 results
    log_v1_v2_comparison(
        session_id="2025_24_Qualifying",
        driver="NOR",
        v1_results=v1_corner_results,
        v2_results=v2_corner_results
    )
"""

import json
import logging
from dataclasses import asdict
from typing import Any, Dict, List, Optional

logger = logging.getLogger("analysis_service.comparison_logger")


def _safe_array(arr, default_value: float = 0.0):
    """
    Safely convert input to numpy array, handling None/empty/NaN cases.

    This is included per CLAUDE.md standard for all new modules.
    """
    import numpy as np

    if arr is None or (hasattr(arr, "__len__") and len(arr) == 0):
        logger.warning(f"Empty/None array received, using default [{default_value}]")
        return np.array([default_value])

    result = np.array(arr, dtype=float)

    if np.any(np.isnan(result)):
        nan_count = np.sum(np.isnan(result))
        logger.warning(f"Array contains {nan_count} NaN values, interpolating")
        mask = np.isnan(result)
        if np.any(~mask):
            result[mask] = np.interp(
                np.flatnonzero(mask), np.flatnonzero(~mask), result[~mask]
            )
        else:
            result = np.full_like(result, default_value)

    return result


def log_v1_v2_comparison(
    session_id: str,
    driver: str,
    v1_results: List[Any],
    v2_results: List[Any],
    reference_driver: str = ""
) -> Dict[str, Any]:
    """
    Log detailed comparison between v1 and v2 corner analysis results.

    This function logs:
    1. Per-corner delta differences
    2. Total delta difference
    3. Confidence changes
    4. Zone boundary differences

    Args:
        session_id: Session identifier
        driver: Comparison driver code
        v1_results: List of CornerResult from v1 analysis
        v2_results: List of CornerResultV2 from v2 analysis
        reference_driver: Reference driver code

    Returns:
        Dict containing comparison summary
    """
    if len(v1_results) != len(v2_results):
        logger.warning(
            f"V1/V2 corner count mismatch for {driver}: "
            f"v1={len(v1_results)}, v2={len(v2_results)}"
        )
        return {"error": "corner_count_mismatch"}

    corners_comparison = []
    total_v1_delta = 0.0
    total_v2_delta = 0.0
    total_diff = 0.0

    for v1, v2 in zip(v1_results, v2_results):
        diff = v2.delta_change - v1.delta_change
        total_diff += abs(diff)
        total_v1_delta += v1.delta_change
        total_v2_delta += v2.delta_change

        corner_data = {
            "corner_number": v1.corner_number,
            "v1_delta": round(v1.delta_change, 4),
            "v2_delta": round(v2.delta_change, 4),
            "diff": round(diff, 4),
            "v1_zone": f"{v1.zone_start:.0f}-{v1.zone_end:.0f}m",
            "v2_zone": f"{v2.zone_start:.0f}-{v2.zone_end:.0f}m",
            "v1_confidence": v1.confidence,
            "v2_confidence": v2.confidence,
        }

        # Add v2-specific fields if available
        if hasattr(v2, "detected_apex"):
            corner_data["apex_shift"] = round(
                v2.detected_apex - v1.apex_distance, 1
            )
        if hasattr(v2, "exit_distance"):
            corner_data["exit_distance"] = round(v2.exit_distance, 0)

        corners_comparison.append(corner_data)

    comparison = {
        "session_id": session_id,
        "driver": driver,
        "reference_driver": reference_driver,
        "total_v1_delta": round(total_v1_delta, 4),
        "total_v2_delta": round(total_v2_delta, 4),
        "total_diff": round(total_diff, 4),
        "mean_abs_diff": round(total_diff / len(v1_results), 4) if v1_results else 0,
        "corners": corners_comparison,
    }

    # Log as structured JSON for easy parsing
    logger.info(f"CORNER_V1_V2_COMPARISON: {json.dumps(comparison)}")

    return comparison


def log_v2_metrics(
    session_id: str,
    driver: str,
    corner_results: List[Any],
    sector_validation: Optional[List[Any]] = None,
    confidence_adjustment: float = 1.0
) -> Dict[str, Any]:
    """
    Log v2-specific metrics for monitoring and debugging.

    Args:
        session_id: Session identifier
        driver: Driver code
        corner_results: List of CornerResultV2
        sector_validation: Optional list of SectorValidation results
        confidence_adjustment: Confidence adjustment from sector validation

    Returns:
        Dict containing v2 metrics summary
    """
    # Calculate detection statistics
    apex_deviations = []
    zone_sizes = []
    confidence_counts = {"high": 0, "medium": 0, "low": 0}

    for cr in corner_results:
        if hasattr(cr, "detected_apex"):
            apex_deviations.append(abs(cr.detected_apex - cr.apex_distance))

        zone_sizes.append(cr.zone_end - cr.zone_start)

        if cr.confidence in confidence_counts:
            confidence_counts[cr.confidence] += 1

    metrics = {
        "session_id": session_id,
        "driver": driver,
        "total_corners": len(corner_results),
        "avg_apex_deviation": round(
            sum(apex_deviations) / len(apex_deviations), 1
        ) if apex_deviations else 0,
        "max_apex_deviation": round(max(apex_deviations), 1) if apex_deviations else 0,
        "avg_zone_size": round(
            sum(zone_sizes) / len(zone_sizes), 1
        ) if zone_sizes else 0,
        "confidence_distribution": confidence_counts,
        "confidence_adjustment": round(confidence_adjustment, 3),
    }

    # Add sector validation if available
    if sector_validation:
        metrics["sector_validation"] = [
            {
                "sector": sv.sector_number,
                "corner_sum": round(sv.corner_delta_sum, 4),
                "official": round(sv.official_delta, 4),
                "diff": round(sv.difference, 4),
                "valid": sv.is_valid,
            }
            for sv in sector_validation
        ]

    logger.info(f"CORNER_V2_METRICS: {json.dumps(metrics)}")

    return metrics


def log_deceleration_stats(
    driver: str,
    distance: List[float],
    decel: List[float]
) -> Dict[str, Any]:
    """
    Log deceleration statistics for debugging.

    Args:
        driver: Driver code
        distance: Distance array
        decel: Deceleration array (m/s²)

    Returns:
        Dict containing deceleration statistics
    """
    import numpy as np

    decel_arr = np.array(decel)

    # Find heavy braking zones
    heavy_braking_mask = decel_arr < -5.0
    heavy_braking_count = np.sum(heavy_braking_mask)

    stats = {
        "driver": driver,
        "min_decel": round(float(decel_arr.min()), 2),
        "max_decel": round(float(decel_arr.max()), 2),
        "mean_decel": round(float(decel_arr.mean()), 2),
        "heavy_braking_points": int(heavy_braking_count),
        "heavy_braking_pct": round(
            heavy_braking_count / len(decel_arr) * 100, 1
        ) if len(decel_arr) > 0 else 0,
    }

    logger.debug(f"DECELERATION_STATS: {json.dumps(stats)}")

    return stats
