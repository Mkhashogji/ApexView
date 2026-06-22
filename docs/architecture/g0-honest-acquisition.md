# G0 — Honest Acquisition & Native Detection (Architecture Note)

**Status:** implemented on `feature/g0-honest-acquisition` (uncommitted at user request)
**Evidence base:** `diagnostics/granularity/REPORT.md` | **Gate evidence:** `diagnostics/g0/G0_REPORT.md`

## What changed and why

The qualifying telemetry analysis pipeline previously obtained per-lap data from
FastF1's `lap.get_telemetry()`, which merges two **interleaved ~4 Hz streams** —
car data (Speed/RPM/Throttle/Brake/nGear/DRS) and position data (X/Y/Z) — onto
the union of their timestamps. The streams share **zero** timestamps, so ~51% of
every car channel in the merged frame is linear interpolation presented as
measurement. Downstream brake/apex detection and the kinematic deceleration
backward-walk consumed those phantom rows as if they were real samples.

G0 retires `get_telemetry()` from the analysis path:

```
BEFORE  lap.get_telemetry()  ──merged 686 rows (~51% interpolated)──▶ everything

AFTER   lap.get_car_data()  ──332 real rows, provenance REAL_CAR──▶ TelemetryBundle.car_native ──▶ /telemetry ──▶ detection + delta grid
        lap.get_pos_data()  ──352 real rows, provenance REAL_POS──▶ TelemetryBundle.pos_native    (consumed by NOTHING at G0; fusion substrate)
```

- **`apps/api/app/services/telemetry/native_acquisition.py`** — dual-stream
  acquisition: provenance tagging, gap detection, structured failures
  (`NativeAcquisitionError`; **no silent fallback** to the merged path).
- **`fastf1_client.py`** — `get_telemetry` / `get_delta_analysis` became
  dispatchers. The legacy bodies moved **verbatim** to `_get_telemetry_legacy`
  / `_get_delta_analysis_legacy` (A/B-verified byte-identical). Native paths
  build the same wire schema from `car_native`. New `get_telemetry_meta`.
- **`routes/telemetry.py`** — optional `acquisition` query override
  (`native|legacy`), `NativeAcquisitionError → HTTP 502` with structured
  detail, and the new additive `GET /telemetry/meta`.
- **Analysis service** — plumbing only: `acquisition_mode` passthrough
  (request → orchestrator → API fetch), `DeltaResult` grid metadata
  (real-sample counts/spacing; internal), `CornerResult.gap_flag` (internal),
  `apply_gap_flags` in the orchestrator. **No detection algorithm, threshold,
  confidence weight, or template changed.**

Because the analysis service obtains telemetry exclusively over HTTP from
`GET /telemetry`, switching the API's substrate automatically moved brake/apex
detection, `compute_deceleration`, and the Phase-2 delta-grid inputs onto
native car samples — the detection rewire is an acquisition-layer change, not
an algorithm change.

## The gap-law-vs-closure design decision

Gaps (car-stream dt **strictly** > 3× the lap's median dt; ≈0.72 s threshold on
reference data) are **detected and recorded as metadata only**
(`/telemetry/meta`, orchestrator `gap_flag` on internal corner results). The
Phase-2 1000-point delta grid **keeps interpolating end-to-end across gaps**:
severing or down-weighting the grid inside a gap would break the closure
invariant (`delta[-1] == official_gap`), which anchors every per-corner time
attribution to official timing. Modelling uncertainty growth through gaps is
the fusion track's job at a later gate. The boundary is exclusive
(dt == 3×median is NOT a gap) and unit-tested.

## Provenance schema

`Provenance ∈ {REAL_CAR, REAL_POS, DERIVED_RPM, FUSED, GAP}` — defined in full
now so the enum is stable across gates; **only `REAL_CAR`/`REAL_POS` may appear
in G0 output** (test-asserted). Provenance is internal to the bundle: the wire
schema is frozen against the golden contract, so provenance is *not* serialized.

## Contract preservation

- Response schemas of `/telemetry`, `/telemetry/delta`,
  `/analysis/performance-insights` are byte-shape frozen (golden snapshots in
  `diagnostics/g0/golden/legacy/`; A/B harness asserts shape identity and
  legacy-head byte identity).
- Brake serialises as `0.0/1.0` floats on the wire in both modes (bool ndarray
  → pydantic `List[float]` coercion — bundle preserves the bool dtype
  internally).
- New surface is **additive only**: `/telemetry/meta`, `acquisition` query
  param, `acquisition_mode` optional request field (never sent by the
  frontend).
- Native Parquet cache entries use `data_type="telemetry_native_v1"` — a
  key-space disjoint from legacy `"telemetry"` entries by construction.
  First-run re-materialisation is logged at INFO, not an error.

## Known divergences (deliberate, documented)

1. **Legacy cache-write bug left intact:** the legacy path writes
  `session_part`-filtered telemetry under the unfiltered cache key
  (`fastf1_client.py` legacy body, pre-existing). The native path gates the
  write on `not session_part` (correct behaviour). Legacy is byte-identical by
  requirement; the bug is a candidate for the legacy-path removal gate.
2. **End-of-lap coverage:** the native car stream ends at the last real car
  sample; the merged frame integrated ~15–20 m of *phantom* distance beyond it
  (interpolated rows after the final car timestamp). Corners whose nominal
  apex lies in that tail (Shanghai T16 apex 5380 m vs native end ~5375 m;
  Monaco T19 apex 3300 m vs native end ~3277 m) lose a few metres of
  (previously phantom) coverage. See G0_REPORT §STOP-3 for the measured
  consequence and options.

## Legacy-flag removal plan

`acquisition=legacy` / `ACQUISITION_MODE=legacy` exist **solely** for the A/B
harness. Removal is scheduled for the cleanup gate after the solution-design
track signs off on G0+1: delete `_get_telemetry_legacy`,
`_get_delta_analysis_legacy`, the query-param `legacy` value, and the
`acquisition_mode` passthrough; re-capture goldens from the native head at that
point.
