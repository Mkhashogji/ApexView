# G0 A/B Harness — legacy vs native acquisition

Permanent regression gate (not scratch). Runs the fixed fixture set
(Shanghai 2025 Q3 PIA/RUS, Monaco 2025 Q3 NOR/LEC) through both acquisition
heads and asserts the G0 Phase 5 expectations programmatically; exits non-zero
on any hard violation.

## Files

- `metrics.py` — pure metric computation over captured endpoint responses
  (shared with `diagnostics/g0/extract_legacy_metrics.py`).
- `run_ab.py` — the runner + assertions + report emitter
  (`ab_report.md` / `ab_report.json`).

## Run (inside the f1-api container)

```powershell
docker exec f1-api mkdir -p /tmp/g0/tools/ab_harness /tmp/g0/out
docker cp tools/ab_harness/metrics.py f1-api:/tmp/g0/tools/ab_harness/metrics.py
docker cp tools/ab_harness/run_ab.py  f1-api:/tmp/g0/tools/ab_harness/run_ab.py
docker cp diagnostics/g0/golden/legacy f1-api:/tmp/g0/golden_legacy
docker exec -u root f1-api chmod -R 777 /tmp/g0
docker exec -e ANALYSIS_URL=http://analysis:8501 -w /tmp/g0 f1-api `
  python tools/ab_harness/run_ab.py --golden /tmp/g0/golden_legacy --out /tmp/g0/out
docker cp f1-api:/tmp/g0/out/ab_report.md   diagnostics/g0/ab_report.md
docker cp f1-api:/tmp/g0/out/ab_report.json diagnostics/g0/ab_report.json
```

Requires both containers healthy and the FastF1 cache populated for rounds 2
and 8 of 2025. Environment: `API_URL` (default `http://localhost:8000`),
`ANALYSIS_URL` (default `http://analysis:8501`).

## Assertion → Phase 5 mapping

See the docstring at the top of `run_ab.py` for the full expectation →
implementation map, including the closure-criterion adaptation documented in
`diagnostics/g0/00_phase0_report.md` §6 (legacy Monaco already violates the
5 ms lap-breakdown closure).

Provenance note: row-level provenance is internal to the bundle (never
serialized), so the 100%-tagged assertion lives in
`apps/api/tests/test_native_acquisition.py`; the harness asserts
`meta.schemaVersion == "native_v1"` as the wire-visible witness.

## Known-deviations registry (G0 continuation §4)

`known_deviations.json` (override with `--known-deviations <path>`) encodes the
owner-accepted deviations (STOP-3, STOP-4) and the owner-pending open findings
(OPEN-1/OPEN-2). Enforcement — accepted ≠ invisible:

- every registered match is rendered in a **KNOWN-DEVIATION** section, never
  silently green;
- a registered deviation that **grows beyond its recorded bound** is a hard
  failure;
- any **unregistered** hard violation stays a hard failure;
- registered brake-shift corners are excluded from the >20% aggregate but stay
  in the per-corner diff table (exclude-but-preserve).

Exit codes: `1` = hard failure (incl. bound growth / unregistered violation);
`3` = no hard failures but OPEN FINDINGS pending owner sign-off; `0` = clean.
Tamper-proofing is verified by deregistering an entry and confirming exit 1.
