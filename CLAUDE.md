# ApexView — Codebase Reference

**Document Version:** 6.0 | **Last Updated:** March 2026
**Status:** Qualifying ✅ | Race ✅ | Practice ✅
**Test Baseline:** 313 API tests, 271 analysis tests passing
**Lighthouse:** 94–97 (Qualifying), high 90s (Race)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Implementation Status](#2-implementation-status)
3. [Practice Page — Implementation](#3-practice-page--implementation)
4. [Architecture & Conventions](#4-architecture--conventions)
5. [Telemetry Analysis Pipeline (Qualifying)](#5-telemetry-analysis-pipeline-qualifying)
6. [Track Intelligence](#6-track-intelligence)
7. [Issues & Lessons Learned](#7-issues--lessons-learned)
8. [Verification Commands](#8-verification-commands)

---

## 1. Project Overview

ApexView is a Formula 1 telemetry analytics platform transforming raw FastF1 session data into interactive analytical insights across qualifying, race, and practice sessions.

**Tech stack:**
- **Frontend:** Next.js 14 (TypeScript), React 18, Plotly.js, Tailwind CSS
- **Backend:** FastAPI (Python), FastF1, NumPy/SciPy
- **Shared types:** `packages/models/` TypeScript interfaces
- **Infrastructure:** Docker (3-service stack), pnpm monorepo

**Monorepo structure:**
```
apps/
├── api/app/
│   ├── services/telemetry/     # FastF1 client, Parquet caching
│   ├── services/race/          # Race data pipeline
│   ├── services/practice/      # Practice data pipeline
│   ├── routes/                 # API routers (laps, race, practice)
│   ├── models/dto.py           # Pydantic DTOs (CamelCaseModel base)
│   └── utils/transforms.py
├── api/tests/                  # pytest (313 tests)
├── analysis_service/                 # Analysis service (qualifying analysis, 271 tests)
├── web/
│   ├── app/qualifying/
│   ├── app/race/
│   ├── app/practice/
│   ├── app/track/
│   ├── app/transparency/       # Privacy, data sources, methodology
│   ├── components/
│   └── lib/                    # Hooks, API client, utilities
└── packages/models/src/
    ├── types.ts
    └── data/tracks/            # Track Intelligence (24 circuits)
```

**Key design principles:**
- Server-side computation — all statistical calculations in FastAPI, frontend renders only
- Official timing as ground truth — all calculations anchor to official F1 lap times
- Anti-hallucination — template-based text generation, no LLM speculation
- Graceful degradation — shows "unavailable" rather than wrong data
- Progressive rendering — SSR header, independent panel loading, deferred below-fold content

---

## 2. Implementation Status

### Qualifying Page — ✅ COMPLETE

Interactive qualifying analysis: Q1/Q2/Q3 tabs, lap time comparisons, gap analysis, sector breakdowns, and full Telemetry Analysis Pipeline (delta, corner, technique, insight generation). All 7 components include "How to read this chart" interpretability guides with methodology descriptions verified against production code.

**Race condition fix:** Added `!isTrackPlaceholder` guard to `usePerformanceInsightsQuery` — prevents stale corner data from a previous circuit feeding the analysis request when switching GPs via `keepPreviousData`.

| Metric | Before | After |
|--------|--------|-------|
| Lighthouse Score | 42 | 90+ |
| JavaScript Bundle | 1.3 MiB | 472 KiB |
| First Contentful Paint | ~2.0s | 0.2s |
| Total Blocking Time | ~800ms | 0ms |

Key optimisations: `PlotlyLazy` dynamic import (`next/dynamic`, `ssr: false`), `next/font/google`, barrel import elimination, `plotly.js-cartesian-dist-min` (~800 KiB vs ~3.5 MiB; supports scatter, bar, box, histogram, violin). These patterns became the foundation for all subsequent pages.

---

### Race Page — ✅ COMPLETE

**Data pipeline (`services/race/`):**
- **Lap classification:** 8 types (RACING, IN_LAP, OUT_LAP, SAFETY_CAR, VSC, RED_FLAG, FORMATION, ANOMALY) + `is_warm_up` flag (tyre_life ≤ 2)
- **Fuel correction:** Circuit-specific factors (0.028–0.036 s/kg) from Track Intelligence; normalises to empty tank
- **Outlier detection:** Two-tier OR logic — IQR upper fence OR 1.10× driver median, keyed by `(driver, compound)` tuple
- **Traffic derivation:** Gap-to-car-ahead via cumulative session time; laps with gap < 1.5s flagged `in_traffic`
- **Caching:** `get_processed_race_data()` in-memory dict keyed by `session_id + fuel_effect`
- **130 backend tests** across 6 files

**Panels:**
- **Race Pace Distribution:** Box plot (`RacePaceBoxPlot.tsx`), pre-computed statistics, team-coloured, fuel-corrected toggle. DNF shown in red.
- **Tyre Degradation:** Fuel-adjusted scatter + linear regression (`scipy.stats.linregress`, min 7 laps); first 2 laps of each stint excluded (warm-up). Driver/team mode via `AnalysisModeToggle`.
- **Pit Stop Analysis:** Three views (ByTeam, ByDriver, GapToFastest). Tiered consistency (IQR for ≥3 stops, abs diff for 2). Anomaly exclusion: `pit_lane_time > 35.0s` OR `> 2.0× team_median`. Template-based insight cards.
- **Team Performance Quadrant:** SpeedST vs mean speed decomposition, four-quadrant scatter (High Efficiency / High Downforce / Low Downforce / Low Efficiency), deterministic insight cards.

**Frontend infrastructure (established here, reused in Practice):**
- `useVisibility.ts`: IntersectionObserver (200px rootMargin) for deferred below-fold loading
- `ErrorBoundary.tsx`: sessionId-keyed reset (`key={context-${sessionId}}`)
- `plotlyTheme.ts`: `BASE_LAYOUT`, `BASE_AXIS`, `BASE_CONFIG`, `CHART_CONTAIN_STYLE` — consumed by 8+ components
- `staleTime: Infinity` + navigation prefetch on all race query hooks
- `content-defer` CSS class (`content-visibility: auto`, `contain-intrinsic-size: auto 400px`)
- `race-lookup.ts`: lightweight circuit lookup (circuitName + fuelEffectPerKg only) — saves 304 KiB vs full Track Intelligence import

**Post-build enhancements:**
- DNF status resolution: `_resolve_status()` normalises retirements, `_resolve_finishing_position()` returns position for finishers only
- Per-compound outlier detection: thresholds keyed by `(driver, compound)` to prevent wet-tyre laps inflating dry-tyre thresholds
- Null `tyre_life` guard in `tyre_degradation.py`

---

### Practice Page — ✅ COMPLETE

Three-phase build. See [Section 3](#3-practice-page--implementation) for full details.

### Track Intelligence — ✅ COMPLETE

All 24 GP circuits. See [Section 6](#6-track-intelligence).

### Telemetry Analysis Pipeline (Qualifying) — ✅ COMPLETE

7-phase pipeline, 271 analysis tests. See [Section 5](#5-telemetry-analysis-pipeline-qualifying).

---

## 3. Practice Page — Implementation

### Overview

The Practice page analyses FP1/FP2/FP3 sessions across three panels: long run race pace, short run qualifying simulation, and cross-session progression.

**Design principles:** Simpler than Race (~40-50% effort), maximise reuse, arithmetic-only statistics (no scipy regression), no template-based insights.

**Session handling:**
- Traditional weekend: FP1/FP2/FP3 tabs
- Sprint weekend: FP1 only
- Every session treated as independent driver lineup (rookie drivers display normally)

---

### Phase 1: Data Foundation & Long Run Pace — ✅ COMPLETE

#### Backend (`services/practice/`)

| File | Purpose |
|------|---------|
| `transforms.py` | `classify_practice_laps()`, `apply_practice_fuel_correction()`, `derive_practice_traffic()` |
| `practice_data_service.py` | Central pipeline: `get_processed_practice_data()`, `_filter_representative_long_runs()`, in-memory cache |
| `routes/practice.py` | 5 endpoints (sessions, long-runs, short-runs, sector-analysis, progression) |

**Practice vs Race transforms:**

| Aspect | Race | Practice |
|--------|------|----------|
| Lap classifications | 8 types | 5 types (no FORMATION/SC/VSC) |
| Fuel correction | Known ~110 kg, linear depletion | Optional toggle, within-stint heuristic (~1.6 kg/lap) |
| Outlier detection | IQR + 1.10× median, per (driver, compound) | Same, ≥ 4 laps |
| Run classification | N/A | `long_run` (≥ 4 valid laps) / `short_run` (< 4) |

**Data pipeline flow:**
1. Load laps via `get_practice_laps()` (Parquet-cached)
2. Classify laps → tag classification, `is_warm_up`, `is_valid`
3. Optional fuel correction (within-stint normalisation to end-of-stint baseline)
4. Traffic derivation with graceful fallback (50% availability threshold)
5. Group into stints by `(driver, stint_number)`, classify run type
6. Compute per-stint: box stats (min/Q1/median/Q3/max/mean/std_dev), degradation hint, clean-air %, lap points
7. `_filter_representative_long_runs()`: 8s median threshold, excludes installation/sensor laps
8. Cache and return

**Per-stint computations:**
- Box stats: 1.5×IQR Tukey whiskers, `ddof=1` std dev
- `display_stint_number`: sequential 1-based per driver, assigned chronologically before sorting by pace
- Degradation hint: `avg(last 2 laps) − avg(first 2 laps)`, requires ≥ 4 valid laps
- Gap to fastest: `stint.average_time − fastest_stint.average_time`

**Tests:** 40 transforms + 74 data service = 114 tests

#### Frontend

`LongRunPacePanel.tsx` — single Plotly violin per driver-stint:
- Violin fill: team colour at 30% opacity, team-coloured border; `box: { visible: false }`, `meanline: { visible: false }`
- Dots: compound-coloured (`marker.size: 6`), native Plotly `points: 'all'`
- React dual legend below chart: team (violin fill) + compound (dots); `showlegend: false` on all traces
- Percentile y-axis range: P2/P98 bounds `[p2 - 0.5, p98 + 1.5]`
- Hover tooltip: Avg, Median, SD, Gap, Push, Deg, Clean Air via `buildViolinHoverText()`
- X-axis: `"DRIVER Stint N"` labels with `tickvals`/`ticktext` for dot jitter
- Sorted by `averageTime` ascending; scrollable container with dynamic `minWidth`
- `CompoundTabs` filter (ALL / SOFT / MEDIUM / HARD)
- Filter status note when `stintsFilteredCount > 0`
- Stint summary cards (180px, team colour top border)

---

### Phase 2: Short Run, Sector Analysis & Track Map — ✅ COMPLETE

#### Backend

Both endpoints query the same cached `get_processed_practice_data()`.

**`GET /practice/short-runs`:**
- Uses official FIA timing (raw `LapTime`, never fuel-corrected) for ranking
- Two-tier session-best extraction: FastF1 `is_personal_best` flag → fallback computed minimum
- `session_best_from_short_run` boolean + `session_best_source` field (`fastf1_flag` / `computed_minimum`)
- Sorted by `best_lap_time` ascending; gap-to-P1 computed

**`GET /practice/sector-analysis`:**
- Per-driver best S1/S2/S3 across all laps (may come from different laps)
- Theoretical best: `best_S1 + best_S2 + best_S3` per driver; cross-driver session minimum
- Max SpeedST per driver; potential gain: `actual_session_best − theoretical_best`

**Tests:** 41 short run + 17 sector analysis = 58 tests

#### Frontend

**`ShortRunPanel.tsx`:** Horizontal bar chart, team-coloured bars + compound scatter markers. Tight x-axis starting `sessionBestLap - 0.6`. Verification indicators (✓ = session-best from short run; * = from long run). Dynamic height: `Math.min(480, Math.max(220, barCount * 38 + 80))`.

**`SectorAnalysisPanel.tsx`:** Three sections — sector times table (fastest sector per column in purple), theoretical best lap card, speed trap bar chart (tight x-axis, 5 km/h below slowest).

**`SectorMapPanel.tsx`:** Dual-layer SVG — thick grey base (6px) + thin coloured sector overlay (3px). S1 red `#EF4444`, S2 blue `#3B82F6`, S3 amber `#FBBF24`. SVG parsed via DOMParser from Gumroad format. Graceful degradation if SVG unavailable. 24 circuit SVGs in `public/tracks/*.svg`.

`lib/circuitMap.ts`: 24-entry `CIRCUIT_SVG_MAP` record (round → SVG filename).

---

### Phase 3: Session Progression & Performance Optimisation — ✅ COMPLETE

#### Backend

**`GET /practice/progression`** (weekend-level, not session-level):
- Loads all available sessions via `get_processed_practice_data(session_id, fuel_effect=0.0)` — always raw times
- Per-session `try/except` for partial result resilience
- Gap-to-session-best per driver per session; `max(0.0, gap)` guard for float imprecision
- Sprint weekend: returns `is_sprint_weekend` flag + FP1 data only
- Variable lineup: rookies in FP1 get FP1 entry only (no phantom points)
- Sorted by smallest gap across all sessions

**Tests:** 11 progression tests

#### Frontend

**`SessionProgressionPanel.tsx`:** Connected dot plot — line trace (team-coloured, 1.5px) + marker trace (compound-coloured dots, 10px, team-coloured border). Y-axis inverted via explicit reversed range `[maxGap + 0.3, -0.05]`. `DriverChipSelector` with `displayMode="inline"` (togglable chips). URL state: `spMode` + `spDrivers` query params (sp-prefixed to avoid collision). Sprint weekend renders `SprintProgressionList` (ranked list, FP1 best laps). `content-defer` outer + `card-panel` inner structural split (prevents paint containment clipping of dropdown).

**`DriverChipSelector.tsx` extension:** Added `displayMode?: 'dropdown' | 'inline'` prop.

**Performance optimisation (all pages):**
- `useVisibility` on all below-fold panels
- `content-defer` CSS on all panel containers
- `staleTime: Infinity` on all new query hooks
- `ErrorBoundary` wrapping with sessionId-keyed reset

---

## 4. Architecture & Conventions

### Backend

- **Services:** `apps/api/app/services/{feature}/` with `__init__.py`
- **Routes:** `apps/api/app/routes/{feature}.py`, one file per domain; registered via `app.include_router(router, prefix="/{feature}")`
- **DTOs:** Extend `CamelCaseModel` in `models/dto.py` — snake_case auto-serialises to camelCase JSON
- **Cache:** In-memory dict per service, keyed by `session_id + parameters`
- **Data service factory:** `get_data_service()` returns `FastF1Client` or `MockDataService` based on `LIVE_DATA` env var
- **Tests:** `test_{feature}_{area}.py`, self-contained with own `_make_lap()` helpers, `pytest.approx()`, `asyncio.run()` for async

### Frontend

- **Pages:** `app/{feature}/page.tsx` (Server Component) + `{Feature}Content.tsx` (Client) + `{Feature}PageSkeleton.tsx`
- **Components:** `components/{feature}/PascalCase.tsx`
- **Hooks:** `lib/hooks/use{Feature}{Entity}Query.ts`
- **Query keys:** `queryKeys.{feature}.{entity}()` factory in `queryKeys.ts`
- **Fetch functions:** `fetch{Entity}()` in `api.ts`
- **Charts:** `PlotlyLazy` + `plotlyTheme` (`BASE_LAYOUT`, `BASE_AXIS`, `BASE_CONFIG`, `CHART_CONTAIN_STYLE`) + `plotly.js-cartesian-dist-min`
- **State:** Props drilling from Content to panels (no Context providers)
- **Session IDs:** `${season}_${round}_${sessionType}` (e.g. `2025_1_FP2`, `2025_24_Race`)
- **Cache:** `staleTime: Infinity` for historical data, `keepPreviousData` for smooth GP switching
- **Weekend persistence:** `ANALYSIS_PAGES` set in `Navigation.tsx` controls which nav links forward `round`/`season` URL params. Includes all 5 pages: `/`, `/qualifying`, `/race`, `/practice`, `/track`. Home page feature cards also forward params via `buildCardHref()`.
- **"How to read this chart" guides:** Collapsible section at bottom of each panel. `showGuide` state, `&#9656;` chevron, `border-white/10 bg-white/[0.02]` container. Present on all analytical pages (Qualifying, Race, Practice). Qualifying guides include methodology verification against production code.

### Shared Infrastructure

| Component | File | Used By |
|-----------|------|---------|
| PlotlyLazy | `components/charts/PlotlyLazy.tsx` | All chart panels |
| plotlyTheme | `lib/plotlyTheme.ts` | All chart panels |
| ErrorBoundary | `components/race/ErrorBoundary.tsx` | Race, Practice |
| useVisibility | `lib/hooks/useVisibility.ts` | Race, Practice |
| compounds.ts | `lib/compounds.ts` | Race, Practice |
| race-lookup.ts | `data/tracks/race-lookup.ts` | Race, Practice (fuel values, 304 KiB saving vs full import) |
| CompoundTabs | `components/race/CompoundTabs.tsx` | Race, Practice |
| AnalysisModeToggle | `components/race/AnalysisModeToggle.tsx` | Race (Tyre Deg) |
| DriverChipSelector | `components/race/DriverChipSelector.tsx` | Race, Practice (`displayMode?: 'dropdown' \| 'inline'`) |
| circuitMap.ts | `lib/circuitMap.ts` | Practice (SectorMapPanel) |
| formatLapTime / formatDelta | `lib/formatters.ts` | All pages |
| getTeamColor / getDriverInfo | `lib/drivers.ts` | All pages |
| CamelCaseModel | `models/dto.py` | All backend DTOs |

### CSS Classes (`globals.css`)

`.card-panel`, `.card-panel-header`, `.skeleton`, `.session-tab`, `.session-tab-active`, `.content-defer`

### API Endpoints

**Qualifying** (`/laps`): qualifying lap and telemetry endpoints

**Race** (`/race`):
- `GET /race/pace` — box plot statistics per driver
- `GET /race/tyre-degradation` — fuel-corrected regression per compound
- `GET /race/pit-stops` — durations, consistency metrics, insights
- `GET /race/team-performance` — SpeedST, mean speed, quadrant classification

**Practice** (`/practice`):
- `GET /practice/sessions` — available FP sessions for a weekend
- `GET /practice/long-runs` — long run stint analysis
- `GET /practice/short-runs` — best lap per driver from short runs
- `GET /practice/sector-analysis` — sector times, speed traps, theoretical best
- `GET /practice/progression` — cross-session gap-to-best (weekend-level)

**Analysis Service** (`/analysis`, port 8501):
- `POST /analysis/performance-insights` — unified qualifying analysis (orchestrates all phases)
- `POST /analysis/scaled-delta` — delta computation with official timing scaling
- `POST /analysis/corner-analysis` — corner-by-corner time attribution
- `POST /analysis/technique-profile` — 5-dimension technique profiling
- `POST /analysis/generate-insight` — template-based insight generation

### Test Coverage

| Area | Files | Tests |
|------|-------|-------|
| Analysis Service (qualifying) | 8 | 271 |
| Race transforms | 1 | 38 |
| Race data service | 1 | 21 |
| Race integration | 1 | 2 |
| Pit stop analysis | 1 | 15 |
| Tyre degradation | 1 | 33 |
| Team performance | 1 | 21 |
| Practice transforms | 1 | 40 |
| Practice data service | 1 | 74 |
| Practice short runs | 1 | 41 |
| Practice sector analysis | 1 | 17 |
| Practice progression | 1 | 11 |
| **API Total** | **12** | **313** |

---

## 5. Telemetry Analysis Pipeline (Qualifying)

Replaces a failed cosine similarity approach (measured vector angles — 99.9% similar for all drivers — rather than magnitude differences creating 0.1–2.0s gaps). Answers WHERE, WHY, and WHAT.

### Pipeline

| Phase | Service | Purpose |
|-------|---------|---------|
| 1. Data Foundation | `fastf1_client.py` | `_filter_valid_laps()` removes deleted/pit/invalid laps |
| 2. Delta Analysis | `delta_analysis.py` | RelativeDistance alignment + official timing scaling → scale factors (1.0000x) |
| 3. Corner Analysis | `corner_analysis.py` | Physics-based V2 brake detection, per-corner braking/apex/exit attribution |
| 4. Technique Profiling | `technique_profiling.py` | 5-dimension profile with session-relative percentiles |
| 5. Insight Generation | `insight_generation.py` | Anti-hallucination template-based text |
| 6. API Orchestration | `performance_orchestrator.py` | Unified endpoint, graceful degradation |
| 7. Frontend | `app/qualifying/` | SSR → Suspense → parallel React Query hooks |

### Key Technical Details

**RelativeDistance (Phase 2):** `RelativeDistance = Distance / TotalLapDistance` normalises all drivers to 0–1. Official timing scaling: `scale = official_time / telemetry_span` guarantees `scaled_time[-1] == official_time`.

**Brake Detection V2 (Phase 3):** Two-stage detection. Stage 1 finds boolean brake candidate where `brake_normalized >= 0.5` (50%). Stage 2 refines backward using v² kinematics deceleration `(v2² - v1²) / (2 × Δd)`, locating where heavy deceleration first begins — where deceleration crosses the circuit-specific threshold (-4.0 to -6.5 m/s², configurable per circuit via `CornerAnalysisConfig`). Confidence = alignment distance between the two stages (High ≤20m, Medium ≤40m, Low >40m).

**Straight-Line Integration (5th Dimension):** Mathematical closure — Corners + Straights = Official within 5ms. Primary factor classified as `aero_efficiency`, `high_drag_setup`, `exit_traction`, `poor_traction`, or `balanced`.

**Component hierarchy:**
```
PerformanceInsightsPanel
├── DeltaPlot
├── LapBreakdownPanel      # Corners + Straights = Official
├── CornerBreakdownPanel
├── TechniqueProfileDisplay
└── InsightsPanel
```

---

## 6. Track Intelligence

All 24 circuits on the 2025 F1 calendar. Located in `packages/models/src/data/tracks/`.

**Data per circuit:** metadata, sector breakdowns, DRS zones, corner data (including validated corner names), elevation, Pirelli characteristics (traction/braking/lateral/track evolution/asphalt grip, 1–5), defining characteristics (~60–80 chars), strategic insights, weather profile, `fuelEffectPerKg`.

**Corner names:** All 24 circuits include validated corner names in their JSON data files (`apps/api/app/data/tracks/*.json`), mapped from an official reference. Five circuits required physical feature matching (corner type and distance) where turn numbering differs between sources.

**Fuel sensitivity tiers:**

| Tier | Range (s/kg) | Circuit Type | Examples |
|------|-------------|--------------|---------|
| Low | 0.028–0.029 | High-speed, flowing | Silverstone, Monza, Spa, Suzuka |
| Mid | 0.031–0.033 | Mixed speed | Most circuits (16 of 24) |
| High | 0.034–0.036 | Stop-go, traction-limited | Monaco, Singapore, Hungary, Bahrain, Montreal |

**Lightweight access:** `data/tracks/race-lookup.ts` exports only `circuitName` + `fuelEffectPerKg` per round (saves 304 KiB vs full module import). Used by Race and Practice pages.

---

## 7. Issues & Lessons Learned

| # | Issue | Severity | Root Cause | Resolution |
|---|-------|----------|------------|------------|
| 1 | All circuits showing identical data | Critical | `apps/api/.env` overrode root `.env`, forcing `LIVE_DATA=false` | Delete service-specific `.env`, use root only |
| 2 | Delta falling back to Tier 3 | High | `relative_distance` and `time` fields not passed to calculation function | Added fields to all 5 call sites (camelCase keys) |
| 3 | All corners "MEDIUM" confidence | Medium | Gradient checked at wrong index (FROM vs INTO brake point) | Check `zone_brake[i+1]` against `gradient[i]` |
| 4 | Floating-point test failures | Low | Direct equality on floats | Use `pytest.approx()` with `abs=1e-6` |
| 5 | Catastrophic corner analysis (Singapore) | High | Telemetry contradicts official timing on some circuits | Hide corner analysis when `abs(scale_factor) > 2.0` |
| 6 | Corner Analysis not updating on GP switch | High | Race condition: `keepPreviousData` on both `useTrackQuery` and `usePerformanceInsightsQuery` — stale corners fed to analysis request | Add `!isTrackPlaceholder` guard to performance query `enabled` condition |
| 7 | Weekend selector resetting on navigation | Medium | Home and Track Intelligence excluded from `ANALYSIS_PAGES` set — params stripped on navigation | Expand set to all 5 pages, forward params through Home feature cards and logo link |

**Key principle:** Display accurate results or no results — never misleading data.

---

## 8. Verification Commands

```bash
# All API tests
cd apps/api && python -m pytest tests/ -v

# Practice-specific tests
cd apps/api && python -m pytest tests/test_practice_transforms.py tests/test_practice_data_service.py tests/test_practice_short_runs.py tests/test_practice_sector_analysis.py tests/test_practice_session_progression.py -v

# Analysis service tests
docker exec f1-analysis pytest tests/ -v

# Practice endpoints
curl "http://localhost:8000/practice/sessions?year=2025&round_num=1" | python -m json.tool
curl "http://localhost:8000/practice/long-runs?session=2025_24_FP2" | python -m json.tool
curl "http://localhost:8000/practice/long-runs?session=2025_24_FP2&fuel_effect=0.032" | python -m json.tool
curl "http://localhost:8000/practice/short-runs?session=2025_24_FP2" | python -m json.tool
curl "http://localhost:8000/practice/sector-analysis?session=2025_24_FP2" | python -m json.tool
curl "http://localhost:8000/practice/progression?year=2025&round_num=24" | python -m json.tool

# Race endpoint
curl "http://localhost:8000/race/pace?session=2025_17_Race" | python -m json.tool

# Verify delta accuracy
curl -X POST http://localhost:8501/analysis/performance-insights \
  -H "Content-Type: application/json" \
  -d '{"year":2025,"event":"Monaco","session":"Q3","reference_driver":"VER","compare_drivers":["LEC"]}' \
  | jq '.insights[0].delta_analysis | {official_gap, scaling_factor, confidence}'

# Frontend build check
pnpm --filter web build
```

---

*Documentation Version 6.0 — March 2026*