# G0 Report — Honest Acquisition & Native Detection

**Claim under test:** *every value the detection path consumes is now a real
measurement, and nothing downstream noticed except in the ways predicted.*

**Branch:** `feature/g0-honest-acquisition` (working tree, uncommitted at user request)
**Environment:** `f1-api` / `f1-analysis` rebuilt images; FastF1 3.8.3, numpy 2.4.6,
pandas 2.3.3 (API) / 3.0.3 (analysis); fixture set: Shanghai 2025 Q3 (PIA/RUS),
Monaco 2025 Q3 (NOR/LEC).

**Verdict (updated by the continuation, see §10 + [CONTINUATION_LOG.md](CONTINUATION_LOG.md)):
SUBSTANTIATED — 0 hard failures; STOP-3/STOP-4 resolved under conditional sign-off and
encoded in a bounded known-deviations registry; gate BLOCKED only on OPEN-1/OPEN-2
(Monaco T10/T17 brake-shift quantisation, outside the acceptance) awaiting owner ruling.**

*(Original pre-continuation verdict preserved below for the record:)*
**Verdict: SUBSTANTIATED — gate BLOCKED on 2 findings requiring sign-off.**
The substrate swap is complete, contract-clean, and test-green. The A/B harness
passes 87 checks including legacy byte-identity and exact delta-grid closure on
all heads. Three hard A/B failures remain; all three are root-caused below, and
none is a defect in the acquisition layer itself — they are (a) a pre-existing
fragility in excluded zone-arithmetic code that any boundary movement can
trigger, and (b) detector indeterminacy on corners that contain no real braking
event or sit inside a *measured acquisition gap*. Resolution options are listed
in §7; per the G0 ground rules they need a decision, not improvisation.

---

## 1. Phase 0 (gate passed)

Full report: [`00_phase0_report.md`](00_phase0_report.md). Summary:
consumer table proves the telemetry/delta/performance-insights machinery is
**Qualifying-only** (Race/Practice/Home/Track/Transparency untouched);
handshake frozen; golden snapshots + baseline metrics captured against images
verified byte-identical to the working tree; cache versioning plan written.
STOP-1 raised and resolved there (§6 of that report): **legacy Monaco already
violates the 5 ms lap-breakdown closure (0.492 s)** → closure criterion adapted
to "native ≤ legacy + 5 ms, Shanghai ≤ 5 ms absolute, delta-grid closure exact".

## 2. What was built

See [`docs/architecture/g0-honest-acquisition.md`](../../docs/architecture/g0-honest-acquisition.md).
In one line: `lap.get_telemetry()` (merged frame, ~51% interpolated car values)
is retired from the analysis path in favour of a provenance-tagged dual-stream
bundle (`native_acquisition.py`), with `acquisition: native|legacy` dispatch,
a new additive `GET /telemetry/meta` (gap inventory), structured
`NativeAcquisitionError` (no silent fallback), versioned native Parquet keys,
and internal-only `gap_flag` / `DeltaResult` grid metadata in the analysis
service. Detection algorithms, thresholds, confidence weights, templates,
frontend, Race/Practice: untouched (verified via `git diff --name-only main`).

## 3. Tests

| Suite | Result |
|---|---|
| API (`apps/api/tests`) | **332 passed** = 313 baseline + 19 new (`test_native_acquisition.py`) |
| Analysis (`apps/analysis_service/tests`) | **313 passed** = 303 pre-existing + 10 new (`test_g0_native_substrate.py`) |

New coverage: gap-law boundary (uniform / jittered / 1.0 s hole / **exact-3×
exclusive**), provenance completeness + reserved-values-unused, distance-
integration parity vs `add_distance` (1e-6), Brake bool→bundle→0.0/1.0-wire,
structured failures, detector-on-native synthetic corner (resolution envelope =
1 sample + smoothing half-window), gap-flag overlap logic (camel+snake),
schema-freeze (`gap_flag` not serialized), `DeltaResult` metadata population
(tier 1 + 3) and default-None compatibility.
Note: the analysis baseline documented as 271 in CLAUDE.md measures 303 on
main — the documented count was stale; every pre-existing test passes.

## 4. A/B results (Phase 5 expectations)

Full diff: [`ab_report.md`](ab_report.md) / [`ab_report.json`](ab_report.json).
**87 passed · 26 flags · 3 hard failures.**

