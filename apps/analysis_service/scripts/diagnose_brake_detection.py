#!/usr/bin/env python3
# WARNING (G0 - Honest Acquisition): this script runs detection on the MERGED-FRAME
# SUBSTRATE (lap.get_telemetry(), ~51% interpolated car values). Production detection
# now consumes NATIVE car frames (app.services.telemetry.native_acquisition). Do NOT
# tune thresholds or validate detection with this script until it is ported to
# acquire_native_bundle (G0 continuation review L2-5).
"""
Brake Detection Threshold Diagnostic

Investigates why brake detection shows "medium" confidence for all corners.
Tests current thresholds against real FastF1 telemetry from multiple circuits.

This version finds braking zones DYNAMICALLY from actual telemetry data,
then tests whether the current detection algorithm would work.

Usage:
    python diagnose_brake_detection.py
"""

import fastf1
import numpy as np
import pandas as pd
import warnings

warnings.filterwarnings("ignore")

# Current thresholds from corner_analysis.py
BRAKE_THRESHOLD_PERCENT = 20.0
BRAKE_GRADIENT_THRESHOLD = 5.0

# Test circuits
TEST_CIRCUITS = {
    "Bahrain": {"session": ("2025", "Bahrain", "Q")},
    "Spa": {"session": ("2025", "Belgium", "Q")},
    "Monaco": {"session": ("2025", "Monaco", "Q")},
    "Monza": {"session": ("2025", "Italy", "Q")},
}


def find_braking_zones(telemetry: pd.DataFrame, min_zone_length: float = 30.0):
    """
    Find all braking zones in telemetry data.
    
    Returns list of (brake_start_dist, brake_end_dist, zone_data)
    """
    distance = telemetry["Distance"].values
    brake_raw = telemetry["Brake"].values
    
    # Convert boolean to 0-100
    brake = np.array(brake_raw, dtype=float) * 100.0
    
    braking_zones = []
    in_zone = False
    zone_start_idx = None
    
    for i in range(len(brake)):
        if brake[i] >= BRAKE_THRESHOLD_PERCENT and not in_zone:
            # Start of braking zone
            in_zone = True
            zone_start_idx = i
        elif brake[i] < BRAKE_THRESHOLD_PERCENT and in_zone:
            # End of braking zone
            in_zone = False
            zone_end_idx = i
            zone_length = distance[zone_end_idx] - distance[zone_start_idx]
            
            if zone_length >= min_zone_length:
                braking_zones.append({
                    "start_dist": distance[zone_start_idx],
                    "end_dist": distance[zone_end_idx],
                    "start_idx": zone_start_idx,
                    "end_idx": zone_end_idx,
                    "length": zone_length,
                })
    
    return braking_zones


