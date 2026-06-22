"""
OPEN-1/OPEN-2 forensics — sample-level reconstruction of the Monaco T10/T17
brake-point shifts, legacy (merged frame) vs native (real car samples).

Runs the PRODUCTION detection path by importing the REAL analysis-service
functions (no re-implementation) and feeding them the exact arrays each
acquisition head serves. Production calls analyze_corners_v2 WITHOUT circuit_id,
so detection uses the DEFAULT CornerAnalysisConfig (braking_decel_threshold
-5.0, decel_smoothing_window 5, apex_search_margin 50, braking_point_tolerance
20) — NOT Monaco's overrides. This script mirrors that exactly.

Two hypotheses tested per corner:
  H-quantisation: legacy brake point sat on an INTERPOLATED merged row (FastF1
    Source != 'car'); native snapped to the nearest real car sample; the shift
    is withdrawn phantom precision.
  H-defect: native distance integration / window registration / detector
    indexing puts the brake point on the WRONG real sample.

Run inside f1-api (fastf1 + cache + copied analysis modules at /tmp/asvc):
    python open_findings_forensics.py
"""
import sys
sys.path.insert(0, "/tmp/asvc")   # analysis-service services/ + core/
sys.path.insert(0, "/app")        # f1-api app (native_acquisition, FastF1Client)

import numpy as np
import fastf1

from services.corner_analysis import (
    compute_deceleration,
    detect_apex_from_speed_v2,
    detect_braking_zone_v2,
)
from core.corner_config import CornerAnalysisConfig
from app.services.telemetry.native_acquisition import acquire_native_bundle
from app.services.telemetry.fastf1_client import FastF1Client

CONFIG = CornerAnalysisConfig()  # DEFAULT — matches production (no circuit_id)
REF = "NOR"
SESSION = (2025, 8)              # Monaco
CORNERS = {10: 2050.0, 17: 3000.0}  # nominal apex distances from marina_bay.json
# reported brake_distance (NOR ref) from diagnostics/g0/ab_report.json:
REPORTED = {10: {"legacy": 1966.08, "native": 1946.92},
            17: {"legacy": 2807.86, "native": 2794.59}}


def served_arrays_legacy(lap):
    """Exactly what _get_telemetry_legacy serves: the merged-frame columns."""
    tel = lap.get_telemetry()
    return tel  # keep the frame (need Source/SessionTime too)


def detect(dist, speed, brake_bool, nominal_apex):
    """Replicates analyze_single_corner_v2's detection prelude + the three
    detector calls, returning every intermediate for tracing."""
    dist = np.asarray(dist, dtype=float)
    speed = np.asarray(speed, dtype=float)
    brake = np.asarray(brake_bool, dtype=float)
    if brake.max() <= 1.0:           # production up-converts 0/1 -> 0/100
        brake = brake * 100.0
    decel = compute_deceleration(dist, speed, CONFIG.decel_smoothing_window)
    apex, apex_speed, apex_conf = detect_apex_from_speed_v2(
        dist, speed, nominal_apex, CONFIG.apex_search_margin)
    brake_dist, conf, meta = detect_braking_zone_v2(
        dist, brake, speed, decel, apex, CONFIG)
    return {
        "dist": dist, "speed": speed, "brake": brake, "decel": decel,
        "detected_apex": apex, "apex_speed": apex_speed, "apex_conf": apex_conf,
        "brake_dist": brake_dist, "conf": conf, "meta": meta,
    }