| Expectation | Shanghai | Monaco | Status |
|---|---|---|---|
| Delta-grid closure (`delta[-1]`==official, ≤1e-6) | 0.00e+00 both heads | 0.00e+00 both heads | **PASS (hard)** |
| Lap-breakdown closure (adapted: native ≤ legacy+5 ms) | legacy 0.000 → native **0.086 s** | legacy 0.492 → native **0.257 s** ✓ (48% improvement) | **FAIL Shanghai** → §6 STOP-3 |
| Response schemas identical to golden | identical | identical | **PASS (hard)** |
| Legacy head byte-identical to golden (gate #4) | telemetry+delta byte-identical; insights value-identical (timing stripped) | same | **PASS (hard)** |
| Brake shift ≤ 1 local native gap | 13/16 (81%) | **14/19 (74%)** | **FAIL Monaco >20%** → §6 STOP-4 |
| Apex min-speed (fixed legacy window) | 8 corners ≤1e-2, 8 flagged (≤9 km/h) | 11 ≤1e-2, 8 flagged (≤16 km/h) | flagged, investigated §5 |
| Total corner delta (sum stable, partitions wiggle) | +0.013→+0.242 s (official +0.082) | +0.906→**+0.157 s** (official +0.109) | reported; redistribution allowed — note Monaco's native corner total lands far closer to the official gap than legacy's 8.3× overshoot |
| Confidence tiers (consequence-only changes) | T15 M→L, T16 M→H | T1 H→M, T2 M→H, T5 L→M, T10 H→M | listed; no confidence code edited |
| Registration (median min-speed-loc shift < 5 m) | **+1.58 m** | **−0.09 m** | **PASS (hard)** |
| Provenance | unit-asserted at bundle level; wire witness `schemaVersion=native_v1` | same | **PASS** |
| Gap law (real dropouts found, no false jitter gaps) | 3 gaps, ratios 3.2–3.5 | 6 gaps, ratios 3.2–4.8 | **PASS** (all ratios strictly >3.0) |
| Performance | insights 10.3→12.8 s | 10.1→14.3 s | informational; +2–4 s is the extra `/telemetry/meta` round-trip + uncached native fetches (Q3 requests bypass Parquet by design) |

Sample counts (merged → native): PIA 686→332, RUS 694→343, NOR 521→257,
LEC 531→258 — i.e. the native head serves **~49% of the merged row count**,
which is exactly the measured phantom fraction being removed.

## 5. Gap inventory (both circuits)

| Driver | dt | ratio | location |
|---|---|---|---|
| PIA (Shanghai) | 0.76 s | 3.2 | 485–542 m |
| RUS (Shanghai) | 0.76 s | 3.2 | 3249–3287 m |
| RUS (Shanghai) | 0.84 s | 3.5 | 4414–4492 m |
| NOR (Monaco) | 0.76 s | 3.2 | 851–884 m |
| **NOR (Monaco)** | **1.08 s** | **4.5** | **1642–1721 m — the Tunnel** |
| NOR (Monaco) | 0.88 s | 3.7 | 2408–2466 m |
| LEC (Monaco) | 1.16 s | 4.8 | 883–943 m |
| LEC (Monaco) | 0.76 s | 3.2 | 2091–2116 m |
| LEC (Monaco) | 1.08 s | 4.5 | 3076–3147 m |

No false gaps at normal jitter (unit-tested at the exact 3× boundary;
all detected ratios strictly exceed 3.0). The Monaco Tunnel dropout
(NOR, 1.08 s ≈ 90 m of track) lands **inside T9's analysis zone (1406–1721 m)**
— see STOP-4: the corner whose brake detection moved most is the corner sitting
on a measured acquisition hole. The gap law caught exactly what it exists to catch.

## 6. STOP conditions encountered

**STOP-1 (Phase 0, resolved).** Legacy Monaco lap-breakdown closure = 0.492 s
violates the assumed ≤5 ms invariant before any change. Criterion adapted,
documented in `00_phase0_report.md` §6 before implementation began.

**STOP-2 (pre-implementation probe, resolved by categorisation).** Integration
drift between native and merged distance channels is a *constant* −0.648 m
(Shanghai) / −0.088 m (Monaco) — far under the 5 m/corner threshold (A/B
registration medians +1.58 m / −0.09 m confirm). The exception is **endpoint
coverage**: the merged frame integrated 15–20 m of *phantom* distance beyond
the last real car sample, so nominal apexes in that tail (Monaco T19 @3300 m vs
native end ~3277 m; Shanghai T16 @5380 m vs ~5375 m) lose a few metres of
previously-phantom coverage. Measured in `probe_registration.py` output;
categorised as coverage, not drift.

**STOP-3 (A/B, BLOCKING): Shanghai lap-breakdown closure 0.000 → 0.086 s.**
Root cause confirmed from analysis-service logs:
`Corner 15: zone too small after clamping (50m < 50m)`. Native exit detection
for T14 landed 11.8 m later (one sample), squeezing T15's clamped zone to
49.6 m — **0.4 m under `MIN_ZONE_LENGTH=50`** — which triggers the
`zone_too_small` path (`corner_analysis.py:1500-1507`). That path **keeps the
stale pre-clamp `delta_change`** while the straight segments tile against the
clamped bounds → a double-counted slice → 0.086 s residual. This stale-delta
mechanism is the same family that produces Monaco's pre-existing 0.492 s
failure on the legacy head, lives in **excluded** zone-arithmetic code, and can
be triggered by *any* sub-sample boundary movement. It is not an
acquisition-honesty defect; the acquisition change merely moved a boundary by
one sample and landed on the tripwire.

**STOP-4 (A/B, BLOCKING): Monaco brake-shift violations 5/19 (26%) > 20%.**
Decomposition of the five:
- **T9 (+82.0 m): the Tunnel.** Zone 1406–1721 m contains NOR's measured
  1.08 s acquisition gap (1642–1721 m), and the corner has no sustained
  braking event (≈−11 km/h "drop"). The decel-only detection path is
  positionally unstable on *any* substrate here (threshold crossings exist on
  both; probe `probe_t9_noise.py`). Shanghai's equivalent flag (T9, +157.4 m,
  not a hard failure there) is the same phenomenon without the gap: a flat-out
  kink with no braking event to detect. `gap_flag` now marks the Monaco case
  internally — which is precisely the G0-designed behaviour.
