"""
G0 Phase 0.4 — extract baseline analytical metrics from the golden legacy snapshots.

Reads diagnostics/g0/golden/legacy/*.json, computes the metric set the A/B
harness will diff (closure, per-corner brake points, min-speed, per-phase
deltas, confidence tiers, sample counts), and writes
diagnostics/g0/golden/legacy_metrics.json.

Run from repo root:  python diagnostics/g0/extract_legacy_metrics.py
(or inside the f1-api container with the repo files copied in — numpy required)
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "tools" / "ab_harness"))
from metrics import fixture_metrics, load_json  # noqa: E402

GOLDEN = Path(__file__).resolve().parent / "golden" / "legacy"
FIXTURES = ["shanghai", "monaco"]


def main():
    out = {"source": "golden/legacy", "fixtures": {}}
    for name in FIXTURES:
        telemetry = load_json(GOLDEN / f"telemetry_{name}.json")
        insights = load_json(GOLDEN / f"insights_{name}.json")
        track = load_json(GOLDEN / f"track_{name}.json")
        delta = load_json(GOLDEN / f"delta_{name}.json")
        out["fixtures"][name] = fixture_metrics(telemetry, insights, track, delta)
        c = out["fixtures"][name]["closure"]
        print(f"[{name}] official_gap={c['official_gap']:+.3f}s "
              f"grid_closure_err={c['delta_grid_closure_error']:.6f}s "
              f"lap_breakdown_err={c['lap_breakdown']['reconciliation_error']:.3f}s "
              f"valid={c['lap_breakdown']['reconciliation_valid']}")

    target = GOLDEN.parent / "legacy_metrics.json"
    with open(target, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"written -> {target}")


if __name__ == "__main__":
    main()
