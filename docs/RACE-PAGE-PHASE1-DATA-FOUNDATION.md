# Race Page Phase 1: Race Data Foundation

**Status:** Complete
**Implemented:** February 2026
**Test Baseline:** 59/59 tests passing (38 transform + 19 service + 2 integration)
**Live Validation:** Baku 2025 (19 drivers, 44 laps) — traffic counts verified against race narrative
**TypeScript:** Zero new compilation errors

---

## Table of Contents

1. [Purpose and Significance](#1-purpose-and-significance)
2. [Theoretical and Logical Background](#2-theoretical-and-logical-background)
3. [End-to-End Workflow and Data Flow](#3-end-to-end-workflow-and-data-flow)
4. [Technical Implementation Breakdown](#4-technical-implementation-breakdown)
5. [Test Cases and Verification](#5-test-cases-and-verification)
6. [Alignment with Broader Race Page Plan](#6-alignment-with-broader-race-page-plan)

---

## 1. Purpose and Significance

### What Phase 1 Does

Phase 1 builds the **backend data pipeline** that every Race page feature depends on. It extracts all race laps from FastF1 (typically 1,000-1,400 records per race: 50-70 laps x 20 drivers), classifies them by type, applies fuel correction to reveal true pace, derives traffic context, extracts stint boundaries and pit stop events, and computes pre-aggregated box plot statistics for the Race Pace Distribution panel.

### Why It Matters

The existing qualifying infrastructure uses `pick_fastest()` to collapse the dataset to one lap per driver. Race analysis requires the full dataset — every single lap driven by every driver — because the analytical questions are fundamentally different:

| Qualifying | Race |
|-----------|------|
| "Who is fastest over one lap?" | "Who had the best pace over a full race distance?" |
| ~20 data points (1 per driver) | ~1,200 data points (all laps) |
| Clean, controlled conditions | Pit stops, safety cars, traffic, fuel, tyre degradation |
| Single classification (valid/invalid) | 8 classification categories |

Phase 1 is entirely backend-focused with no frontend deliverables. Every number that the Race page will eventually show to users originates from what this phase delivers.

### Position in the Race Page Architecture

Phase 1 is the first of six planned phases:

| Phase | Name | Depends On |
|-------|------|-----------|
| **1** | **Race Data Foundation** | — |
| 2 | Race Pace Distribution (Box Plot) | Phase 1 |
| 3 | Tyre Degradation Analysis | Phase 1 |
| 4 | Pit Stop Analysis | Phase 1 |
| 5 | Team Performance Quadrant | Phase 1 |
| 6 | Performance Optimization & Integration | Phases 1-5 |

Every subsequent phase calls into Phase 1's shared processing service to obtain its slice of the enriched dataset. The pipeline runs once per session and caches the result in memory.

---

## 2. Theoretical and Logical Background

### 2.1 Lap Classification Model

Race laps fall into 8 categories. Different downstream features require different subsets — for example, pace analysis uses RACING laps while pit stop extraction uses IN_LAP laps. The classification must happen before any statistical computation.

**Classification Priority (first match wins):**

| Priority | Classification | Detection Rule | In Pace Analysis? | In Tyre Deg? |
|----------|---------------|----------------|-------------------|-------------|
| 1 | `FORMATION` | `lap_number <= 1` with no valid `lap_time` | No | No |
| 2 | `IN_LAP` | `pit_in_time` is set | No | No |
| 3 | `OUT_LAP` | `pit_out_time` is set | No | No |
| 4 | `SAFETY_CAR` | `track_status` contains `'4'` | No | No |
| 5 | `VSC` | `track_status` contains `'6'` or `'7'` | No | No |
| 6 | `RED_FLAG` | `track_status` contains `'5'` | No | No |
| 7 | `RACING` | All remaining laps with valid `lap_time` | Yes | Yes |
| 8 | `ANOMALY` | RACING lap that fails outlier test | Yes (as outlier dot) | No |

**Priority ordering matters.** A pit in-lap during a safety car period should be classified as `IN_LAP`, not `SAFETY_CAR`, because the pit stop information is the more operationally relevant classification. The `continue` statement after each match enforces first-match-wins.

**TrackStatus encoding:** FastF1 concatenates status codes into strings (e.g., `'14'` = green + safety car transition). The implementation uses the `in` operator (`'4' in track_status`) rather than equality checks to correctly detect status within concatenated codes.

### 2.2 Outlier Detection (Two-Tier, OR Logic)

After primary classification, RACING laps undergo outlier detection to identify anomalous times that would skew statistical analysis. Two independent tests are applied per driver:

1. **IQR-based:** `lap_time > Q3 + 1.5 * IQR` (Tukey's method, robust to skew)
2. **Percentage cap:** `lap_time > 1.10 * driver_median` (safety net for tight distributions)

Either condition alone triggers reclassification to `ANOMALY` (OR logic). This two-tier approach catches both statistically extreme times and obviously slow laps that might survive IQR detection in distributions with high variance.

A minimum of 4 laps per driver is required for meaningful IQR computation. Drivers with fewer laps skip outlier detection entirely.

### 2.3 Warm-Up Flag

The first 2 laps of each stint (identified by `tyre_life <= 2`) are flagged with `is_warm_up = True`. These laps are still classified as `RACING` (they appear in pace analysis) but will be excluded from tyre degradation regression in Phase 3, since cold-tyre performance is not representative of the compound's degradation trend.

The flag is only set on RACING laps — a safety car lap with `tyre_life = 1` does not get the warm-up flag.

### 2.4 Fuel Correction Model

F1 cars start with approximately 110 kg of fuel and burn it evenly across the race (~1.8-2.2 kg/lap depending on circuit). Each kilogram of fuel adds 0.028-0.036 seconds per lap depending on circuit characteristics.

The correction normalizes all lap times to an empty-tank equivalent:

```
fuel_per_lap = total_fuel_kg / total_race_laps
fuel_remaining = total_fuel_kg - (fuel_per_lap * lap_number)
fuel_remaining = max(fuel_remaining, 0.0)              # Clamp to zero

corrected = raw_time - (fuel_remaining * fuel_effect_per_kg)
```

**Direction: subtraction.** Earlier laps get a larger subtraction because the car is heavier. A lap 1 correction with 110 kg remaining at 0.032 s/kg removes 3.52 seconds. A lap 50 correction (near race end) with minimal fuel removes almost nothing.

This reveals the tyre degradation trend that is otherwise hidden by the offsetting fuel burn benefit.

**Circuit-specific factors** range from 0.028 s/kg (low-drag circuits like Silverstone, Monza) to 0.036 s/kg (traction-limited circuits like Monaco, Singapore). These values are stored in the Track Intelligence database and flow from the frontend as query parameters.

### 2.5 Traffic Derivation

Laps driven in traffic (within 1.5 seconds of the car ahead) are aerodynamically compromised — reduced downforce in dirty air affects cornering performance. The pipeline computes gap-to-car-ahead and flags affected laps.

**Data source:** FastF1's `Time` column — the cumulative session time at lap completion (`timedelta64[ns]`, 100% non-null for validated sessions). This provides the actual physical gap between cars on track, unlike lap time differentials which only measure pace similarity.

**Why cumulative time, not lap time differentials:** Two drivers can post identical 90-second laps while running 15 seconds apart on track. A lap-time-differential proxy would flag both as "in traffic" (0s gap) when they are nowhere near each other. Cumulative session time gives the true interval: `gap = abs(5415.0 - 5400.0) = 15.0s → not in traffic`.

**Algorithm:**
- Group all laps by `lap_number`
- Sort each group by `position` (P1 first)
- Filter to laps with valid `position` and `cumulative_time`
- For consecutive positions, compute `gap = abs(current.cumulative_time - ahead.cumulative_time)`
- Flag `in_traffic = True` when `gap < threshold` (default 1.5 seconds)

The race leader is never flagged. The threshold (1.5s) is parameterized and reflects the aerodynamic influence range for 2022+ ground-effect cars. Laps missing `cumulative_time` or `position` receive safe defaults (`in_traffic = False`, `gap_to_car_ahead = None`).

**Validation (Baku 2025):** VER (race winner) = 0 laps in traffic (0%), field average = 16.6 laps (37.8%), range 0-32 laps. This matches the race narrative — VER led in clear air, NOR/LEC battled closely (~70%), backmarkers spent significant time in traffic.

### 2.6 Box Plot Statistics

The Race Pace Distribution panel requires pre-computed statistics per driver. These are computed server-side to avoid sending raw lap data to the frontend:

- **Q1, Median, Q3** — from RACING laps only
- **Whiskers** — Tukey standard: Q1 - 1.5*IQR to Q3 + 1.5*IQR
- **Outliers** — All times (including ANOMALY) beyond the upper whisker
- **Gap to fastest** — This driver's mean minus the fastest driver's mean
- **Consistency score** — Mean of per-stint standard deviations (requires 3+ laps per stint)
- **Tyre strategy** — Ordered list of compounds from stints
- **Traffic count** — Number of laps flagged `in_traffic`

Drivers are sorted by mean ascending (fastest first). Mean is used because ANOMALY laps are already excluded upstream, making the dataset clean. This matches industry convention (FDataAnalysis, F1-Tempo). Median is still computed and stored for box plot rendering.

---

## 3. End-to-End Workflow and Data Flow

### 3.1 Request Flow

```
Client Request
  GET /race/pace?session=2025_17_Race&fuel_effect=0.032
       │
       ▼
  race.py router
       │ calls get_processed_race_data(session_id, fuel_effect)
       │ then  compute_race_pace_stats(race_data)
       ▼
  race_data_service.py
       │ Check _race_data_cache → hit? return cached
       │                       → miss? proceed ▼
       ▼
  data_service.py factory
       │ get_data_service() → FastF1Client or MockDataService
       ▼
  fastf1_client.py: get_race_laps(session_id)
       │ Check Parquet cache → hit? return cached records
       │                     → miss? load from FastF1 ▼
       ▼
  FastF1 library
       │ session.laps (ALL laps, ~1,200 rows)
       │ Extract: Driver, Team, LapNumber, LapTime, Sectors,
       │          Compound, TyreLife, Stint, Position,
       │          PitInTime, PitOutTime, TrackStatus, IsPersonalBest,
       │          Time (cumulative session time → cumulative_time)
       │ Write to Parquet cache
       ▼
  Back in race_data_service.py:
       │
       ├── 1. classify_race_laps(raw_laps)
       │     Formation → In/Out Lap → SC/VSC/RF → Racing → Outlier → Warm-up
       │
       ├── 2. apply_fuel_correction(classified, total_laps, fuel_effect)
       │     corrected = raw - (fuel_remaining * factor)
       │
       ├── 3. derive_traffic(fuel_corrected)
       │     Group by lap → sort by position → cumulative time gaps → flag
       │
       ├── 4. extract_stints(enriched)
       │     Group by (driver, stint) → StintResponse list
       │
       └── 5. extract_pit_stops(enriched)
             Find IN_LAP laps → compute duration → flag anomalies
       │
       ▼
  Cache result in _race_data_cache
       │
       ▼
  compute_race_pace_stats(race_data)
       │ Per-driver: Q1, median, mean, Q3, outliers, gap, consistency, strategy
       ▼
  RacePaceResponse → JSON (auto camelCase) → Client
```

### 3.2 Caching Strategy

Two levels of caching ensure the pipeline only processes each session once:

| Layer | Cache | Key | Scope | Persistence |
|-------|-------|-----|-------|------------|
| Raw data | Parquet files | `{session_id}_race_laps` | FastF1Client | Disk (survives restart) |
| Processed data | In-memory dict | `{session_id}_{fuel_effect}` | RaceDataService | Memory (cleared on restart) |

The Parquet cache stores raw lap data after extraction from FastF1, avoiding repeated API calls. The in-memory cache stores the fully processed result (classified, fuel-corrected, with stints and pit stops), avoiding repeated computation for the same session.

---

## 4. Technical Implementation Breakdown

### 4.1 Files Created

| File | Purpose | Lines |
|------|---------|-------|
| `apps/api/app/services/race/__init__.py` | Package init | 1 |
| `apps/api/app/services/race/transforms.py` | Classification, fuel correction, traffic | 215 |
| `apps/api/app/services/race/race_data_service.py` | Shared processing service + stats computation | 323 |
| `apps/api/app/routes/race.py` | API endpoint | 26 |
| `apps/api/tests/__init__.py` | Test package init | 0 |
| `apps/api/tests/test_race_transforms.py` | Transform unit tests (38 tests) | 561 |
| `apps/api/tests/test_race_data_service.py` | Service unit tests (19 tests) | 297 |
| `apps/api/tests/test_race_integration.py` | Full-pipeline integration tests (2 tests) | 181 |

### 4.2 Files Modified

| File | Change | Impact |
|------|--------|--------|
| `apps/api/app/models/dto.py` | Added 6 race DTOs after line 122 | New types: `LapClassificationType`, `RaceLapResponse`, `StintResponse`, `PitStopResponse`, `DriverPaceResponse`, `RacePaceResponse` |
| `apps/api/app/services/telemetry/fastf1_client.py` | Added `get_race_laps()` method | Returns ALL laps (no `pick_fastest()`) with Parquet caching |
| `apps/api/app/services/mock_data.py` | Added `get_race_laps()` method | Synthetic data: 4 drivers x 57 laps |
| `apps/api/app/main.py` | Registered race router | `app.include_router(race.router, prefix="/race", tags=["race"])` |
| `packages/models/src/types.ts` | Added 6 TypeScript interfaces | `LapClassification`, `RaceLapData`, `RaceStintData`, `PitStopData`, `DriverPaceData`, `RacePaceResponse` |
| `apps/web/data/tracks/types.ts` | Added `fuelEffectPerKg?: number` | Optional field on `TrackIntelligence` interface |
| All 24 circuit `.ts` files | Added `fuelEffectPerKg` value | Per-circuit fuel correction factors (0.028-0.036) |

### 4.3 DTOs (`apps/api/app/models/dto.py`)

Six new models extending `CamelCaseModel` (which provides automatic snake_case to camelCase JSON serialization):

**`LapClassificationType`** — `Literal["RACING", "IN_LAP", "OUT_LAP", "SAFETY_CAR", "VSC", "RED_FLAG", "FORMATION", "ANOMALY"]`

**`RaceLapResponse`** — Complete enriched lap record with 21 fields covering timing (lap_time, sector times, fuel_corrected_time, cumulative_time), tyre state (compound, tyre_life, stint), position, classification, traffic context, and pit timing.

**`StintResponse`** — Stint summary: driver, team, stint_number, compound, start_lap, end_lap, lap_count.

**`PitStopResponse`** — Pit event: driver, team, stop_number, lap_number, pit_lane_time, is_anomaly.

**`DriverPaceResponse`** — Pre-computed box plot statistics: min, Q1, median, mean, Q3, max (within whiskers), outliers list, gap_to_fastest, tyre_strategy, consistency_score, laps_in_traffic, total_racing_laps.

**`RacePaceResponse`** — Top-level response: session_id + list of DriverPaceResponse.

### 4.4 Transform Functions (`apps/api/app/services/race/transforms.py`)

Three pure functions with no FastF1 dependency — they operate on lists of plain dicts and are fully unit-testable without any external service:

**`classify_race_laps(laps)`**
- Phase 1: Primary classification with priority-based first-match-wins
- Phase 2: Per-driver outlier detection (IQR + 110% median, OR logic, minimum 4 laps)
- Phase 3: Warm-up flag on RACING laps with `tyre_life <= 2`
- Modifies laps in-place and returns the list

**`apply_fuel_correction(laps, total_race_laps, fuel_effect_per_kg, total_fuel_kg)`**
- Computes `fuel_per_lap = total_fuel_kg / total_race_laps`
- For each RACING/ANOMALY lap: `corrected = raw - (fuel_remaining * factor)`
- Clamps `fuel_remaining` to 0.0 minimum (handles laps beyond race length)
- Non-racing laps and laps with `None` time get `fuel_corrected_time = None`
- Edge case: `total_race_laps = 0` sets all corrections to `None`

**`derive_traffic(laps, threshold)`**
- Sets safe defaults (`gap_to_car_ahead = None`, `in_traffic = False`) on all laps
- Groups by lap_number, filters to laps with valid position + cumulative_time
- Sorts by position, computes gap as `abs(current.cumulative_time - ahead.cumulative_time)` for consecutive positions
- Flags `in_traffic = True` when `gap < threshold`
- Falls back gracefully when position or cumulative_time data is missing

### 4.5 Race Data Service (`apps/api/app/services/race/race_data_service.py`)

**`get_processed_race_data(session_id, fuel_effect_per_kg)`** — Async orchestrator:
1. Check `_race_data_cache` → return cached if hit
2. Lazy-import `get_data_service` (avoids pulling FastF1/pyarrow at module level)
3. Call `data_service.get_race_laps(session_id)` for raw data
4. Pipeline: classify → fuel correct → derive traffic → extract stints → extract pit stops
5. Cache and return the enriched result dict

**`extract_stints(laps)`** — Groups laps by (driver, stint_number), computes per-stint summary (compound via mode, start/end lap, count). Returns `List[StintResponse]`.

**`extract_pit_stops(laps)`** — Finds all IN_LAP-classified laps, matches to next-lap OUT_LAP for duration computation (`pit_out_time - pit_in_time`). Sequential stop numbering per driver. Anomaly flagging: `pit_lane_time > 35.0` OR `pit_lane_time > 2.0 * team_median`.

**`compute_race_pace_stats(race_data)`** — Per-driver box plot statistics:
- Filters to RACING + ANOMALY laps with valid lap_time
- RACING times used for Q1/median/Q3/mean; ANOMALY times included only in outlier list
- Whisker bounds: Q3 + 1.5*IQR (upper), Q1 - 1.5*IQR (lower)
- Consistency: mean of per-stint standard deviations (minimum 3 laps per stint)
- Tyre strategy extracted from stints in stint-number order
- Sorted by mean ascending; gap_to_fastest computed relative to fastest driver's mean

### 4.6 FastF1Client Extension (`apps/api/app/services/telemetry/fastf1_client.py`)

New `get_race_laps()` method (does NOT modify existing `get_laps()`):
- Returns ALL laps: no `pick_fastest()`, no `_filter_valid_laps()` — race analysis needs pit and out laps
- Parquet cache with `data_type="race_laps"` (separate from qualifying cache)
- NaN handling: `v != v` pattern for NaN detection on cache read; `pd.notna()` guards on all FastF1 field access
- Timedelta→seconds: `.total_seconds()` for LapTime, Sectors, PitInTime, PitOutTime, Time (→ `cumulative_time`)
- `cumulative_time`: Extracted from FastF1's `Time` column — cumulative session time at lap completion. Used by `derive_traffic()` for actual physical gap computation
- Stint column: checked with `'Stint' in lap.index` before access
- Returns `List[dict]` — classification and enrichment happen in RaceDataService

### 4.7 Mock Data Service (`apps/api/app/services/mock_data.py`)

New `get_race_laps()` method generating synthetic data:
- 4 drivers (VER, NOR, LEC, HAM) x 57 laps
- 2 stints per driver with compound change (MEDIUM → HARD)
- Realistic base times (~90s) with driver-specific offsets and per-lap random variation
- Pit in-lap (lap 25) and out-lap (lap 26) with pit times
- Safety car laps (laps 35-36)
- One anomalous lap per driver
- Incrementing tyre age, position ordering
- `cumulative_time`: Growing value per lap per driver, with faster drivers accumulating less total time and gaps increasing over the race (realistic)

### 4.8 API Route (`apps/api/app/routes/race.py`)

```
GET /race/pace?session={session_id}&fuel_effect={fuel_effect_per_kg}
```

- `session` (required): Session ID (e.g., `2025_17_Race`)
- `fuel_effect` (optional, default 0.032): Fuel correction factor in seconds per kg
- Response model: `RacePaceResponse`
- Calls `get_processed_race_data()` then `compute_race_pace_stats()`

Registered in `main.py` with `prefix="/race"`, `tags=["race"]`.

### 4.9 TypeScript Types (`packages/models/src/types.ts`)

Six interfaces matching backend DTOs with camelCase field names:

- `LapClassification` — Union type of 8 classification strings
- `RaceLapData` — Complete enriched lap including `cumulativeTime` (mirrors `RaceLapResponse`)
- `RaceStintData` — Stint summary (mirrors `StintResponse`)
- `PitStopData` — Pit event (mirrors `PitStopResponse`)
- `DriverPaceData` — Box plot statistics (mirrors `DriverPaceResponse`)
- `RacePaceResponse` — Top-level response: `sessionId` + `drivers: DriverPaceData[]`

Uses existing `TyreCompound` type for compound fields.

### 4.10 Track Intelligence Fuel Sensitivity (`apps/web/data/tracks/`)

Added `fuelEffectPerKg?: number` to the `TrackIntelligence` interface (optional to avoid breaking existing code). All 24 circuit files updated with research-validated values:

| Tier | Range (s/kg) | Circuits |
|------|-------------|----------|
| **Low (0.028-0.029)** | Low-drag, high-speed | Silverstone (0.028), Monza (0.028), Spa (0.029), Suzuka (0.029) |
| **Mid (0.031-0.033)** | Mixed profiles | Australia (0.032), China (0.032), Jeddah (0.031), Miami (0.033), Imola (0.031), Spain (0.033), Austria (0.031), Zandvoort (0.032), Azerbaijan (0.032), USA (0.033), Mexico (0.031), Brazil (0.033), Las Vegas (0.031), Qatar (0.032), Abu Dhabi (0.033) |
| **High (0.034-0.036)** | Traction-limited, heavy braking | Bahrain (0.034), Monaco (0.036), Canada (0.034), Hungary (0.035), Singapore (0.036) |

Derivation heuristic: baseline 0.032, +0.002-0.003 if Pirelli braking severity >= 4 AND traction >= 4, -0.002-0.003 if high average speed with few low-speed corners.

---

## 5. Test Cases and Verification

### 5.1 Test Execution

**Command:**
```bash
cd apps/api && python -m pytest tests/test_race_transforms.py tests/test_race_data_service.py tests/test_race_integration.py -v
```

**Result:** 59/59 passed in 0.45s

```
tests/test_race_transforms.py::TestLapClassification::test_empty_list PASSED
tests/test_race_transforms.py::TestLapClassification::test_normal_racing_lap PASSED
tests/test_race_transforms.py::TestLapClassification::test_in_lap_classified PASSED
tests/test_race_transforms.py::TestLapClassification::test_out_lap_classified PASSED
tests/test_race_transforms.py::TestLapClassification::test_safety_car_classified PASSED
tests/test_race_transforms.py::TestLapClassification::test_vsc_classified PASSED
tests/test_race_transforms.py::TestLapClassification::test_red_flag_classified PASSED
tests/test_race_transforms.py::TestLapClassification::test_formation_lap_no_time PASSED
tests/test_race_transforms.py::TestLapClassification::test_concatenated_track_status PASSED
tests/test_race_transforms.py::TestLapClassification::test_outlier_iqr_detection PASSED
tests/test_race_transforms.py::TestLapClassification::test_outlier_percentage_cap PASSED
tests/test_race_transforms.py::TestLapClassification::test_warm_up_flag PASSED
tests/test_race_transforms.py::TestLapClassification::test_warm_up_not_set_for_non_racing PASSED
tests/test_race_transforms.py::TestLapClassification::test_pit_classification_priority_over_track_status PASSED
tests/test_race_transforms.py::TestFuelCorrection::test_early_lap_corrected_more PASSED
tests/test_race_transforms.py::TestFuelCorrection::test_corrected_time_less_than_raw PASSED
tests/test_race_transforms.py::TestFuelCorrection::test_non_racing_laps_not_corrected PASSED
tests/test_race_transforms.py::TestFuelCorrection::test_none_lap_time_handled PASSED
tests/test_race_transforms.py::TestFuelCorrection::test_fuel_remaining_clamped_to_zero PASSED
tests/test_race_transforms.py::TestFuelCorrection::test_custom_fuel_factor PASSED
tests/test_race_transforms.py::TestFuelCorrection::test_zero_fuel_effect PASSED
tests/test_race_transforms.py::TestFuelCorrection::test_anomaly_laps_get_corrected PASSED
tests/test_race_transforms.py::TestFuelCorrection::test_empty_laps PASSED
tests/test_race_transforms.py::TestFuelCorrection::test_zero_total_laps PASSED
tests/test_race_transforms.py::TestTrafficDerivation::test_leader_not_in_traffic PASSED
tests/test_race_transforms.py::TestTrafficDerivation::test_close_following_flagged PASSED
tests/test_race_transforms.py::TestTrafficDerivation::test_gap_above_threshold_not_flagged PASSED
tests/test_race_transforms.py::TestTrafficDerivation::test_custom_threshold PASSED
tests/test_race_transforms.py::TestTrafficDerivation::test_empty_laps PASSED
tests/test_race_transforms.py::TestTrafficDerivation::test_single_car PASSED
tests/test_race_transforms.py::TestTrafficDerivation::test_missing_position_fallback PASSED
tests/test_race_transforms.py::TestTrafficDerivation::test_missing_cumulative_time_fallback PASSED
tests/test_race_transforms.py::TestTrafficDerivation::test_distinguishes_close_pace_from_close_gap PASSED
tests/test_race_transforms.py::TestTrafficDerivation::test_multi_car_train PASSED
tests/test_race_transforms.py::TestComplexScenarios::test_multiple_safety_car_periods PASSED
tests/test_race_transforms.py::TestComplexScenarios::test_driver_dnf_mid_race PASSED
tests/test_race_transforms.py::TestComplexScenarios::test_red_flag_restart_stint_numbering PASSED
tests/test_race_transforms.py::TestFuelCorrectionMathematical::test_correction_magnitude_matches_physics PASSED
tests/test_race_data_service.py::TestStintExtraction::test_single_stint PASSED
tests/test_race_data_service.py::TestStintExtraction::test_two_stints PASSED
tests/test_race_data_service.py::TestStintExtraction::test_stint_compound PASSED
tests/test_race_data_service.py::TestStintExtraction::test_multiple_drivers PASSED
tests/test_race_data_service.py::TestStintExtraction::test_empty_laps PASSED
tests/test_race_data_service.py::TestPitStopExtraction::test_pit_stop_from_in_lap PASSED
tests/test_race_data_service.py::TestPitStopExtraction::test_pit_duration_computed PASSED
tests/test_race_data_service.py::TestPitStopExtraction::test_anomalous_stop_flagged PASSED
tests/test_race_data_service.py::TestPitStopExtraction::test_stop_numbering_sequential PASSED
tests/test_race_data_service.py::TestPitStopExtraction::test_no_pit_stops PASSED
tests/test_race_data_service.py::TestRacePaceStats::test_median_computed_correctly PASSED
tests/test_race_data_service.py::TestRacePaceStats::test_sorted_by_mean PASSED
tests/test_race_data_service.py::TestRacePaceStats::test_gap_to_fastest PASSED
tests/test_race_data_service.py::TestRacePaceStats::test_tyre_strategy_ordered PASSED
tests/test_race_data_service.py::TestRacePaceStats::test_consistency_score PASSED
tests/test_race_data_service.py::TestRacePaceStats::test_outliers_beyond_whiskers PASSED
tests/test_race_data_service.py::TestRacePaceStats::test_total_racing_laps_count PASSED
tests/test_race_data_service.py::TestRacePaceStats::test_empty_laps PASSED
tests/test_race_data_service.py::TestRacePaceStats::test_traffic_count PASSED
tests/test_race_integration.py::TestFullPipeline::test_pipeline_produces_valid_output PASSED
tests/test_race_integration.py::TestFullPipeline::test_pipeline_handles_all_dnf PASSED

======================== 59 passed, 1 warning in 0.45s ========================
```

### 5.2 Test Coverage by Component

#### Transform Tests (`test_race_transforms.py` — 38 tests)

**TestLapClassification (14 tests):**

| Test | Context | Verifies | Output Indicates |
|------|---------|----------|-----------------|
| `test_empty_list` | Edge case: no data | Empty in → empty out | Safe handling of empty input |
| `test_normal_racing_lap` | 20 standard laps | Most laps classified as RACING | Normal path works correctly |
| `test_in_lap_classified` | Mixed lap set | IN_LAP detected via pit_in_time | Pit entry correctly identified |
| `test_out_lap_classified` | Mixed lap set | OUT_LAP detected via pit_out_time | Pit exit correctly identified |
| `test_safety_car_classified` | Mixed lap set | track_status '4' → SAFETY_CAR | SC detection works |
| `test_vsc_classified` | Mixed lap set | track_status '6' → VSC | VSC detection works |
| `test_red_flag_classified` | Mixed lap set | track_status '5' → RED_FLAG | Red flag detection works |
| `test_formation_lap_no_time` | Mixed lap set | Lap 1 with no time → FORMATION | Formation lap handled |
| `test_concatenated_track_status` | TrackStatus '14' | '4' detected within '14' | `in` operator handles concatenated codes |
| `test_outlier_iqr_detection` | 20 normal + 1 extreme (130s) | 130s lap → ANOMALY | IQR-based outlier detection works |
| `test_outlier_percentage_cap` | 20 laps at 90s + 1 at 100s | 100s > 110% of 90s median → ANOMALY | Percentage cap catches borderline outliers |
| `test_warm_up_flag` | Mixed lap set | tyre_life <= 2 + RACING → is_warm_up | Warm-up detection targets correct laps |
| `test_warm_up_not_set_for_non_racing` | SC lap with tyre_life=1 | SC lap NOT flagged warm_up | Non-racing laps excluded from warm-up |
| `test_pit_classification_priority_over_track_status` | pit_in_time set + track_status '4' | Classified as IN_LAP, not SC | Priority ordering enforced correctly |

**TestFuelCorrection (10 tests):**

| Test | Context | Verifies | Output Indicates |
|------|---------|----------|-----------------|
| `test_early_lap_corrected_more` | Lap 1 vs Lap 50 | Correction(lap1) > Correction(lap50) | Heavier car → larger subtraction |
| `test_corrected_time_less_than_raw` | 50 racing laps | All corrected < raw | Fuel always adds weight, never removes |
| `test_non_racing_laps_not_corrected` | IN_LAP + OUT_LAP | fuel_corrected_time = None | Non-racing excluded from correction |
| `test_none_lap_time_handled` | Lap with None time | fuel_corrected_time = None | None propagated safely |
| `test_fuel_remaining_clamped_to_zero` | Lap 55 in a 50-lap race | corrected ≈ raw (zero correction) | No negative fuel remaining |
| `test_custom_fuel_factor` | 0.028 vs 0.036 s/kg | Higher factor → lower corrected time | Circuit-specific factors work |
| `test_zero_fuel_effect` | factor = 0.0 | corrected == raw | Zero factor produces no correction |
| `test_anomaly_laps_get_corrected` | ANOMALY classification | correction applied | ANOMALY treated like RACING for fuel |
| `test_empty_laps` | No data | Empty out | Safe empty input handling |
| `test_zero_total_laps` | total_race_laps = 0 | fuel_corrected_time = None | Division-by-zero guard |

**TestTrafficDerivation (9 tests):**

All traffic tests use `cumulative_time` (cumulative session time) for gap computation, reflecting the actual physical distance between cars on track.

| Test | Context | Verifies | Output Indicates |
|------|---------|----------|-----------------|
| `test_leader_not_in_traffic` | P1 + P2 with cumulative times | Leader: in_traffic=False, gap=None | Leader never flagged |
| `test_close_following_flagged` | 0.8s cumulative gap | Follower: in_traffic=True, gap≈0.8 | Physical gap < threshold triggers flag |
| `test_gap_above_threshold_not_flagged` | 3.5s cumulative gap | Follower: in_traffic=False, gap≈3.5 | Physical gap > threshold: no flag |
| `test_custom_threshold` | 1.0s gap, threshold=0.5 | Not flagged (1.0 > 0.5) | Custom threshold respected |
| `test_empty_laps` | No data | Empty out | Safe empty handling |
| `test_single_car` | One car on track | Not flagged | Single car: no traffic possible |
| `test_missing_position_fallback` | position=None | in_traffic=False (safe default) | Graceful degradation |
| `test_missing_cumulative_time_fallback` | No cumulative_time field | in_traffic=False, gap=None | Old data without cumulative_time handled |
| `test_distinguishes_close_pace_from_close_gap` | Identical pace (90s), 15s physical gap | NOT in traffic (gap=15.0) | Validates the core fix: same pace ≠ same position on track |
| `test_multi_car_train` | 3-car DRS train (0.5s + 0.7s intervals) | Pairwise gaps correct, all followers flagged | Verifies consecutive-position interval computation in a train |

**TestComplexScenarios (3 tests):**

| Test | Context | Verifies | Output Indicates |
|------|---------|----------|-----------------|
| `test_multiple_safety_car_periods` | Two SC periods in race | Correct classification of SC laps | Multiple SC periods handled |
| `test_driver_dnf_mid_race` | DNF at lap 10 | Partial data processed correctly | Incomplete races handled |
| `test_red_flag_restart_stint_numbering` | Red flag with restart | Stint numbering continues correctly | Red flag doesn't reset stints |

**TestFuelCorrectionMathematical (1 test):**

| Test | Context | Verifies | Output Indicates |
|------|---------|----------|-----------------|
| `test_correction_magnitude_matches_physics` | Full race with known parameters | Correction magnitude matches physical model | Fuel correction math is physically accurate |

#### Service Tests (`test_race_data_service.py` — 19 tests)

**TestStintExtraction (5 tests):**

| Test | Context | Verifies | Output Indicates |
|------|---------|----------|-----------------|
| `test_single_stint` | 20 laps, one stint | 1 stint, laps 1-20 | Single-stint detection correct |
| `test_two_stints` | Two stints with compound change | 2 stints, MEDIUM then HARD | Multi-stint boundary + compound detection |
| `test_stint_compound` | 3 laps all MEDIUM | compound=MEDIUM | Mode-based compound selection works |
| `test_multiple_drivers` | 2 drivers, 20 laps each | 1 stint per driver | Per-driver stint isolation |
| `test_empty_laps` | No data | Empty list | Safe empty handling |

**TestPitStopExtraction (5 tests):**

| Test | Context | Verifies | Output Indicates |
|------|---------|----------|-----------------|
| `test_pit_stop_from_in_lap` | IN_LAP + OUT_LAP pair | 1 stop at correct lap | IN_LAP→pit stop event mapping works |
| `test_pit_duration_computed` | pit_in=900, pit_out=925 | duration ≈ 25.0s | PitOutTime - PitInTime correctly computed |
| `test_anomalous_stop_flagged` | 40s pit stop | is_anomaly=True | >35s threshold triggers anomaly flag |
| `test_stop_numbering_sequential` | 2 stops for same driver | stop 1, stop 2 | Sequential numbering per driver |
| `test_no_pit_stops` | No pit activity | Empty list | Clean handling of no-stop races |

**TestRacePaceStats (9 tests):**

| Test | Context | Verifies | Output Indicates |
|------|---------|----------|-----------------|
| `test_median_computed_correctly` | 2 drivers, 20 laps | VER median between 90-91.5s | Median from RACING laps only |
| `test_sorted_by_mean` | VER faster than NOR | VER first in output, mean ascending | Ascending mean sort correct |
| `test_gap_to_fastest` | VER ~2s faster than NOR | VER gap=0, NOR gap = mean difference | Gap computed relative to fastest driver's mean |
| `test_tyre_strategy_ordered` | MEDIUM→HARD stints | strategy=["MEDIUM","HARD"] | Compounds in stint order |
| `test_consistency_score` | Synthetic low-variance data | score < 1.0 | Mean of stint stdevs works |
| `test_outliers_beyond_whiskers` | 20 normal + 1 ANOMALY (130s) | 130.0 in outliers list | ANOMALY laps appear as outlier dots |
| `test_total_racing_laps_count` | 20 RACING laps per driver | total_racing_laps=20 | Only RACING counted |
| `test_empty_laps` | No data | drivers=[] | Safe empty handling |
| `test_traffic_count` | 5 of 20 laps in_traffic=True | laps_in_traffic=5 | Traffic count correctly aggregated |

#### Integration Tests (`test_race_integration.py` — 2 tests)

These tests run the full pipeline end-to-end (classify → fuel correct → derive traffic → extract stints → extract pit stops → compute stats) on realistic multi-driver race data:

| Test | Context | Verifies | Output Indicates |
|------|---------|----------|-----------------|
| `test_pipeline_produces_valid_output` | 3-driver, 30-lap race with SC, pit stops, anomaly | Full pipeline produces valid RacePaceResponse | All stages chain correctly, stints/strategies correct |
| `test_pipeline_handles_all_dnf` | Single lap, single driver (edge case) | Pipeline completes with minimal data | Graceful handling of near-empty datasets |

### 5.3 TypeScript Compilation

**Command:**
```bash
pnpm --filter web build
```

**Result:** Zero new TypeScript errors. The only error was a pre-existing one in `packages/models/src/lapSimilarity.ts` (unrelated `TelemetryPoint` export), confirming that the new type definitions are syntactically correct and compatible with existing types.

### 5.4 Integration Verification Commands

For live verification with the Docker stack running:

```bash
# Verify endpoint is registered
curl http://localhost:8000/openapi.json | python -m json.tool | grep race

# Test with mock data (LIVE_DATA=false)
curl "http://localhost:8000/race/pace?session=2025_17_Race"

# Test with real race data (LIVE_DATA=true)
curl "http://localhost:8000/race/pace?session=2025_17_Race&fuel_effect=0.032"

# Verify response structure
curl -s "http://localhost:8000/race/pace?session=2025_17_Race" | python -m json.tool | head -50
```

### 5.5 Live Validation Results

Live validation was performed against three real race sessions via the Docker stack (`LIVE_DATA=true`):

**Endpoint tests (4/4 passed):**
- `GET /race/pace?session=2025_17_Race` → 200 OK, valid JSON
- Response structure: `sessionId` + `drivers[]` with all expected fields
- Custom `fuel_effect` parameter: accepted and applied
- Missing `session` parameter: 422 Unprocessable Entity

**Baku 2025 (Azerbaijan GP — primary validation race):**
- 19 drivers, 44 racing laps per driver
- VER on top (fastest mean)
- Traffic counts validated against race narrative:

| Driver | Position | Traffic Laps | Total | % | Narrative Match |
|--------|----------|-------------|-------|---|----------------|
| VER | P1 | 0 | 44 | 0.0% | Led from front in clear air |
| ANT | P2 | 21 | 44 | 47.7% | Battled in midfield before late surge |
| RUS | P3 | 13 | 44 | 29.5% | Ran with moderate traffic |
| SAI | P4 | 2 | 44 | 4.5% | Ran in clean air most of race |
| NOR | P5 | 31 | 44 | 70.5% | Battled closely with LEC throughout |
| LEC | P6 | 30 | 44 | 68.2% | Battled closely with NOR throughout |
| TSU | P7 | 15 | 43 | 34.9% | Moderate midfield traffic |
| LAW | P8 | 5 | 44 | 11.4% | Ran own race in gap |
| ALB | P9 | 24 | 44 | 54.5% | Significant midfield traffic |
| HAM | P10 | 18 | 44 | 40.9% | Moderate traffic throughout |

Field average: 16.6 laps (37.8%), range 0-32 laps. This represents a structurally correct result — the prior lap-time-differential proxy produced 30-46 laps (70-100%) for nearly every driver including the race leader.

**Bahrain 2024:** 20 drivers, VER on top — confirmed historical data loads correctly.
**Bahrain 2025:** 20 drivers, PIA on top — confirmed 2025 season data loads correctly.

---

## 6. Alignment with Broader Race Page Plan

### 6.1 What Phase 1 Delivers to Downstream Phases

| Downstream Phase | Data Consumed from Phase 1 |
|-----------------|---------------------------|
| **Phase 2: Race Pace Box Plot** | `compute_race_pace_stats()` output directly (pre-computed per-driver statistics) |
| **Phase 3: Tyre Degradation** | Fuel-corrected laps filtered to RACING + `is_warm_up=False`, grouped by stint and compound |
| **Phase 4: Pit Stop Analysis** | `extract_pit_stops()` output directly (per-stop events with anomaly flags) |
| **Phase 5: Team Performance** | Enriched laps with classification for team-level aggregation; requires telemetry extension |

### 6.2 Design Decisions Carried Forward

| Decision | Phase 1 Implementation | Downstream Impact |
|----------|----------------------|-------------------|
| Server-side computation | All stats computed in FastAPI | Frontend receives ready-to-render data; no client-side numpy/scipy |
| Shared processing service | `_race_data_cache` keyed by session | Each endpoint queries the same cached result — no redundant computation |
| Lazy imports | `get_data_service` imported inside function body | Tests run without FastF1/pyarrow installed; Docker dependency isolation |
| `CamelCaseModel` base | All DTOs extend it | Automatic JSON serialization matches frontend TypeScript interfaces |
| Parquet caching | `data_type="race_laps"` separate from qualifying | No interference with existing qualifying cache |
| Circuit-specific fuel factors | Stored in Track Intelligence, passed as query param | Frontend flows the value from track data → API call → correction function |

### 6.3 Constraints Respected

- Existing `get_laps()` and all qualifying methods are unmodified
- `get_data_service()` factory pattern used in routes (not direct instantiation)
- All FastF1 field access guarded with `pd.notna()`
- TrackStatus codes handled with `in` operator for concatenated strings
- Fuel correction direction: subtraction (normalize to empty tank)
- Outlier detection: OR logic (IQR or 110% median)
- `fuelEffectPerKg` is optional on `TrackIntelligence` interface to avoid breaking existing code

### 6.4 Known Limitations

1. **Fuel correction assumes linear fuel burn.** Real fuel consumption varies slightly by circuit sector and driving style. The linear model is the industry standard for public analysis and sufficient for the use case.

2. **Cumulative time gaps are measured at lap completion, not continuously.** The `cumulative_time` field records when each driver crosses the start/finish line, so the computed gap reflects the interval at that moment. Intra-lap position changes (e.g., an overtake mid-lap) are not captured until the next lap boundary.

3. **Track evolution not modelled.** Rubber buildup over a race distance improves grip for later stints. This is a background factor that affects tyre degradation regression (Phase 3) rather than Phase 1's classification or gap computation.

---

*Phase 1 documentation — February 2026*
