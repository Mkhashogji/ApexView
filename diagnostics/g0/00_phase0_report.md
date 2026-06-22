# G0 Phase 0 — Verification & Contract Freeze (Gate Report)

**Branch:** `feature/g0-honest-acquisition` (branched from `main` @ `731116d`)
**Date captured:** 2026-06-11
**Environment:** `f1-api` / `f1-analysis` Docker containers, images verified byte-identical
to the working tree (md5 spot-check on `fastf1_client.py`, `telemetry.py` routes,
`performance_orchestrator.py`, `delta_analysis.py`). FastF1 3.8.3, numpy 2.4.6,
pandas 2.3.3 (API) / 3.0.3 (analysis), scipy 1.17.1.

**Gate verdict: PASS** — with one STOP-condition finding (§6) that was resolved by
adapting one Phase 5 criterion *before* implementation, documented below.

---

## 1. Consumer table (Phase 0.1 — blast-radius proof)

Full machine-readable findings with file:line evidence: [`phase0_recon_findings.json`](phase0_recon_findings.json)
(6 parallel read-only recon sweeps).

| Function / endpoint | Direct consumers | Page(s) |
|---|---|---|
| `FastF1Client.get_telemetry` (`services/telemetry/fastf1_client.py:579`) | `GET /telemetry` route (`routes/telemetry.py:9-25`); `routes/analysis.py:64,140` (lap-similarity / clustering proxies) | Qualifying only |
| `FastF1Client.get_delta_analysis` (`:765`) | `GET /telemetry/delta` route (`routes/telemetry.py:28-43`) | **None live** — frontend `fetchDelta` (`apps/web/lib/api.ts:93`) is defined but never imported/called; no `useDeltaQuery` hook exists. Dead-but-exposed endpoint, still in G0 rewire scope. |
| `GET /telemetry` | Frontend `fetchTelemetry` → Qualifying telemetry panels; analysis service: `performance_orchestrator.py:407` + `main.py:343,546,882,1196` (scaled-delta / corner-analysis / technique-profile / generate-insight each fetch it directly) | Qualifying only |
| `GET /laps/sectors` | Analysis service (official lap times for scaling) — same call sites | Qualifying only |
| `POST /analysis/performance-insights` (:8501) | Frontend `fetchPerformanceInsights` (`api.ts:443-480`) via `usePerformanceInsightsQuery` | Qualifying only |
| Race page | `/race/*` endpoints only (own pipeline, `services/race/`) | not a consumer |
| Practice page | `/practice/*` endpoints only (own pipeline, `services/practice/`) | not a consumer |
| Home / Track Intelligence / Transparency | static or `/track/*` only | not consumers |

**Additional facts established:**
- `apps/api/app/services/fastf1_client.py` (root duplicate) is **dead code** — no live imports; only `app.services.telemetry.fastf1_client` is used (`data_service.py:8`, `routes/analysis.py:6`).
- `get_data_service()` (`services/data_service.py:12`) returns `FastF1Client` when `LIVE_DATA=true` (production), else `MockDataService`.
- `analyze_corners_v2` accepts `circuit_id: str = ""` but the orchestrator never passes it (`performance_orchestrator.py:630-640`) → production corner analysis runs on the **default** `CornerAnalysisConfig` for every circuit. Not changed at G0 (exclusion list); documented because the A/B harness must replicate default thresholds, not per-circuit ones.

**STOP condition (out-of-scope consumer): not triggered.** All consumption is inside the
Qualifying telemetry/delta/performance-insights flow.

## 2. Handshake documentation (Phase 0.2)

**API → analysis-service payload path.** The analysis service obtains telemetry
exclusively over HTTP from the API service:

- `GET {API}/telemetry?session={id}&drivers={d}&drivers={d}…[&session_part=Qn]`
  — orchestrator `fetch_driver_telemetry` (`performance_orchestrator.py:399-450`)
  consumes: `distance`, `speed`, `brake`, `throttle`, `lapTime`, `relativeDistance`, `time`.
  Builds dict keys: `distance, speed, brake, throttle, lap_time, relative_distance, time`.
- `GET {API}/laps/sectors?…` — official lap/sector times (`totalTime`, `sector1/2/3`).

**Wire schema (`TelemetryResponse`, `models/dto.py:51-68`, CamelCase serialisation):**
`driver: str`, `lapNumber: int`, `lapTime: float|null`, `distance: float[]`,
`speed: float[]`, `throttle: float[]`, `brake: float[]` (bool ndarray coerced by
pydantic to `0.0/1.0` floats on the wire — verified in golden), `gear: int[]`,
`relativeDistance: float[]|null`, `time: float[]|null` (lap-relative seconds, starts 0),
`rpm: int[]|null`, `drs: int[]|null`.

**Performance-insights request (`PerformanceInsightsRequest`, `models/schemas.py:768-810`):**
`session_id, reference_driver, compare_drivers[], corners[{corner_number:int,
apex_distance:float, corner_type:str, name:str|null}], mode, session_part|null,
circuit_name|null, track_length:float|null, include_telemetry:bool`.
Frontend payload construction verbatim at `apps/web/lib/api.ts:457-471`: corners mapped
from `GET /track/{round}` response (`cornerNumber→corner_number`, `distance→apex_distance`,
`type→corner_type`), `include_telemetry: true`, `track_length` = track `length`.
Frontend does **not** send `circuit_name`.