def trace_threshold(res, label):
    """Reproduce detect_braking_zone_v2's two-stage decision and print it."""
    dist, brake, decel = res["dist"], res["brake"], res["decel"]
    apex = res["detected_apex"]
    ss, se = apex - 300, apex - 30
    ss = max(ss, dist.min()); se = min(se, dist.max())
    zmask = (dist >= ss) & (dist <= se)
    zidx = np.where(zmask)[0]
    bn = brake / 100.0 if brake.max() > 1.0 else brake
    cand = zidx[bn[zidx] >= 0.5]
    print(f"    [{label}] search zone [{ss:.1f}, {se:.1f}]m  ({len(zidx)} samples)")
    if len(cand) == 0:
        print(f"    [{label}] STAGE 1: no boolean brake>=0.5 in zone -> decel-only/fallback")
        print(f"    [{label}] meta: {res['meta']}")
        return
    b_idx = int(cand[0])
    print(f"    [{label}] STAGE 1 boolean brake-on: idx {b_idx} @ {dist[b_idx]:.1f}m "
          f"(brake={bn[b_idx]:.0f})")
    # stage 2 backward walk
    r = b_idx; steps = []
    while r > zidx[0]:
        di = min(r - 1, len(decel) - 1)
        dval = decel[di] if di >= 0 else float("nan")
        if di >= 0 and dval > CONFIG.braking_decel_threshold:
            steps.append((r, dist[r], dval, "STOP decel>thr"))
            break
        steps.append((r, dist[r], dval, "walk back (decel<=thr)"))
        r -= 1
    print(f"    [{label}] STAGE 2 backward walk (stop when decel > {CONFIG.braking_decel_threshold}):")
    for (i, d, dv, why) in steps:
        print(f"        idx {i} @ {d:7.1f}m  decel[i-1]={dv:6.1f} m/s^2  -> {why}")
    print(f"    [{label}] => brake_dist = {res['brake_dist']:.2f}m  conf={res['conf']}  "
          f"stage={res['meta'].get('stage')}")


def zone_table(merged, native_res, legacy_res, num, apex_for_zone):
    """Print every native sample in the braking search zone with the legacy
    and native brake points overlaid, and the legacy brake row's Source tag."""
    nd = native_res["dist"]; ns = native_res["speed"]; nb = native_res["brake"]
    ndecel = native_res["decel"]
    ss, se = apex_for_zone - 300, apex_for_zone - 30
    zmask = (nd >= ss) & (nd <= se)
    zidx = np.where(zmask)[0]
    leg_bp = legacy_res["brake_dist"]; nat_bp = native_res["brake_dist"]
    print(f"\n  --- T{num}: native braking search zone [{ss:.0f},{se:.0f}]m "
          f"(native detected apex {native_res['detected_apex']:.1f}m) ---")
    print(f"  {'idx':>4} {'dist_m':>9} {'speed':>7} {'brake':>6} {'dt_prev_m':>10} "
          f"{'decel':>8}  marker")
    md = merged["Distance"].to_numpy()
    for i in zidx:
        dt_prev = nd[i] - nd[i - 1] if i > 0 else 0.0
        dv = ndecel[i - 1] if 0 < i <= len(ndecel) else float("nan")
        marks = []
        if i > 0 and nd[i - 1] <= nat_bp <= nd[i]:
            marks.append("NATIVE-BP-between")
        if abs(nd[i] - nat_bp) < 1e-6:
            marks.append("NATIVE-BP")
        if i > 0 and nd[i - 1] <= leg_bp <= nd[i]:
            marks.append("legacy-BP-between(native-axis)")
        print(f"  {i:>4} {nd[i]:>9.1f} {ns[i]:>7.0f} {nb[i]/100:>6.0f} {dt_prev:>10.1f} "
              f"{dv:>8.1f}  {' '.join(marks)}")
    # legacy brake row Source classification (on the MERGED frame)
    leg_idx = int(np.argmin(np.abs(md - leg_bp)))
    src = merged["Source"].to_numpy()[leg_idx] if "Source" in merged.columns else "?"
    print(f"  legacy brake point {leg_bp:.1f}m -> nearest merged row idx {leg_idx} "
          f"@ {md[leg_idx]:.1f}m, FastF1 Source = '{src}'  "
          f"({'REAL car measurement' if src == 'car' else 'INTERPOLATED car channels'})")
    # boolean brake row source too
    bn = (merged['Brake'].to_numpy().astype(float))
    return src


def gap_distribution(nd, brake_pt, label):
    """Local native gap stats in the +/-60m window the harness uses, plus the
    ACTUAL gap straddling the brake point."""
    win = (nd >= brake_pt - 60) & (nd <= brake_pt + 60)
    pts = np.sort(nd[win])
    gaps = np.diff(pts)
    gaps = gaps[gaps > 0]
    # actual gap straddling the brake point
    below = nd[nd <= brake_pt]
    above = nd[nd >= brake_pt]
    actual = (above.min() - below.max()) if len(below) and len(above) else float("nan")
    print(f"    [{label}] local gaps (+/-60m, n={len(gaps)}): "
          f"median={np.median(gaps):.1f}m  min={gaps.min():.1f}m  max={gaps.max():.1f}m  "
          f"actual-straddling={actual:.1f}m")
    return float(np.median(gaps)), float(actual)


