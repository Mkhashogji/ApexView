"""
G0 A/B harness — legacy vs native acquisition diff (permanent regression gate).

Runs the fixed fixture set through both acquisition heads and emits a single
diff report (markdown + JSON). Asserts the G0 Phase 5 expectations
programmatically and exits non-zero on violation, so it can serve as a
CI-style regression gate from G0 onward.

Phase 5 expectation -> implementation map
-----------------------------------------
- Closure invariant (adapted per diagnostics/g0/00_phase0_report.md §6):
    delta-grid closure |delta[-1] - official_gap| <= 1e-6 on BOTH heads (hard);
    lap_breakdown error: native <= legacy + 5 ms (hard);
    Shanghai lap_breakdown <= 5 ms absolute (hard).
    (The original <=5 ms absolute is unachievable on Monaco at G0: the LEGACY
    pipeline already measures 0.492 s there, caused by excluded zone logic.)
- Response schemas: recursive shape/type compare vs golden (hard).
- Brake-point shift: <= one LOCAL native inter-sample gap per corner
  (computed from native data at that corner, never hardcoded); flag each
  violation; > 20% of corners violating -> STOP (hard).
- Apex speed: min speed inside the FIXED legacy zone on both heads' telemetry
  (fixed window isolates the substrate effect from zone-boundary drift);
  |diff| > 1e-2 km/h -> flag and report (not a failure).
- Total lap delta attribution: native sum vs legacy sum reported;
  redistribution between phases/corners is NOT a failure.
- Confidence tiers: transition table reported (no confidence code changed).
- Corner registration: median per-corner min-speed-location shift < 5 m
  (median across corners suppresses sample-quantisation noise; the
  pre-implementation probe measured constant offsets of 0.65 m / 0.09 m).
- Provenance: row tagging is asserted at bundle level by
  apps/api/tests/test_native_acquisition.py (provenance is internal and never
  serialized); the harness asserts meta.schemaVersion == native_v1 (hard).
- Gap law: known Monaco dropouts detected; no false gaps at normal jitter
  (gap inventory reported; ratio sanity-checked > 3.0) (hard if inventory
  endpoint fails).
- Performance: runtimes reported (informational).
- Gate #4: legacy head byte-identical to golden snapshots after stripping
  volatile fields (phase_timing, total_duration_ms) (hard).

Usage (inside the f1-api container, repo files under /tmp/g0):
    python tools/ab_harness/run_ab.py \
        --golden diagnostics/g0/golden/legacy \
        --out diagnostics/g0
Environment: API_URL (default http://localhost:8000),
             ANALYSIS_URL (default http://analysis:8501).
"""
import argparse
import json
import os
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from metrics import (  # noqa: E402
    fixture_metrics,
    load_json,
    local_sample_gap,
    min_speed_in_zone,
)

API_URL = os.environ.get("API_URL", "http://localhost:8000")
ANALYSIS_URL = os.environ.get("ANALYSIS_URL", "http://analysis:8501")

FIXTURES = [
    {"name": "shanghai", "session": "2025_2_Qualifying", "round": 2, "ref": "PIA", "comp": "RUS"},
    {"name": "monaco", "session": "2025_8_Qualifying", "round": 8, "ref": "NOR", "comp": "LEC"},
]

VOLATILE_INSIGHT_KEYS = {"phase_timing", "total_duration_ms"}


# =============================================================================
# HTTP helpers (stdlib only — the api image has no httpx)
# =============================================================================

def http_get(url, timeout=300):
    t0 = time.time()
    with urllib.request.urlopen(url, timeout=timeout) as r:
        body = r.read()
    return json.loads(body), body, time.time() - t0


def http_post(url, payload, timeout=300):
    data = json.dumps(payload).encode()
    req = urllib.request.Request(
        url, data=data, headers={"Content-Type": "application/json"})
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as r:
        body = r.read()
    return json.loads(body), body, time.time() - t0


