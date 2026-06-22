# G0 Continuation Log — Review Rerun, Cache Verification, STOP Resolution

**Branch:** `feature/g0-honest-acquisition` (working tree; **no commits per owner instruction** —
prepared commit messages under [`commit_msgs/`](commit_msgs/))
**Date:** 2026-06-12 | **Environment:** rebuilt `f1-api`/`f1-analysis` images

## 1. Adversarial review rerun — findings table

Rerun succeeded with plain-text reviewer output (previous run lost all 4 reviewers to a
structured-output tooling failure). 5 hostile lenses, full reports archived in the
workflow transcript; triage below. **REAL = violates a stated G0 contract → fixed.
NOISE = logged with rationale, not fixed.**

### REAL → fixed (code)

| # | Finding (lens) | Fix |
|---|---|---|
| R1 | NaN/NaT samples cast to fabricated ints wearing REAL_CAR; NaN dt invisible to the gap law (`NaN > x` is False); non-monotonic time corrupts integration; duplicate timestamps bias the gap-law median upward (L1-2, L3-2..4) | validation block in `acquire_native_bundle` → `NativeAcquisitionError("validate_car", …)`; 6 new tests |
| R2 | `/analysis/lap-similarity` + `/driver-style-clustering` swallow `NativeAcquisitionError` into stringified 500s (L2-2, L4-1) | structured 502 arms in `routes/analysis.py` |
| R3 | Native paths leak unexpected exceptions as raw 500s (unwrapped cache read, lap selection, `int(LapNumber)`, `calculate_delta`) (L4-2) | `_impl` wrappers on all 3 native methods → `NativeAcquisitionError("unexpected")`; route 502 translation now exhaustive; 2 tests |
| R4 | env-`ACQUISITION_MODE=legacy` rollback still ran native acquisition server-side via `/telemetry/meta` and mixed substrates in gap flags (L3-1, L4-5, L2-3) | meta route returns structured 501 when service mode is legacy; orchestrator degrades gracefully; test |
| R5 | `ACQUISITION_MODE` free string — typo silently dispatches native (L4-3) | `Literal["native","legacy"]` — bad env fails at startup |
| R6 | `acquisition_mode` request field unconstrained → garbage degrades into N per-driver 422s (L4-4) | `pattern="^(native|legacy)$"` on the schema field |
| R7 | `GapInterval.t_*` on the car-frame Time axis vs the re-zeroed wire `time` array — undocumented frame mismatch (L1-5) | DTO docstring: d-bounds are the consumption contract; t-frame noted |
| R8 | comp-driver gap distances vs ref/grid axis — undocumented cross-domain approximation (L3-6) | call-site comment: measured constant <1 m drift, no padding at G0 |
| R9 | brake-detection diagnostic scripts still run on the merged substrate — post-G0 threshold tuning would validate the wrong data (L2-5) | warning headers on both scripts (initial PowerShell write mojibake'd Unicode chars — restored from git, re-added via UTF-8-safe edit) |
| R10 | (self-found during tamper test) registry loader rejected Windows BOM | `utf-8-sig` in `load_registry` |

### REAL → fixed (test gaps, lens 5)

Dispatcher matrix (L5-1), NAE propagation + route 502 (L5-2), `/telemetry/meta` route
guards (L5-3), `GapInterval` wire-key pin `dStart` (L5-4), `fetch_all_native_meta`
degradation ×5 (L5-5), cache keyspace disjointness + versioned-key read (L5-6),
near-duplicate-distance decel pathology actually exercised (L5-7), integration parity
asserted on the bundle (L5-8), downsample-branch consistency (L5-9), combined
jitter+hole & two-hole gap fixtures (L5-10), unconditional two-stage assertion (L5-11),
DeltaResult-metadata ∉ response schemas pin (L5-12), symmetric gap-touch edge (L5-14).
**New totals: API 361 passed (was 332), analysis 319 passed (was 313 + corrected count).**

### NOISE → logged, not fixed

| Finding | Rationale |
|---|---|
| Cache-served arrays not re-bound to gaps/meta; `get_telemetry_meta` never cache-first (L1-1, residual) | Production qualifying path (`session_part=Q3`) bypasses Parquet entirely; the schema-version guard (Task 2) now reads `meta` on every cache hit; full cache-coherence design belongs to the cleanup/fusion gate |
| Mock service honours explicit `acquisition=native` with synthetic data (L1-3) | `LIVE_DATA=false` globally declares synthetic data (dev-only); `/telemetry/meta` already 501s in mock mode |
| Dormant downsample branch would desync gaps/meta (L1-4) | unreachable (~330 samples ≪ 5000); slice-consistency now tested |
| Dead duplicate `apps/api/app/services/fastf1_client.py` (L2-1, L4-6) | zero importers verified; deletion scheduled at the legacy-removal cleanup gate per the G0 spec |
| `fastf1_main_tmp.py` scratch file at repo root (L2-6) | untracked, pre-dates the G0 branch, cannot be committed accidentally; **recommend owner deletes it** |
| `median<=0 → []` silent path (L3-5) | unreachable after R1 guards (duplicate/monotonic validation rejects such frames first) |
| Inclusive gap-touch counts as overlap (L3-7) | intentional and conservative-only; boundary semantics test-pinned both edges |
| `GAP_DT_MULTIPLIER == 3.0` constant pin (L5-13) | acceptable contract pin; boundary behaviour separately tested |

Reviewer no-finding verdicts worth recording: legacy bodies **token-identical** to main
(line-diffed against `git show main:…`); dto.py additive-only; cache keyspaces
collision-free; FastF1 `slice_by_lap` adds no synthetic edge samples
(`interpolate_edges=False` default verified in installed source); reserved provenance
values appear nowhere outside the enum/tests.

## 2. Native Parquet cache round-trip (Task 2)

Cache row schema upgraded to bundle fidelity: Brake serialised as **JSON booleans**
(bundle bool dtype, not wire floats), `provenance_car`/`provenance_pos` columns added,
and the read path now refuses any row whose `meta.schema_version != "native_v1"`
(cache miss → re-materialise, logged — never silently parsed as native). Helpers
`_native_cache_row` / `_native_row_to_response` extracted for testability.

Permanent test [`test_native_cache_roundtrip.py`](../../apps/api/tests/test_native_cache_roundtrip.py),
4 tests, all green:
- **cold subprocess read** (fresh python process, zero shared state): channels at 1e-6,
  Brake values are booleans, provenance == REAL_CAR/REAL_POS, gaps exact, meta intact;
- warm service-path read reconstructs a **wire-identical** response (`model_dump` equality);
- legacy-shaped frame under the native key → **refused** (None → re-materialise);
- wrong `schema_version` → refused.

## 3. STOP-3 — attribution evidence and fork taken

1. **Legacy closure, identical pair:** 0.0000 s (golden + fresh legacy-head rerun; every
   legacy corner/straight internally consistent — ledger mismatch exactly 0).
2. **Per-zone delta ledger** ([`stop3_ledger.py`](stop3_ledger.py),
   output [`stop3_ledger_output.txt`](stop3_ledger_output.txt)) — full 85.8 ms attributed
   **within 5 ms**:
   - **+51.7 ms — T15 stale delta**: reported +0.0303 s vs −0.0215 s recomputed over its
     own clamped bounds [5169.3, 5218.9] — the `zone_too_small` tripwire
     (`corner_analysis.py:1500-1507`) keeping the pre-clamp value; confirmed by the
     service log `Corner 15: zone too small after clamping (50m < 50m)`.
   - **−34.1 ms — uncovered HEAD [0.0, 4.6 m]**: `calculate_straight_segments` emits no
     straight before the first corner zone; legacy T1's zone happened to start at 0.0,
     native T1's at 4.6 m (one-sample detection shift), exposing a pre-existing coverage
     hole containing a Tier-1 head-clamping delta step.
   - All other corners and all straight segments: mismatch +0.0000.
3. **Fork taken: fork 1 via its OR-clause** — the ledger proves the full residual lives
   in two pre-existing excluded-zone-logic mechanisms that G0 did not author or alter;
   the honest substrate moved zone boundaries by one sample onto both tripwires.
   Registered (bound 0.10 s), owner: zone-logic gate. No scratch-branch neutralisation
   needed (ledger attribution complete).

## 4. STOP-4 — classification table (Option 1, exclude-but-preserve)

[`stop4_classify.py`](stop4_classify.py) / [`stop4_classification.txt`](stop4_classification.txt);
pseudo-corner criterion: pre-apex speed drop ≤ 15 km/h on native ref telemetry.

| T | shift (m) | local gap (m) | zone (m) | speed drop | gap overlap | pseudo | disposition |
|---|---|---|---|---|---|---|---|
| 9 | +82.0 | 6.6 | 1406–1721 | 150 km/h | **NOR 1642–1721 (Tunnel, dt 1.08 s)** | no | **REGISTERED** (bound 100 m) |
| 10 | −19.2 | 13.9 | 1915–2075 | 214 km/h | none | no | **OPEN-1 — NOT covered, owner pending** |
| 11 | −19.2 | 13.9 | 2075–2094 | 217 km/h | LEC 2091–2116 | no | **REGISTERED** (bound 25 m) |
| 14 | −16.5 | 15.9 | 2408–2503 | 30 km/h | NOR 2408–2466 | no | **REGISTERED** (bound 22 m) |
| 17 | −13.3 | 8.4 | 2896–2977 | 115 km/h | none | no | **OPEN-2 — NOT covered, owner pending** |

**The §3a halt condition fired**: T10 and T17 are real braking corners with no gap
overlap — explicitly outside the conditional acceptance. They are honest
substrate-quantisation effects (detector lands 1.38×/1.58× the local median native
sample spacing away from its merged-frame position; T10's attribution shifts
+0.522 → +0.257 s, confidence high → medium; T17 ±16 ms, confidence unchanged). They
were **not registered**; they are carried as OPEN FINDINGS in the registry file and
rendered loudly by the harness with a dedicated exit code. Fork-independent work
continued; **the gate cannot fully close until the owner rules on OPEN-1/OPEN-2.**

## 5. Known-deviations registry (as landed)

[`tools/ab_harness/known_deviations.json`](../../tools/ab_harness/known_deviations.json):
STOP-3 (shanghai, lap_breakdown closure, bound 0.10 s, measured 0.0858, both root-cause
mechanisms named) and STOP-4 (monaco, corners 9/11/14 with per-corner bounds 100/25/22 m
and gap classifications) + OPEN-1/OPEN-2 carried as non-accepted open findings.
Harness enforcement (`run_ab.py`): KNOWN-DEVIATION section always rendered (accepted ≠
invisible); **hard fail if a deviation grows beyond its bound**; **hard fail on any
unregistered violation**; registered corners excluded from the >20% aggregate
(exclude-but-preserve — they stay in the per-corner table); exit codes: 1 = hard
failure, 3 = open findings pending, 0 = clean.

**Verification runs:**
- Full harness: `0 hard failures · 4 KNOWN-DEVIATIONs (all within bounds) ·
  2 OPEN-FINDINGs · 23 flags · 89 passed → exit 3` ([`ab_report.md`](ab_report.md)).
  Legacy byte-identity re-proven on the rebuilt, review-fixed images inside this run.
- **Tamper test**: STOP-3 removed from a registry copy → harness reverts to strict
  closure checks → `FAIL [shanghai] lap_breakdown closure …` ×2 → **exit 1**. Enforcement proven.

## 6. Final gate status

| # | Completion-gate item | Status |
|---|---|---|
| 1 | Consumer table Qualifying-only | ✅ |
| 2 | Phase 5 green | ⚠️ **0 hard failures; 4 registered KNOWN-DEVIATIONs within bounds; BLOCKED on OPEN-1/OPEN-2 (Monaco T10/T17) — owner sign-off required** |
| 3 | Unit + integration tests in Docker | ✅ 361 API + 319 analysis; round-trip integration test added; harness = CI gate (exit 3 by design until item 2 closes) |
| 4 | legacy byte-identical to golden | ✅ re-proven post-review-fixes |
| 5 | Exclusion list untouched | ✅ final `git diff --stat main`: 14 files, none excluded; corner_analysis.py diff = gap_flag field + comments only |
| 6 | Architecture note | ✅ |
| 7 | A/B report + goldens + registry | ✅ in working tree (commits withheld per owner instruction) |

## 7. Closing claim

**What G0 now claims:** every value the qualifying detection path consumes is a real,
provenance-tagged car-data measurement (332/343/257/258 native samples vs 686/694/521/531
merged rows, ~51% of which were interpolation); acquisition failures surface structured,
never silently; acquisition gaps are detected (strict 3× law), inventoried, and flagged
against corner zones; the legacy path remains byte-identical behind an isolated,
startup-validated flag.

**What G0 does not yet claim (registered non-claims):**
- **gap-region behaviour** — the delta grid still interpolates end-to-end across
  acquisition gaps (closure-preserving by design); uncertainty modelling through gaps
  belongs to the fusion gate;
- **zone-logic debts** — STOP-3's two tripwires (stale-delta-on-small-zone, missing head
  segment), Monaco's pre-existing 0.492 s legacy closure failure, and gap-overlapped
  corners T9/T11/T14 are owned by the zone-logic gate;
- **no smoothing** — derivative noise on the native substrate is unchanged at G0
  (Savitzky-Golay/upsampling deliberately out of scope);
- **OPEN-1/OPEN-2** — brake-point quantisation shifts at Monaco T10/T17 (1.4–1.6
  native samples, real braking corners) await the owner's ruling.
