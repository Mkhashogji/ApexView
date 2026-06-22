"""
STOP-4 classification — Monaco brake-shift violating corners (owner sign-off, Option 1).

For each corner that violated the Phase-5 brake-shift expectation, determine:
- gap-overlap: the corner's NATIVE analysis zone intersects a flagged
  acquisition gap (either driver's car stream);
- pseudo-corner: pre-apex speed drop <= 15 km/h on the native reference
  telemetry (max speed in [apex-250, apex] minus min speed in the zone) —
  no real braking event exists for the detector to locate.

Exclude-but-preserve: classified corners stay in the report with their shifts;
they are excluded only from the Phase-5 pass/fail count. Any violating corner
that is NEITHER is an OPEN FINDING not covered by the acceptance (halt+report).

Usage: python stop4_classify.py <ab_report.json> <native_telemetry_monaco.json>
Emits a table + JSON to stdout (the JSON block feeds known_deviations.json).
"""
import json
import sys

import numpy as np

PSEUDO_DROP_KMH = 15.0


def main():
    with open(sys.argv[1], encoding="utf-8") as f:
        ab = json.load(f)
    with open(sys.argv[2], encoding="utf-8") as f:
        tel = json.load(f)

    fx = next(x for x in ab["fixtures"] if x["fixture"] == "monaco")
    tel_by_driver = {t["driver"]: t for t in tel}
    ref = fx["native_metrics"]["reference_driver"]
    ref_tel = tel_by_driver[ref]
    rd = np.asarray(ref_tel["distance"], dtype=float)
    rv = np.asarray(ref_tel["speed"], dtype=float)

    # all gaps, both drivers (camelCase from the wire)
    gaps = []
    for drv, glist in fx["gap_inventory"].items():
        for g in glist:
            gaps.append((drv, float(g["dStart"]), float(g["dEnd"]), float(g["dt"])))

    native_corners = {c["corner_number"]: c for c in fx["native_metrics"]["corners"]}
    violators = [d for d in fx["corner_diffs"] if not d["brake_within_one_gap"]]

    print(f"reference driver: {ref}; gaps considered: {len(gaps)} (both drivers)")
    print(f"pseudo-corner criterion: pre-apex speed drop <= {PSEUDO_DROP_KMH} km/h "
          f"(native ref telemetry)\n")
    hdr = (f"{'T':>3} {'shift_m':>8} {'gap_m':>6} {'zone':>20} {'drop_kmh':>9} "
           f"{'gap?':>5} {'pseudo?':>8}  classification")
    print(hdr)

    registry_corners, open_findings = [], []
    for v in sorted(violators, key=lambda x: x["corner"]):
        num = v["corner"]
        nc = native_corners[num]
        zs, ze = nc["zone_start"], nc["zone_end"]
        apex = nc["apex_distance_nominal"]

        overlapping = [(drv, gs, ge) for (drv, gs, ge, _) in gaps if gs <= ze and ge >= zs]

        pre = (rd >= apex - 250) & (rd <= apex)
        inzone = (rd >= zs) & (rd <= ze)
        if pre.sum() >= 2 and inzone.sum() >= 2:
            drop = float(rv[pre].max() - rv[inzone].min())
        else:
            drop = float("nan")
        pseudo = (not np.isnan(drop)) and drop <= PSEUDO_DROP_KMH

        if overlapping and pseudo:
            cls = "gap-overlap + pseudo-corner"
        elif overlapping:
            cls = "gap-overlap (" + ", ".join(
                f"{d} {gs:.0f}-{ge:.0f}m" for d, gs, ge in overlapping) + ")"
        elif pseudo:
            cls = "pseudo-corner (no braking event)"
        else:
            cls = "** NEITHER — OPEN FINDING **"

        print(f"{num:>3} {v['brake_shift_m']:>+8.1f} {v['local_native_gap_m']:>6.1f} "
              f"[{zs:7.1f},{ze:7.1f}] {drop:>9.1f} {'Y' if overlapping else 'N':>5} "
              f"{'Y' if pseudo else 'N':>8}  {cls}")

        entry = {
            "corner": num,
            "brake_shift_m": round(v["brake_shift_m"], 2),
            "local_native_gap_m": round(v["local_native_gap_m"], 2),
            "zone": [round(zs, 1), round(ze, 1)],
            "pre_apex_speed_drop_kmh": None if np.isnan(drop) else round(drop, 1),
            "gap_overlap": [f"{d} {gs:.0f}-{ge:.0f}m" for d, gs, ge in overlapping],
            "pseudo_corner": bool(pseudo),
            "classification": cls,
        }
        if "OPEN FINDING" in cls:
            open_findings.append(entry)
        else:
            registry_corners.append(entry)

    print()
    print("REGISTRY_JSON_BEGIN")
    print(json.dumps({"covered": registry_corners, "open_findings": open_findings}, indent=2))
    print("REGISTRY_JSON_END")
    if open_findings:
        print(f"\n*** {len(open_findings)} corner(s) NOT covered by the acceptance — HALT AND REPORT ***")
        sys.exit(2)


if __name__ == "__main__":
    main()
