"""
A/B harness metric computation — pure functions over captured endpoint responses.

Used by:
  - diagnostics/g0/extract_legacy_metrics.py  (Phase 0.4 baseline extraction)
  - tools/ab_harness/run_ab.py                (Phase 4 legacy-vs-native diff)

All functions operate on plain dicts parsed from the captured JSON responses —
no application imports, no network. Runs anywhere with numpy.

Terminology: "fixture" = one captured lap pair (session, ref driver, comp driver)
with its telemetry / delta / insights / track responses.

NOTE on phase splits: determine_cause() in the analysis service splits each
corner zone using the *detected* apex, which is internal and not serialized.
We anchor the same split formula on the *nominal* apex_distance from the
response instead. Because legacy and native are measured with the IDENTICAL
formula, the legacy-vs-native comparison remains apples-to-apples; the values
are labelled "phase_*_approx" to flag the approximation.
"""
import json
import numpy as np

# Mirrors corner_analysis.determine_cause boundaries (PHASE_SPLIT_RATIO = 0.33)
PHASE_SPLIT_RATIO = 0.33


def load_json(path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def delta_at(distance_arr, delta_arr, d):
    """Replicates get_delta_at_distance: clamp + linear interp on the delta grid."""
    distance_arr = np.asarray(distance_arr, dtype=float)
    delta_arr = np.asarray(delta_arr, dtype=float)
    d = float(np.clip(d, distance_arr.min(), distance_arr.max()))
    return float(np.interp(d, distance_arr, delta_arr))


def delta_change(distance_arr, delta_arr, start, end):
    return delta_at(distance_arr, delta_arr, end) - delta_at(distance_arr, delta_arr, start)


def phase_deltas(distance_arr, delta_arr, zone_start, zone_end, apex):
    """Per-phase delta split, anchored on nominal apex (see module note)."""
    zone_len = zone_end - zone_start
    if zone_len <= 0:
        return {"braking": 0.0, "apex": 0.0, "exit": 0.0}
    braking_end = min(apex - 20, zone_start + zone_len * PHASE_SPLIT_RATIO)
    exit_start = max(apex + 20, zone_end - zone_len * PHASE_SPLIT_RATIO)
    braking_end = max(braking_end, zone_start)
    exit_start = min(exit_start, zone_end)
    return {
        "braking": delta_change(distance_arr, delta_arr, zone_start, braking_end),
        "apex": delta_change(distance_arr, delta_arr, braking_end, exit_start),
        "exit": delta_change(distance_arr, delta_arr, exit_start, zone_end),
    }


def min_speed_in_zone(distance, speed, zone_start, zone_end):
    """Min speed + its location within a distance window. None if no samples."""
    distance = np.asarray(distance, dtype=float)
    speed = np.asarray(speed, dtype=float)
    mask = (distance >= zone_start) & (distance <= zone_end)
    if mask.sum() == 0:
        return None, None
    idx = np.argmin(speed[mask])
    return float(speed[mask][idx]), float(distance[mask][idx])


def local_sample_gap(distance, at_distance, window_m=60.0):
    """
    Median inter-sample distance gap in a window around a track position.
    This is the LOCAL granularity floor used to judge brake-point shifts
    (Phase 5: shift <= one local native inter-sample gap).
    """
    distance = np.asarray(distance, dtype=float)
    mask = (distance >= at_distance - window_m) & (distance <= at_distance + window_m)
    pts = np.sort(distance[mask])
    if pts.size < 3:
        # fall back to whole-lap median spacing
        pts = np.sort(distance)
    gaps = np.diff(pts)
    gaps = gaps[gaps > 0]
    return float(np.median(gaps)) if gaps.size else float("nan")


def telemetry_summary(telemetry_item):
    """Per-driver array stats from a /telemetry response item."""
    dist = np.asarray(telemetry_item["distance"], dtype=float)
    spacing = np.diff(np.sort(dist))
    spacing = spacing[spacing > 0]
    return {
        "driver": telemetry_item["driver"],
        "lap_number": telemetry_item.get("lapNumber"),
        "lap_time": telemetry_item.get("lapTime"),
        "n_samples": int(dist.size),
        "total_distance_m": float(dist[-1] - dist[0]),
        "median_spacing_m": float(np.median(spacing)) if spacing.size else None,
    }


def fixture_metrics(telemetry, insights, track, delta_endpoint=None):
    """
    Compute the full metric set for one fixture from its captured responses.

    Args:
        telemetry: parsed /telemetry response (list of driver items)
        insights:  parsed /analysis/performance-insights response
        track:     parsed /track/{round} response
        delta_endpoint: parsed /telemetry/delta response (optional; legacy-only
                        raw-speed-integration endpoint, no frontend consumer)
    """
    tel_by_driver = {t["driver"]: t for t in telemetry}
    ref = insights["reference_driver"]
    result = insights["results"][0]
    comp = result["driver"]
    distance_arr = result["distance"]
    delta_arr = result["delta"]

    out = {
        "session_id": insights["session_id"],
        "reference_driver": ref,
        "compare_driver": comp,
        "circuit": track.get("circuitName"),
        "track_length": track.get("length"),
        "telemetry": {d: telemetry_summary(t) for d, t in tel_by_driver.items()},
        "closure": {
            "official_gap": result["official_gap"],
            "delta_grid_final": float(delta_arr[-1]) if delta_arr else None,
            "delta_grid_closure_error": (
                abs(float(delta_arr[-1]) - result["official_gap"]) if delta_arr else None
            ),
            "scaling_factor": result.get("scaling_factor"),
            "scaling_confidence": result.get("scaling_confidence"),
            "lap_breakdown": (
                {
                    "corner_total": result["lap_breakdown"]["corner_total"],
                    "straight_total": result["lap_breakdown"]["straight_total"],
                    "reconciliation_error": result["lap_breakdown"]["reconciliation_error"],
                    "reconciliation_valid": result["lap_breakdown"]["reconciliation_valid"],
                    "track_coverage": result["lap_breakdown"].get("track_coverage"),
                }
                if result.get("lap_breakdown")
                else None
            ),
        },
        "corners": [],
        "totals": {
            "total_corner_delta": result.get("total_corner_delta"),
            "corners_gaining": result.get("corners_gaining"),
            "corners_losing": result.get("corners_losing"),
        },
    }

    ref_tel = tel_by_driver.get(ref)
    comp_tel = tel_by_driver.get(comp)

    for cr in result["corner_results"]:
        zone_start, zone_end = cr["zone_start"], cr["zone_end"]
        apex = cr["apex_distance"]
        entry = {
            "corner_number": cr["corner_number"],
            "name": cr.get("name"),
            "apex_distance_nominal": apex,
            "brake_distance": cr["brake_distance"],
            "zone_start": zone_start,
            "zone_end": zone_end,
            "delta_change": cr["delta_change"],
            "cause": cr["cause"],
            "confidence": cr["confidence"],
            "phase_deltas_approx": phase_deltas(distance_arr, delta_arr, zone_start, zone_end, apex),
        }
        if ref_tel:
            spd, loc = min_speed_in_zone(ref_tel["distance"], ref_tel["speed"], zone_start, zone_end)
            entry["ref_min_speed_kmh"] = spd
            entry["ref_min_speed_location_m"] = loc
            entry["local_sample_gap_m"] = local_sample_gap(ref_tel["distance"], cr["brake_distance"])
        if comp_tel:
            spd, loc = min_speed_in_zone(comp_tel["distance"], comp_tel["speed"], zone_start, zone_end)
            entry["comp_min_speed_kmh"] = spd
            entry["comp_min_speed_location_m"] = loc
        out["corners"].append(entry)

    if delta_endpoint:
        d0 = delta_endpoint[0]
        out["delta_endpoint"] = {
            "n_points": len(d0["delta"]),
            "final_delta": d0["delta"][-1],
            "note": "raw speed-integration endpoint; no frontend consumer (dead code path, in G0 scope)",
        }

    return out