def registration_delta(merged, bundle, at_distance):
    """native Distance - merged Distance at the merged sample nearest a track
    position, evaluated at the same SessionTime instant."""
    md = merged["Distance"].to_numpy()
    mt = merged["SessionTime"].dt.total_seconds().to_numpy()
    cd = bundle.car_native["Distance"].to_numpy()
    ct = bundle.car_native["SessionTime"].dt.total_seconds().to_numpy()
    mi = int(np.argmin(np.abs(md - at_distance)))
    t = mt[mi]
    nd_at = float(np.interp(t, ct, cd))
    return nd_at - md[mi]


def main():
    fastf1.Cache.enable_cache("/app/data/cache")
    client = FastF1Client()
    session = fastf1.get_session(*SESSION, "Q")
    session.load()
    status = session.session_status if hasattr(session, "session_status") else None
    lap = client._select_fastest_valid_lap(session, REF, "Q3", status)
    print(f"reference {REF}: lap {int(lap['LapNumber'])}  time {lap['LapTime']}")
    print(f"config: DEFAULT (braking_decel_threshold={CONFIG.braking_decel_threshold}, "
          f"decel_smoothing_window={CONFIG.decel_smoothing_window}, "
          f"apex_search_margin={CONFIG.apex_search_margin})  -- matches production\n")

    merged = lap.get_telemetry()
    bundle = acquire_native_bundle(lap, driver=REF, session="2025_8_Qualifying")
    if "Source" in merged.columns:
        import collections
        print("merged Source tag counts:", dict(collections.Counter(merged["Source"].to_numpy())))
    print(f"merged rows {len(merged)}  native car rows {len(bundle.car_native)}\n")

    leg_dist = merged["Distance"].to_numpy()
    leg_speed = merged["Speed"].to_numpy()
    leg_brake = merged["Brake"].to_numpy()
    nat_dist = bundle.car_native["Distance"].to_numpy()
    nat_speed = bundle.car_native["Speed"].to_numpy()
    nat_brake = bundle.car_native["Brake"].to_numpy()

    for num, nominal in CORNERS.items():
        print("=" * 78)
        print(f"CORNER T{num}  (nominal apex {nominal:.0f}m)")
        print("=" * 78)
        leg = detect(leg_dist, leg_speed, leg_brake, nominal)
        nat = detect(nat_dist, nat_speed, nat_brake, nominal)

        print(f"  detected apex: legacy {leg['detected_apex']:.1f}m  native {nat['detected_apex']:.1f}m  "
              f"(delta {nat['detected_apex'] - leg['detected_apex']:+.1f}m)")
        print(f"  brake point:   legacy {leg['brake_dist']:.2f}m  native {nat['brake_dist']:.2f}m  "
              f"(shift {nat['brake_dist'] - leg['brake_dist']:+.2f}m)")
        print(f"  reproduces reported? legacy {leg['brake_dist']:.1f} vs {REPORTED[num]['legacy']} | "
              f"native {nat['brake_dist']:.1f} vs {REPORTED[num]['native']}")

        print("\n  THRESHOLD-CROSSING TRACE:")
        trace_threshold(leg, "legacy")
        trace_threshold(nat, "native")

        src = zone_table(merged, nat, leg, num, nat["detected_apex"])

        print("\n  LOCAL GAP DISTRIBUTION:")
        med, actual = gap_distribution(nat_dist, leg["brake_dist"], "native@legacy-bp")
        shift = abs(nat["brake_dist"] - leg["brake_dist"])
        print(f"    shift {shift:.1f}m  =>  {shift/med:.2f}x median local gap  |  "
              f"{shift/actual:.2f}x actual straddling gap")

        print("\n  REGISTRATION DELTA (native - merged Distance at same instant):")
        for d in (nominal, leg["brake_dist"]):
            print(f"    at {d:.0f}m: {registration_delta(merged, bundle, d):+.3f}m")
        print()


if __name__ == "__main__":
    main()
