# Practice Page Phase 1: Data Foundation & Long Run Pace Comparison

**Status:** Complete
**Implemented:** March 2026
**Test Baseline:** 104/104 new tests passing (40 transform + 64 data service), full suite 234+ with 0 regressions
**TypeScript:** Zero compilation errors

---

## Table of Contents

1. [Purpose and Significance](#1-purpose-and-significance)
2. [Theoretical and Logical Background](#2-theoretical-and-logical-background)
3. [End-to-End Workflow and Data Flow](#3-end-to-end-workflow-and-data-flow)
4. [Technical Implementation Breakdown](#4-technical-implementation-breakdown)
5. [Test Cases and Verification](#5-test-cases-and-verification)
6. [Learnings and How They Influenced Decisions](#6-learnings-and-how-they-influenced-decisions)
7. [Alignment with Broader Practice Page Plan](#7-alignment-with-broader-practice-page-plan)

---

## 1. Purpose and Significance

### What Phase 1 Does

Phase 1 builds the **complete backend data pipeline** and the **centrepiece frontend panel** for practice session analysis. It extracts all laps from FP1/FP2/FP3 sessions via FastF1, classifies them by type, optionally applies fuel correction, derives traffic context, groups laps into stints, classifies run types (long run vs short run), computes per-stint statistics, and renders an interactive Long Run Pace violin plot comparison panel.

Unlike Race page Phase 1 (which was entirely backend-focused), Practice Phase 1 delivers both the data foundation and the primary analytical visualisation in a single phase. This was a deliberate decision — the practice data pipeline is simpler than the race pipeline, and delivering a visible frontend panel immediately provided tangible value and a verification surface.

### Why It Matters

Practice sessions are the only window teams have to gather data before qualifying and the race. Long run pace — sustained stint performance on race fuel loads — is the strongest predictor of race day competitiveness. A driver who is P15 in qualifying but has the fastest long run pace in FP2 is likely to be a strong race contender.

The existing qualifying infrastructure optimises for single-lap performance (one best lap per driver). Race infrastructure handles full race distances with known fuel loads and controlled conditions (formation lap, safety cars, pit windows). Practice sessions sit in between: they produce multi-stint data with **unknown** fuel loads, **unknown** engine modes, and **highly variable** run plans across teams.

Phase 1 is the foundation that Phases 2 (Short Run / Best Lap) and 3 (Session Progression) consume. Both planned phases query the same cached `get_processed_practice_data()` pipeline rather than loading and processing data independently.

### Position in the Practice Page Architecture

| Phase | Name | Status | Depends On |
|-------|------|--------|-----------|
| **1** | **Data Foundation & Long Run Pace** | ✅ Complete | — |
| 2 | Short Run / Best Lap Comparison | 📋 Planned | Phase 1 |
| 3 | Session Progression & Performance Optimisation | 📋 Planned | Phase 1 |

---

## 2. Theoretical and Logical Background

### 2.1 Practice vs Race: Why a Separate Pipeline

The Race page pipeline (`services/race/`) classifies laps into 8 categories (RACING, IN_LAP, OUT_LAP, SAFETY_CAR, VSC, RED_FLAG, FORMATION, ANOMALY) and applies fuel correction using a known total fuel load (~110 kg) depleted linearly over a race distance. Practice sessions differ fundamentally:

| Aspect | Race | Practice |
|--------|------|----------|
| Lap classifications | 8 types | 5 types (no FORMATION, SC, VSC) |
| Fuel load | Known (~110 kg start) | Unknown (varies by run plan) |
| Fuel correction model | Linear depletion over race distance | Within-stint heuristic (~1.6 kg/lap estimate) |
| Run structure | Continuous with pit windows | Fragmented: installation laps, short runs, long runs, cooldown laps |
| Safety car | Common and must be filtered | Extremely rare in practice |
| Traffic data quality | High (cumulative timing always available) | Variable (FastF1 often lacks position/cumulative_time for practice) |
| Core analytical question | "Who had the best race pace?" | "Who has the best race-simulation pace?" |

These differences justify a dedicated pipeline in `services/practice/` rather than adapting the race pipeline.

### 2.2 Lap Classification Model

Practice laps are classified into 5 categories. The classification uses a priority chain where the first match wins:

| Priority | Classification | Detection Rule | In Pace Analysis? | In Stats? |
|----------|---------------|----------------|-------------------|-----------|
| 1 | `IN_LAP` | `pit_in_time` is set | No | No |
| 2 | `OUT_LAP` | `pit_out_time` is set | No | No |
| 3 | `RED_FLAG` | `track_status` contains `'5'` | No | No |
| 4 | `ANOMALY` | RACING lap that fails outlier test | Visible but excluded | No |
| 5 | `RACING` | All remaining laps with valid `lap_time` | Yes | Yes |

**Why no FORMATION, SAFETY_CAR, or VSC:**
- Practice sessions do not have a formation lap.
- Safety car and VSC deployments in practice are extremely rare and are not reliably flagged by FastF1 for non-race sessions. Including them would add classification complexity with no practical benefit.

**Why IN_LAP takes priority over RED_FLAG:**
A driver entering the pit lane during a red flag should be classified as `IN_LAP` — the pit stop context is more operationally relevant than the red flag status. The `continue` statement after each match in the classification loop enforces this first-match-wins logic.

### 2.3 Outlier Detection

Outliers are detected per driver per compound group, using two-tier OR logic:

```
is_outlier = (lap_time > Q3 + 1.5 × IQR) OR (lap_time > 1.10 × driver_compound_median)
```

Both conditions are applied only when the group has ≥ 4 laps. With fewer laps, no outlier detection runs (the statistical basis is too weak to reliably identify anomalies).

**Why OR logic:** The IQR method is robust to skewed distributions but can fail when a group is uniformly slow (all laps are outliers by absolute standard but not by IQR). The 110% median cap provides a safety net — any lap more than 10% slower than the median is flagged regardless of IQR bounds. This mirrors the approach used in the Race pipeline.

**Why per driver per compound:** A soft tyre stint at 91s and a hard tyre stint at 93s are both valid — outlier detection must scope to the same driver on the same compound to avoid cross-compound false positives.

### 2.4 Warm-Up Flagging

Laps with `tyre_life <= 2` on RACING laps receive `is_warm_up = True`. These laps remain classified as RACING (they appear in pace visualisations) but are excluded from the `is_valid` flag that governs statistical computation (distribution statistics, degradation hints). This prevents artificially slow warm-up laps from skewing stint statistics.

### 2.5 Fuel Correction: The Within-Stint Heuristic

Race fuel correction knows the total fuel load and computes fuel remaining at each lap linearly. Practice sessions have **no known fuel load** — teams run varying amounts depending on the run plan (installation laps use minimal fuel, long run simulations approximate race conditions).

The within-stint heuristic normalises each stint independently to its **end-of-stint baseline** (lightest point):

```
For each lap in a stint:
    laps_remaining = max_tyre_life_in_stint - current_tyre_life
    fuel_remaining = laps_remaining × 1.6 kg/lap
    corrected_time = raw_time - (fuel_remaining × fuel_effect_per_kg)
```

**Key properties:**
- The last lap of each stint has `laps_remaining = 0`, so `correction = 0` (it becomes the baseline).
- Earlier laps get progressively larger subtractions (they carried more fuel).
- Each stint is corrected independently — a 5-lap stint and a 15-lap stint use different `max_tyre_life` values.
- The ~1.6 kg/lap burn rate is an approximate industry average. Actual rates vary by circuit, engine mode, and lift-and-coast strategy.
- The circuit-specific `fuel_effect_per_kg` value (0.028–0.036 s/kg) comes from Track Intelligence via `race-lookup.ts`.

**Why this is approximate:** Without knowing the actual starting fuel, the correction only removes the within-stint fuel mass trend. It does not normalise across stints or across drivers. The UI labels this explicitly as "approximate fuel correction."

**Why default OFF:** Given the inherent imprecision, fuel correction is disabled by default. Users opt in via a toggle, understanding the approximation.

### 2.6 Traffic Derivation

Traffic detection identifies laps where a driver was closely following another car, potentially affecting their pace through dirty air (aerodynamic wake).

```
For each lap_number, group all drivers:
    Sort by position
    For each driver (except P1):
        gap = |cumulative_time(driver) - cumulative_time(driver_ahead)|
        in_traffic = (gap < 1.5s)
```

**The 50% data-availability threshold:** Practice sessions often lack `position` and `cumulative_time` fields in FastF1 data. If fewer than 50% of drivers on a given lap number have both fields, traffic derivation is skipped entirely for that lap group and all laps default to `in_traffic = False`. This is a conservative fallback — missing data means "assume clean air" rather than "assume traffic."

**Why 1.5 seconds:** This threshold represents the approximate distance at which ground-effect F1 cars (2022 regulations onward) experience measurable aerodynamic disturbance from the car ahead. The value is parameterised (not hardcoded) so it can be adjusted.

### 2.7 Run Type Classification

After stints are grouped by `(driver, stint_number)`, each stint is classified:

- **Long run** (`long_run`): ≥ 4 valid laps (RACING, not warm-up)
- **Short run** (`short_run`): < 4 valid laps

The threshold of 4 laps is stored as the constant `LONG_RUN_MIN_LAPS`. This threshold aligns with external F1 analytics sources and captures shorter race-simulation stints that would be excluded by a higher threshold. Long runs represent race simulation stints — the primary focus of practice analysis. Short runs typically represent qualifying simulation laps or installation checks.

### 2.8 Per-Stint Statistics

For each stint with at least one valid lap:

**Box plot and distribution statistics** (Tukey convention, 1.5×IQR whiskers):
- `lowerfence`: max(min_value, Q1 - 1.5×IQR)
- `q1`: 25th percentile
- `median`: 50th percentile
- `q3`: 75th percentile
- `upperfence`: min(max_value, Q3 + 1.5×IQR)
- `mean`: arithmetic mean
- `std_dev`: sample standard deviation (Bessel's correction, `ddof=1`). Returns 0.0 for single-element stints.

All values are rounded to 3 decimal places for consistency with Plotly rendering.

**Individual lap points** (`_build_lap_points()`):
Per-lap data for violin overlay and compound-coloured scatter dots:
- `lap_number`, `lap_time` (fuel-corrected or raw, rounded to 3dp), `compound`, `tyre_life`, `in_traffic`
- Returned as `List[PracticeLapPoint]` on the stint DTO

**Display stint number** (`display_stint_number`):
Sequential 1-based numbering per driver, assigned chronologically by raw `stint_number` **before** sorting by average pace. This ensures a driver's stints are labelled S1, S2, S3 in run order regardless of their final sorted position in the chart.

**Degradation hint** (long runs only, ≥ 4 valid laps):
```
deg_hint = avg(last 2 valid laps) - avg(first 2 valid laps)
```
Positive = getting slower (tyre degradation). Negative = getting faster (track evolution or tyre warm-up). Returns `None` for short runs or stints with fewer than 4 valid laps.

**Clean-air percentage:** Fraction of valid laps with `in_traffic == False`. Range 0.0–1.0. Returns 1.0 if no traffic data is available (conservative default).

**Gap to fastest:** `stint.average_time - fastest_stint.average_time`. Computed by `compute_long_run_stats()` after all stints are assembled, so the fastest stint serves as the reference.

### 2.9 Representative Stint Filtering

Practice sessions include installation runs, aero rake laps, and other non-representative running that may technically have 4+ laps on the same compound but are not genuine race-simulation stints. These stints have average lap times far slower than actual race pace (30–50+ seconds slower), and their inclusion compresses the y-axis range, making it impossible to distinguish real pace differences between genuine long runs.

`_filter_representative_long_runs()` addresses this by computing the **median** average pace across all detected long run stints and excluding any stint whose average is more than `max_gap_to_median` seconds slower:

```
median_pace = median of all stint average_times
threshold = median_pace + max_gap_to_median (default: 8.0s)
keep if: stint.average_time <= threshold
```

**Why 8 seconds:** The gap from the fastest team to the slowest backmarker in practice is typically 2–4 seconds. An 8-second threshold provides generous headroom for legitimate pace differences while reliably excluding installation-pace stints. This is a dual-layer defence working with the frontend's percentile-based y-axis range (P2/P98 bounds) — the filter removes extreme outliers at the data level, while the percentile range handles any remaining edge cases at the visual level.

**Metadata tracking:** `compute_long_run_stats()` tracks `total_long_runs_detected` (before filtering) and `stints_filtered_count` (how many were removed). The frontend displays a note: "Showing N of M long run stints (K non-representative excluded)" when `stints_filtered_count > 0`.

**Edge cases:** Single stints are never filtered (nothing to compare against). Empty input returns an empty list.

---

## 3. End-to-End Workflow and Data Flow

### 3.1 Request Flow

```
Browser                    Next.js                   FastAPI                    FastF1/Mock
  │                          │                          │                          │
  │  GET /practice?          │                          │                          │
  │  season=2025&round=1     │                          │                          │
  │ ──────────────────────>  │                          │                          │
  │                          │  PracticeContent          │                          │
  │                          │  derives sessionId        │                          │
  │                          │  = "2025_1_FP2"          │                          │
  │                          │                          │                          │
  │                          │  useLongRunQuery()        │                          │
  │                          │  ─────────────────────>   │                          │
  │                          │  GET /practice/long-runs  │                          │
  │                          │  ?session=2025_1_FP2      │                          │
  │                          │  &fuel_effect=0           │                          │
  │                          │                          │                          │
  │                          │                          │  get_processed_           │
  │                          │                          │  practice_data()          │
  │                          │                          │  ─────────────────────>   │
  │                          │                          │  get_practice_laps()      │
  │                          │                          │  (Parquet cache or        │
  │                          │                          │   FastF1 live fetch)      │
  │                          │                          │  <─────────────────────   │
  │                          │                          │                          │
  │                          │                          │  Pipeline:                │
  │                          │                          │  1. classify_practice_    │
  │                          │                          │     laps()               │
  │                          │                          │  2. apply_practice_       │
  │                          │                          │     fuel_correction()    │
  │                          │                          │  3. derive_practice_      │
  │                          │                          │     traffic()            │
  │                          │                          │  4. _group_into_stints() │
  │                          │                          │  5. Cache result          │
  │                          │                          │                          │
  │                          │                          │  compute_long_run_        │
  │                          │                          │  stats()                  │
  │                          │                          │  → PracticeLongRunResponse│
  │                          │  <─────────────────────  │                          │
  │                          │  JSON (camelCase)        │                          │
  │                          │                          │                          │
  │  <──────────────────── │                          │                          │
  │  LongRunPacePanel        │                          │                          │
  │  renders violin plot     │                          │                          │
```

### 3.2 Data Pipeline Stages

**Stage 1: Raw Lap Loading**

`FastF1Client.get_practice_laps()` loads ALL laps from a practice session (typically 400-600 laps per FP session across 20 drivers). Unlike qualifying's `pick_fastest()`, this returns every lap including installation laps, in-laps, out-laps, and aborted attempts.

Each raw lap is a dict with fields: `driver`, `team`, `lap_number`, `lap_time`, `sector1_time`, `sector2_time`, `sector3_time`, `compound`, `tyre_life`, `stint`, `pit_in_time`, `pit_out_time`, `track_status`, `position`, `cumulative_time`.

Results are cached via Parquet (`parquet_cache.write(session, "practice_laps", df)`) for subsequent requests.

**Stage 2: Lap Classification**

`classify_practice_laps()` makes a single pass through laps, applying the 5-category priority chain. A second pass detects outliers within RACING laps per driver per compound. A third pass flags warm-up laps. A fourth pass computes the `is_valid` boolean. The function modifies laps in place and returns the same list.

**Stage 3: Fuel Correction (Optional)**

`apply_practice_fuel_correction()` runs only when `fuel_effect_per_kg > 0`. It computes `max_tyre_life` per `(driver, stint)` pair, then subtracts the estimated fuel penalty from each lap. Non-RACING and non-ANOMALY laps receive `fuel_corrected_time = None`.

**Stage 4: Traffic Derivation**

`derive_practice_traffic()` groups laps by `lap_number`, checks the 50% data-availability threshold, and computes gap-to-car-ahead for qualifying laps. All laps receive `gap_to_car_ahead` and `in_traffic` fields.

**Stage 5: Stint Grouping and Statistics**

`_group_into_stints()` groups by `(driver, stint_number)`, filters to stints with valid laps, determines compound (mode of valid laps), classifies run type, computes box plot and distribution statistics (including `std_dev`), degradation hint, clean-air percentage, and individual lap points via `_build_lap_points()`.

**Stage 6: Caching**

The complete result (enriched laps, all stints, long/short run partitions) is cached in `_practice_data_cache` keyed by `session_id + fuel_effect_per_kg`. Subsequent requests for the same session with the same fuel correction setting return instantly.

**Stage 7: Outlier Filtering and DTO Assembly**

`compute_long_run_stats()` filters to long run stints, then applies `_filter_representative_long_runs()` to exclude non-representative stints (installation laps, sensor runs — see Section 2.9). It assigns `display_stint_number` (sequential 1-based per driver, chronologically by raw `stint_number`) before sorting by `average_time` ascending, computes `gap_to_fastest`, and builds the `PracticeLongRunResponse` DTO with `PracticeLongRunStint`, `PracticeLapPoint`, and `PracticeStintStats` nested models. The response includes `total_long_runs_detected` and `stints_filtered_count` metadata for UI reporting.

### 3.3 Frontend Rendering

`LongRunPacePanel` receives the `PracticeLongRunResponse` via `useLongRunQuery()` and renders:

1. **Violin plot** — One Plotly violin trace per driver-stint using `points: 'all'` for native dot rendering inside the violin shape. Layered colour design: violin body uses **team colour** at ~30% opacity (`teamColor + '4D'`) with team-coloured border (`line.width: 1.5`), matching the Race page box plot pattern. Individual dots use **compound colour** (red/yellow/white for Soft/Medium/Hard) to preserve tyre information. Key Plotly settings: `jitter: 0.12`, `pointpos: 0`, `bandwidth: 0.15`, `scalegroup: 'stints'`, `box: { visible: false }`, `meanline: { visible: false }`. Sorted by `averageTime` ascending (fastest left).

2. **Hover tooltips** — Violin body hover (`hoveron: 'points+violins'`) shows: Driver, Stint, Compound, Avg, Median, SD, Gap, Push Laps, Deg, Clean Air. Individual dot hover shows: Lap number, time, compound, traffic flag. No static annotations below the violins — hover tooltips and stint summary cards provide all statistics.

3. **Y-axis range** — Percentile-based: P2/P98 bounds (`[p2 - 0.5, p98 + 1.5]`) for tight y-axis without wasted space. Normal orientation (faster times at bottom). Works in tandem with backend outlier filtering (Section 2.9).

4. **Scrollable container** — `overflow-x-auto` with dynamic `minWidth` (`Math.max(900, stints × 55)px`) to accommodate sessions with many stints without squishing violins.

5. **Dual legend** — React-based legend below chart (not Plotly native — `showlegend: false` on all traces): team legend row (coloured squares via `deduplicateTeams()`) + compound legend row (coloured circles). Matches the pattern established by `RacePaceBoxPlot.tsx`.

6. **Compound tabs** — ALL / SOFT / MEDIUM / HARD filter (reuses `CompoundTabs` from Race page).

7. **Filter status note** — "Showing N of M long run stints (K non-representative excluded)" when `stintsFilteredCount > 0`.

8. **Stint summary cards** — 180px cards with team colour top border and compound badge, showing Avg, Gap, Push, SD, Deg, and Air metrics. Clean-air annotations: green ≥80%, amber 50-79%, red <50%.

9. **Fuel correction indicator** — "(approximate fuel correction applied)" or "(raw lap times)".

10. **Chart title** — "Long Run Pace — {Circuit} ({Session}) {Year}" via `formatChartTitle()` using `getRaceCircuitName()`.

11. **"How to read this chart" guide** — Collapsible section with 4 subsections (What This Chart Shows, Reading the Violins, Stint Summary Cards, Fuel Correction), matching the Race page pattern.

12. **States** — Skeleton loading, error with message, empty ("No long runs with 4+ push laps found"), content with `isPlaceholderData` opacity transition for smooth session switching.

---

## 4. Technical Implementation Breakdown

### 4.1 Backend Files

| File | Purpose | Key Functions/Classes |
|------|---------|----------------------|
| `services/practice/__init__.py` | Package init | — |
| `services/practice/transforms.py` | Pure transform functions (no FastF1 dependency) | `classify_practice_laps()`, `apply_practice_fuel_correction()`, `derive_practice_traffic()` |
| `services/practice/practice_data_service.py` | Central processing pipeline with caching | `get_processed_practice_data()`, `_group_into_stints()`, `_compute_box_stats()`, `_compute_degradation_hint()`, `_compute_clean_air_pct()`, `_get_analysis_times()`, `_build_lap_points()`, `_filter_representative_long_runs()`, `compute_long_run_stats()`, `get_available_sessions()` |
| `routes/practice.py` | API router with 2 endpoints | `GET /practice/sessions`, `GET /practice/long-runs` |
| `models/dto.py` (modified) | Practice-specific Pydantic DTOs | `PracticeStintStats`, `PracticeLapPoint`, `PracticeLongRunStint`, `PracticeLongRunResponse`, `PracticeSessionsResponse` |
| `services/telemetry/fastf1_client.py` (modified) | FastF1 practice data extraction | `get_practice_laps()` |
| `services/mock_data.py` (modified) | Synthetic practice data for development | `get_practice_laps()` (4 drivers × 30 laps, 3 stints) |
| `main.py` (modified) | Router registration | `app.include_router(router, prefix="/practice", tags=["practice"])` |

### 4.2 Frontend Files

| File | Purpose |
|------|---------|
| `app/practice/page.tsx` | Server Component (SSR header + Suspense wrapper) |
| `app/practice/PracticeContent.tsx` | Client orchestrator: URL state, session tabs, fuel toggle, panel rendering |
| `app/practice/PracticePageSkeleton.tsx` | Loading skeleton matching exact layout dimensions |
| `components/practice/PracticeSessionTabs.tsx` | FP1/FP2/FP3 tabs with `.session-tab` CSS, single label for sprint weekends |
| `components/practice/LongRunPacePanel.tsx` | Violin plot panel with team-coloured fills, compound-coloured dots, dual legend, hover tooltips, scrollable container, stint summary cards, compound tabs, filter status note, guide section |
| `lib/hooks/useLongRunQuery.ts` | React Query hook (`staleTime: Infinity`, `keepPreviousData`) |
| `lib/hooks/usePracticeSessionsQuery.ts` | Sessions query hook |
| `lib/hooks/queryKeys.ts` (modified) | Added `practice.sessions()` and `practice.longRuns()` key factories |
| `lib/api.ts` (modified) | Added `fetchPracticeSessions()` and `fetchLongRuns()` functions |
| `packages/models/src/types.ts` (modified) | Added `PracticeLongRunResponse` (incl. `totalLongRunsDetected`, `stintsFilteredCount`), `PracticeLongRunStint` (incl. `displayStintNumber`, `lapTimes`), `PracticeStintStats` (incl. `stdDev`), `PracticeLapPoint`, `PracticeSessionsResponse` TypeScript interfaces |

### 4.3 API Endpoints

**`GET /practice/sessions?year={year}&round_num={round}`**

Returns available practice sessions for a race weekend. Traditional weekends return `["FP1", "FP2", "FP3"]`; sprint weekends return `["FP1"]`. Falls back to the default three-session list if session enumeration fails.

Response: `PracticeSessionsResponse { year, roundNum, sessions }`

**`GET /practice/long-runs?session={session_id}&fuel_effect={fuel_effect}`**

Returns long run stint analysis with pre-computed distribution statistics, individual lap points, degradation hints, and clean-air percentages. Non-representative stints (installation laps, sensor runs) are filtered out. Stints are sorted by average pace (fastest first). Returns an empty stints list (not an error) if no long runs are found.

Response: `PracticeLongRunResponse { sessionId, fuelCorrected, stints[], sessionBestAverage, totalLongRunsDetected, stintsFilteredCount }`

### 4.4 DTO Architecture

All DTOs extend `CamelCaseModel`, which auto-serialises snake_case Python fields to camelCase JSON:

```
PracticeLongRunResponse
├── session_id: str
├── fuel_corrected: bool
├── session_best_average: Optional[float]
├── total_long_runs_detected: int          # Count before filtering
├── stints_filtered_count: int             # How many non-representative stints were removed
└── stints: List[PracticeLongRunStint]
    ├── driver: str
    ├── team: Optional[str]
    ├── stint_number: int
    ├── display_stint_number: int           # Sequential 1-based per driver, chronological
    ├── compound: Optional[str]
    ├── valid_lap_count: int
    ├── total_lap_count: int
    ├── average_time: float
    ├── gap_to_fastest: float
    ├── degradation_hint: Optional[float]
    ├── clean_air_pct: float
    ├── stats: PracticeStintStats
    │   ├── lowerfence: float
    │   ├── q1: float
    │   ├── median: float
    │   ├── q3: float
    │   ├── upperfence: float
    │   ├── mean: float
    │   └── std_dev: float                  # Sample standard deviation (ddof=1)
    └── lap_times: List[PracticeLapPoint]   # Individual lap data for violin overlay
        ├── lap_number: int
        ├── lap_time: float
        ├── compound: Optional[str]
        ├── tyre_life: Optional[int]
        └── in_traffic: bool
```

### 4.5 Caching Strategy

**Backend:** `_practice_data_cache` is an in-memory Python dict keyed by `f"{session_id}_{fuel_effect_per_kg}"`. The full processed dataset (enriched laps + all stints) is cached after the first request. The `/long-runs` endpoint calls `compute_long_run_stats()` on the cached data — a lightweight filter-and-sort operation.

**FastF1/Parquet:** Raw laps are cached via the Parquet cache singleton after the first FastF1 fetch. Subsequent requests skip the network call entirely.

**Frontend:** `useLongRunQuery` uses `staleTime: Infinity` (F1 practice data is immutable once the session ends) and `gcTime: 30 * 60 * 1000` (30 minutes) to prevent memory growth. `keepPreviousData` enables smooth transitions when switching sessions without a flash of empty content.

### 4.6 Session State Management

`PracticeContent` manages three state dimensions:
- **Season + Round:** Parsed from URL search params (`?season=2025&round=24`), defaulting to 2025/24.
- **Practice session:** Local state (`selectedSession`), defaulting to "FP2" for traditional weekends. Auto-adjusts if the selected session is unavailable (sprint weekends).
- **Fuel correction:** Boolean toggle, defaulting to OFF. When ON, the circuit-specific `fuelEffectPerKg` from `race-lookup.ts` is passed as a query parameter.

Session ID is derived as `${season}_${round}_${activeSession}` (e.g., `2025_24_FP2`).

### 4.7 Component Reuse from Race Page

| Component | Source | Reuse Type |
|-----------|--------|-----------|
| PlotlyLazy | `components/charts/PlotlyLazy.tsx` | Direct import |
| plotlyTheme | `lib/plotlyTheme.ts` | Direct import |
| ErrorBoundary | `components/race/ErrorBoundary.tsx` | Direct import |
| CompoundTabs | `components/race/CompoundTabs.tsx` | Direct import |
| race-lookup.ts | `data/tracks/race-lookup.ts` | Direct import (fuel values) |
| compounds.ts | `lib/compounds.ts` | Direct import (colour mapping) |
| formatLapTime / formatDelta | `lib/formatters.ts` | Direct import |
| getTeamColor / getDriverInfo | `lib/drivers.ts` | Direct import |
| CSS classes | `globals.css` | `.card-panel`, `.session-tab`, `.skeleton` |

---

## 5. Test Cases and Verification

### 5.1 Transform Tests (`test_practice_transforms.py` — 40 tests)

| Test Class | Count | Key Coverage |
|-----------|-------|-------------|
| `TestPracticeClassification` | 11 | All 5 classification types, priority ordering, missing lap_time handling, warm-up flagging, is_valid computation |
| `TestPracticeOutlierDetection` | 5 | IQR-based detection, 110% median cap, OR logic, per-driver/compound scoping, minimum 4 laps threshold |
| `TestPracticeWarmUp` | 4 | tyre_life ≤ 2 flagging, tyre_life > 2 remains valid, warm-up excluded from is_valid |
| `TestPracticeFuelCorrection` | 11 | Correction magnitude verification, last lap zero correction, multi-stint independence, disabled correction (fuel_effect=0), non-RACING laps skipped, missing tyre_life handling |
| `TestPracticeTraffic` | 9 | Gap computation, 1.5s threshold, 50% data-availability fallback, position sorting, P1 has no gap, empty laps |

**Key test: `test_correction_magnitude`** — Verifies the exact formula by computing the expected correction for a known stint and asserting the fuel-corrected time matches `raw_time - (laps_remaining × 1.6 × fuel_effect_per_kg)`.

**Key test: `test_multi_stint_independence`** — Verifies that two stints with different lengths are corrected independently, each using its own `max_tyre_life`.

### 5.2 Data Service Tests (`test_practice_data_service.py` — 64 tests)

| Test Class | Count | Key Coverage |
|-----------|-------|-------------|
| `TestStintGrouping` | 9 | Basic grouping, run type classification (≥4 laps = long_run, boundary at 3/4/5), compound determination (mode), invalid-only stints skipped, multi-driver grouping, stats present in output |
| `TestBoxStats` | 6 | All 6 base statistics (lowerfence/q1/median/q3/upperfence/mean), 3-decimal rounding, uniform data, 1.5×IQR whisker bounds |
| `TestDegradationHint` | 7 | Long run computation (avg last 2 - avg first 2), short run returns None, insufficient data returns None, positive/negative values, exactly 4 laps edge case |
| `TestCleanAirPct` | 5 | All clean, mixed, all traffic, empty list returns 1.0, 2-decimal rounding |
| `TestAnalysisTimes` | 4 | Raw mode, fuel-corrected mode, fallback when fuel_corrected_time is None, missing lap_time skipped |
| `TestComputeLongRunStats` | 7 | Sorting by average_time, gap_to_fastest computation, empty stints returns empty response, fuel_corrected flag, session_best_average rounding, DTO field mapping, filter metadata in response (total_long_runs_detected, stints_filtered_count) |
| `TestStdDev` | 6 | Known-value verification, single-value returns 0.0, identical values return 0.0, two-value computation, key presence in box stats dict, 3-decimal rounding |
| `TestLapPoints` | 8 | Population from valid laps, all fields present (lap_number/lap_time/compound/tyre_life/in_traffic), raw time mode, fuel-corrected mode, fallback when fuel_corrected_time is None, skip when time is None, 3-decimal rounding, presence in stint output dict |
| `TestLongRunMinLaps` | 1 | Constant `LONG_RUN_MIN_LAPS` equals 4 |
| `TestDisplayStintNumber` | 4 | Sequential 1-based numbering for single driver, numbering with stint number gaps, independent numbering across multiple drivers, display_stint_number present in DTO output |
| `TestFilterRepresentativeLongRuns` | 7 | Normal stints all retained, extreme outlier (50s gap) removed, slow backmarker (3s gap) retained, threshold boundary precision (exactly at vs just over), single stint never filtered, empty input returns empty, multiple outliers removed |

### 5.3 Verification Approach

All 104 new tests were self-contained with `_make_lap()` and `_make_stint_laps()` factory helpers. Tests used `pytest.approx()` for floating-point comparisons with `abs=1e-6` for time values and `abs=1e-4` for percentages. No external dependencies or fixtures were required.

The full regression suite (234+ tests) was run to confirm zero regressions across existing qualifying, race, and Analysis service tests.

TypeScript compilation was verified via `pnpm --filter web exec tsc --noEmit` (clean, zero errors). Note: `pnpm --filter web build` encounters a pre-existing EPERM symlink error on Windows/OneDrive during the standalone file-copy step — this is an environment issue, not a code defect.

---

## 6. Learnings and How They Influenced Decisions

### 6.1 Learning: Practice Data Quality Is Lower Than Race Data

**Observation:** FastF1 provides less reliable `position` and `cumulative_time` data for practice sessions compared to race sessions. During implementation, it became clear that traffic derivation would frequently fail if we required the same data completeness as the race pipeline.

**Decision:** Introduced the 50% data-availability threshold — if fewer than half the drivers on a given lap number have both `position` and `cumulative_time`, traffic derivation is skipped entirely for that lap group. All laps default to `in_traffic = False` (conservative: "assume clean air if we don't know").

**Impact:** This prevents spurious traffic flags based on incomplete data while still capturing genuine traffic when the data is available.

### 6.2 Learning: Fuel Correction Must Be Explicitly Approximate

**Observation:** Race fuel correction is deterministic — the total fuel and race distance are known. Practice fuel correction is inherently approximate because teams vary starting fuel by run type and no telemetry reveals the actual fuel load.

**Decision:** Made fuel correction default OFF and explicitly labelled "(approximate fuel correction applied)" in the UI. The correction normalises within each stint independently rather than attempting cross-stint normalisation that would require fuel load assumptions.

**Impact:** Users understand the limitation before enabling the feature. The within-stint heuristic correctly reveals degradation trends within a stint without making unjustified claims about cross-stint or cross-driver fuel-corrected comparisons.

### 6.3 Learning: Reuse the Race Pipeline Pattern, Not the Code

**Observation:** The race transform functions (`classify_race_laps`, `apply_fuel_correction`, `derive_traffic`) in `utils/transforms.py` could have been parameterised to handle practice sessions. However, the differences are significant enough that conditional branching would make the code harder to read and test.

**Decision:** Created a separate `services/practice/transforms.py` with dedicated functions. The _pattern_ (classify → fuel correct → traffic derive → group → compute stats) is identical to the race pipeline. The _implementation_ is adapted to practice-specific requirements (fewer classifications, within-stint fuel model, 50% data threshold).

**Impact:** Each pipeline is independently testable and readable. Changes to practice classification don't risk regressions in race classification. The test suites are separate and self-contained.

### 6.4 Learning: Deliver the Frontend Panel in Phase 1

**Observation:** Race page Phase 1 was entirely backend — the first visible UI came in Phase 2. This meant the data pipeline was validated only through backend tests and curl commands until Phase 2 was built.

**Decision:** For practice, Phase 1 includes the Long Run Pace panel. This provides an immediate visual verification surface and delivers user value from day one.

**Impact:** Issues in DTO serialisation (camelCase field mapping), Plotly trace construction, and React Query configuration were caught and resolved within Phase 1 rather than surfacing as integration surprises in Phase 2.

### 6.5 Learning: Compound Tabs Are Universally Applicable

**Observation:** The `CompoundTabs` component built for the Race page's Tyre Degradation panel works identically for practice long runs — filter stints by compound with an ALL option.

**Decision:** Imported `CompoundTabs` directly from `components/race/` without modification. The component is UI-agnostic — it renders tabs and calls `onChange` with the selected compound string.

**Impact:** Zero new code for compound filtering UI. This validates the architectural principle of building feature-agnostic shared components during Race page development.

### 6.6 Learning: Mock Data Must Reflect Real Structure

**Observation:** The `MockDataService.get_practice_laps()` method needed to produce data with the same field names, types, and structural properties (multiple stints, varying compounds, installation laps, in-laps) as real FastF1 data. Early test failures were caused by missing fields like `track_status` in mock data.

**Decision:** The mock generates 4 drivers × 30 laps each across 3 stints (MEDIUM long run, SOFT short runs, HARD long run), with realistic pit in/out laps, warm-up effects, and compound-specific pace differences.

**Impact:** The mock data service enables development without a FastF1 connection while exercising the full classification and enrichment pipeline.

---

## 7. Alignment with Broader Practice Page Plan

### 7.1 What Phase 1 Established for Phases 2 and 3

**Shared data pipeline:** Both Phase 2 (Short Run / Best Lap) and Phase 3 (Session Progression) will call `get_processed_practice_data()` with the same session ID. The cached result contains both `long_run_stints` and `short_run_stints` — Phase 2 simply reads the `short_run_stints` partition that Phase 1 already computes but does not yet expose via an endpoint.

**Frontend patterns:** The `PracticeContent` orchestrator is designed with placeholder slots for Phase 2 and Phase 3 panels (commented-out `ErrorBoundary` blocks). Each new panel follows the same pattern: dedicated query hook, independent loading state, `ErrorBoundary` wrapping with sessionId-keyed reset.

**Session state:** The session tabs, fuel correction toggle, and session ID derivation logic are shared across all panels. Phase 2 and 3 panels receive `sessionId` and `fuelEffect` as props from `PracticeContent`, matching the Race page's props-drilling pattern.

### 7.2 Phase 2 Preparation

Phase 2 will add:
- `GET /practice/short-runs` endpoint querying the cached pipeline
- `PracticeShortRunResponse` DTO
- Horizontal bar chart component
- `useShortRunQuery` hook

The backend effort is minimal — the data is already computed and cached. The effort is primarily frontend (new chart component and hook).

### 7.3 Phase 3 Preparation

Phase 3 will add cross-session comparison (FP1 → FP2 → FP3) and performance optimisation. This requires loading data from multiple sessions (calling `get_processed_practice_data()` for each FP session) and computing gap-to-session-best to neutralise track evolution.

The `get_available_sessions()` function (Phase 1) already provides the session list that Phase 3 needs to know which sessions to query.
