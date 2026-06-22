# G0 — Detailed Implementation Report (standing record)

The comprehensive record the condensed [G0_REPORT.md](G0_REPORT.md) and
[CONTINUATION_LOG.md](CONTINUATION_LOG.md) summarised. Scope: Gate G0 — Honest
Acquisition & Native Detection — as built on `feature/g0-honest-acquisition`.
Companion forensics: [OPEN_FINDINGS_FORENSICS.md](OPEN_FINDINGS_FORENSICS.md).

---

## 1. Architecture as built

### 1.1 The problem G0 removes
FastF1's `lap.get_telemetry()` merges two interleaved ~4 Hz streams — car data
(Speed/RPM/Throttle/Brake/nGear/DRS) and position data (X/Y/Z) — onto the union of their
timestamps. The streams share **zero** timestamps, so on the reference laps ~51 % of every
car channel in the merged frame is linear interpolation presented as measurement
(Shanghai: 332 real car rows → 686 merged; Monaco: 257 → 521). Brake/apex detection and the
kinematic deceleration walk consumed those phantom rows as if real. Evidence base:
[../granularity/REPORT.md](../granularity/REPORT.md).

### 1.2 Native acquisition layer — `apps/api/app/services/telemetry/native_acquisition.py`
- **`Provenance(str, Enum)`** — `REAL_CAR`, `REAL_POS` active at G0; `DERIVED_RPM`, `FUSED`,
  `GAP` defined-but-reserved (asserted unused). `G0_ALLOWED_PROVENANCE` gates output.
- **`TelemetryBundle`** dataclass: `car_native` (DataFrame: Time/SessionTime, Speed, RPM,
  Throttle, Brake [bool dtype preserved], nGear, DRS, + `Distance`, `RelativeDistance`,
  `Provenance=REAL_CAR`), `pos_native` (X/Y/Z + `Provenance=REAL_POS`; acquired/tagged/cached
  but **consumed by nothing at G0** — substrate for the fusion gate), `gaps` (list),
  `meta` (dict).
- **Gap law** — `detect_gaps(time_s, distance_m, multiplier=3.0)`: an interval is a gap when
  `dt > 3 × median(dt)` (**strict** `>`; exclusive boundary, unit-tested). Returns
  `{t_start, t_end, d_start, d_end, dt, ratio}` — distance bounds are the consumption
  contract.
