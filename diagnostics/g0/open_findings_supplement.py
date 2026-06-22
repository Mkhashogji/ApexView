"""
OPEN-1/OPEN-2 supplement:
(A) T10/T17 brake point vs smoothing window — proves whether the shift is
    driven by compute_deceleration's SAMPLE-COUNT smoothing interacting with
    the (sparser) native spacing.
(B) Generality scan — |shift| / local-gap distribution across ALL corners on
    BOTH circuits, median-gap AND actual-straddling-gap, with a text histogram.
    Answers: are T10/T17 outliers or the visible tail of a distribution?

Run inside f1-api (analysis modules at /tmp/asvc).
"""
import sys, json
sys.path.insert(0, "/tmp/asvc")
sys.path.insert(0, "/app")

import numpy as np
import fastf1

from services.corner_analysis import (
    compute_deceleration, detect_apex_from_speed_v2, detect_braking_zone_v2,
)
from core.corner_config import CornerAnalysisConfig
from app.services.telemetry.native_acquisition import acquire_native_bundle
from app.services.telemetry.fastf1_client import FastF1Client

CONFIG = CornerAnalysisConfig()
# Corners loaded from the GOLDEN REQUEST bodies — the exact apex_distance values
# production sent (avoids any track-file ambiguity; e.g. Monaco's file is
# monaco.json, NOT marina_bay.json which is Singapore).
FIXTURES = [
    {"name": "shanghai", "round": 2, "ref": "PIA",
     "request": "/tmp/g0c/insights_request_shanghai.json"},
    {"name": "monaco", "round": 8, "ref": "NOR",
     "request": "/tmp/g0c/insights_request_monaco.json"},
]


def detect_brake(dist, speed, brake_bool, nominal_apex, smoothing):
    dist = np.asarray(dist, float); speed = np.asarray(speed, float)
    brake = np.asarray(brake_bool, float)
    if brake.max() <= 1.0:
        brake = brake * 100.0
    decel = compute_deceleration(dist, speed, smoothing)
    apex, _, _ = detect_apex_from_speed_v2(dist, speed, nominal_apex, CONFIG.apex_search_margin)
    bd, conf, meta = detect_braking_zone_v2(dist, brake, speed, decel, apex, CONFIG)
    return bd


def load(fix):
    fastf1.Cache.enable_cache("/app/data/cache")
    client = FastF1Client()
    s = fastf1.get_session(2025, fix["round"], "Q"); s.load()
    status = s.session_status if hasattr(s, "session_status") else None
    lap = client._select_fastest_valid_lap(s, fix["ref"], "Q3", status)
    merged = lap.get_telemetry()
    bundle = acquire_native_bundle(lap, driver=fix["ref"], session=f"2025_{fix['round']}_Q")
    with open(fix["request"], encoding="utf-8-sig") as f:  # tolerate PS BOM
        corners = [(c["corner_number"], float(c["apex_distance"]))
                   for c in json.load(f)["corners"]]
    return merged, bundle, corners


def local_gap(nd, at, win=60.0):
    pts = np.sort(nd[(nd >= at - win) & (nd <= at + win)])
    g = np.diff(pts); g = g[g > 0]
    below = nd[nd <= at]; above = nd[nd >= at]
    actual = (above.min() - below.max()) if len(below) and len(above) else np.nan
    return (float(np.median(g)) if len(g) else np.nan), float(actual)


