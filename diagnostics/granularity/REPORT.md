# Telemetry Granularity Diagnostic — Evidence Report

**Scope:** read-only investigation of the qualifying telemetry analysis pipeline
(`apps/analysis_service`). No application code, thresholds, or config were
modified. All scripts live in `diagnostics/granularity/` (scratch) and were run
inside the production `f1-api` container against the production FastF1 cache.

**Verdict (up front): CONFIRMED.** Granularity is the dominant source of
analytical imprecision in corner-scale calculations, and the confidence
tolerances are — by the code's own comments — sized to absorb it. Root cause is a
**combination**: an inherent ~4 Hz FastF1 source, amplified by our use of
`get_telemetry()` (which merges two interleaved ~4 Hz streams, roughly half the
resulting rows being interpolated), and further masked by our Phase-2 alignment
resampling everything onto a fixed 1000-point grid that is ~3× denser than the
native car-channel measurements.

---

## 1. Environment & session

| Item | Value |
|------|-------|
| Runtime | `f1-api` Docker container (matches production) |
| FastF1 | 3.8.3 |
| NumPy / pandas / SciPy | 2.4.6 / 2.3.3 / 1.17.1 |
| Cache | `/app/data/cache` (production FastF1 cache, fully populated, offline reads) |
| **Primary session** | **2025 Chinese GP (Shanghai), Qualifying Q3** |
| Primary drivers | PIA `1:30.641` (raw-audit reference) vs RUS `1:30.723` — two fastest in Q3 |
| **Contrast session** | **2025 Monaco GP, Qualifying Q3** (street circuit) |
| Contrast drivers | NOR `1:09.954` vs LEC `1:10.063` — two fastest in Q3 |

Drivers were chosen programmatically as the two fastest valid Q3 laps per session
(`_common.top_two_drivers`). "Q3" = the final qualifying segment; laps were taken
from `Session.laps.split_qualifying_sessions()` then `pick_fastest()`, mirroring
the production `session_part='Q3'` filter.

**F1 terms used:** *lap telemetry* = per-sample channels (Speed, Brake, Gear…)
along one timed lap; *apex* = geometric corner mid-point; *braking zone* = the
track segment from brake application to apex; *delta* = cumulative time difference
between two drivers vs track position.

---

## 2. Root-cause map (Phase 0) — how a sample reaches Phase 2

Full detail in [`00_entry_path_notes.md`](00_entry_path_notes.md). Summary with
file/line refs:

1. **FastF1 call:** `fastest_lap.get_telemetry()`
   — `apps/api/app/services/telemetry/fastf1_client.py:665` (telemetry endpoint),
   `:807/:828` (delta endpoint). This is FastF1's high-level accessor: internally
   it calls `get_car_data()` + `get_pos_data()`, `merge_channels()` onto the
   **union** of both timebases, then `add_distance()` / `add_relative_distance()`.
   **An interpolation/merge step is therefore baked in before our code sees data.**
   No `frequency=` / `resample_channels()` is passed anywhere (grep-clean).
2. **API downsample (no-op here):** `:696-714` downsamples only if
   `len > DOWNSAMPLE_THRESHOLD` (= **5000**, `config.py:19`). A quali lap is
   ~300–700 rows → branch never fires; raw samples pass through to the analysis
   service untouched.
3. **Phase 2 alignment (ours):** `delta_analysis.py` resamples onto
   `np.linspace(0,1,1000)` (`:292`) via `np.interp` (`:295-296`); `num_points`
   default **1000** (`performance_orchestrator.py:71,584`). *This is the second,
   self-inflicted resampling.*
4. **Phase 3 corner detection (ours):** brake/apex/exit run on the **raw merged
   arrays** (`performance_orchestrator.py:630-640`); `compute_deceleration`
   (`corner_analysis.py:809`) and the `detect_braking_zone_v2` backward walk
   (`:1027-1032`) iterate those samples. But the *time gained/lost per corner* is
   read from the 1000-pt delta grid via `get_delta_change_in_range` →
   `np.interp` (`delta_analysis.py:631-702`).