- **T10/T11 (−19.2 m), T14 (−16.5 m), T17 (−13.3 m):** shifts of 1.2–1.4×
  the local median native gap (13.9–15.9 m) — i.e. *one-to-one-and-a-half
  samples* of quantisation on the honest substrate, against a criterion of
  ≤1.0× the **median** local gap. Against the local **maximum** gap these
  would largely pass; the criterion choice (median vs max) was fixed before
  measurement and is not being silently re-traded here.

## 7. Resolution options (decision required — not improvised)

1. **Accept-with-classification (recommended).** Extend the Phase-0 §6
   criterion adaptation: (a) exclude no-braking-event pseudo-corners and
   gap-overlapped corners (now machine-identifiable via `gap_flag`) from the
   brake-shift population — Monaco becomes 4/18 marginal-quantisation
   violations of a median-based criterion, all ≤1.4 samples; (b) treat
   lap-breakdown closure regressions whose logged root cause is
   `zone_too_small` as owned by the excluded zone-arithmetic gate (where
   Monaco's 0.492 s already lives), keeping the delta-grid closure (exact,
   passing) as G0's closure invariant. Gate then passes with both items
   documented as known-issue handoffs to the zone-logic gate.
2. **Fix the tripwire minimally.** A one-line change (`zone_too_small` →
   recompute `delta_change` over the clamped bounds, or treat <50 m zones as
   zero-contribution) would close STOP-3 — but it edits excluded zone logic,
   so it is out of G0 scope without an explicit scope renegotiation.
3. **Reject native default until the zone gate lands.** Keep
   `ACQUISITION_MODE=legacy` as default; ship the layer dark. Costs: phantom
   samples remain in production analysis; the A/B harness keeps both heads
   honest in the meantime.

## 8. Completion-gate checklist