def analyze_braking_zone(
    telemetry: pd.DataFrame, 
    zone: dict,
    zone_num: int,
) -> dict:
    """
    Analyze a braking zone to see if detection would achieve HIGH confidence.
    
    The detection algorithm looks in apex - 250m to apex - 50m.
    We'll simulate this by treating the zone end as a hypothetical apex
    and checking if the zone start falls within the search window.
    """
    distance = telemetry["Distance"].values
    brake_raw = telemetry["Brake"].values
    brake = np.array(brake_raw, dtype=float) * 100.0
    
    # Look at 50 meters before the zone start to 50m into the zone
    # This is where the gradient detection should work
    search_start = max(zone["start_dist"] - 50, 0)
    search_end = zone["start_dist"] + 50
    
    mask = (distance >= search_start) & (distance <= search_end)
    zone_indices = np.where(mask)[0]
    
    if len(zone_indices) < 3:
        return {
            "zone_num": zone_num,
            "brake_start": zone["start_dist"],
            "brake_end": zone["end_dist"],
            "zone_length": zone["length"],
            "status": "NO_DATA",
            "max_gradient": None,
            "would_detect_high": False,
        }
    
    zone_distance = distance[zone_indices]
    zone_brake = brake[zone_indices]
    
    # Calculate gradient exactly like corner_analysis.py
    # gradient[i] = change FROM zone_brake[i] TO zone_brake[i+1]
    # So gradient[i] represents the change LEADING INTO index i+1
    distance_diff = np.diff(zone_distance)
    brake_diff = np.diff(zone_brake)
    distance_diff = np.maximum(distance_diff, 0.1)
    gradient = (brake_diff / distance_diff) * 10.0
    
    # Find point meeting BOTH criteria using CORRECTED logic:
    # Check zone_brake[i+1] >= threshold AND gradient[i] >= threshold
    # (brake at next point is high AND gradient leading into it is high)
    high_confidence_points = 0
    for i in range(len(gradient)):
        if zone_brake[i + 1] >= BRAKE_THRESHOLD_PERCENT and gradient[i] >= BRAKE_GRADIENT_THRESHOLD:
            high_confidence_points += 1
    
    max_gradient = float(np.max(gradient)) if len(gradient) > 0 else 0.0
    
    # Find the gradient leading INTO the first braking point
    brake_onset_gradient = None
    for i in range(len(gradient)):
        if zone_brake[i + 1] >= BRAKE_THRESHOLD_PERCENT:
            brake_onset_gradient = gradient[i]  # Gradient leading INTO the braking point
            break
    
    return {
        "zone_num": zone_num,
        "brake_start": zone["start_dist"],
        "brake_end": zone["end_dist"],
        "zone_length": zone["length"],
        "status": "ANALYZED",
        "max_gradient": max_gradient,
        "brake_onset_gradient": brake_onset_gradient,
        "high_confidence_points": high_confidence_points,
        "would_detect_high": high_confidence_points > 0,
    }