5. **Pre-admission in config:** `core/corner_config.py:9` ("~5 Hz sampling, ~17m
   between samples"), `:52-53` (`braking_point_tolerance = 20.0  # ±20m at ~5 Hz`).
   These feed the High/Medium/Low confidence ladder in `detect_braking_zone_v2`
   (`:1040-1045`).

**Two interpolation amplifications stack:** native car samples → merged
`get_telemetry` (~2×) → 1000-pt delta grid (~3× vs native).

---

## 3. Evidence tables (one section per phase)

### Phase 1 — Raw sample-interval audit (Shanghai, PIA)
[`results/01_sample_intervals.json`](results/01_sample_intervals.json)

| Source | rows | median dt | eff. Hz | min dt | max dt | std |
|--------|-----:|----------:|--------:|-------:|-------:|----:|
| car_data (Speed/RPM/Throttle/Brake/Gear) | 332 | 0.241 s | **4.15** | 0.16 s | 0.76 s | 0.089 |
| pos_data (X/Y/Z) | 352 | 0.240 s | **4.17** | 0.04 s | 0.82 s | 0.094 |
| get_telemetry (merged) | 686 | 0.136 s | 7.35* | 0.003 s | 0.695 s | 0.086 |

*Interpretation:* the "~4 Hz" assumption is **accurate as a median** but the
stream is **jittered**, not uniform — car-data dt ranges 0.16–0.76 s (a 4.75×
spread). The merged "7.35 Hz" is *illusory* (see Phase 2). Two cached circuits,
same picture.

### Phase 2 — Channel-rate divergence (Shanghai, PIA)
| Metric | Value |
|--------|------:|
| car timestamps (unique) | 332 |
| pos timestamps (unique) | 352 |
| **shared exact timestamps** | **0 (0.0%)** |
| union (= merged rows) | 684 (~686) |
| merged `Source` tags | `pos: 352, car: 332, interpolation: 2` |

*Interpretation:* car-data and pos-data are **completely interleaved, never
co-sampled**. `get_telemetry()` therefore produces 686 rows where only **332
carry native car-channel measurements**; the other **352 rows have Speed, Brake,
Throttle, etc. linearly interpolated** onto position timestamps. Any downstream
code that treats the 686-row array as 686 measurements is consuming ~51% phantom
car-channel points.

### Phase 3 — Spatial resolution at speed
[`results/02_spatial_resolution_PIA.json`](results/02_spatial_resolution_PIA.json),
[`..._NOR.json`](results/02_spatial_resolution_NOR.json)

metres between consecutive **native** samples (`gap = speed · dt`):

| Band | Shanghai (PIA) median | Monaco (NOR) median |
|------|----------------------:|--------------------:|
| all speeds | 15.0 m | 11.1 m |
| ≥ 200 km/h | 19.1 m | 17.4 m |
| ≥ 250 km/h | 21.1 m | 17.9 m |
| ≥ 300 km/h | 21.0 m | — (top 289 km/h) |
| top speed | 330 km/h | 289 km/h |
| **high-speed worst case** | **18.3 m @ 330 km/h (200 ms); max 39.7 m** | **25.6 m @ 288 km/h (320 ms); max 77.9 m** |

*Interpretation:* at racing speed, consecutive measurements are **~18–22 m apart
typically and up to ~40–78 m in the worst dropouts**. End-of-straight brake
points cannot be located more finely than this. The effect scales with speed
(generality confirmed on a second, lower-speed circuit: Monaco's median gap is
smaller everywhere, but its dropouts are larger).

### Phase 4 — Derivative-noise demonstration (Shanghai, PIA, T2 braking zone)
[`results/03_derivative_noise_PIA.json`](results/03_derivative_noise_PIA.json)

15 native samples in the [400, 680] m zone (318 → 161 km/h). v²-kinematic
deceleration `a = (v₂²−v₁²)/(2·Δd)` — the exact formula in `compute_deceleration`:

Raw native decel sequence (m/s²):
`1.7, 0.0, 0.0, -5.6, -17.4, -14.3, -5.8, -18.6, -16.3, -8.8, -16.1, -7.0, -14.3, -12.7`

| Variant | mean \|point-to-point\| | max \|Δ\| | std |
|---------|------------------------:|----------:|----:|
| RAW (native ~4 Hz) | **6.03 m/s²** | 12.7 m/s² | 6.97 |
| Cubic-spline upsample (uniform, ×10) — *comparison only* | 0.80 m/s² | 2.67 m/s² | 7.43 |
| Savitzky-Golay (uniform, win 11) — *comparison only* | 0.78 m/s² | 2.63 m/s² | 7.40 |

*Interpretation:* on the raw signal, deceleration swings violently
(−5 ↔ −18 m/s² between adjacent points, plus a non-physical +1.7 m/s² where the
car is braking). Smoothing on a uniform grid cuts point-to-point variation by
**~87%**. This is illustrative, **not a proposed fix** — and note the smoothing
must be done on a *uniformly resampled* grid; a naïve Savitzky-Golay on the raw
non-uniform/merged array produces artifacts (it assumes constant spacing).

### Phase 5 — Per-channel signal character (Shanghai, PIA, merged)
[`results/04_channel_character_PIA.json`](results/04_channel_character_PIA.json)

| Channel | dtype | #unique | character | range |
|---------|-------|--------:|-----------|-------|
| Speed | float64 | 517 | continuous | 65–330 |
| RPM | float64 | 656 | continuous | 5497–12303 |
| Throttle | float64 | 164 | continuous | 0–99 |
| **Brake** | **bool** | **2** | **binary (no cubic spline)** | False/True |
| nGear | int64 | 7 | discrete step | 2–8 |
| DRS | int64 | 4 | discrete step | 8–14 |

*Interpretation:* any upsampling strategy must be **per-channel**: Speed/RPM/
Throttle tolerate spline interpolation; **Brake is boolean** (interpolation would
fabricate fractional brake — use step/nearest or explicit onset modelling);
Gear/DRS are discrete step functions.

### Phase 6 — Corner-scale impact (headline)
[`results/05_corner_scale_PIA.json`](results/05_corner_scale_PIA.json),
[`..._NOR.json`](results/05_corner_scale_NOR.json)

Real samples inside the v2 braking search zone (apex−300 … apex−30 m) and from
detected brake point to apex:

| Corner | speed drop | zone samples (merged / **native**) | brake→apex (merged / **native**) |
|--------|-----------:|-----------------------------------:|---------------------------------:|
| Shanghai T2 (heaviest, 318→161) | 129 km/h | 24 / **12** | 17 / **8** |
| Shanghai T4 | — | 57 / **27** | 54 / **24** |
| Monaco T11 (heaviest, 190 drop) | 190 km/h | 40 / **22** | 33 / **17** |
| Monaco T8 (Portier) | 28 km/h | 90 / **46** | 95 / **49** |

Full 16- / 19-corner tables (native zone counts) are in the JSON; native zone
counts range **10–28 (Shanghai)** and **10–46 (Monaco)**. The v2 kinematic
backward-walk traversed **0–4 samples** in the sampled corners.

> **The brake event for a heavy corner is characterised from ~8–24 native
> samples** (Shanghai T2: ~8 brake→apex; Monaco T11: ~17). The backward-walk
> "refinement" has only a handful of points to walk over.

### Phase 7 — Alignment vs resolution
[`results/06_alignment_interaction_PIA.json`](results/06_alignment_interaction_PIA.json),
[`..._NOR.json`](results/06_alignment_interaction_NOR.json)

| Metric | Shanghai (PIA) | Monaco (NOR) |
|--------|---------------:|-------------:|
| native car samples | 332 | ~270 |
| merged get_telemetry samples | 686 | 521 |
| Phase-2 delta grid points | 1000 | 1000 |
| grid / merged ratio | 1.46× (31% interpolated) | 1.92× (48% interpolated) |
| **grid / native ratio** | **~3.0×** | **~3.7×** |
| mean real spacing | 7.9 m (merged) | 6.3 m (merged) |
| mean grid spacing | 5.4 m | 3.3 m |
| samples per 80 m corner phase | 14.8 grid vs **10.2 real** | 24.3 grid vs **12.6 real** |

*Interpretation:* the alignment provides **spatial co-location** at 1000 points
but **cannot add temporal resolution**. Roughly **two-thirds of the delta grid
points are interpolated relative to native car measurements.** Cause attribution
(`determine_cause` splits each corner zone into braking/apex/exit thirds and reads
`get_delta_change_in_range` off this grid) therefore queries delta at synthetic
positions backed by only ~10–13 real samples per phase. The grid does **not**
mask the issue so much as **launder** it: interpolated points look like
measurements to every downstream consumer.

---

## 4. Headline findings

1. **Effective sample rate ≈ 4.15 Hz** (car-data median dt 0.241 s), jittered
   0.16–0.76 s — not the uniform "4 Hz" assumed.
2. **~18–22 m between samples at racing speed** (worst case 18.3 m @ 330 km/h,
   dropouts to 40–78 m) — the spatial floor for brake-point detection.
3. **A heavy-braking event is characterised from ~8–24 native samples**
   (Shanghai T2 ≈ 8 brake→apex).
4. **~67% of the 1000-point delta grid is interpolated** relative to native car
   measurements (332 native → 1000 grid ≈ 3.0×); smoothing the raw derivative on
   a uniform grid cuts point-to-point noise ~87% but adds **no** independent
   brake-point information.

---

## 5. Verdict & root cause

**CONFIRMED.** Granularity is the dominant limiter of corner-scale precision
(brake-point/apex location, deceleration, per-phase cause attribution), and the
confidence tolerances are explicitly sized to it.

**Root cause — a combination, in order of contribution:**
1. **Inherent to the FastF1 source** — both car-data and pos-data arrive at
   ~4 Hz, jittered. This is the hard ceiling; nothing downstream can recover
   sub-~18 m brake-point resolution at speed.
2. **How we call FastF1** — `get_telemetry()` merges two **interleaved** ~4 Hz
   streams (0 shared timestamps) into one array that is ~51% interpolated for
   car channels yet looks like ~7 Hz, so downstream code overcounts measurements.
3. **Our alignment code** — Phase 2 resamples to a fixed 1000-pt grid (~3× native
   density) and Phase 3 reads per-corner deltas off it, treating interpolated
   grid points as measurements. This compounds (2) rather than mitigating it.

---

## 6. Implications per layer

| Layer | Granularity-attributable imprecision | Genuine analytical uncertainty |
|-------|--------------------------------------|--------------------------------|
| **Corner analysis** | Brake/apex location quantised to ±~one sample = **±18–22 m at speed**; backward-walk has 0–4 points; `braking_point_tolerance = 20 m` ≈ one sample → most Medium/Low confidence is granularity-bound. | Genuine driver-line/brake-bias differences below ~one sample are unresolvable, not "uncertain." |
| **Technique profiling** | Aggregates corner deltas → inherits corner-level noise; per-dimension raw values noisy at the few-ms level. | Cross-driver **percentile ranking** stays valid (all drivers equally limited); absolute magnitudes are the soft part. |
| **Confidence scoring** | **Partly defensive compensation** — confirmed by `corner_config.py:9,52-53` comments and the ±20 m tolerance ≈ one high-speed sample. | The High/Medium/Low ladder also legitimately reflects brake-signal clarity. |
| **Insight generation** | Template hedging fires for low-confidence corners that are granularity-limited. | Wording is deterministic; no added uncertainty. |

---

## 7. Open questions for solution design

1. **Channel-rate reconciliation.** car (4.15 Hz) and pos (4.17 Hz) share **zero**
   timestamps. Any upsampling must pick one time/distance base. pos-data
   occasionally has finer dt (min 0.04 s) — marginal gains possible by anchoring
   on it, but car channels remain ~4 Hz.
2. **Per-channel interpolation policy.** Speed/RPM/Throttle → spline OK; **Brake
   is boolean** (step/nearest or model onset, never spline); Gear/DRS discrete
   (step). One global interpolator is wrong.
3. **Alignment vs resolution.** Increasing `num_points` beyond ~native density
   adds nothing real — 1000 is already ~3× native. Decide whether downstream
   should consume native samples (and interpolate only at query time) instead of
   a denser-than-source grid that disguises interpolation as measurement.
4. **Achievable ceiling.** With a ~4 Hz source, smoothing can clean derivatives
   (~87% point-to-point reduction shown) and stabilise apex/deceleration
   *estimates*, but **cannot** add independent brake-point information below
   ~18–22 m at speed. Any precision claim finer than that is interpolation, and
   should be labelled as such (or the confidence ladder kept).

---

## 8. Reproduce

```powershell
# from repo root, containers up (f1-api healthy)
docker exec f1-api mkdir -p /tmp/diag/results /tmp/diag/tracks
docker cp diagnostics/granularity/. f1-api:/tmp/diag/
docker cp apps/api/app/data/tracks/shanghai.json f1-api:/tmp/diag/tracks/shanghai.json
docker cp apps/api/app/data/tracks/monaco.json   f1-api:/tmp/diag/tracks/monaco.json
docker exec -w /tmp/diag f1-api bash run_all.sh
docker cp f1-api:/tmp/diag/results/. diagnostics/granularity/results/
```

Scripts: `01_sample_intervals.py` (P1–2), `02_spatial_resolution.py` (P3),
`03_derivative_noise.py` (P4), `04_channel_character.py` (P5),
`05_corner_scale.py` (P6), `06_alignment_interaction.py` (P7). All read-only.
