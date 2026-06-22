#!/usr/bin/env python3
# WARNING (G0 - Honest Acquisition): this script runs detection on the MERGED-FRAME
# SUBSTRATE (lap.get_telemetry(), ~51% interpolated car values). Production detection
# now consumes NATIVE car frames (app.services.telemetry.native_acquisition). Do NOT
# tune thresholds or validate detection with this script until it is ported to
# acquire_native_bundle (G0 continuation review L2-5).
"""
Validate Corner Analysis V2 with real FastF1 data.

This script loads actual F1 qualifying sessions and validates the V2 corner
analysis against real telemetry data to verify accuracy.

Usage:
    # Single session validation (Mexico 2025 Q3)
    python scripts/validate_v2.py --circuit rodriguez --year 2025 --round 20 --ref LEC --comp NOR

    # Multi-circuit validation
    python scripts/validate_v2.py --multi

Requirements:
    - fastf1 library installed
    - Internet connection for first-time data download
"""

import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import argparse
import logging
from typing import List, Tuple, Dict, Any, Optional
from dataclasses import dataclass

import numpy as np

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating V2 corner analysis against real data."""

    circuit: str
    session: str
    ref_driver: str
    comp_driver: str
    official_gap: float
    v2_corner_delta_total: float
    implied_straight_delta: float
    corner_count: int
    high_confidence_corners: int
    validation_notes: List[str]


def load_fastf1():
    """Import fastf1 with cache enabled."""
    try:
        import fastf1

        # Enable cache for faster subsequent loads
        cache_dir = os.path.join(
            os.path.dirname(os.path.abspath(__file__)), "..", "fastf1_cache"
        )
        os.makedirs(cache_dir, exist_ok=True)
        fastf1.Cache.enable_cache(cache_dir)
        return fastf1
    except ImportError:
        logger.error("fastf1 library not installed. Install with: pip install fastf1")
        sys.exit(1)


def validate_session(
    year: int,
    round_num: int,
    circuit_id: str,
    ref_driver: str,
    comp_driver: str,
    session_type: str = "Q",
) -> Optional[ValidationResult]:
    """
    Validate V2 corner analysis for a single session.

    Args:
        year: Season year (e.g., 2025)
        round_num: Round number
        circuit_id: Circuit identifier for config lookup
        ref_driver: Reference driver code (e.g., 'LEC')
        comp_driver: Comparison driver code (e.g., 'NOR')
        session_type: Session type ('Q' for qualifying, 'R' for race)

    Returns:
        ValidationResult with analysis metrics, or None if validation failed
    """
    fastf1 = load_fastf1()

    logger.info(f"\n{'='*60}")
    logger.info(f"VALIDATING: {year} Round {round_num} - {circuit_id.upper()}")
    logger.info(f"Reference: {ref_driver}, Comparison: {comp_driver}")
    logger.info(f"{'='*60}")

    try:
        # Load session
        logger.info(f"Loading {year} R{round_num} {session_type}...")
        session = fastf1.get_session(year, round_num, session_type)
        session.load()

        # Get fastest laps for both drivers
        ref_laps = session.laps.pick_driver(ref_driver)
        comp_laps = session.laps.pick_driver(comp_driver)

        ref_lap = ref_laps.pick_fastest()
        comp_lap = comp_laps.pick_fastest()

        if ref_lap is None or comp_lap is None:
            logger.error(f"Could not find fastest laps for {ref_driver} or {comp_driver}")
            return None

        # Get telemetry
        ref_tel = ref_lap.get_telemetry()
        comp_tel = comp_lap.get_telemetry()

        # Extract arrays
        ref_distance = ref_tel["Distance"].values.astype(float)
        ref_speed = ref_tel["Speed"].values.astype(float)
        ref_brake = ref_tel["Brake"].values.astype(float) * 100  # 0-1 to 0-100

        comp_distance = comp_tel["Distance"].values.astype(float)
        comp_speed = comp_tel["Speed"].values.astype(float)
        comp_brake = comp_tel["Brake"].values.astype(float) * 100

        # Get official times
        ref_time = ref_lap["LapTime"].total_seconds()
        comp_time = comp_lap["LapTime"].total_seconds()
        official_gap = comp_time - ref_time

        logger.info(f"Reference: {ref_driver} - {ref_time:.3f}s")
        logger.info(f"Comparison: {comp_driver} - {comp_time:.3f}s")
        logger.info(f"Official gap: {official_gap:+.3f}s")

        # Get corners from circuit info
        try:
            circuit_info = session.get_circuit_info()
            corners_df = circuit_info.corners

            corners = []
            for _, c in corners_df.iterrows():
                corners.append(
                    {
                        "corner_number": int(c["Number"]),
                        "apex_distance": float(c["Distance"]),
                        "name": f"T{c['Number']}",
                        "corner_type": "unknown",
                    }
                )
            logger.info(f"Found {len(corners)} corners from circuit info")
        except Exception as e:
            logger.warning(f"Could not get circuit corners: {e}")
            return None

        # Import local modules
        from services.delta_analysis import calculate_scaled_delta
        from services.corner_analysis import analyze_corners_v2, CornerInput
        from core.corner_config import get_config_for_circuit

        # Build telemetry dicts for calculate_scaled_delta
        ref_telemetry = {
            "distance": ref_distance.tolist(),
            "speed": ref_speed.tolist(),
        }
        comp_telemetry = {
            "distance": comp_distance.tolist(),
            "speed": comp_speed.tolist(),
        }

        # Calculate delta
        delta_result = calculate_scaled_delta(
            ref_telemetry=ref_telemetry,
            comp_telemetry=comp_telemetry,
            ref_official_time=ref_time,
            comp_official_time=comp_time,
            ref_driver=ref_driver,
            comp_driver=comp_driver,
        )

        # Convert corners to CornerInput objects
        corner_inputs = [CornerInput(**c) for c in corners]

        # Run V2 analysis
        config = get_config_for_circuit(circuit_id)
        logger.info(f"Using config for {circuit_id}: braking_threshold={config.braking_decel_threshold}")

        v2_result = analyze_corners_v2(
            delta_result=delta_result,
            ref_distance=ref_distance,
            ref_speed=ref_speed,
            ref_brake=ref_brake,
            comp_distance=comp_distance,
            comp_speed=comp_speed,
            comp_brake=comp_brake,
            corners=corner_inputs,
            circuit_id=circuit_id,
        )

        # Calculate totals
        v2_total = sum(cr.delta_change for cr in v2_result.corner_results)
        implied_straight = official_gap - v2_total
        high_conf = sum(1 for cr in v2_result.corner_results if cr.confidence == "high")

        logger.info(f"\n{'─'*60}")
        logger.info("RESULTS")
        logger.info(f"{'─'*60}")
        logger.info(f"V2 corner delta total: {v2_total:+.3f}s")
        logger.info(f"Implied straight delta: {implied_straight:+.3f}s")
        logger.info(f"High confidence corners: {high_conf}/{len(v2_result.corner_results)}")

        # Analyze results
        notes = []

        # Check for sign agreement
        if official_gap < 0 and v2_total > 0.1:
            notes.append(
                f"ANOMALY: Comp driver faster overall ({official_gap:.3f}s) but V2 shows corner loss (+{v2_total:.3f}s)"
            )
        elif official_gap > 0 and v2_total < -0.1:
            notes.append(
                f"ANOMALY: Comp driver slower overall ({official_gap:+.3f}s) but V2 shows corner gain ({v2_total:.3f}s)"
            )

        # Check for unrealistic straight delta
        if abs(implied_straight) > 1.0:
            notes.append(f"WARNING: Large implied straight delta ({implied_straight:+.3f}s)")

        # Corner-by-corner breakdown
        logger.info(f"\n{'─'*60}")
        logger.info("CORNER-BY-CORNER BREAKDOWN")
        logger.info(f"{'─'*60}")
        logger.info(f"{'Corner':<10} {'Delta':>10} {'Cause':<12} {'Conf':<8}")
        logger.info("─" * 42)

        for cr in v2_result.corner_results:
            logger.info(
                f"T{cr.corner_number:<9} {cr.delta_change:>+10.3f}s {cr.cause:<12} {cr.confidence:<8}"
            )

        if notes:
            logger.info(f"\n{'─'*60}")
            logger.info("NOTES")
            logger.info(f"{'─'*60}")
            for note in notes:
                logger.info(f"  • {note}")

        return ValidationResult(
            circuit=circuit_id,
            session=f"{year}_R{round_num}_{session_type}",
            ref_driver=ref_driver,
            comp_driver=comp_driver,
            official_gap=official_gap,
            v2_corner_delta_total=v2_total,
            implied_straight_delta=implied_straight,
            corner_count=len(v2_result.corner_results),
            high_confidence_corners=high_conf,
            validation_notes=notes,
        )

    except Exception as e:
        logger.error(f"Validation failed: {e}")
        import traceback

        traceback.print_exc()
        return None


def run_multi_circuit_validation() -> List[ValidationResult]:
    """
    Run validation across multiple circuits from the 2025 season.

    Returns:
        List of ValidationResult objects
    """
    # Test cases: (year, round, circuit_id, ref_driver, comp_driver)
    # Based on 2025 F1 calendar
    TEST_CASES = [
        # Mexico 2025 Q3 - The original problem case
        (2025, 20, "rodriguez", "LEC", "NOR"),
        # Monza 2025 Q3 - Heavy braking circuit
        (2025, 16, "monza", "LEC", "NOR"),
        # Monaco 2025 Q3 - Tight corners, light braking
        (2025, 8, "monaco", "LEC", "VER"),
        # Silverstone 2025 Q3 - High-speed flowing corners
        (2025, 12, "silverstone", "NOR", "VER"),
    ]

    results = []

    for year, rnd, circuit, ref, comp in TEST_CASES:
        try:
            result = validate_session(year, rnd, circuit, ref, comp)
            if result:
                results.append(result)
        except Exception as e:
            logger.error(f"Failed to validate {circuit}: {e}")

    # Print summary
    if results:
        logger.info(f"\n{'='*60}")
        logger.info("VALIDATION SUMMARY")
        logger.info(f"{'='*60}")
        logger.info(
            f"{'Circuit':<15} {'Official':>10} {'V2 Corner':>12} {'Straight':>10} {'Conf':<10}"
        )
        logger.info("─" * 60)

        for r in results:
            conf_str = f"{r.high_confidence_corners}/{r.corner_count}"
            logger.info(
                f"{r.circuit:<15} {r.official_gap:>+10.3f} {r.v2_corner_delta_total:>+12.3f} "
                f"{r.implied_straight_delta:>+10.3f} {conf_str:<10}"
            )

        # Analyze overall accuracy
        logger.info(f"\n{'─'*60}")
        logger.info("ANALYSIS")
        logger.info(f"{'─'*60}")

        anomalies = sum(1 for r in results if r.validation_notes)
        logger.info(f"Sessions with anomalies: {anomalies}/{len(results)}")

        avg_straight = np.mean([abs(r.implied_straight_delta) for r in results])
        logger.info(f"Average |implied straight delta|: {avg_straight:.3f}s")

    return results


def main():
    """Main entry point for validation script."""
    parser = argparse.ArgumentParser(
        description="Validate Corner Analysis V2 with real FastF1 data"
    )
    parser.add_argument("--circuit", default="rodriguez", help="Circuit ID")
    parser.add_argument("--year", type=int, default=2025, help="Season year")
    parser.add_argument("--round", type=int, default=20, help="Round number")
    parser.add_argument("--ref", default="LEC", help="Reference driver code")
    parser.add_argument("--comp", default="NOR", help="Comparison driver code")
    parser.add_argument(
        "--multi", action="store_true", help="Run multi-circuit validation"
    )
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Configure logging
    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    if args.multi:
        run_multi_circuit_validation()
    else:
        validate_session(
            args.year, args.round, args.circuit, args.ref, args.comp
        )


if __name__ == "__main__":
    main()