| # | Item | Status |
|---|---|---|
| 1 | Consumer table Qualifying-only | ✅ |
| 2 | Phase 5 green | ⚠️ 87 pass / 3 hard fail — root-caused (§6), options pending sign-off (§7) |
| 3 | Unit + integration tests pass in Docker | ✅ 332 + 313; harness exit code is the integration gate (currently non-zero by design until §7 is decided) |
| 4 | `acquisition_mode=legacy` byte-identical to golden | ✅ (telemetry/delta byte-identical; insights value-identical after stripping `phase_timing`/`total_duration_ms`) |
| 5 | Exclusion list untouched | ✅ `git diff --name-only main` — no corner_config / confidence weights / templates / frontend / Race / Practice |
| 6 | Architecture note | ✅ `docs/architecture/g0-honest-acquisition.md` |
| 7 | A/B report + goldens under `diagnostics/g0/` | ✅ (uncommitted at user request) |

## 9. The G0 claim, assessed

*"Every value the detection path consumes is now a real measurement"* — **true**:
the native head serves 332/343/257/258 provenance-tagged car samples where the
merged head served 686/694/521/531 rows (~51% interpolated); provenance is
asserted at bundle level; the wire witness (`schemaVersion=native_v1`) is
harness-asserted.

*"Nothing downstream noticed except in the ways predicted"* — **true with two
sharp edges**: schemas identical, legacy byte-identical, delta-grid closure
exact, registration sub-2 m, 81%/74% of brake points within one native sample.
The two hard edges are an excluded-code tripwire (stale-delta on
`zone_too_small`, §6 STOP-3) and detector indeterminacy exactly where the data
is dishonest or the corner is fictitious (§6 STOP-4) — the second of which G0's
own gap law now detects and marks.

Two unprompted improvements the honest substrate delivered on Monaco — the
circuit where granularity bites hardest — are worth recording: the
lap-breakdown closure error fell from 0.492 s to 0.257 s, and the corner-delta
total fell from +0.906 s (an 8.3× overshoot of the official +0.109 s gap) to
+0.157 s. Cleaner inputs made the *excluded, unchanged* zone arithmetic less
wrong on its own.

---

## 10. Continuation — gate close (2026-06-12)

Full detail: [CONTINUATION_LOG.md](CONTINUATION_LOG.md). Summary of what changed
after the original verdict:

- **Adversarial review rerun** (5 lenses, plain-text output): 10 REAL code fixes
  (input validation against NaN/NaT/non-monotonic/duplicate-timestamp frames;
  exhaustive structured-502 error translation incl. the analysis-proxy routes;
  env-legacy isolation of `/telemetry/meta`; `Literal`-validated acquisition
  mode; request-schema pattern; doc fixes) + 13 contract-coverage test gaps
  closed. 8 NOISE findings logged with rationale. Legacy bodies re-verified
  **token-identical** to main by the reviewer.
- **Native Parquet cache round-trip** (the one path the harness never touched):
  bundle-fidelity cache schema (boolean Brake, provenance columns,
  schema-version read guard that refuses legacy-shaped frames) + a permanent
  4-test integration suite including a cold-subprocess read. All green.
- **STOP-3 resolved — fork 1 via OR-clause.** The per-zone delta ledger
  ([stop3_ledger_output.txt](stop3_ledger_output.txt)) attributes the full
  85.8 ms within 5 ms: +51.7 ms T15 `zone_too_small` stale delta, −34.1 ms
  pre-existing head-coverage hole [0–4.6 m] in `calculate_straight_segments`.
  Both mechanisms are excluded-zone logic G0 did not author or alter. Legacy
  closes at 0.0000 s on the identical pair. Registered, bound 0.10 s.
- **STOP-4 partially resolved.** Classification
  ([stop4_classification.txt](stop4_classification.txt)): T9/T11/T14
  gap-overlapped (T9 = the Tunnel dropout) → **registered** with per-corner
  bounds; **T10/T17 are real braking corners with no gap overlap — the §3a
  halt fired**; they are carried as OPEN-1/OPEN-2 (not accepted, loudly
  rendered, dedicated harness exit code 3) pending owner ruling.
- **Known-deviations registry** (`tools/ab_harness/known_deviations.json`)
  enforced by the harness: accepted ≠ invisible (always rendered), growth
  beyond bound = hard fail, unregistered violation = hard fail. **Tamper test
  proven** (deregistering STOP-3 → exit 1).
- **Final state:** harness `0 hard / 4 known-deviation / 2 open / 89 passed →
  exit 3`; suites **361 API + 319 analysis** green; legacy byte-identity
  re-proven on the rebuilt images; exclusion list re-verified untouched.
  Gate item 2 closes when the owner rules on OPEN-1/OPEN-2.