def fetch_head(fixture, head):
    """Fetch all endpoint responses for one fixture under one acquisition head."""
    f = fixture
    q = urllib.parse.urlencode
    out = {"head": head, "runtimes_s": {}}

    track, _, dt = http_get(f"{API_URL}/track/{f['round']}?season=2025")
    out["track"] = track
    out["runtimes_s"]["track"] = dt

    tel_q = q([("session", f["session"]), ("drivers", f["ref"]), ("drivers", f["comp"]),
               ("session_part", "Q3"), ("acquisition", head)])
    out["telemetry"], out["telemetry_bytes"], dt = http_get(f"{API_URL}/telemetry?{tel_q}")
    out["runtimes_s"]["telemetry"] = dt

    d_q = q([("session", f["session"]), ("reference_driver", f["ref"]),
             ("compare_drivers", f["comp"]), ("session_part", "Q3"), ("acquisition", head)])
    out["delta"], out["delta_bytes"], dt = http_get(f"{API_URL}/telemetry/delta?{d_q}")
    out["runtimes_s"]["delta"] = dt

    if head == "native":
        m_q = q([("session", f["session"]), ("drivers", f["ref"]), ("drivers", f["comp"]),
                 ("session_part", "Q3")])
        out["meta"], _, dt = http_get(f"{API_URL}/telemetry/meta?{m_q}")
        out["runtimes_s"]["meta"] = dt

    corners = [
        {"corner_number": c["cornerNumber"], "name": c.get("name"),
         "apex_distance": c["distance"], "corner_type": c["type"]}
        for c in track["corners"]
    ]
    payload = {
        "session_id": f["session"],
        "reference_driver": f["ref"],
        "compare_drivers": [f["comp"]],
        "corners": corners,
        "mode": "engineer",
        "session_part": "Q3",
        "include_telemetry": True,
        "track_length": track["length"],
        "acquisition_mode": head,
    }
    out["insights"], out["insights_bytes"], dt = http_post(
        f"{ANALYSIS_URL}/analysis/performance-insights", payload)
    out["runtimes_s"]["insights"] = dt
    return out


# =============================================================================
# Schema / byte comparison
# =============================================================================

def shape_of(obj, depth=0):
    """Recursive structural shape: dict key-sets, list element shape, scalar type."""
    if isinstance(obj, dict):
        return {k: shape_of(v, depth + 1) for k, v in sorted(obj.items())}
    if isinstance(obj, list):
        if not obj:
            return ["<empty>"]
        return [shape_of(obj[0], depth + 1)]
    if obj is None:
        return "null"
    if isinstance(obj, bool):
        return "bool"
    if isinstance(obj, (int, float)):
        return "number"
    return type(obj).__name__


def shapes_equal(a, b, path="$"):
    """Compare structural shapes; returns list of mismatch descriptions."""
    issues = []
    if type(a) is not type(b):
        # tolerate null vs typed (optional fields legitimately null)
        if "null" in (a, b):
            return issues
        issues.append(f"{path}: {a} != {b}")
        return issues
    if isinstance(a, dict):
        only_a = set(a) - set(b)
        only_b = set(b) - set(a)
        if only_a:
            issues.append(f"{path}: keys only in golden: {sorted(only_a)}")
        if only_b:
            issues.append(f"{path}: keys only in live: {sorted(only_b)}")
        for k in set(a) & set(b):
            issues.extend(shapes_equal(a[k], b[k], f"{path}.{k}"))
    elif isinstance(a, list):
        if a != ["<empty>"] and b != ["<empty>"]:
            issues.extend(shapes_equal(a[0], b[0], f"{path}[0]"))
    elif a != b:
        issues.append(f"{path}: {a} != {b}")
    return issues


def strip_volatile(obj):
    if isinstance(obj, dict):
        return {k: strip_volatile(v) for k, v in obj.items() if k not in VOLATILE_INSIGHT_KEYS}
    if isinstance(obj, list):
        return [strip_volatile(v) for v in obj]
    return obj