def main():
    print("=" * 80)
    print("BRAKE DETECTION THRESHOLD DIAGNOSTIC")
    print("=" * 80)
    print(f"\nCurrent Thresholds:")
    print(f"  BRAKE_THRESHOLD_PERCENT: {BRAKE_THRESHOLD_PERCENT}%")
    print(f"  BRAKE_GRADIENT_THRESHOLD: {BRAKE_GRADIENT_THRESHOLD} %/10m")
    print(f"\nDetection requires BOTH conditions at SAME telemetry point")
    print("=" * 80)

    # Enable FastF1 cache
    import os
    cache_dir = os.environ.get("FASTF1_CACHE", "/app/data/cache/sqlite")
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir, exist_ok=True)
    fastf1.Cache.enable_cache(cache_dir)

    all_results = []
    all_gradients = []
    all_onset_gradients = []

    for circuit_name, circuit_data in TEST_CIRCUITS.items():
        print(f"\n{'='*60}")
        print(f"CIRCUIT: {circuit_name}")
        print(f"{'='*60}")

        try:
            year, event, session_type = circuit_data["session"]
            print(f"Loading {year} {event} {session_type}...")
            session = fastf1.get_session(int(year), event, session_type)
            session.load()

            # Get fastest lap
            fastest_lap = session.laps.pick_fastest()
            if fastest_lap is None:
                print(f"  No fastest lap found for {circuit_name}")
                continue

            driver = fastest_lap["Driver"]
            print(f"Analyzing {driver}'s fastest lap")

            telemetry = fastest_lap.get_telemetry()
            if telemetry is None or len(telemetry) == 0:
                print(f"  No telemetry for {circuit_name}")
                continue

            # Find all braking zones dynamically
            braking_zones = find_braking_zones(telemetry)
            print(f"Found {len(braking_zones)} braking zones")

            for i, zone in enumerate(braking_zones):
                result = analyze_braking_zone(telemetry, zone, i + 1)
                all_results.append(result)

                if result["status"] == "ANALYZED" and result["max_gradient"] is not None:
                    all_gradients.append(result["max_gradient"])
                    if result["brake_onset_gradient"] is not None:
                        all_onset_gradients.append(result["brake_onset_gradient"])

                    print(f"\n  Zone {i+1}: {zone['start_dist']:.0f}m - {zone['end_dist']:.0f}m ({zone['length']:.0f}m)")
                    print(f"    Max Gradient near zone start: {result['max_gradient']:.2f} %/10m")
                    print(f"    Gradient at brake onset: {result['brake_onset_gradient']:.2f} %/10m" 
                          if result["brake_onset_gradient"] else "    Gradient at brake onset: N/A")
                    print(f"    Would detect HIGH confidence: {'YES' if result['would_detect_high'] else 'NO'}")
                    print(f"    Points meeting BOTH thresholds: {result['high_confidence_points']}")

        except Exception as e:
            print(f"  Error loading {circuit_name}: {e}")
            import traceback
            traceback.print_exc()
            continue

    # Summary and recommendations
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)

    analyzed = [r for r in all_results if r["status"] == "ANALYZED"]
    high_detected = [r for r in analyzed if r["would_detect_high"]]

    print(f"\nBraking zones analyzed: {len(analyzed)}")
    print(f"Would detect HIGH confidence: {len(high_detected)} / {len(analyzed)} ({100*len(high_detected)/len(analyzed):.0f}%)" if analyzed else "")

    if all_gradients:
        print(f"\nMax Gradient Statistics (per zone):")
        print(f"  Min: {np.min(all_gradients):.2f} %/10m")
        print(f"  Max: {np.max(all_gradients):.2f} %/10m")
        print(f"  Mean: {np.mean(all_gradients):.2f} %/10m")
        print(f"  Median: {np.median(all_gradients):.2f} %/10m")

    if all_onset_gradients:
        print(f"\nBrake Onset Gradient Statistics:")
        print(f"  Min: {np.min(all_onset_gradients):.2f} %/10m")
        print(f"  Max: {np.max(all_onset_gradients):.2f} %/10m")
        print(f"  Mean: {np.mean(all_onset_gradients):.2f} %/10m")
        print(f"  Median: {np.median(all_onset_gradients):.2f} %/10m")

        # Test different threshold values
        print("\n" + "=" * 80)
        print("THRESHOLD SENSITIVITY ANALYSIS (brake onset gradients)")
        print("=" * 80)

        for test_threshold in [5.0, 10.0, 20.0, 30.0, 40.0, 50.0, 75.0, 100.0]:
            zones_above = sum(1 for g in all_onset_gradients if g >= test_threshold)
            pct = (zones_above / len(all_onset_gradients)) * 100
            print(f"  Onset Gradient >= {test_threshold:.0f}: {zones_above}/{len(all_onset_gradients)} zones ({pct:.0f}%)")

        # Recommendation
        print("\n" + "=" * 80)
        print("RECOMMENDATIONS")
        print("=" * 80)

        median_gradient = np.median(all_onset_gradients)
        p10_gradient = np.percentile(all_onset_gradients, 10)
        
        print(f"\n  Observed brake onset gradients range from {np.min(all_onset_gradients):.1f} to {np.max(all_onset_gradients):.1f} %/10m")
        print(f"  Median onset gradient: {median_gradient:.1f} %/10m")
        print(f"  10th percentile: {p10_gradient:.1f} %/10m")
        
        if BRAKE_GRADIENT_THRESHOLD < p10_gradient:
            print(f"\n  Current BRAKE_GRADIENT_THRESHOLD ({BRAKE_GRADIENT_THRESHOLD}) is BELOW 10th percentile ({p10_gradient:.1f})")
            print(f"  This should detect most zones with HIGH confidence")
        else:
            recommended = round(p10_gradient * 0.9, 1)
            print(f"\n  Current BRAKE_GRADIENT_THRESHOLD ({BRAKE_GRADIENT_THRESHOLD}) is TOO HIGH")
            print(f"  RECOMMENDED: Lower threshold to ~{recommended} %/10m")
            print(f"  This would capture 90%+ of braking zones with HIGH confidence")


if __name__ == "__main__":
    main()
