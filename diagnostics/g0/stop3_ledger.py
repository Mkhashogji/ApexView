"""
STOP-3 attribution evidence — per-zone delta ledger (read-only).

Question (owner sign-off, G0 continuation §3): does the full 86 ms Shanghai
native lap-breakdown residual live in the pre-existing `zone_too_small`
stale-delta tripwire (`corner_analysis.py:1500-1507`, excluded code), or did
G0's changes corrupt the values themselves?

Method: for every corner in the captured native insights response, recompute
`delta_change` over its REPORTED clamped zone bounds via np.interp on the
response's own delta/distance arrays — exactly replicating
`get_delta_change_in_range` (clamp + linear interp). A corner whose reported
delta matches the recomputation is internally consistent; a mismatch means the
reported value was NOT computed over the reported bounds — which is precisely
what the `zone_too_small` path does (keeps the stale pre-clamp delta while the
bounds shrink). The sum of mismatches must localise the lap-breakdown residual.

Usage: python stop3_ledger.py <insights_json> [<insights_json_legacy>]
Run anywhere with numpy (no app imports, no network).
"""
import json
import sys

import numpy as np


def delta_at(distance, delta, d):
    d = float(np.clip(d, distance.min(), distance.max()))
    return float(np.interp(d, distance, delta))


def ledger(insights_path):
    with open(insights_path, encoding="utf-8") as f:
        ins = json.load(f)
    res = ins["results"][0]
    distance = np.asarray(res["distance"], dtype=float)
    delta = np.asarray(res["delta"], dtype=float)
    lb = res["lap_breakdown"]

    print(f"file: {insights_path}")
    print(f"official_gap={res['official_gap']:+.4f}s  "
          f"corner_total={lb['corner_total']:+.4f}s  straight_total={lb['straight_total']:+.4f}s  "
          f"reconciliation_error={lb['reconciliation_error']:.4f}s  valid={lb['reconciliation_valid']}")
    print()
    print(f"{'corner':>7} {'zone':>20} {'reported':>10} {'recomputed':>11} {'mismatch':>10}")

    rows = []
    for cr in res["corner_results"]:
        zs, ze = cr["zone_start"], cr["zone_end"]
        reported = cr["delta_change"]
        recomputed = delta_at(distance, delta, ze) - delta_at(distance, delta, zs)
        mismatch = reported - recomputed
        rows.append((cr["corner_number"], zs, ze, reported, recomputed, mismatch))
        marker = "  <-- STALE (zone_too_small)" if abs(mismatch) > 0.0005 else ""
        print(f"  T{cr['corner_number']:<5d} [{zs:8.1f},{ze:8.1f}] {reported:+10.4f} "
              f"{recomputed:+11.4f} {mismatch:+10.4f}{marker}")

    corner_mismatch = sum(r[5] for r in rows)

    # ---- straight-segment ledger (same recomputation over reported bounds) ----
    print()
    print(f"{'straight':>9} {'span':>22} {'reported':>10} {'recomputed':>11} {'mismatch':>10}")
    straight_mismatch = 0.0
    for seg in lb.get("straight_segments", []):
        ss, se = seg["start_distance"], seg["end_distance"]
        reported = seg["delta_change"]
        recomputed = delta_at(distance, delta, se) - delta_at(distance, delta, ss)
        mismatch = reported - recomputed
        straight_mismatch += mismatch
        marker = "  <-- STALE" if abs(mismatch) > 0.0005 else ""
        print(f"  S{seg['segment_number']:<6d} [{ss:9.1f},{se:9.1f}] {reported:+10.4f} "
              f"{recomputed:+11.4f} {mismatch:+10.4f}{marker}")

    # ---- tiling audit: holes/overlaps between consecutive reported intervals ----
    intervals = [(r[1], r[2], f"T{r[0]}") for r in rows]
    intervals += [(s["start_distance"], s["end_distance"], f"S{s['segment_number']}")
                  for s in lb.get("straight_segments", [])]
    intervals.sort()
    print()
    print("tiling audit (holes/overlaps between consecutive reported intervals):")
    tiling_delta = 0.0
    prev_end, prev_name = None, None
    for (s, e, name) in intervals:
        if prev_end is not None and abs(s - prev_end) > 0.05:
            d = delta_at(distance, delta, s) - delta_at(distance, delta, prev_end)
            kind = "HOLE" if s > prev_end else "OVERLAP"
            # a hole's delta is MISSING from the sum (+d uncounted); an overlap's
            # delta is double-counted (-d to reconcile)
            contrib = d if s > prev_end else -d
            tiling_delta += contrib
            print(f"  {kind:7s} {prev_name}->{name}: [{min(prev_end, s):9.1f},{max(prev_end, s):9.1f}] "
                  f"span={abs(s - prev_end):7.1f}m  delta={d:+.4f}s  contribution={contrib:+.4f}s")
        prev_end, prev_name = e, name
    # boundary coverage at lap start/end
    lo, hi = intervals[0][0], max(e for _, e, _ in intervals)
    head = delta_at(distance, delta, lo) - delta_at(distance, delta, distance.min())
    tail = delta_at(distance, delta, distance.max()) - delta_at(distance, delta, hi)
    if abs(head) > 0.0005:
        print(f"  HEAD    grid_start->first interval [{distance.min():.1f},{lo:.1f}]: uncounted {head:+.4f}s")
    if abs(tail) > 0.0005:
        print(f"  TAIL    last interval->grid_end [{hi:.1f},{distance.max():.1f}]: uncounted {tail:+.4f}s")
    uncovered = head + tail

    print()
    explained = corner_mismatch + straight_mismatch - tiling_delta - uncovered
    print(f"corner stale mismatches      : {corner_mismatch:+.4f}s")
    print(f"straight stale mismatches    : {straight_mismatch:+.4f}s")
    print(f"tiling holes/overlaps        : {tiling_delta:+.4f}s (uncounted/double-counted delta)")
    print(f"uncovered head/tail          : {uncovered:+.4f}s")
    print(f"reported sum - telescoped    : {explained:+.4f}s   (residual is |this|)")
    print(f"lap_breakdown residual       : {lb['reconciliation_error']:.4f}s")
    fully = abs(abs(explained) - lb["reconciliation_error"]) <= 0.005
    print(f"ATTRIBUTION: {'COMPLETE within 5ms' if fully else 'NOT fully attributed'}")
    return explained, lb["reconciliation_error"]


if __name__ == "__main__":
    for path in sys.argv[1:]:
        ledger(path)
        print("=" * 70)