# =============================================================================
# Assertions
# =============================================================================

class Check:
    """
    Verdict ledger with known-deviation semantics (G0 continuation §4):
    - KNOWN-DEVIATION: a registered, bounded acceptance — visibly flagged,
      never silently green; HARD FAIL if it grows beyond its recorded bound.
    - OPEN-FINDING: recognised but NOT accepted (owner decision pending) —
      rendered loudly, drives a distinct non-zero exit code.
    - any unregistered hard violation stays a hard failure.
    """

    def __init__(self):
        self.hard_failures = []
        self.flags = []
        self.info = []
        self.known_deviations = []
        self.open_findings = []

    def hard(self, ok, msg):
        (self.info if ok else self.hard_failures).append(("PASS " if ok else "FAIL ") + msg)

    def flag(self, ok, msg):
        (self.info if ok else self.flags).append(("ok   " if ok else "FLAG ") + msg)

    def known(self, msg):
        self.known_deviations.append("KNOWN-DEVIATION " + msg)

    def open_finding(self, msg):
        self.open_findings.append("OPEN-FINDING " + msg)


def load_registry(path):
    """Load known_deviations.json; absent registry = empty (everything hard).
    utf-8-sig: tolerate the BOM that Windows editors prepend."""
    p = Path(path)
    if not p.exists():
        return {"deviations": [], "open_findings": []}
    with open(p, encoding="utf-8-sig") as f:
        reg = json.load(f)
    return {"deviations": reg.get("deviations", []),
            "open_findings": reg.get("open_findings", [])}


def _registered_closure(registry, fixture):
    for d in registry["deviations"]:
        if d["fixture"] == fixture and d["scope"] == "lap_breakdown_closure":
            return d
    return None


def _registered_brake_corners(registry, fixture):
    merged = {}
    for d in registry["deviations"]:
        if d["fixture"] == fixture and d["scope"] == "brake_shift":
            merged.update({int(k): v for k, v in d.get("corners", {}).items()})
    return merged


def _open_brake_corners(registry, fixture):
    return {of["corner"]: of for of in registry["open_findings"]
            if of["fixture"] == fixture and of["scope"] == "brake_shift"}