- **`acquire_native_bundle(lap, …)`** — `get_car_data()` → validate (continuation hardening:
  reject NaN/NaT, non-monotonic Time, >10 % duplicate timestamps, non-finite channels) →
  `add_distance()` (FastF1's own cumulative `∫speed·dt`) → `add_relative_distance()` →
  tag → `get_pos_data()` → tag → `detect_gaps` → assemble meta. Any failure raises
  **`NativeAcquisitionError`** (structured `stage`/`reason`/`driver`/`session`,
  `to_detail()` for HTTP). **No silent fallback** to the merged path, ever.
- `SCHEMA_VERSION = "native_v1"`.

### 1.3 Config switch — `apps/api/app/core/config.py`
`ACQUISITION_MODE: Literal["native","legacy"] = "native"`. Literal-typed so a typo'd env
value fails at startup rather than silently dispatching native. `legacy` exists solely for
the A/B harness; scheduled for deletion at the cleanup gate.

### 1.4 Dispatch & native paths — `apps/api/app/services/telemetry/fastf1_client.py`
`get_telemetry` / `get_delta_analysis` became dispatchers: `mode = acquisition or
settings.ACQUISITION_MODE` (read at call time); `legacy` → `_get_telemetry_legacy` /
`_get_delta_analysis_legacy` (bodies moved **verbatim** from `main`, reviewer-verified
token-identical); native → `_impl` methods wrapped so any unexpected exception becomes
`NativeAcquisitionError("unexpected")` (exhaustive 502). Native serves the same
`TelemetryResponse` schema built from `car_native`; Brake serialises bool→`0.0/1.0` floats
exactly as legacy. New `get_telemetry_meta` exposes gaps + meta. Native Parquet cache:
`data_type="telemetry_native_v1"` (keyspace disjoint from legacy `"telemetry"` by
construction), rows carry boolean brake + `provenance_car/pos` + `gaps` + `meta`; the read
guard refuses any row whose `meta.schema_version != "native_v1"` (cache miss →
re-materialise, logged). Helpers `_native_cache_row` / `_native_row_to_response` extracted
for testability.

### 1.5 Routes — `apps/api/app/routes/telemetry.py`, `routes/analysis.py`
`GET /telemetry` & `/telemetry/delta`: `acquisition` query param `pattern=^(native|legacy)$`;
`NativeAcquisitionError → HTTP 502` with structured detail. New **`GET /telemetry/meta`**:
returns gap inventory + per-stream stats; 501 in mock mode AND when `ACQUISITION_MODE=legacy`
(rollback isolation — native acquisition must not run server-side under env-legacy). The
`/analysis/lap-similarity` & `/driver-style-clustering` proxy routes gained the same
structured-502 arm (continuation fix).

### 1.6 Analysis-service plumbing (no algorithm/threshold/template change)
- `delta_analysis.py`: `DeltaResult` gains four **optional, internal** grid-metadata fields
  (`ref/comp_sample_count`, `ref/comp_median_spacing_m`) computed via `_median_sample_spacing`;
  splatted into all three tier returns; never serialized.
- `corner_analysis.py`: `CornerResult.gap_flag: bool = False` — **internal**, set by the
  orchestrator, excluded from `_corner_result_to_dict` (schema-frozen).
- `performance_orchestrator.py`: `acquisition_mode` threaded into the `/telemetry` fetch;
  `fetch_all_native_meta` (graceful-degrade gap fetch; skipped under explicit legacy);
  `apply_gap_flags` / `_gap_overlaps_zone` flag corners whose zones overlap a gap. The
  **delta grid keeps interpolating end-to-end across gaps** (closure-preserving by design;
  gap-region uncertainty is the fusion gate's job).
- `schemas.py` / `main.py`: `acquisition_mode: Optional[str]` (`pattern`-validated) request
  field, passed through.

### 1.7 Data-flow narrative — one Monaco Q3 lap (NOR), native vs legacy
1. Orchestrator `GET /telemetry?session=2025_8_Qualifying&drivers=NOR&drivers=LEC&session_part=Q3`
   (no `acquisition` → API default native), plus `GET /telemetry/meta` (gap inventory).
2. API loads the FastF1 session from `/app/data/cache`, selects NOR's fastest valid Q3 lap.
   **Native:** `acquire_native_bundle` → 257 real car rows, Distance integrated from real
   speed, 3 gaps detected, every row `REAL_CAR`. **Legacy:** `lap.get_telemetry()` → 521
   merged rows (`Source`: 257 car, 262 pos, 2 interpolation).
3. API serves arrays: native 257 samples / legacy 521. (`session_part=Q3` ⇒ Parquet bypassed
   on both heads.)
4. Orchestrator → `calculate_scaled_delta` (Tier 1: RelativeDistance+Time → 1000-pt grid,
   `delta[-1] == official_gap` exactly) → `analyze_corners_v2` on the **default** config
   (no `circuit_id`): `compute_deceleration` (smoothing window 5) → apex from speed min →
   two-stage brake detection on the served arrays → per-corner delta read off the 1000-pt
   grid → lap breakdown.
5. `apply_gap_flags` marks corners whose zones overlap NOR/LEC gaps (internal).
6. Response assembled field-explicitly (internal metadata cannot leak).
**Where legacy diverges:** step 2/3 only — every value downstream is identical machinery on a
different substrate.

---

## 2. Testing record

**Totals: 361 API + 319 analysis tests passing** (was 313 + 271 documented; the analysis
baseline was actually 303 on `main` — the 271 in CLAUDE.md was stale). Continuation additions
in **bold**.

| Group | File | Coverage |
|---|---|---|
| Gap law | test_native_acquisition.py | uniform / jitter / 1 s hole / **exact-3× exclusive boundary** / **combined jitter+hole** / **two-hole ordering** / too-short |
| Input validation | test_native_acquisition.py | **NaN speed/RPM, NaT time, non-monotonic, excessive/limited duplicate timestamps** |
| Provenance | test_native_acquisition.py | 100 %-tagged, only REAL_CAR/REAL_POS, reserved-values-unused, pos independent |
| Distance integration | test_native_acquisition.py | **1e-6 parity on the BUNDLE's Distance** (was: on the library) |
| Wire format | test_native_acquisition.py | Brake bool→0.0/1.0 floats; lap fields; **downsample-branch array consistency**; **GapInterval emits `dStart`/`dEnd`** |
| Structured failure | test_native_acquisition.py | empty/missing-channel/stream-exception → NativeAcquisitionError + to_detail |
| Dispatcher/routes | **test_native_dispatch.py (new)** | **native/legacy/default matrix; error propagation (not swallowed); /telemetry & /delta 502; /telemetry/meta 200 / mock-501 / env-legacy-501 / 502; cache keyspace disjoint + versioned-key read** |
| Cache round-trip | **test_native_cache_roundtrip.py (new)** | **cold-subprocess read (channels 1e-6, boolean brake, provenance, gaps, meta); warm wire-identical reconstruction; legacy-frame refusal; wrong-schema-version refusal** |
| Detector on native | test_g0_native_substrate.py | brake detection within resolution envelope; **unconditional two-stage assertion**; **near-duplicate-distance decel finiteness (real pathology)** |
| Gap flags | test_g0_native_substrate.py | overlap camel+snake; **symmetric touch edge**; only-overlapping set; values/confidence unchanged; default-false |
| Meta degradation | test_g0_native_substrate.py | **non-200 / non-list / missing-gaps / exception → {}; valid parse** |
| Schema freeze | test_g0_native_substrate.py | gap_flag not serialized; **DeltaResult metadata ∉ response models** |
| Delta grid metadata | test_g0_native_substrate.py | populated tier-1 & tier-3; default-None compat |

**Deliberate coverage gaps (rationale):** (a) no end-to-end FastF1-live integration test — the
suites isolate from the network by design, and the A/B harness is the live integration gate;
(b) cache-coherence across a stale-but-valid native entry from an older FastF1 build is not
tested (the schema-version guard covers incompatible schemas; same-version drift is a fusion-
gate concern); (c) the `/analysis` proxy routes' substrate switch has unit-level error
translation but no live A/B (out of the qualifying-insights scope).

---

## 3. A/B results in depth

Both heads through the fixed fixtures; harness exit **3** (0 hard failures, 4 known-deviations
within bounds, 2 open findings). Full: [ab_report.md](ab_report.md) / [ab_report.json](ab_report.json).

### 3.1 Closure & totals
| metric | Shanghai L→N | Monaco L→N |
|---|---|---|
| official gap | +0.082 s | +0.109 s |
| delta-grid closure `|delta[-1]−official|` | 0 → 0 | 0 → 0 |
| lap_breakdown reconciliation error | 0.0000 → **0.0858 s** | 0.4924 → **0.2569 s** |
| corner-delta total | +0.013 → +0.242 s | +0.906 → **+0.157 s** |
| track coverage | 0.649 → 0.663 | 0.813 → 0.821 |
| median per-corner min-speed-location shift | **+1.58 m** | **−0.09 m** |

Monaco's honest substrate **improved** the (excluded, unchanged) zone arithmetic: lap-breakdown
error fell 0.492 → 0.257 s and the corner total fell from an 8.3× overshoot (+0.906 s vs +0.109)
to +0.157 s. Shanghai's 0.0858 s regression is fully attributed (§5 / STOP-3).

### 3.2 Per-corner brake shifts (reference driver) — the headline diffs
Shanghai flags: T9 +157.4 m (no-braking kink), T14/T15 −26.5 m (brake-on fallback double).
Monaco violators: T9 +82.0, T10 −19.2, T11 −19.2, T14 −16.5, T17 −13.3 m. Of these, **28 of 35
corner-instances across both circuits shift ≤ one real native sample** (median 0.56× actual gap;
[OPEN_FINDINGS_FORENSICS.md](OPEN_FINDINGS_FORENSICS.md) §generality). Apex min-speed diffs are
mostly ≤1e-2 km/h; the flagged ones (up to 16 km/h) occur where the native zone exposes a
different real minimum sample (fixed-window comparison artifact, not a value error).

### 3.3 Confidence-tier transitions (no confidence code changed)
Shanghai: T15 medium→low, T16 medium→high. Monaco: T1 high→medium, T2 medium→high,
T5 low→medium, T10 high→medium. All are downstream consequences of brake/zone movement on the
honest substrate, not edits to the confidence ladder.

### 3.4 Gap inventories
Shanghai: PIA 1 gap (0.76 s @485 m), RUS 2 (0.76 s @3249, 0.84 s @4414). Monaco: NOR 3
(0.76 @851, **1.08 @1642 — the Tunnel**, 0.88 @2408), LEC 3 (1.16 @883, 0.76 @2091, 1.08 @3076).
All ratios strictly > 3.0; no false gaps at jitter.

### 3.5 Sample counts & runtimes
Samples (merged→native): PIA 686→332, RUS 694→343, NOR 521→257, LEC 531→258 (~49 % — exactly the
phantom fraction removed). Telemetry fetch is **faster** native (smaller arrays: Shanghai
6.71→4.84 s, Monaco 5.68→4.51 s). Insights total is slower native (Shanghai 10.9→13.5 s, Monaco
11.0→15.7 s) — the extra `/telemetry/meta` round-trip + uncached native materialisation (Q3
bypasses Parquet by design). Informational; not a gate criterion.

---

## 4. Errors & incidents log

| # | Symptom | Root cause | Fix | Lesson encoded |
|---|---|---|---|---|
| 1 | Docker daemon down mid-session | Desktop stopped between sessions | Restart + `compose up`; md5 image-vs-tree check | Always verify running images match the tree before capturing goldens |
| 2 | `docker cp /tmp/...` "no such file" | Git-Bash MSYS path mangling | Use PowerShell for container paths | — |
| 3 | First adversarial review returned 0 findings | 4 agents failed forced StructuredOutput | Rerun with **plain-text** agents | Don't force schema on free-form review output |
| 4 | Savitzky-Golay blew up (std 100) in the granularity diagnostic | ran on merged near-duplicate distances | switch to native car_data on a uniform grid | Smoothing requires uniform resampling first |
| 5 | `tests/tests` nesting → inflated counts (638) | `docker cp tests` into an image that already had `/app/tests` | `rm -rf /app/tests/tests`, recount | Verify test collection counts after cp |
| 6 | pytest missing in fresh containers | not in the baked image | ephemeral `pip install pytest pytest-asyncio` | Tests run via cp+install, not baked |
| 7 | Two-stage detector test failed (378 vs 400 ± 18) | envelope ignored the smoothing half-window | widen envelope to `spacing × (1 + window//2)` | The smoothing window IS a resolution term — foreshadowed §5 |
| 8 | Script header write mojibake'd Unicode (`─`→`â”€`) | PowerShell `Set-Content` re-encoded existing UTF-8 box-drawing chars | restored from `git`, re-added via UTF-8-safe Edit | Never bulk-rewrite a UTF-8 source file via PowerShell |
| 9 | Registry tamper test crashed on load | Windows BOM in the JSON | `utf-8-sig` in `load_registry` | BOM-tolerant loaders for PS-written JSON |
| 10 | **NaN invisible to the gap law** (review finding) | `NaN > threshold` is `False`; NaN dropped from median | validation block rejecting non-finite/NaT/dup frames | New tests; honest acquisition must refuse fabricated samples |
| 11 | Native paths could leak raw 500s | unwrapped cache read / lap select / `int(LapNumber)` / `calculate_delta` | `_impl` wrappers → `NativeAcquisitionError("unexpected")` | Route 502 translation now exhaustive; tested |
| 12 | **Forensics used `marina_bay.json` (Singapore) for Monaco** | wrong track file for round 8 | load corners from the golden request bodies (exact production apexes) | Cross-check reconstructions reproduce reported values before trusting them — caught by the main forensics matching to ±0.02 m |
| 13 | **Native cache write does NOT match its test** (found by the OPEN-finding adversarial verification) | the continuation extracted `_native_cache_row` (boolean brake + provenance cols) and wired the cache **read** to `_native_row_to_response`, but the native **write** at `fastf1_client.py:1163-1178` still uses an older **inline dict** (wire-float brake, no provenance columns). `_native_cache_row` is exercised only by `test_native_cache_roundtrip.py`. | **NOT fixed (read-only task)** — documented; recommended one-line fix: replace the inline dict with `self._native_cache_row(driver, telemetry_response, bundle)` | A test must exercise the production path, not a helper production doesn't call on that side; verify by writing through the real service method, not the helper |

---

## 5. Impact statement

**Observable changes for the Qualifying page** (vs golden, with `ACQUISITION_MODE=native`):
- Telemetry traces are drawn from ~49 % fewer points — every one a real measurement. Shapes
  are unchanged at chart scale (median min-speed-location shift +1.58 m Shanghai / −0.09 m
  Monaco).
- Per-corner brake points move by ≤ one real native sample on 28/35 corner-instances; a handful
  (T10/T17 etc.) move ~1–1.5 samples (smoothing × spacing, §forensics); two no-braking "kink"
  corners (T9 both circuits) move materially.
- A few confidence tiers shift as a consequence of brake/zone movement (§3.3); no confidence
  code changed.
- Monaco's lap-breakdown reconciliation **improved** (0.492 → 0.257 s).

**Provably unchanged:** legacy head byte-identical to golden (harness check, every run); response
schemas shape-identical; exclusion list untouched (`git diff --name-only main`: no
corner_config values, confidence weights 1.0/0.7/0.3, insight templates, frontend, Race/Practice);
delta-grid closure exact.

**Registered debts and owners (zone-logic / detector gate):**
- **STOP-3** (Shanghai 0.0858 s lap-breakdown): +51.7 ms T15 `zone_too_small` stale delta;
  −34.1 ms uncovered head segment [0–4.6 m] in `calculate_straight_segments`. Both pre-existing.
- **STOP-4** (Monaco gap-overlapped T9/T11/T14) + **Monaco's pre-existing 0.492 s** legacy
  zone-arithmetic failure.
- **OPEN-1/OPEN-2** (Monaco T10/T17): detector decel-smoothing window × native spacing
  (`compute_deceleration:864-866`) — recommended for registration (§forensics).
- Gap-region delta behaviour (grid still interpolates across gaps) — fusion gate.

**Out-of-scope bug flagged for follow-up:** the **legacy telemetry cache-poisoning** bug —
`_get_telemetry_legacy` writes `session_part`-filtered telemetry under the unfiltered cache key
(the read is gated by `if not session_part`, the write is not); a later unfiltered request can
be served Q3-filtered data. The native path already gates its write correctly. Tracked as a
spawned background task ("Fix legacy telemetry cache-poisoning bug", task_8077a0b7); candidate to
fix-or-delete at the legacy-removal cleanup gate.

---

## 6. Vital awareness items (read before the next gate)

**Operational / config:**
- **Production runs the DEFAULT `CornerAnalysisConfig` for every circuit** — the orchestrator
  never passes `circuit_id` to `analyze_corners_v2`, so all per-circuit overrides in
  `corner_config.py` (Monaco's −4.0 / window 7, etc.) are **dead code on the live path**.
  Confirmed by the forensics reproducing production brake points exactly with the default config.
  This pre-dates G0 but is decision-relevant for the detector gate.
- `ACQUISITION_MODE=legacy` is a true rollback: dispatchers serve the byte-identical merged path
  AND `/telemetry/meta` returns 501 so the orchestrator skips gap flags (no mixed-substrate run).
- Native Parquet cache (`telemetry_native_v1`) is bypassed for every Q3 request (`session_part`
  set). First non-`session_part` request re-materialises and logs at INFO — not an error.
- `acquire_native_bundle` now **rejects** frames with NaN/NaT, non-monotonic time, or >10 %
  duplicate timestamps — a genuinely corrupt session surfaces a 502, not silent bad data. If a
  real cached session legitimately trips this, it will need investigation, not a loosened guard.

**Sharp edges in the code:**
- `compute_deceleration`'s smoothing window is **sample-count based**, so it behaves differently
  as spacing changes — the proximate cause of OPEN-1/OPEN-2 and a latent fragility across all
  corners. Any detector-gate work should make it distance-based.
- **Native cache write/test divergence (errors-log #13):** the production native cache write
  (`fastf1_client.py:1163-1178`) uses an inline dict (wire-float brake, no provenance columns);
  the boolean-fidelity + provenance behaviour asserted by `test_native_cache_roundtrip.py` lives
  only in the unused `_native_cache_row` helper. **No production qualifying impact** (Q3 always
  bypasses the cache via `not session_part`), and round-trip still functions (the inline dict
  writes `meta`, so the read guard passes; brake reloads as floats). But the test over-claims
  vs production. One-line fix recommended (use `_native_cache_row` in the write); do it at the
  same time as the legacy cache-poisoning fix (both are cache-write touch-ups).
- `gap_flag` / `DeltaResult` grid metadata are **internal only**; the response assembly is
  field-explicit, so an `asdict()`/`model_dump()` refactor of `main.py` would leak them. Tests
  pin the disjointness, but reviewers should keep the assembly explicit.
- `GapInterval.t_start/t_end` are on the car-frame Time axis (offset from the re-zeroed wire
  `time` array); the **distance** bounds are the consumption contract.

**Things I would re-examine under third-party review:**
- The OPEN-1/OPEN-2 window-sweep is the load-bearing evidence that the shifts are smoothing, not
  G0 code. It was already adversarially verified this turn (two independent skeptics →
  VERDICT-STANDS; [OPEN_FINDINGS_FORENSICS.md](OPEN_FINDINGS_FORENSICS.md) §Adversarial
  verification). A third-party re-run on the same native arrays would re-confirm in minutes.
- The STOP-3 −34.1 ms head-coverage term: confirm `calculate_straight_segments` genuinely emits
  no pre-first-corner straight (the ledger infers it; a direct read would seal it).
- Whether STOP-4's T11/T14 "gap-overlap" acceptance should be re-tagged given the forensics
  shows T11's shift is smoothing-driven (gap incidental) and T14 is mixed — a labelling
  refinement, not a correctness issue.
- The `/analysis` proxy routes (lap-similarity/clustering) silently switched to native with no
  A/B coverage — low traffic, but unverified on the honest substrate.
- Runtime: native insights is ~3–4 s slower (extra meta round-trip); if that matters, fold gaps
  into the `/telemetry` response or cache the meta.