def part_a(merged, bundle, corners):
    print("=" * 78)
    print("PART A SUPPLEMENT — brake point vs smoothing window (Monaco T10/T17)")
    print("=" * 78)
    ld, ls, lb = (merged[c].to_numpy() for c in ("Distance", "Speed", "Brake"))
    nd, nspd, nb = (bundle.car_native[c].to_numpy() for c in ("Distance", "Speed", "Brake"))
    apex = {c: a for c, a in corners}
    print(f"  {'corner':>6} {'window':>7} {'legacy_bp':>10} {'native_bp':>10} {'shift':>8}")
    for num in (9, 10, 11, 14, 17):  # all five Monaco brake-shift violators
        if num not in apex:
            continue
        for w in (1, 3, 5):
            lbp = detect_brake(ld, ls, lb, apex[num], w)
            nbp = detect_brake(nd, nspd, nb, apex[num], w)
            print(f"  T{num:<5d} {w:>7d} {lbp:>10.1f} {nbp:>10.1f} {nbp - lbp:>+8.1f}")
        print()
    print("  Interpretation: if native_bp -> legacy_bp as window -> 1, the shift is a")
    print("  smoothing-window x spacing artifact in compute_deceleration (excluded code).")
    print("  A shift that PERSISTS at window=1 is structural (no-braking-event / gap).")


def part_b(all_rows):
    print("\n" + "=" * 78)
    print("PART B — generality scan: |shift| / local-gap across ALL corners, both circuits")
    print("=" * 78)
    print(f"  {'fix':>9} {'T':>3} {'legacy_bp':>10} {'native_bp':>10} {'shift_m':>8} "
          f"{'medgap':>7} {'actgap':>7} {'x_med':>6} {'x_act':>6}")
    xmed_all, xact_all = [], []
    for r in all_rows:
        print(f"  {r['fix']:>9} {r['corner']:>3} {r['legacy_bp']:>10.1f} {r['native_bp']:>10.1f} "
              f"{r['shift']:>+8.1f} {r['med']:>7.1f} {r['act']:>7.1f} "
              f"{r['x_med']:>6.2f} {r['x_act']:>6.2f}")
        if np.isfinite(r["x_med"]):
            xmed_all.append(r["x_med"])
        if np.isfinite(r["x_act"]):
            xact_all.append(r["x_act"])

    def hist(vals, label):
        vals = np.array(vals)
        edges = [0, 0.25, 0.5, 0.75, 1.0, 1.25, 1.5, 2.0, 3.0, 1e9]
        names = ["0-.25", ".25-.5", ".5-.75", ".75-1", "1-1.25", "1.25-1.5",
                 "1.5-2", "2-3", ">3"]
        print(f"\n  histogram of |shift|/{label} (n={len(vals)}):")
        for i in range(len(names)):
            c = int(np.sum((vals >= edges[i]) & (vals < edges[i + 1])))
            print(f"    {names[i]:>9} | {'#' * c} {c}")
        print(f"    median={np.median(vals):.2f}  p90={np.percentile(vals, 90):.2f}  max={vals.max():.2f}")
    hist(xmed_all, "median-local-gap")
    hist(xact_all, "actual-straddling-gap")
    print("\n  corners exceeding 1.0x ACTUAL straddling gap (the honest 'one real sample' bar):")
    for r in all_rows:
        if np.isfinite(r["x_act"]) and r["x_act"] > 1.0001:
            print(f"    {r['fix']} T{r['corner']}: {r['x_act']:.2f}x actual  ({r['shift']:+.1f}m)")


def main():
    all_rows = []
    for fix in FIXTURES:
        merged, bundle, corners = load(fix)
        if fix["name"] == "monaco":
            part_a(merged, bundle, corners)
        ld, ls, lb = (merged[c].to_numpy() for c in ("Distance", "Speed", "Brake"))
        nd, nspd, nb = (bundle.car_native[c].to_numpy() for c in ("Distance", "Speed", "Brake"))
        for num, nominal in corners:
            lbp = detect_brake(ld, ls, lb, nominal, CONFIG.decel_smoothing_window)
            nbp = detect_brake(nd, nspd, nb, nominal, CONFIG.decel_smoothing_window)
            shift = nbp - lbp
            med, act = local_gap(nd, lbp)
            all_rows.append({
                "fix": fix["name"], "corner": num, "legacy_bp": lbp, "native_bp": nbp,
                "shift": shift, "med": med, "act": act,
                "x_med": abs(shift) / med if med else np.nan,
                "x_act": abs(shift) / act if act and np.isfinite(act) else np.nan,
            })
    part_b(all_rows)


if __name__ == "__main__":
    main()