def compare_fixture(fixture, legacy, native, golden_dir, check, registry):
    name = fixture["name"]
    out = {"fixture": name}

    m_leg = fixture_metrics(legacy["telemetry"], legacy["insights"], legacy["track"], legacy["delta"])
    m_nat = fixture_metrics(native["telemetry"], native["insights"], native["track"], native["delta"])
    out["legacy_metrics"] = m_leg
    out["native_metrics"] = m_nat

    # ---- closure (adapted criterion; Phase 0 report §6 + §4 registry) ----
    for head, m in (("legacy", m_leg), ("native", m_nat)):
        err = m["closure"]["delta_grid_closure_error"]
        check.hard(err is not None and err <= 1e-6,
                   f"[{name}] {head} delta-grid closure |delta[-1]-official| = {err:.2e} <= 1e-6")
    lb_leg = m_leg["closure"]["lap_breakdown"]["reconciliation_error"]
    lb_nat = m_nat["closure"]["lap_breakdown"]["reconciliation_error"]
    closure_reg = _registered_closure(registry, name)
    if closure_reg is not None:
        # registered acceptance: bounded, visibly flagged, growth = hard fail
        if lb_nat <= closure_reg["bound"]:
            check.known(
                f"[{name}] {closure_reg['id']}: lap_breakdown closure {lb_nat:.4f}s "
                f"<= registered bound {closure_reg['bound']:.3f}s "
                f"(accepted {closure_reg['accepted']}, owner: {closure_reg['owner_gate']})")
        else:
            check.hard(False,
                       f"[{name}] {closure_reg['id']} GREW BEYOND BOUND: "
                       f"{lb_nat:.4f}s > {closure_reg['bound']:.3f}s")
        check.flag(True, f"[{name}] lap_breakdown legacy reference: {lb_leg:.4f}s")
    else:
        check.hard(lb_nat <= lb_leg + 0.005,
                   f"[{name}] lap_breakdown closure native {lb_nat:.3f}s <= legacy {lb_leg:.3f}s + 5ms")
        if name == "shanghai":
            check.hard(lb_nat <= 0.005,
                       f"[{name}] lap_breakdown closure native {lb_nat:.3f}s <= 5ms absolute")

    # ---- schema identity vs golden ----
    for ep, live in (("telemetry", native["telemetry"]), ("delta", native["delta"]),
                     ("insights", native["insights"])):
        golden = load_json(Path(golden_dir) / f"{ep}_{name}.json")
        issues = shapes_equal(shape_of(golden), shape_of(live))
        check.hard(not issues,
                   f"[{name}] native {ep} schema identical to golden"
                   + ("" if not issues else f" — {issues[:3]}"))

    # ---- gate #4: legacy head byte-identical to golden (volatile-stripped) ----
    for ep, live_bytes, live_obj in (
            ("telemetry", legacy["telemetry_bytes"], legacy["telemetry"]),
            ("delta", legacy["delta_bytes"], legacy["delta"])):
        golden_bytes = (Path(golden_dir) / f"{ep}_{name}.json").read_bytes()
        check.hard(golden_bytes == live_bytes,
                   f"[{name}] legacy {ep} byte-identical to golden snapshot")
    golden_ins = strip_volatile(load_json(Path(golden_dir) / f"insights_{name}.json"))
    live_ins = strip_volatile(legacy["insights"])
    check.hard(golden_ins == live_ins,
               f"[{name}] legacy insights value-identical to golden (volatile timing stripped)")

    # ---- per-corner diffs ----
    nat_tel = {t["driver"]: t for t in native["telemetry"]}
    leg_tel = {t["driver"]: t for t in legacy["telemetry"]}
    ref = fixture["ref"]
    corners_leg = {c["corner_number"]: c for c in m_leg["corners"]}
    corners_nat = {c["corner_number"]: c for c in m_nat["corners"]}
    reg_corners = _registered_brake_corners(registry, name)
    open_corners = _open_brake_corners(registry, name)
    corner_diffs, brake_violations = [], 0
    n_aggregate_corners = 0
    loc_shifts = []
    for num in sorted(corners_leg):
        cl, cn = corners_leg[num], corners_nat.get(num)
        if cn is None:
            continue
        local_gap = local_sample_gap(nat_tel[ref]["distance"], cl["brake_distance"])
        brake_shift = cn["brake_distance"] - cl["brake_distance"]
        brake_ok = abs(brake_shift) <= local_gap
        if num in reg_corners:
            # registered acceptance (exclude-but-preserve: stays in the table,
            # out of the aggregate; growth beyond bound = hard fail)
            bound = reg_corners[num]["bound"]
            if abs(brake_shift) <= bound:
                check.known(
                    f"[{name}] STOP-4 T{num}: |shift| {abs(brake_shift):.1f}m <= bound {bound:.0f}m "
                    f"({reg_corners[num]['classification'].split(':')[0]})")
            else:
                check.hard(False,
                           f"[{name}] STOP-4 T{num} GREW BEYOND BOUND: "
                           f"|shift| {abs(brake_shift):.1f}m > {bound:.0f}m")
        else:
            n_aggregate_corners += 1
            if not brake_ok:
                brake_violations += 1
                if num in open_corners:
                    check.open_finding(
                        f"[{name}] T{num}: shift {brake_shift:+.1f}m vs local gap {local_gap:.1f}m "
                        f"— {open_corners[num]['id']} pending owner sign-off")
        # fixed-window apex comparison (legacy zone on both substrates)
        leg_min, leg_loc = min_speed_in_zone(
            leg_tel[ref]["distance"], leg_tel[ref]["speed"], cl["zone_start"], cl["zone_end"])
        nat_min, nat_loc = min_speed_in_zone(
            nat_tel[ref]["distance"], nat_tel[ref]["speed"], cl["zone_start"], cl["zone_end"])
        apex_dv = (None if leg_min is None or nat_min is None else nat_min - leg_min)
        apex_dloc = (None if leg_loc is None or nat_loc is None else nat_loc - leg_loc)
        if apex_dloc is not None:
            loc_shifts.append(apex_dloc)
        corner_diffs.append({
            "corner": num,
            "brake_legacy_m": cl["brake_distance"],
            "brake_native_m": cn["brake_distance"],
            "brake_shift_m": brake_shift,
            "local_native_gap_m": local_gap,
            "brake_within_one_gap": brake_ok,
            "apex_minspeed_legacy_kmh": leg_min,
            "apex_minspeed_native_kmh": nat_min,
            "apex_minspeed_diff_kmh": apex_dv,
            "apex_location_shift_m": apex_dloc,
            "delta_change_legacy_s": cl["delta_change"],
            "delta_change_native_s": cn["delta_change"],
            "cause_legacy": cl["cause"], "cause_native": cn["cause"],
            "confidence_legacy": cl["confidence"], "confidence_native": cn["confidence"],
        })
        if num not in reg_corners:  # registered corners already reported via known()
            check.flag(brake_ok,
                       f"[{name}] T{num} brake shift {brake_shift:+.1f}m vs local gap {local_gap:.1f}m")
        if apex_dv is not None:
            check.flag(abs(apex_dv) <= 1e-2,
                       f"[{name}] T{num} apex min-speed diff {apex_dv:+.3f} km/h (fixed legacy window)")
    out["corner_diffs"] = corner_diffs

    # Aggregate over UNREGISTERED corners only (exclude-but-preserve): the
    # registry removes accepted corners from the pass/fail population; open
    # findings remain counted (they are not accepted) and additionally drive
    # the open-finding exit path.
    check.hard(brake_violations <= 0.20 * max(1, n_aggregate_corners),
               f"[{name}] brake-shift violations {brake_violations}/{n_aggregate_corners} "
               f"unregistered corners <= 20%")

    # ---- registration: median min-speed-location shift across corners ----
    if loc_shifts:
        med = sorted(loc_shifts)[len(loc_shifts) // 2]
        check.hard(abs(med) < 5.0,
                   f"[{name}] median per-corner min-speed location shift {med:+.2f}m < 5m")
        out["median_location_shift_m"] = med

    # ---- totals & redistribution (informational) ----
    check.flag(True,
               f"[{name}] total corner delta: legacy {m_leg['totals']['total_corner_delta']:+.3f}s"
               f" -> native {m_nat['totals']['total_corner_delta']:+.3f}s"
               f" (official {m_nat['closure']['official_gap']:+.3f}s; redistribution allowed)")

    # ---- confidence transitions ----
    transitions = [
        f"T{d['corner']}: {d['confidence_legacy']} -> {d['confidence_native']}"
        for d in corner_diffs if d["confidence_legacy"] != d["confidence_native"]
    ]
    out["confidence_transitions"] = transitions
    check.flag(True, f"[{name}] confidence transitions: {len(transitions)} "
               + ("(none)" if not transitions else "; ".join(transitions)))

    # ---- gap inventory + provenance schema ----
    gaps_out = {}
    for item in native.get("meta", []):
        gaps_out[item["driver"]] = item["gaps"]
        check.hard(item["meta"]["schemaVersion"] == "native_v1",
                   f"[{name}] {item['driver']} meta schemaVersion == native_v1")
        for g in item["gaps"]:
            check.hard(g["ratio"] > 3.0,
                       f"[{name}] {item['driver']} gap ratio {g['ratio']:.2f} > 3.0 (strict law)")
    out["gap_inventory"] = gaps_out
    n_gaps = sum(len(v) for v in gaps_out.values())
    check.flag(True, f"[{name}] gap inventory: {n_gaps} gap(s) across drivers")

    # ---- sample counts & runtimes ----
    out["sample_counts"] = {
        d: {"legacy": len(leg_tel[d]["distance"]), "native": len(nat_tel[d]["distance"])}
        for d in leg_tel if d in nat_tel
    }
    out["runtimes_s"] = {"legacy": legacy["runtimes_s"], "native": native["runtimes_s"]}
    for d, c in out["sample_counts"].items():
        check.flag(True, f"[{name}] {d} samples: merged {c['legacy']} -> native {c['native']} "
                   f"({100.0 * c['native'] / c['legacy']:.0f}%)")
    return out


# =============================================================================
# Report emission
# =============================================================================

def emit_markdown(results, check, path):
    lines = ["# G0 A/B Report — legacy vs native acquisition", ""]
    lines.append(f"**Hard failures: {len(check.hard_failures)}** | "
                 f"KNOWN-DEVIATIONS: {len(check.known_deviations)} | "
                 f"OPEN FINDINGS: {len(check.open_findings)} | "
                 f"Flags: {len(check.flags)} | Checks passed: {len(check.info)}")
    lines.append("")
    if check.hard_failures:
        lines.append("## HARD FAILURES")
        lines += [f"- {m}" for m in check.hard_failures]
        lines.append("")
    if check.known_deviations:
        lines.append("## KNOWN-DEVIATIONS (registered acceptances — bounded, never silently green)")
        lines += [f"- {m}" for m in check.known_deviations]
        lines.append("")
    if check.open_findings:
        lines.append("## OPEN FINDINGS (recognised, NOT accepted — owner decision pending)")
        lines += [f"- {m}" for m in check.open_findings]
        lines.append("")
    if check.flags:
        lines.append("## Flags (review, not failures)")
        lines += [f"- {m}" for m in check.flags]
        lines.append("")
    for r in results:
        n = r["fixture"]
        lines.append(f"## Fixture: {n}")
        mc_l, mc_n = r["legacy_metrics"]["closure"], r["native_metrics"]["closure"]
        lines.append("| metric | legacy | native |")
        lines.append("|---|---|---|")
        lines.append(f"| official gap | {mc_l['official_gap']:+.3f}s | {mc_n['official_gap']:+.3f}s |")
        lines.append(f"| delta-grid closure err | {mc_l['delta_grid_closure_error']:.2e} | {mc_n['delta_grid_closure_error']:.2e} |")
        lines.append(f"| lap_breakdown err | {mc_l['lap_breakdown']['reconciliation_error']:.3f}s | {mc_n['lap_breakdown']['reconciliation_error']:.3f}s |")
        lines.append(f"| total corner delta | {r['legacy_metrics']['totals']['total_corner_delta']:+.3f}s | {r['native_metrics']['totals']['total_corner_delta']:+.3f}s |")
        sc = r["sample_counts"]
        leg_counts = ", ".join("{}:{}".format(d, v["legacy"]) for d, v in sc.items())
        nat_counts = ", ".join("{}:{}".format(d, v["native"]) for d, v in sc.items())
        lines.append(f"| samples | {leg_counts} | {nat_counts} |")
        lines.append("")
        lines.append("### Per-corner diff")
        lines.append("| T | brake leg (m) | brake nat (m) | shift (m) | local gap (m) | ok | minV diff (km/h) | dΔ leg (s) | dΔ nat (s) | conf |")
        lines.append("|---|---|---|---|---|---|---|---|---|---|")
        for d in r["corner_diffs"]:
            mv = "—" if d["apex_minspeed_diff_kmh"] is None else f"{d['apex_minspeed_diff_kmh']:+.3f}"
            lines.append(
                f"| {d['corner']} | {d['brake_legacy_m']:.1f} | {d['brake_native_m']:.1f} | "
                f"{d['brake_shift_m']:+.1f} | {d['local_native_gap_m']:.1f} | "
                f"{'✓' if d['brake_within_one_gap'] else '✗'} | {mv} | "
                f"{d['delta_change_legacy_s']:+.3f} | {d['delta_change_native_s']:+.3f} | "
                f"{d['confidence_legacy'][:1].upper()}→{d['confidence_native'][:1].upper()} |")
        lines.append("")
        if r.get("gap_inventory"):
            lines.append("### Gap inventory (native)")
            for drv, gaps in r["gap_inventory"].items():
                if gaps:
                    for g in gaps:
                        lines.append(f"- {drv}: dt={g['dt']:.2f}s (ratio {g['ratio']:.1f}) at "
                                     f"{g['dStart']:.0f}–{g['dEnd']:.0f}m")
                else:
                    lines.append(f"- {drv}: none")
            lines.append("")
        rt = r["runtimes_s"]
        lines.append(f"Runtimes (s): telemetry {rt['legacy']['telemetry']:.2f}→{rt['native']['telemetry']:.2f}, "
                     f"insights {rt['legacy']['insights']:.2f}→{rt['native']['insights']:.2f}")
        lines.append("")
    Path(path).write_text("\n".join(lines), encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--golden", required=True, help="dir with golden legacy snapshots")
    ap.add_argument("--out", required=True, help="output dir for ab_report.{md,json}")
    ap.add_argument("--known-deviations",
                    default=str(Path(__file__).resolve().parent / "known_deviations.json"),
                    help="known-deviations registry (G0 continuation §4)")
    args = ap.parse_args()

    registry = load_registry(args.known_deviations)
    print(f"registry: {len(registry['deviations'])} accepted deviation(s), "
          f"{len(registry['open_findings'])} open finding(s) "
          f"from {args.known_deviations}", flush=True)

    check = Check()
    results = []
    for fixture in FIXTURES:
        print(f"=== fixture {fixture['name']} : fetching legacy head ===", flush=True)
        legacy = fetch_head(fixture, "legacy")
        print(f"=== fixture {fixture['name']} : fetching native head ===", flush=True)
        native = fetch_head(fixture, "native")
        print(f"=== fixture {fixture['name']} : comparing ===", flush=True)
        results.append(compare_fixture(fixture, legacy, native, args.golden, check, registry))

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    serializable = []
    for r in results:
        serializable.append({k: v for k, v in r.items()})
    with open(out_dir / "ab_report.json", "w", encoding="utf-8") as f:
        json.dump({"hard_failures": check.hard_failures,
                   "known_deviations": check.known_deviations,
                   "open_findings": check.open_findings,
                   "flags": check.flags,
                   "passed": check.info, "fixtures": serializable}, f, indent=2, default=str)
    emit_markdown(results, check, out_dir / "ab_report.md")

    print("\n".join(check.hard_failures + check.known_deviations
                    + check.open_findings + check.flags))
    print(f"\nhard failures: {len(check.hard_failures)}  "
          f"known-deviations: {len(check.known_deviations)}  "
          f"open findings: {len(check.open_findings)}  "
          f"flags: {len(check.flags)}  passed: {len(check.info)}")
    print(f"report -> {out_dir / 'ab_report.md'}")
    # exit semantics: 1 = hard failure (incl. deviation growth / unregistered
    # violation); 3 = no hard failures but owner-pending OPEN FINDINGS exist;
    # 0 = clean (known-deviations alone do not fail the gate, but are always
    # rendered — accepted != invisible).
    if check.hard_failures:
        sys.exit(1)
    if check.open_findings:
        sys.exit(3)
    sys.exit(0)


if __name__ == "__main__":
    main()