**Response notes:** corner result dicts (`_corner_result_to_dict`,
`performance_orchestrator.py:330-342`) expose only
`corner_number, name, apex_distance (nominal input), brake_distance (ref driver detected),
zone_start, zone_end, delta_change, cause, confidence` — `detected_apex` / `apex_speed`
stay internal. Volatile fields in the response: `phase_timing[]`, `total_duration_ms`
(must be normalised out of byte-comparisons).

## 3. Golden snapshots (Phase 0.3)

Captured pre-change, raw bytes, by [`capture_golden.ps1`](capture_golden.ps1) →
[`golden/legacy/`](golden/legacy/). Fixture set:

| Fixture | Session | Ref lap | Comp lap | Files |
|---|---|---|---|---|
| shanghai | `2025_2_Qualifying` Q3 | PIA #19, 90.641 s | RUS #21, 90.723 s | track, telemetry (686/694 pts), delta (1000 pts), insights (+ exact request body) |
| monaco | `2025_8_Qualifying` Q3 | NOR #26, 69.954 s | LEC #26, 70.063 s | track, telemetry (521/531 pts), delta, insights (+ request body) |

Contract at G0: response **schemas** identical; numeric **values** may move only within
Phase 5 expectations. `insights_request_*.json` files preserve the exact request bodies
for replay parity.

## 4. Baseline analytical reference (Phase 0.4)

[`golden/legacy_metrics.json`](golden/legacy_metrics.json), computed by
[`extract_legacy_metrics.py`](extract_legacy_metrics.py) using the shared metric module
`tools/ab_harness/metrics.py` (the same code the A/B harness diffs with).

| Metric | shanghai | monaco |
|---|---|---|
| official gap | +0.082 s | +0.109 s |
| delta-grid closure (`delta[-1]` vs official) | 0.000000 s | 0.000000 s |
| lap_breakdown reconciliation error | **0.000 s (valid)** | **0.492 s (INVALID)** |
| corners analysed | 16 | 19 |
| confidence tiers H/M/L | 2 / 14 / 0 | 7 / 10 / 2 |
| scaling factor / confidence | 1.0 / 1.0 | 1.0 / 1.0 |

Per-corner brake points, zone boundaries, min-speed values+locations, per-phase delta
splits (nominal-apex-anchored approximation — flagged as such in the module docstring),
and local inter-sample gaps are stored per corner in the JSON.

## 5. Cache audit & versioning plan (Phase 0.5)

- **Parquet cache:** `app/services/cache/parquet_cache.py` — flat-file keying
  `"{session_id}_{data_type}_{k=v}…".parquet` under `PARQUET_DIR=/app/data/cache/parquet`
  (`_generate_key`, lines 23-51; md5-hashed if >200 chars). Merged telemetry is cached as
  `data_type="telemetry"` with `drivers=…_…, lap_type=fastest` and stores arrays as JSON
  strings per driver row. **Note:** the cache is bypassed whenever `session_part` is set
  (`fastf1_client.py:600`) — i.e. for every production Q3 request.
- **Versioning plan:** native bundles cache under a new
  `data_type="telemetry_native_v1"` → key-space disjoint from legacy by construction;
  legacy frames can never be misread as native and vice versa. Schema version string is
  also embedded in the bundle `meta`. First-run re-materialisation is logged at INFO.
- **FastF1 cache:** unchanged. `fastf1.Cache.enable_cache(settings.CACHE_DIR)`
  (`core/cache.py:7`, `/app/data/cache`). Native `get_car_data()`/`get_pos_data()` draw
  on the same cached raw responses — verified empirically during the granularity
  diagnostic (offline cache-only loads of both streams on both fixture circuits).
- **Container note:** source code is baked into images (compose mounts only
  `./data/cache`) → every code change requires `docker compose build api analysis`.

## 6. STOP-condition finding: legacy Monaco violates the closure invariant

Phase 5 expects "closure invariant ≤ 5 ms on native path, every fixture pair (hard
fail)". Measured reality: the **legacy** pipeline already fails this on Monaco —
`lap_breakdown.reconciliation_error = 0.492 s` (`reconciliation_valid = false`), vs
0.000 s on Shanghai. Root cause is corner-zone coverage arithmetic
(`calculate_lap_breakdown`, `corner_analysis.py:1893-1984`: straights are computed as
complements of corner zones; Monaco's 19 tightly-packed corners trigger
`_clamp_zones_to_prevent_overlap` midpoint clamping, leaving coverage holes). This is
**not** an acquisition property, and zone logic is on the G0 exclusion list.

**Resolution (criterion adaptation, decided before implementation):**
1. The **delta-grid closure** (`delta[-1] == official_gap`) must hold to ≤ 1e-6 s on the
   native path for every fixture (Tier-1 guarantee; legacy measures 0.000000 on both).
2. `lap_breakdown` reconciliation error on the native path must be **≤ legacy + 5 ms**
   per fixture (no worsening), and Shanghai must remain ≤ 5 ms absolute.
3. The original ≤ 5 ms absolute expectation for Monaco's lap_breakdown is recorded as
   **unachievable at G0 without touching excluded zone logic** and is deferred to the
   gate that owns corner-zone arithmetic.

## 7. Gate 0 pass list

- [x] Consumer table complete; Qualifying-only confirmed (no STOP)
- [x] Handshake documented (§2)
- [x] Golden snapshots + exact request bodies stored (§3)
- [x] Legacy metrics stored (§4)
- [x] Cache plan written (§5)
- [x] STOP finding raised & resolved by documented criterion adaptation (§6)

Proceeding to Phase 1 (native acquisition layer).
