# ApexView — Codebase Reference

**Document Version:** 4.2
**Last Updated:** March 2026
**Status:** Qualifying Complete, Race Complete, Practice Phase 1 Complete, Phases 2-3 Planned
**Test Baseline:** 234+ API tests, 167+ ML tests passing
**Lighthouse Performance:** 94-97 (Qualifying), high 90s (Race)

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Current Implementation Status](#2-current-implementation-status)
3. [Practice Page — Implementation Plan](#3-practice-page--implementation-plan)
4. [Architecture & Conventions](#4-architecture--conventions)
5. [Refined AI Architecture (Qualifying)](#5-refined-ai-architecture-qualifying)
6. [Track Intelligence](#6-track-intelligence)
7. [Issues & Lessons Learned](#7-issues--lessons-learned)
8. [Verification Commands](#8-verification-commands)

---

## 1. Project Overview

ApexView is a Formula 1 telemetry analytics platform that transforms raw FastF1 race session data into interactive analytical insights. It covers qualifying single-lap performance, full race distance analysis, and practice session pace evaluation.

**Tech stack:**
- **Frontend:** Next.js 14 (TypeScript), React 18, Plotly.js visualisations, Tailwind CSS
- **Backend:** FastAPI (Python), FastF1 library for F1 data access, NumPy/SciPy for computation
- **Shared types:** `packages/models/` TypeScript interfaces consumed by frontend
- **Infrastructure:** Docker containerisation (3-service stack), pnpm monorepo with workspaces

**Monorepo structure:**

```
apps/
├── api/app/                    # FastAPI backend
│   ├── services/telemetry/     # FastF1 client, Parquet caching
│   ├── services/race/          # Race data pipeline
│   ├── services/practice/      # Practice data pipeline
│   ├── routes/                 # API routers (laps, race, practice)
│   ├── models/dto.py           # Pydantic DTOs (CamelCaseModel base)
│   └── utils/transforms.py    # Shared utilities
├── api/tests/                  # pytest test suite (206+ tests)
├── ml_service/                 # ML service (qualifying analysis)
│   ├── services/               # Delta, corner, technique, insights, orchestrator
│   └── tests/                  # 167+ tests
├── web/                        # Next.js frontend
│   ├── app/qualifying/         # Qualifying page
│   ├── app/race/               # Race page
│   ├── app/practice/           # Practice page
│   ├── components/             # Reusable components
│   └── lib/                    # Hooks, API client, utilities
└── packages/models/src/
    ├── types.ts                # Shared TypeScript types
    └── data/tracks/            # Track Intelligence (24 circuits)
```

**Key design principles:**
- Server-side computation — all statistical calculations in FastAPI, frontend renders only
- Official timing as ground truth — all calculations anchor to official F1 lap times
- Anti-hallucination — template-based text generation, no LLM speculation
- Graceful degradation — system functions when data quality is poor, shows "unavailable" rather than wrong data
- Progressive rendering — SSR header, independent panel loading, deferred below-fold content

---

## 2. Current Implementation Status

### Qualifying Page — ✅ COMPLETE

Interactive qualifying session analysis with Q1/Q2/Q3 session tabs, lap time comparisons, gap analysis, sector-level breakdowns, and the full Refined AI Architecture pipeline (delta analysis, corner analysis, technique profiling, insight generation).

**Performance optimised:** Lighthouse score improved from 42 to 94-97.

| Metric | Before | After |
|--------|--------|-------|
| Lighthouse Score | 42 | 94-97 |
| JavaScript Bundle | 1.3 MiB | 472 KiB |
| First Contentful Paint | ~2.0s | 0.2s |
| Total Blocking Time | ~800ms | 0ms |

Key optimisations: PlotlyLazy dynamic import (`next/dynamic`, `ssr: false`), self-hosted fonts via `next/font/google`, barrel import elimination, `plotly.js-cartesian-dist-min` (~800 KiB vs ~3.5 MiB full; supports scatter, bar, box, histogram, violin). These patterns became the foundation for Race and Practice pages.

---

### Race Page — ✅ COMPLETE (Six-Phase Build)

#### Phase 1: Race Data Foundation

Shared backend data pipeline in `services/race/`.

- **Lap classification:** 8 types (RACING, IN_LAP, OUT_LAP, SAFETY_CAR, VSC, RED_FLAG, FORMATION, ANOMALY) with `is_warm_up` flagging (tyre_life ≤ 2)
- **Fuel correction:** Circuit-specific factors (0.028–0.036 s/kg, 0.032 default) from Track Intelligence. Normalises to empty tank: `corrected = raw - (fuel_remaining × factor)`
- **Outlier detection:** Two-tier with OR logic — IQR upper fence (`> Q3 + 1.5 × IQR`) OR percentage cap (`> 1.10 × driver_median`)
- **Traffic derivation:** Gap-to-car-ahead via cumulative session time. Laps with gap < 1.5s flagged as `in_traffic`
- **Stint detection:** From FastF1 Stint column
- **Pit stop extraction:** PitInTime/PitOutTime delta
- **Caching:** `get_processed_race_data()` with in-memory dict keyed by `session_id + fuel_effect`
- **Tests:** 130 backend tests across 6 test files

#### Phase 2: Race Pace Distribution

- Box plot visualisation (`RacePaceBoxPlot.tsx`) with pre-computed statistics (min, Q1, median, mean, Q3, max, outliers)
- Team-coloured styling, custom tooltips with consistency score and traffic count, fuel-corrected toggle
- Collapsible "How to read this chart" guide
- Established all frontend patterns: `useRacePaceQuery`, PlotlyLazy, skeleton states, ErrorBoundary wrapping, progressive rendering (SSR + Suspense)

#### Phase 3: Tyre Degradation Analysis

- Fuel-adjusted scatter plots with server-side linear regression (`scipy.stats.linregress`, minimum 7 usable laps)
- Wear rate bar charts, `CompoundTabs`, `DriverChipSelector` multi-select
- `AnalysisModeToggle` for driver/team mode switching — team mode pools both drivers' laps before regression
- First 2 laps of each stint excluded from regression (warm-up period)
- Collapsible "How to read this chart" guide

#### Phase 4: Pit Stop Analysis

- Three views via `PitStopViewTabs`: ByTeam, ByDriver, GapToFastest
- **Tiered consistency:** IQR for ≥ 3 stops, abs diff for 2, null for 1
- **Anomaly exclusion:** `pit_lane_time > 35.0s` OR `> 2.0× team_median` — excluded from averages, flagged via `PitStopAnomalyNote.tsx`
- Template-based insight cards (`PitStopInsights.tsx`) — "Quickest on Average" and "Most Consistent" with deterministic fill
- Collapsible "How to read this chart" guide

#### Phase 5: Team Performance Quadrant

- Aerodynamic setup philosophy: SpeedST vs mean speed decomposition
- `TopSpeedDivergence.tsx`, `MeanSpeedDivergence.tsx`, `TeamQuadrantScatter.tsx`
- Four quadrants: High Efficiency (top-right), High Downforce (bottom-right), Low Downforce (top-left), Low Efficiency (bottom-left) — crosshairs via `layout.shapes`
- `TeamPerfInsights.tsx` with deterministic factual insight cards
- SpeedST extraction added to `fastf1_client.py`
- Collapsible "How to read this chart" guide

#### Phase 6: Performance Optimisation & Integration

- `useVisibility.ts`: IntersectionObserver (200px rootMargin, once-visible-stays-visible) for deferred loading of below-fold panels
- `ErrorBoundary.tsx`: class component with `getDerivedStateFromError`, sessionId-keyed reset (`key={context-${sessionId}}`)
- Shared `plotlyTheme.ts` (BASE_LAYOUT, BASE_AXIS, BASE_CONFIG, CHART_CONTAIN_STYLE) consumed by 8+ chart components
- `staleTime: Infinity` on all 4 race query hooks + navigation prefetch
- `content-defer` CSS class (`content-visibility: auto`, `contain-intrinsic-size: auto 400px`)
- Lighthouse: high 90s–100 range, TBT ~60ms

#### Post-Phase 6: Track Intelligence Import Optimisation

- Created `race-lookup.ts` (circuitName + fuelEffectPerKg only) — eliminated 304 KiB eager import of full Track Intelligence module
- Consumed by both Race and Practice pages

---

### Practice Page — 🔄 IN PROGRESS

**Phase 1: Data Foundation & Long Run Pace Comparison — ✅ COMPLETE**

Full backend data pipeline and Long Run Pace panel implemented. See [Section 3](#3-practice-page--implementation-plan) for details.

**Phase 2: Short Run / Best Lap Comparison — 📋 PLANNED**

**Phase 3: Session Progression & Performance Optimisation — 📋 PLANNED**

---

### Track Intelligence — ✅ COMPLETE

All 24 GP circuits implemented with comprehensive data: Pirelli characteristics, sector breakdowns, DRS zones, corner data, elevation, strategic insights, weather profiles, `fuelEffectPerKg` values (0.028–0.036 s/kg range), and condensed `definingCharacteristics` (~60-80 chars). See [Section 6](#6-track-intelligence).

---

### Refined AI Architecture (Qualifying) — ✅ COMPLETE

7-phase pipeline: Data Foundation → Delta Analysis → Corner Analysis → Technique Profiling → Insight Generation → API Orchestration → Frontend. 167+ ML service tests. See [Section 5](#5-refined-ai-architecture-qualifying).

---

## 3. Practice Page — Implementation Plan

### Overview

The Practice page transforms raw FastF1 practice session data (FP1, FP2, FP3) into three interactive analytical panels covering long run race pace, short run qualifying simulation pace, and cross-session performance progression.

**Design principles:**
- Simpler and faster than Race page (~40-50% effort)
- Maximise reuse of existing backend pipeline and frontend patterns
- Statistical complexity limited to arithmetic only (no scipy regression)
- No template-based insights

**Session format handling:**
- Traditional weekend: FP1/FP2/FP3 tabs (FP1 + FP2 Friday, FP3 Saturday)
- Sprint weekend: FP1 only (no tab selector)
- No sprint-specific analysis (sprint qualifying, sprint race excluded)

**Driver lineup handling (defensive design):**
- Every session treated as independent driver lineup
- 2025 rules: teams must run rookie drivers (no more than 2 GP starts) in 2 FP1 sessions per car (4 per team per season)
- Driver list extracted from session data, never inherited across sessions
- Reserve/rookie drivers display normally with team colours

---

### Phase 1: Practice Data Foundation & Long Run Pace Comparison — ✅ COMPLETE

**Purpose:** Establish the complete backend data pipeline for practice sessions and deliver the centrepiece Long Run Pace panel. This is the foundation — Phases 2 and 3 consume the same cached pipeline.

#### Backend — Files Created/Modified

| Action | File | Purpose |
|--------|------|---------|
| Create | `services/practice/__init__.py` | Package init |
| Create | `services/practice/transforms.py` | `classify_practice_laps()`, `apply_practice_fuel_correction()`, `derive_practice_traffic()` |
| Create | `services/practice/practice_data_service.py` | Central processing pipeline with `get_processed_practice_data()`, `_practice_data_cache`, `_filter_representative_long_runs()` |
| Create | `routes/practice.py` | 2 endpoints: `GET /practice/sessions`, `GET /practice/long-runs` |
| Modify | `services/telemetry/fastf1_client.py` | Added `get_practice_laps()` method |
| Modify | `services/mock_data.py` | Added practice mock data (4 drivers × 30 laps, 3 stints) |
| Modify | `models/dto.py` | Added `PracticeLongRunResponse` (incl. `total_long_runs_detected`, `stints_filtered_count`), `PracticeLongRunStint` (incl. `display_stint_number`), `PracticeStintStats`, `PracticeLapPoint`, `PracticeSessionsResponse` |
| Modify | `main.py` | Registered practice router with `prefix="/practice"` |
| Create | `tests/test_practice_transforms.py` | 40 tests: classification, outlier detection, warm-up, fuel correction, traffic |
| Create | `tests/test_practice_data_service.py` | 64 tests: stint grouping, box stats, std_dev, lap points, degradation hint, clean-air, analysis times, DTO builder, display_stint_number, filter representative long runs |

#### Practice Transforms vs Race Transforms

| Aspect | Race | Practice |
|--------|------|----------|
| Lap classifications | 8 types (RACING, IN_LAP, OUT_LAP, SAFETY_CAR, VSC, RED_FLAG, FORMATION, ANOMALY) | 5 types (RACING, IN_LAP, OUT_LAP, RED_FLAG, ANOMALY) — no FORMATION/SC/VSC |
| Fuel correction | Known total fuel (~110 kg), linear depletion model | Optional toggle (default OFF), within-stint heuristic (~1.6 kg/lap burn rate estimate) |
| Outlier detection | IQR + 1.10× median, per driver | Same (IQR + 1.10× median, per driver/compound, ≥ 4 laps) |
| Traffic derivation | Gap < 1.5s via cumulative_time | Same, with 50% data-availability threshold (practice often lacks position/cumulative_time) |
| Run type classification | N/A | `long_run` (≥ 4 valid laps) / `short_run` (< 4) |

#### Data Pipeline Flow

1. Load laps via `get_practice_laps()` (FastF1 client, Parquet-cached)
2. `classify_practice_laps()` → tag each lap with classification, is_warm_up, is_valid
3. `apply_practice_fuel_correction()` → optional, within-stint normalisation to end-of-stint baseline
4. `derive_practice_traffic()` → gap-to-car-ahead with graceful fallback
5. Group into stints by (driver, stint_number)
6. Classify run type: `long_run` (≥ 4 valid laps) / `short_run` (< 4)
7. Compute per-stint: box stats (incl. std_dev), degradation hint, clean-air %, individual lap points
8. `_filter_representative_long_runs()` → median-based outlier filter (8s threshold), excludes installation/sensor laps
9. Cache and return

**Per-stint computations for long runs:**
- Box plot stats: lowerfence, q1, median, q3, upperfence, mean, std_dev (1.5×IQR whiskers, Tukey standard; sample std dev with ddof=1)
- Individual lap points: per-lap `{ lap_number, lap_time, compound, tyre_life, in_traffic }` for violin overlay and compound-coloured dots
- `display_stint_number`: sequential 1-based per driver, assigned chronologically (by raw `stint_number`) before sorting by average_time
- Degradation hint: `avg(last 2 valid laps) − avg(first 2 valid laps)` — requires ≥ 4 valid laps, `None` otherwise. Positive = degrading.
- Clean-air percentage: fraction of valid laps with `in_traffic == False` (0.0–1.0)
- Gap to fastest: `stint.average_time − fastest_stint.average_time`

#### Frontend — Files Created/Modified

| Action | File | Purpose |
|--------|------|---------|
| Replace | `app/practice/page.tsx` | SSR Server Component (header + Suspense) |
| Create | `app/practice/PracticeContent.tsx` | Client orchestrator: URL state, session tabs, fuel toggle |
| Create | `app/practice/PracticePageSkeleton.tsx` | Loading skeleton matching layout |
| Create | `components/practice/PracticeSessionTabs.tsx` | FP1/FP2/FP3 tabs (`.session-tab` CSS classes), single label for sprint |
| Create | `components/practice/LongRunPacePanel.tsx` | Single violin per driver-stint, team-coloured fills, compound-coloured dots, React team+compound legend, chart title, below-violin annotations, scrollable container, percentile y-range, filter status note, sorted by average pace |
| Modify | `packages/models/src/types.ts` | Added `PracticeLongRunResponse` (incl. `totalLongRunsDetected`, `stintsFilteredCount`), `PracticeLongRunStint` (incl. `displayStintNumber`), `PracticeStintStats`, `PracticeLapPoint`, `PracticeSessionsResponse` |
| Modify | `lib/api.ts` | Added `fetchPracticeSessions()`, `fetchLongRuns()` |
| Modify | `lib/hooks/queryKeys.ts` | Added `practice.sessions()`, `practice.longRuns()` key factories |
| Create | `lib/hooks/useLongRunQuery.ts` | React Query hook, `staleTime: Infinity`, `keepPreviousData` |
| Create | `lib/hooks/usePracticeSessionsQuery.ts` | Sessions query hook |

**LongRunPacePanel features (team-coloured violin redesign, consistent with Race page):**
- Single Plotly violin trace per driver-stint with `points: 'all'`, `jitter: 0.12`, `pointpos: 0`, `bandwidth: 0.15`, `scalegroup: 'stints'` — native dot rendering
- Violin fill: team-coloured at ~30% opacity (`teamColor + '4D'`), team-coloured border (`line.width: 1.5`) — matches Race box plot pattern
- `box: { visible: false }`, `meanline: { visible: false }` — clean violin shape without inner box plot
- Dots: compound-coloured (`marker.color: compoundColor`), `marker.size: 6`, rendered inside violin by Plotly's native `points: 'all'`
- Chart title: "Long Run Pace — {Circuit} ({Session}) {Year}" via `formatChartTitle()` using `getRaceCircuitName()`
- React-based dual legend below chart: team legend (violin fill, `deduplicateTeams()`) + compound legend (dots) — `showlegend: false` on all Plotly traces
- Normal y-axis orientation (faster times at bottom, no `autorange: 'reversed'`)
- Percentile-based y-axis range: P2/P98 bounds (`[p2 - 0.5, p98 + 1.5]`) for tight y-axis without wasted space
- Hover tooltip on violin body: Avg, Median, SD, Gap, Push, Deg, Clean Air via `buildViolinHoverText()` — no static annotations (data-first visual)
- `display_stint_number`: sequential 1-based per driver (chronological), computed before pace sorting
- X-axis labels: "DRIVER Stint N" format using `displayStintNumber`
- Numeric x-axis with `tickvals`/`ticktext` for proper dot jitter
- Sorted by `averageTime` ascending (fastest left)
- Scrollable container: `overflow-x-auto` with dynamic `minWidth` for sessions with many stints
- `CompoundTabs` filter (ALL / SOFT / MEDIUM / HARD) — reused from Race page
- Filter status note: "Showing N of M long run stints (K non-representative excluded)" when `stintsFilteredCount > 0`
- Stint summary cards (180px, team colour top border) with driver + S{displayStintNumber}, Avg, Gap, Push, SD, Deg, Air metrics
- Fuel correction label: "(approximate fuel correction applied)" or "(raw lap times)"
- Layout: `height: 550`, `margin: { l: 60, r: 20, t: 60, b: 80 }`, `violingap: 0.3`, `width: 0.5`
- Collapsible "How to read this chart" guide (4 sections: What this chart shows, Reading the violins, Stint summary cards, Fuel correction)
- States: skeleton, error, empty ("No long runs with 4+ push laps found"), content with `isPlaceholderData` opacity transition

**Session state flow:**
- `PracticeContent` manages `practiceSession` state (default "FP2" for traditional weekends)
- Session ID derived as `${season}_${round}_${activeSession}` (e.g. `2025_1_FP2`)
- Fuel correction value from `race-lookup.ts`, passed as query param when toggle is ON
- Props drilled to panels (no Context providers, matching Race page pattern)

**Tests:** 104 tests (40 transforms + 64 data service), all passing. Full suite: 234 tests, 0 regressions.

---

### Phase 2: Short Run / Best Lap Comparison — 📋 PLANNED

**Purpose:** Extract and display each driver's fastest lap from short run stints, providing a quick-reference qualifying simulation pace comparison.

**Backend:**
- Queries the same cached `get_processed_practice_data()` from Phase 1
- Filters for `short_run` stints (< 4 valid laps)
- Extracts best lap per driver, computes gaps to P1
- New endpoint: `GET /practice/short-runs`
- New DTO: `PracticeShortRunResponse`

**Frontend:**
- Ranked horizontal bar chart: fastest lap per driver with compound indicator
- Team-coloured bars, gap to P1 annotated
- Contextual note about unknown fuel loads / engine modes
- `useShortRunQuery` hook, `queryKeys.practice.shortRuns()`
- Reuses PlotlyLazy, plotlyTheme, ErrorBoundary, useVisibility

---

### Phase 3: Session Progression & Performance Optimisation — 📋 PLANNED

**Purpose:** Show how each driver's pace improved (or didn't) across FP1 → FP2 → FP3, plus Lighthouse optimisation of the complete page.

**Backend:**
- Cross-session comparison: best lap per driver per session
- Computes gap-to-session-best (NOT raw times — neutralises track evolution)
- Handles variable lineups (rookies in FP1 only get FP1 data point)
- New endpoint: `GET /practice/progression`
- New DTO: `PracticeProgressionResponse`

**Frontend:**
- Connected dot plot: gap-to-session-best across FP1/FP2/FP3
- Team-coloured markers and lines, partial data for substituted drivers
- Sprint weekend: single column of dots (FP1 only)
- `useSessionProgressionQuery` hook, `queryKeys.practice.progression()`

**Performance optimisation:**
- Lighthouse audit of complete Practice page
- Apply useVisibility, content-defer, and existing patterns as needed
- Expect lighter pass than Race Phase 6 (fewer panels, infrastructure already exists)

---

## 4. Architecture & Conventions

### Backend Conventions

- **Services:** `apps/api/app/services/{feature}/` with `__init__.py`
- **Routes:** `apps/api/app/routes/{feature}.py`, single file per domain
- **Router registration:** `app.include_router(router, prefix="/{feature}", tags=["{feature}"])`
- **DTOs:** Extend `CamelCaseModel` in `models/dto.py` — snake_case Python fields auto-serialise to camelCase JSON
- **Response models:** Typed directly, no wrapper envelope
- **Cache:** In-memory dict per service, keyed by `session_id + parameters`
- **Data service factory:** `get_data_service()` returns `FastF1Client` or `MockDataService` based on `LIVE_DATA` env var
- **Tests:** `apps/api/tests/test_{feature}_{area}.py`, self-contained with own `_make_lap()` helpers, pytest with `pytest.approx()`, `asyncio.run()` for async

### Frontend Conventions

- **Pages:** `app/{feature}/page.tsx` (Server Component) + `{Feature}Content.tsx` (Client Component) + `{Feature}PageSkeleton.tsx`
- **Components:** `components/{feature}/` with PascalCase `.tsx` files
- **Hooks:** `lib/hooks/use{Feature}{Entity}Query.ts`
- **Query keys:** `queryKeys.{feature}.{entity}()` factory in `queryKeys.ts`
- **Fetch functions:** `fetch{Entity}()` in `api.ts`
- **Styling:** 100% Tailwind utility classes; reusable classes in `globals.css`
- **Charts:** PlotlyLazy + plotlyTheme (`BASE_LAYOUT`, `BASE_AXIS`, `BASE_CONFIG`, `CHART_CONTAIN_STYLE`) + `plotly.js-cartesian-dist-min` (supports scatter, bar, box, histogram, violin — ~800 KiB)
- **State:** Props drilling from Content to panels (no Context providers)
- **Session IDs:** `${season}_${round}_${sessionType}` (e.g. `2025_24_Race`, `2025_1_FP2`)
- **Cache:** `staleTime: Infinity` for all historical data, `keepPreviousData` for smooth GP switching
- **Performance:** `useVisibility` for below-fold deferred loading, `ErrorBoundary` with sessionId-keyed reset, `content-defer` CSS class
- **"How to read this chart" guides:** Collapsible section at bottom of each analytical panel. `showGuide` state, `&#9656;` chevron rotation, `border-white/10 bg-white/[0.02]` container. Key terms in `text-gray-400 font-medium`, body in `text-sm text-gray-500`.

### Shared Infrastructure

| Component | File | Used By |
|-----------|------|---------|
| PlotlyLazy | `components/charts/PlotlyLazy.tsx` | All chart panels |
| plotlyTheme | `lib/plotlyTheme.ts` | All chart panels |
| ErrorBoundary | `components/race/ErrorBoundary.tsx` | Race, Practice |
| useVisibility | `lib/hooks/useVisibility.ts` | Race, Practice |
| compounds.ts | `lib/compounds.ts` | Race, Practice (colour mapping) |
| race-lookup.ts | `data/tracks/race-lookup.ts` | Race, Practice (lightweight fuel values) |
| CompoundTabs | `components/race/CompoundTabs.tsx` | Race, Practice |
| AnalysisModeToggle | `components/race/AnalysisModeToggle.tsx` | Race (Tyre Deg) |
| DriverChipSelector | `components/race/DriverChipSelector.tsx` | Race (Tyre Deg) |
| formatLapTime / formatDelta | `lib/formatters.ts` | All pages |
| getTeamColor / getDriverInfo | `lib/drivers.ts` | All pages |
| CamelCaseModel | `models/dto.py` | All backend DTOs |
| data_service factory | `services/data_service.py` | All backend routes |

### CSS Classes (globals.css)

`.card-panel`, `.card-panel-header`, `.skeleton`, `.session-tab`, `.session-tab-active`, `.content-defer`

### API Endpoints

**Qualifying (prefix: /laps):**
- Qualifying lap and telemetry endpoints (existing)

**Race (prefix: /race):**
- `GET /race/pace` — Box plot statistics per driver
- `GET /race/tyre-degradation` — Fuel-corrected regression per compound
- `GET /race/pit-stops` — Pit stop durations with consistency metrics + insights
- `GET /race/team-performance` — SpeedST, mean speed, quadrant classification

**Practice (prefix: /practice):**
- `GET /practice/sessions` — Available FP sessions for a weekend ✅
- `GET /practice/long-runs` — Long run stint analysis ✅
- `GET /practice/short-runs` — Best lap per driver from short runs (Phase 2, planned)
- `GET /practice/progression` — Cross-session gap-to-best comparison (Phase 3, planned)

### Test Coverage

| Area | Test Files | Tests | Status |
|------|-----------|-------|--------|
| ML Service (qualifying) | 7 files | 167+ | ✅ |
| Race transforms | `test_race_transforms.py` | 37 | ✅ |
| Race data service | `test_race_data_service.py` | 22 | ✅ |
| Race integration | `test_race_integration.py` | 2 | ✅ |
| Pit stop analysis | `test_pit_stop_analysis.py` | 15 | ✅ |
| Tyre degradation | `test_tyre_degradation.py` | 25 | ✅ |
| Team performance | `test_team_performance.py` | 20 | ✅ |
| Practice transforms | `test_practice_transforms.py` | 40 | ✅ |
| Practice data service | `test_practice_data_service.py` | 64 | ✅ |
| **API Total** | **9 files** | **234+** | ✅ |

All tests: pytest, self-contained, no shared conftest.

---

## 5. Refined AI Architecture (Qualifying)

The qualifying page is powered by a 7-phase pipeline that replaced a failed cosine similarity approach. Cosine similarity measured vector *angles* (99.9% similar for all drivers) rather than the magnitude differences that create 0.1–2.0s lap time gaps. The Refined AI Architecture answers WHERE, WHY, and WHAT.

### Pipeline

| Phase | Service | Purpose |
|-------|---------|---------|
| 1. Data Foundation | `fastf1_client.py` | `_filter_valid_laps()` removes deleted/pit/invalid laps |
| 2. Delta Analysis | `delta_analysis.py` | RelativeDistance alignment (0–1 normalised) + official timing scaling → perfect scale factors (1.0000x) |
| 3. Corner Analysis | `corner_analysis.py` | Physics-based V2 brake detection (gradient ≥ 5%/10m), per-corner braking/apex/exit attribution |
| 4. Technique Profiling | `technique_profiling.py` | 5-dimension profile (Braking, Apex, Exit, Consistency, Straight-Line) with session-relative percentiles |
| 5. Insight Generation | `insight_generation.py` | Anti-hallucination template-based text with data placeholders |
| 6. API Orchestration | `performance_orchestrator.py` | Unified endpoint with graceful degradation (partial results if corner analysis fails) |
| 7. Frontend | `app/qualifying/` | Server Component → Suspense → Client Component with parallel React Query hooks |

### Key Technical Details

**RelativeDistance (Phase 2):** `RelativeDistance = Distance / TotalLapDistance` normalises all drivers to 0–1 range. Position 0.25 for VER = position 0.25 for LEC = same track position. Official timing scaling: `scale = official_time / telemetry_span` guarantees `scaled_time[-1] == official_time`.

**Brake Detection V2 (Phase 3):** Gradient-based: `gradient = (brake_diff / distance_diff) × 10`. Brake point = first index where `brake[i+1] ≥ 20%` AND `gradient[i] ≥ 5%/10m` (sharp increase INTO that point, not from it — fixed off-by-one bug).

**Straight-Line Integration (5th Dimension):** Achieves mathematical closure: Corners (+0.876s) + Straights (−0.767s) = Official (+0.109s) within 5ms tolerance. Primary factor classified as aero_efficiency, high_drag_setup, exit_traction, poor_traction, or balanced.

**Component hierarchy:**
```
PerformanceInsightsPanel
├── DeltaPlot                  # Delta-to-reference line chart
├── LapBreakdownPanel          # Corners + Straights = Official
├── CornerBreakdownPanel       # Per-corner table
├── TechniqueProfileDisplay    # 5-dimension bars
└── InsightsPanel              # Natural language text
```

---

## 6. Track Intelligence

All 24 circuits on the 2025 F1 calendar have comprehensive Track Intelligence data, verified against official F1 and Pirelli sources. Located in `packages/models/src/data/tracks/`.

**Data per circuit:**
- Circuit metadata (name, country, length, lap count, first GP year)
- Sector breakdowns with distances and characteristics
- DRS zones with activation and detection points
- Corner data (number, name, type, speed, gear, apex distance)
- Elevation data (min, max, total ascent/descent)
- Pirelli circuit characteristics (traction, braking, lateral, track evolution, asphalt grip — each 1–5)
- Defining characteristics (condensed to ~60-80 characters for layout compatibility)
- Strategic insights (typical strategy, pit windows, safety car likelihood)
- Weather profile (typical conditions, temperature ranges)
- `fuelEffectPerKg` — circuit-specific fuel correction factor (0.028–0.036 s/kg)

**Fuel sensitivity tiers:**

| Tier | Range (s/kg) | Circuit Type | Examples |
|------|-------------|--------------|---------|
| Low | 0.028–0.029 | High-speed, flowing | Silverstone, Monza, Spa, Suzuka |
| Mid | 0.031–0.033 | Mixed speed profiles | Most circuits (16 of 24) |
| High | 0.034–0.036 | Stop-go, traction-limited | Monaco, Singapore, Hungary, Bahrain, Montreal |

**Lightweight access:** `data/tracks/race-lookup.ts` exports only `circuitName` + `fuelEffectPerKg` per round — avoids importing the full Track Intelligence module (304 KiB saving).

---

## 7. Issues & Lessons Learned

| # | Issue | Severity | Root Cause | Resolution |
|---|-------|----------|------------|------------|
| 1 | `.env` override — all circuits showing identical data | Critical | `apps/api/.env` overrode root `.env`, forcing `LIVE_DATA=false` | Delete service-specific `.env`, use root `.env` only |
| 2 | ML service integration gap — delta falling back to Tier 3 | High | `relative_distance` and `time` fields not passed to calculation function | Added fields to all 5 call sites (camelCase keys) |
| 3 | Off-by-one in brake detection — all corners "MEDIUM" confidence | Medium | Gradient checked at wrong index (FROM vs INTO point) | Check `zone_brake[i+1]` against `gradient[i]` |
| 4 | Floating-point test failures | Low | Direct equality on floats | Use `pytest.approx()` with `abs=1e-6` |
| 5 | Telemetry-timing mismatch (Singapore) — catastrophic corner analysis | High | Telemetry contradicts official timing on some circuits | Sanity checks: hide corner analysis when `abs(scale_factor) > 2.0` |

**Key principle:** The system should display either **accurate results** or **no results** — never misleading data. Graceful degradation with clear user messaging is preferable to showing impossible values.

---

## 8. Verification Commands

```bash
# Run all API tests (race + practice + pit stops + tyre deg + team perf)
cd apps/api && python -m pytest tests/ -v

# Run practice-specific tests
cd apps/api && python -m pytest tests/test_practice_transforms.py tests/test_practice_data_service.py -v

# Run ML service tests
docker exec f1-ml pytest tests/ -v

# Test practice endpoints
curl "http://localhost:8000/practice/sessions?year=2025&round_num=1" | python -m json.tool
curl "http://localhost:8000/practice/long-runs?session=2025_24_FP2" | python -m json.tool
curl "http://localhost:8000/practice/long-runs?session=2025_24_FP2&fuel_effect=0.032" | python -m json.tool

# Test race endpoints
curl "http://localhost:8000/race/pace?session=2025_17_Race" | python -m json.tool

# Verify delta accuracy
curl -X POST http://localhost:8501/ml/performance-insights \
  -H "Content-Type: application/json" \
  -d '{"year":2025,"event":"Monaco","session":"Q3","reference_driver":"VER","compare_drivers":["LEC"]}' \
  | jq '.insights[0].delta_analysis | {official_gap, scaling_factor, confidence}'

# Frontend build check
pnpm --filter web build
```

---

## Reuse Matrix (Practice Page)

Quick reference for what exists vs what needs building for remaining Practice phases.

| Component | Status | Source |
|-----------|--------|--------|
| Lap classification (5 practice types) | ✅ Built | `services/practice/transforms.py` |
| Outlier detection (IQR + 1.10×) | ✅ Built | `services/practice/transforms.py` |
| Traffic derivation (gap < 1.5s) | ✅ Built | `services/practice/transforms.py` |
| Fuel correction (within-stint, optional) | ✅ Built | `services/practice/transforms.py` |
| Practice data pipeline + caching | ✅ Built | `services/practice/practice_data_service.py` |
| Long/short run classification | ✅ Built | `practice_data_service.py` (4-lap threshold, aligned with external sources) |
| Representative stint filter | ✅ Built | `_filter_representative_long_runs()` (8s median threshold, excludes installation/sensor laps) |
| Degradation hint (start vs end) | ✅ Built | `practice_data_service.py` |
| Clean-air percentage per stint | ✅ Built | `practice_data_service.py` |
| `get_practice_laps()` in FastF1 client | ✅ Built | `fastf1_client.py` |
| Practice API routes | ✅ Built (2 of 4) | `routes/practice.py` |
| Long Run Pace panel (violin + scatter) | ✅ Built | `components/practice/LongRunPacePanel.tsx` |
| FP1/FP2/FP3 session selector | ✅ Built | `components/practice/PracticeSessionTabs.tsx` |
| Practice query hooks | ✅ Built (2 of 4) | `lib/hooks/useLongRunQuery.ts`, `usePracticeSessionsQuery.ts` |
| PlotlyLazy, plotlyTheme | Reuse | `components/charts/`, `lib/plotlyTheme.ts` |
| ErrorBoundary with sessionId key | Reuse | `components/race/ErrorBoundary.tsx` |
| useVisibility (IntersectionObserver) | Reuse | `lib/hooks/useVisibility.ts` |
| CompoundTabs | Reuse | `components/race/CompoundTabs.tsx` |
| compounds.ts colour mapping | Reuse | `lib/compounds.ts` |
| race-lookup.ts fuel values | Reuse | `data/tracks/race-lookup.ts` |
| React Query + staleTime: Infinity | Reuse | All existing hooks |
| .session-tab CSS classes | Reuse | `globals.css` |
| Short run best-lap extraction | **Phase 2** | New endpoint + DTO + hook + panel |
| Gap-to-session-best computation | **Phase 3** | New cross-session endpoint + DTO + hook + panel |

---

*Documentation Version 4.1 — March 2026*
