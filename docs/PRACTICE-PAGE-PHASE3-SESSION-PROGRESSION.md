# Practice Page Phase 3: Session Progression & Performance Optimisation

**Status:** Complete
**Implemented:** March 2026
**Test Baseline:** 52 new tests passing (41 sector analysis + 11 progression), full suite 313+ with 0 regressions
**TypeScript:** Zero compilation errors
**Docker Integration:** All 5 practice endpoints verified live; 7 cross-validation checks passed; cross-endpoint consistency confirmed (progression vs short-runs FP2 times match)
**Frontend Verification:** Component structure validated via accessibility snapshot; `content-defer` applied correctly to 4 below-fold panels; API URL construction verified via network logs

---

## Table of Contents

1. [Purpose and Significance](#1-purpose-and-significance)
2. [Theoretical and Logical Background](#2-theoretical-and-logical-background)
3. [End-to-End Workflow and Data Flow](#3-end-to-end-workflow-and-data-flow)
4. [Technical Implementation Breakdown](#4-technical-implementation-breakdown)
5. [Driver/Team Selector: Interactive Filtering](#5-driverteam-selector-interactive-filtering)
6. [Performance Optimisation Pass](#6-performance-optimisation-pass)
7. [Testing, Verification, and Validation](#7-testing-verification-and-validation)
8. [Key Decisions and Learnings](#8-key-decisions-and-learnings)
9. [Alignment with Broader Practice Page Plan](#9-alignment-with-broader-practice-page-plan)

---

## 1. Purpose and Significance

### What Phase 3 Delivers

Phase 3 completes the Practice page with a cross-session analytical panel and a performance optimisation pass:

1. **Session Progression Panel** — A connected dot plot showing how each driver's relative pace evolved across FP1, FP2, and FP3. Uses gap-to-session-best (not raw lap times) to neutralise track evolution between sessions. Includes a driver/team selector for focused comparisons and a sprint weekend fallback for single-session weekends.

2. **Performance Optimisation Pass** — Application of the same performance infrastructure proven on the Race page: `useVisibility` (IntersectionObserver-based deferred loading), `content-defer` CSS class (paint containment for below-fold panels), `ErrorBoundary` wrapping with sessionId-keyed reset, and `staleTime: Infinity` on all query hooks.

3. **Driver/Team Inline Selector** — An enhancement to the shared `DriverChipSelector` component adding an `inline` display mode where all identifiers appear as toggleable chips. This resolved a paint containment clipping issue and provided a smoother selection experience for the 10-20 item F1 driver/team list.

Together with Phases 1 and 2, the Practice page now provides a complete analytical surface: race simulation pace (Long Run, Phase 1), qualifying simulation pace (Short Run, Phase 2), sector-level breakdown and circuit context (Sector Analysis + Circuit Map, Phase 2), and cross-session performance evolution (Session Progression, Phase 3).

### Why It Matters

The session progression question is one of the most important in a practice weekend: **did a team improve or fall behind across the sessions?** A driver who was P12 in FP1 but P3 in FP3 is trending in the right direction. A driver who topped FP1 but slipped to P8 by FP3 may have encountered setup issues, or other teams may have found more pace.

Raw lap times cannot answer this question because track conditions evolve significantly across a weekend. A Friday afternoon FP2 time of 1:23.4 might be slower than a Saturday FP3 time of 1:22.8, but this difference reflects track rubber-in, not driver improvement. The gap-to-session-best metric neutralises this by measuring each driver's position relative to the fastest driver in that specific session, creating a comparable "how far from the best" value across all sessions.

Sprint weekends — which have only FP1 before sprint qualifying — cannot show session progression (no second data point to connect). Phase 3 handles this gracefully by detecting single-session weekends and rendering a ranked list instead of the connected dot plot.

### Position in the Practice Page Architecture

| Phase | Name | Status | Depends On |
|-------|------|--------|-----------|
| 1 | Data Foundation & Long Run Pace | ✅ Complete | — |
| 2 | Short Run / Best Lap + Sector Analysis + Circuit Map | ✅ Complete | Phase 1 pipeline |
| **3** | **Session Progression & Performance Optimisation** | **✅ Complete** | Phase 1 pipeline |

---

## 2. Theoretical and Logical Background

### 2.1 Gap-to-Session-Best: Neutralising Track Evolution

The central challenge of cross-session comparison is track evolution. Between FP1 (Friday morning, green track, 25°C) and FP3 (Saturday morning, rubbered-in surface, 20°C), raw lap times can drop by 1-3 seconds without any team making setup changes. Comparing raw times across sessions would create a misleading picture where every driver appears to "improve" simply because the track got faster.

Gap-to-session-best solves this by computing each driver's deficit to the fastest driver in that specific session:

```
gap_FP1 = driver_time_FP1 − fastest_time_FP1
gap_FP2 = driver_time_FP2 − fastest_time_FP2
gap_FP3 = driver_time_FP3 − fastest_time_FP3
```

If VER's gap decreases from +0.456s (FP1) to +0.189s (FP3), VER improved relative to the field regardless of whether FP3 was 2 seconds faster in absolute terms. If LEC's gap increases from +0.123s to +0.678s, LEC lost relative competitiveness.

This is the same methodology used by professional F1 analysts and commentary teams. It has a well-understood limitation: it is sensitive to who sets the session-best time. If one driver does a glory run on ultra-soft tyres in FP3 with minimal fuel, all other drivers' gaps will appear larger. The "How to read this chart" guide documents this caveat.

### 2.2 Session-Best Anchoring via Official Timing

Phase 3 reuses the two-tier session-best extraction strategy established in Phase 2:

**Primary path — FastF1's `is_personal_best` flag:** The FIA timing system marks each driver's fastest valid lap. When any driver in the session has this flag, it is used for all drivers.

**Fallback path — computed minimum from RACING laps:** When no flags are present (common with mock data), the system computes the minimum lap time from all RACING-classified laps per driver.

The session-level consistency check ensures all drivers within a single session use the same extraction method. The `source` field (`'fastf1_flag'` or `'computed_minimum'`) propagates through to the frontend for transparency.

Critically, progression always uses raw lap times (`fuel_effect=0.0`). Fuel correction is irrelevant for cross-session gap comparison because the correction would shift all drivers' times within a session by similar amounts, leaving the relative gaps nearly unchanged while adding unnecessary complexity and potential for artefacts.

### 2.3 Variable Driver Lineups

2025 F1 regulations require each team to run a rookie driver (no more than 2 GP starts) in at least 2 FP1 sessions per car across the season. This means the driver lineup in FP1 may differ from FP2 and FP3.

The progression system handles this through independent session loading — each session's driver list is extracted from its own data, never inherited from another session. A rookie who appears in FP1 only will have a single dot on the progression chart (their FP1 gap), with no connecting line. Regular drivers who appear in all three sessions get the full connected dot plot.

This defensive design extends beyond rookies: any driver absence (mechanical failure, team decision, weather cancellation) is handled identically — the driver simply has fewer data points.

### 2.4 Sprint Weekend Detection

Sprint weekends condense the practice schedule to a single FP1 session before sprint qualifying. With only one session, there is no "progression" to chart — a single data point has no trend.

Rather than showing a chart with isolated dots (technically possible but visually unhelpful), Phase 3 detects sprint weekends via `len(available_sessions) == 1` and renders a ranked list instead: each driver's gap-to-session-best from FP1, sorted fastest to slowest, with compound and tyre life annotations.

### 2.5 Paint Containment and Dropdown Clipping

During Phase 3 development, an important CSS interaction was discovered: the `content-defer` class (`content-visibility: auto`) creates a paint containment boundary (`contain: layout style paint`) that clips absolutely-positioned children — including dropdown menus — to the container's bounds. This affected the `DriverChipSelector` dropdown within the Session Progression panel.

The resolution involved two changes:

1. **Structural split:** Separating `content-defer` (outer wrapper) from `card-panel` (inner content div), matching the pattern already used by TyreDegradationPanel on the Race page. This ensures the containment boundary is on the outermost div while interactive content lives inside a non-contained div.

2. **Inline display mode:** Adding a `displayMode='inline'` option to `DriverChipSelector` that renders all identifiers as toggleable chips (selected = solid, unselected = outlined/dashed) instead of using an overlay dropdown. This eliminates the absolute positioning entirely, allowing the panel to auto-size based on the number of items. For F1's 10-20 driver/team count, inline chips are a better UX than a dropdown.

---

## 3. End-to-End Workflow and Data Flow

### 3.1 Request Flow

```
Browser                  Next.js Frontend              FastAPI Backend
  │                           │                              │
  │  Load Practice page       │                              │
  │ ─────────────────────>    │                              │
  │                           │                              │
  │  [PracticeContent.tsx]    │                              │
  │  Derives year + round     │                              │
  │  from URL params          │                              │
  │                           │                              │
  │  ┌─────────────────────────────────────────────────────┐ │
  │  │ Phases 1-2 queries: per-session (session-specific)  │ │
  │  │ ──> GET /practice/long-runs?session=2025_24_FP2     │──>│
  │  │ ──> GET /practice/short-runs?session=2025_24_FP2    │──>│
  │  │ ──> GET /practice/sector-analysis?session=...       │──>│
  │  │                                                     │ │
  │  │ Phase 3 query: per-weekend (year + round)           │ │
  │  │ ──> GET /practice/progression?year=2025&round_num=24│──>│
  │  └─────────────────────────────────────────────────────┘ │
  │                           │                              │
  │                           │     Backend (for progression):
  │                           │     ┌────────────────────────┐
  │                           │     │ 1. get_available_sessions()
  │                           │     │    → ['FP1','FP2','FP3']
  │                           │     │
  │                           │     │ 2. For each session:
  │                           │     │    get_processed_practice_data()
  │                           │     │    (reuses Phase 1 pipeline + cache)
  │                           │     │
  │                           │     │ 3. Extract session_best_laps
  │                           │     │    per session
  │                           │     │
  │                           │     │ 4. compute_progression_stats():
  │                           │     │    - Per session: find fastest time
  │                           │     │    - Per driver: gap = time − fastest
  │                           │     │    - Sort by best gap ascending
  │                           │     │
  │                           │     │ 5. Return PracticeProgressionResponse
  │                           │     └────────────────────────┘
  │                           │                              │
  │  <─────────────────────────────────────────────────────  │
  │  SessionProgressionPanel                                 │
  │  renders connected dot plot                              │
```

### 3.2 Key Architectural Distinction

The progression endpoint is the only practice endpoint that operates at the **weekend level** (year + round) rather than the **session level** (session ID). This is because it must load data from all available sessions to compute cross-session gaps.

All other practice endpoints (long-runs, short-runs, sector-analysis) operate on a single session and share the same cache key pattern: `f"{session_id}_{fuel_effect_per_kg}"`. The progression endpoint calls `get_processed_practice_data()` for each session independently (always with `fuel_effect=0.0`), benefiting from the Phase 1 cache if those sessions were already loaded by other panels.

### 3.3 Cache Interaction

```
User loads Practice page → PracticeContent sets session = "2025_24_FP2"

Panel 1 (Long Run):    GET /practice/long-runs?session=2025_24_FP2
                        → Cache MISS → full pipeline → cache["2025_24_FP2_0.0"]

Panel 2 (Short Run):   GET /practice/short-runs?session=2025_24_FP2
                        → Cache HIT on "2025_24_FP2_0.0" → reuse stints

Panel 5 (Progression): GET /practice/progression?year=2025&round_num=24
                        → Loads FP1: cache MISS → pipeline → cache["2025_24_FP1_0.0"]
                        → Loads FP2: cache HIT (already loaded above)
                        → Loads FP3: cache MISS → pipeline → cache["2025_24_FP3_0.0"]
```

This cache-sharing means the progression endpoint only triggers new data loads for sessions not already requested by the current page view. If the user has browsed all three session tabs, the progression query completes entirely from cache.

---

## 4. Technical Implementation Breakdown

### 4.1 Backend: `compute_progression_stats()`

**Location:** `apps/api/app/services/practice/practice_data_service.py`

**Signature:**
```python
async def compute_progression_stats(year: int, round_num: int) -> dict
```

**Algorithm:**

1. **Determine available sessions** via `get_available_sessions(year, round_num)`. Returns `['FP1', 'FP2', 'FP3']` for traditional weekends or `['FP1']` for sprint weekends.

2. **Detect sprint weekend:** `is_sprint_weekend = len(available_sessions) == 1`

3. **Load session data:** For each session, call `get_processed_practice_data(session_id, fuel_effect=0.0)`. Uses `fuel_effect=0.0` always — raw times for comparable cross-session gaps. Only includes sessions where `session_best_laps` is non-empty.

4. **Compute per-session gaps:**
   - Find `session_best_time = min(all drivers' best_lap_times)` in that session
   - For each driver: `gap = max(0.0, driver_time − session_best_time)`
   - The `max(0.0, ...)` guard prevents negative gaps from floating-point imprecision

5. **Aggregate by driver:** Collect all session entries per driver, preserving compound, tyre_life, and source metadata.

6. **Sort sessions within each driver:** FP1 → FP2 → FP3 ordering, regardless of load order.

7. **Sort drivers:** By their best (minimum) gap_to_session_best across all sessions. The driver who was closest to session-best in at least one session appears first.

**Return structure:**
```python
{
    'year': 2025,
    'round_num': 24,
    'available_sessions': ['FP1', 'FP2', 'FP3'],
    'is_sprint_weekend': False,
    'drivers': [
        {
            'driver': 'VER', 'team': 'Red Bull Racing',
            'sessions': [
                {'session': 'FP1', 'best_lap_time': 83.456, 'compound': 'SOFT',
                 'tyre_life': 3, 'gap_to_session_best': 0.123, 'source': 'fastf1_flag'},
                {'session': 'FP2', ...},
                {'session': 'FP3', ...},
            ]
        },
        ...
    ],
    'total_drivers': 20,
}
```

**Edge case handling:**
- Session load failure: That session is skipped; other sessions still included (graceful partial results)
- All sessions fail: Returns empty `drivers` list; `is_sprint_weekend` still determined from session count
- Variable lineups: Driver appears only in sessions they participated in (1, 2, or 3 entries)

### 4.2 Backend: DTOs

**`PracticeProgressionEntry`** (one per session-appearance):
```python
class PracticeProgressionEntry(CamelCaseModel):
    session: str                 # 'FP1', 'FP2', or 'FP3'
    best_lap_time: float         # Raw lap time in seconds
    compound: str                # Tyre compound used on best lap
    tyre_life: int               # Tyre age on best lap
    gap_to_session_best: float   # Seconds behind session fastest (0.0 for P1)
    source: str                  # 'fastf1_flag' or 'computed_minimum'
```

**`PracticeProgressionDriver`** (one per driver):
```python
class PracticeProgressionDriver(CamelCaseModel):
    driver: str                  # 3-letter abbreviation
    team: str                    # Full team name
    sessions: List[PracticeProgressionEntry]  # 1-3 entries
```

**`PracticeProgressionResponse`** (response envelope):
```python
class PracticeProgressionResponse(CamelCaseModel):
    year: int
    round_num: int
    available_sessions: List[str]
    is_sprint_weekend: bool
    drivers: List[PracticeProgressionDriver]
    total_drivers: int
```

### 4.3 Backend: API Endpoint

**Route:** `GET /practice/progression`
**Query parameters:** `year` (int), `round_num` (int)
**Response:** `PracticeProgressionResponse`

Registered in `routes/practice.py` alongside the existing session, long-run, short-run, and sector-analysis endpoints. Uses the same `CamelCaseModel` base for automatic snake_case → camelCase serialisation.

### 4.4 Frontend: Query Hook

**`useSessionProgressionQuery.ts`:**
```typescript
export function useSessionProgressionQuery(
  year: number,
  round: number,
  enabled: boolean = true,
) {
  return useQuery({
    queryKey: queryKeys.practice.progression(year, round),
    queryFn: () => fetchProgression(year, round),
    enabled: !!year && !!round && enabled,
    staleTime: Infinity,
    gcTime: 30 * 60 * 1000,
    placeholderData: keepPreviousData,
  })
}
```

Key patterns:
- **`staleTime: Infinity`** — Historical practice data never changes; no background refetches
- **`enabled`** gated by `isVisible` from `useVisibility()` — defers query until panel scrolls into viewport
- **`keepPreviousData`** — Shows previous GP's chart while new data loads (no blank state)

**Query key:** `['practice', 'progression', { year, round }]` — keyed by weekend, not session

### 4.5 Frontend: SessionProgressionPanel

**Location:** `apps/web/components/practice/SessionProgressionPanel.tsx`

**Props:** `year: number`, `round: number`

**State management:**
- `showGuide` — Collapsible "How to read this chart" guide
- `mode` — `'driver'` or `'team'` (URL-persisted as `?spMode`)
- `selectedIdentifiers` — Driver/team chip selection (URL-persisted as `?spDrivers`)
- `userHasFiltered` — Tracks whether user has manually adjusted selection

**Plotly chart — connected dot plot:**

For each filtered driver, two traces are created:

**Trace 1: Connecting line** (team-coloured, 1.5px width)
```javascript
{
  type: 'scatter',
  mode: 'lines',
  x: ['FP1', 'FP2', 'FP3'],
  y: [0.456, 0.234, 0.189],
  line: { color: teamColor, width: 1.5 },
  showlegend: false,
  hoverinfo: 'none'
}
```
Only rendered when the driver has 2+ sessions (a single point has no line to draw).

**Trace 2: Compound-coloured markers** (size 10, team-coloured border)
```javascript
{
  type: 'scatter',
  mode: 'markers',
  x: ['FP1', 'FP2', 'FP3'],
  y: [0.456, 0.234, 0.189],
  marker: {
    color: [softColor, mediumColor, softColor],  // Compound per session
    size: 10,
    line: { color: teamColor, width: 2 },
  },
  hovertext: ['VER — FP1\nLap: 1:23.456\nGap: +0.456s\nCompound: SOFT\nTyre life: 3 laps', ...],
  showlegend: true
}
```

**Layout:**
- X-axis: categorical, ordered `['FP1', 'FP2', 'FP3']`
- Y-axis: inverted range `[maxGap + padding, -0.05]` — best (0.000s) at top
- Legend: horizontal below chart, driver abbreviations
- Height: 420px fixed
- Margin: `{ t: 20, b: 80, l: 70, r: 20 }`

**Five return paths:**
1. **Loading skeleton** — Animated placeholder (title + description + 380px bar)
2. **Error state** — Title + "Session progression data unavailable"
3. **Sprint weekend** — Title + explanation + `SprintProgressionList` ranked display
4. **Empty state** — Title + "No progression data available"
5. **Main chart** — Full interactive chart with selector and guide

**Sprint weekend fallback (`SprintProgressionList`):**
Renders a ranked vertical list when only FP1 is available:
```
#1  ● VER  1:23.456  Session Best  ●
#2  ● LEC  1:23.678  +0.222s       ●
#3  ● SAI  1:23.890  +0.434s       ●
```
Left dot = team colour, right dot = compound colour.

---

## 5. Driver/Team Selector: Interactive Filtering

### 5.1 Problem

With 20 drivers on the chart, the connected dot plot becomes visually cluttered. Users who want to compare specific rivals (e.g., the two McLaren drivers vs the two Ferrari drivers) need a way to filter the chart.

### 5.2 Architecture Decision: Reuse, Don't Duplicate

Both `AnalysisModeToggle` and `DriverChipSelector` are generic components in `components/race/` with no Race-specific logic. They were imported directly — no copies, no new components.

**Key difference from TyreDegradationPanel (Race page):** In TyreDegradation, mode change triggers a backend refetch because team mode pools both drivers' laps for regression analysis. In Session Progression, mode change is purely client-side — the API always returns per-driver data, and team mode simply filters by team membership.

### 5.3 URL State Persistence

Following the TyreDegradation pattern with `sp` prefix (session-progression):

| URL Parameter | Default | Purpose |
|---------------|---------|---------|
| `?spMode` | `'driver'` | Analysis mode (driver or team) |
| `?spDrivers` | (all selected) | Comma-separated identifiers when manually filtered |

The `spDrivers` parameter is only present when the user has made a manual selection that differs from "all". This keeps URLs clean by default while preserving user intent across page refreshes and navigation.

### 5.4 Auto-Select and Validation

The `useEffect` on `allIdentifiers` handles three scenarios:

1. **Fresh load (no user filter):** Auto-select all identifiers
2. **GP change (user had filtered):** Prune invalid identifiers (drivers who don't exist in the new GP); if all are invalid, fall back to all
3. **Mode change (driver → team):** `handleModeChange` clears selection and resets `userHasFiltered`; the effect then auto-selects all identifiers in the new mode

### 5.5 Inline Display Mode

The `DriverChipSelector` was enhanced with a `displayMode` prop:

- **`'dropdown'`** (default, Race page): Selected chips shown with `+ Add` button that opens an absolutely-positioned dropdown overlay
- **`'inline'`** (Session Progression): All identifiers shown as toggleable chips — selected are solid with team colour accent, unselected are outlined/dashed. Click to toggle.

The inline mode eliminates all z-index and overflow concerns because everything renders in normal document flow. The panel grows or shrinks naturally as chips are toggled. For F1's 10 teams or ~20 drivers, inline chips provide a better visual overview than a dropdown that hides available options.

---

## 6. Performance Optimisation Pass

### 6.1 Infrastructure Applied

Phase 3 applied the same performance patterns established on the Race page (Race Phase 6):

| Pattern | Implementation | Effect |
|---------|---------------|--------|
| **useVisibility** | `IntersectionObserver` (200px rootMargin) on below-fold panels | Defers data fetching until panel approaches viewport |
| **content-defer** | `content-visibility: auto; contain-intrinsic-size: auto 400px` | Browser skips painting below-fold panels until needed |
| **ErrorBoundary** | `key={context-${sessionId}}` wrapping each panel | Isolates crashes; resets on GP/session change |
| **staleTime: Infinity** | All 6 practice query hooks | Historical data never refetches |
| **keepPreviousData** | All query hooks | Smooth transition when switching GP |
| **PlotlyLazy** | `next/dynamic` with `ssr: false` | Plotly loaded only on client side |
| **plotlyTheme** | `BASE_LAYOUT`, `BASE_AXIS`, `BASE_CONFIG` | Consistent dark theme across all charts |

### 6.2 content-defer Application

The `content-defer` CSS class was applied to 4 below-fold panels:

| Panel | Line | Status |
|-------|------|--------|
| ShortRunPanel | `className="card-panel space-y-3 content-defer"` | Applied |
| SectorAnalysisPanel | `className="card-panel space-y-4 content-defer"` | Applied |
| SectorMapPanel | `className="card-panel content-defer"` | Applied |
| SessionProgressionPanel | Outer `className="content-defer"`, inner `className="card-panel"` | Split structure |

SessionProgressionPanel uses a split structure (outer `content-defer`, inner `card-panel`) to prevent paint containment from clipping the inline chip selector. This matches the pattern used by TyreDegradationPanel on the Race page and is documented as a learning in Section 8.

### 6.3 Skeleton Consistency

The `PracticePageSkeleton` component was updated with placeholder cards for the Sector Analysis and Session Progression panels, ensuring layout stability (CLS prevention) while the client orchestrator streams in.

### 6.4 Expected Performance

The Practice page uses identical infrastructure to the Race page (Lighthouse high 90s-100 range). The lighter panel count (5 vs 4 on Race, but simpler individual panels) and existing optimisation patterns suggest comparable performance:

- **SSR header** for immediate LCP
- **Streaming via Suspense** with skeleton fallback
- **Deferred below-fold queries** via `useVisibility`
- **Paint containment** via `content-defer`
- **Zero-refetch caching** via `staleTime: Infinity`

---

## 7. Testing, Verification, and Validation

### 7.1 Backend Unit Tests

**Phase 3 added 52 new tests across 2 files:**

#### `test_practice_session_progression.py` — 11 tests

| Test | Scenario | Key Assertion |
|------|----------|--------------|
| Traditional weekend | 3 sessions, multiple drivers | Correct gaps per session; FP1/FP2/FP3 ordering |
| Sprint weekend | Single FP1 only | `is_sprint_weekend = True`; single session entry per driver |
| Zero gap for session best | Fastest driver in each session | `gap_to_session_best == 0.0` |
| Variable lineup (rookie sub) | Driver in FP1 only | 1 session entry; regular drivers have 2-3 entries |
| Empty sessions | No available sessions | Empty drivers list; no crash |
| Session load failure | FP2 fails to load | FP1 still included; graceful partial results |
| Compound/tyre_life propagation | Metadata flows through | Compound and tyre_life match session_best_laps values |
| Session ordering | Loaded out of order | Driver entries sorted FP1 → FP2 → FP3 |
| Driver sorting | Multiple drivers | Sorted by best gap across all sessions (ascending) |
| All sessions fail | Every load fails | Empty drivers; `is_sprint_weekend` still determined |
| Float guard | Floating-point edge | `gap_to_session_best >= 0.0` (no negative gaps) |

#### `test_practice_sector_analysis.py` — 41 tests

| Category | Count | Focus |
|----------|-------|-------|
| Basic sector extraction | 2 | Session-best lap sectors correctly extracted |
| Best lap vs best sectors | 3 | Best individual sectors may differ from session-best lap sectors |
| Null handling | 2 | Missing sector times don't crash |
| Summary stats | 2 | Fastest per-sector + driver identification |
| Theoretical best | 2 | Cross-driver sector combination; gain calculation |
| Speed traps | 3 | Max speed per metric per driver; null handling |
| Sorting & ranking | 2 | Drivers by lap time ascending; speed traps by speed descending |
| Data origin | 3 | Compound/team from session_best_laps; sectors from lap matching |
| Empty edge cases | 3 | Empty laps, empty session_best, both → empty structures |
| Additional coverage | 19 | Rounding, multi-driver interactions, partial data |

### 7.2 Full Test Suite Verification

```bash
cd apps/api && python -m pytest tests/ -v
```

**Result:** 313 tests passed, 0 failures, 0 regressions.

| Area | Test Files | Tests | Status |
|------|-----------|-------|--------|
| Analysis Service (qualifying) | 7 files | 167+ | ✅ |
| Race transforms | 1 file | 37 | ✅ |
| Race data service | 1 file | 22 | ✅ |
| Race integration | 1 file | 2 | ✅ |
| Pit stop analysis | 1 file | 15 | ✅ |
| Tyre degradation | 1 file | 25 | ✅ |
| Team performance | 1 file | 20 | ✅ |
| Practice transforms | 1 file | 40 | ✅ |
| Practice data service | 1 file | 64 | ✅ |
| Practice short runs | 1 file | 77 | ✅ |
| Practice sector analysis | 1 file | 41 | ✅ |
| Practice session progression | 1 file | 11 | ✅ |
| **Total** | **18 files** | **313+** | **✅** |

### 7.3 TypeScript Build Verification

```bash
pnpm --filter web build
```

**Result:** Compiled successfully. Linting and type checking passed. All 8 static pages generated. (EPERM symlink error is a pre-existing Windows/OneDrive issue with `output: 'standalone'`, not a build failure.)

### 7.4 Docker Integration Testing

Docker containers (API + ML) were built, started, and verified healthy. Live integration tests confirmed:

**Endpoint Verification (5 endpoints):**

| Endpoint | Result |
|----------|--------|
| `GET /practice/sessions?year=2025&round_num=24` | ✅ Returns `['FP1', 'FP2', 'FP3']` |
| `GET /practice/long-runs?session=2025_24_FP2` | ✅ Stints with stats, lap points, degradation |
| `GET /practice/short-runs?session=2025_24_FP2` | ✅ 20 drivers ranked, verification fields |
| `GET /practice/sector-analysis?session=2025_24_FP2` | ✅ Sectors, theoretical best, speed traps |
| `GET /practice/progression?year=2025&round_num=24` | ✅ 3 sessions, 20 drivers, gaps |

**Data Integrity Cross-Validation (7 checks):**

1. **Driver count consistency:** 20 drivers across all endpoints
2. **Gap non-negativity:** All `gapToSessionBest >= 0.0`
3. **Session-best driver has zero gap:** Confirmed per session
4. **Gap ordering matches position:** Lower gap = better position
5. **Available sessions match sessions endpoint:** `['FP1', 'FP2', 'FP3']` consistent
6. **Compound values valid:** All in `['SOFT', 'MEDIUM', 'HARD']`
7. **Cross-endpoint consistency:** FP2 best-lap times in progression match short-runs FP2 rankings

### 7.5 Frontend Structure Verification

Using the preview tool's accessibility snapshot, the following was verified:

- All 5 panels render in correct order: Long Run → Short Run → Circuit Map → Sector Analysis → Session Progression
- `content-defer` CSS applied correctly to 4 below-fold panels (confirmed via computed styles)
- API URLs constructed correctly for all endpoints
- ErrorBoundary wrapping confirmed around all panels

---

## 8. Key Decisions and Learnings

### 8.1 Weekend-Level vs Session-Level Endpoint

**Decision:** The progression endpoint takes `year + round_num` as parameters (weekend-level), not a session ID.

**Rationale:** Progression is inherently a cross-session concept. The endpoint needs to load all available sessions for the weekend, not just one. Making it session-level would have required either (a) the frontend to make 3 separate calls and combine them, or (b) the backend to infer the full weekend from a single session ID. Both are worse than a clean weekend-level API.

**Impact:** This is the only practice endpoint with this parameter pattern, which required a separate query key factory (`queryKeys.practice.progression(year, round)`) distinct from the session-keyed factories used by other panels.

### 8.2 Always Raw Times for Progression

**Decision:** The progression endpoint always uses `fuel_effect=0.0`, regardless of the user's fuel correction toggle.

**Rationale:** Fuel correction adjusts absolute lap times but has negligible effect on relative gaps (all drivers in a session receive similar corrections). Including fuel correction would add complexity without changing the analytical output, and worse, could introduce artefacts if the within-stint heuristic behaves differently across sessions.

### 8.3 content-defer Split Pattern

**Learning:** `content-visibility: auto` creates `contain: paint` which clips absolutely-positioned descendants. When `content-defer` and `card-panel` are on the same div, dropdown overlays inside the card are clipped to the container's bounds.

**Resolution:** Split into outer `content-defer` wrapper + inner `card-panel` div. This was already the pattern on TyreDegradationPanel (Race page) but hadn't been documented as a requirement. Additionally, the inline chip display mode was introduced to eliminate absolute positioning entirely.

**Documentation:** This learning has been captured here and will inform future panel development.

### 8.4 Inline Chip Selector for Small Lists

**Learning:** For selection lists with 10-20 items (F1 teams/drivers), inline toggleable chips provide a better UX than a dropdown. The dropdown hides available options, requires extra clicks to discover what's available, and is vulnerable to overflow clipping. Inline chips show everything at once, the panel sizes naturally, and toggle state is immediately visible.

**Implementation:** Added `displayMode?: 'dropdown' | 'inline'` to `DriverChipSelector`. Default remains `'dropdown'` for backward compatibility with the Race page. Session Progression uses `'inline'`.

### 8.5 Auto-Select Pattern Stability

**Learning:** The `userHasFiltered` flag pattern (established in TyreDegradation, replicated here) reliably distinguishes between "auto-populate all" and "user made a deliberate choice." Without this flag, the `useEffect` on `allIdentifiers` would reset the user's selection every time data changes, overriding their manual filter.

The key invariant: `userHasFiltered` is set to `true` only by `handleSelectionChange` (user action) and reset to `false` only by `handleModeChange` (mode switch clears selection) or by the validation effect (when all persisted identifiers are invalid for the new data).

### 8.6 Sprint Weekend Fallback

**Decision:** Show a ranked list for sprint weekends rather than a single-column dot chart.

**Rationale:** A connected dot plot with one column of dots and no connecting lines has poor information density — it's essentially a bar chart without bars. The ranked list conveys the same gap information more compactly and intuitively.

### 8.7 Test Independence

**Learning:** All 5 practice test files are fully self-contained with their own `_make_lap()` helpers, fixtures, and mock data generators. No shared conftest. This was a deliberate choice from Phase 1 that proved valuable: each test file can be run independently, and changes to one file's test helpers never cascade into others. The tradeoff (some helper duplication across files) is acceptable for a test suite of this size.

---

## 9. Alignment with Broader Practice Page Plan

### 9.1 Practice Page — Complete

With Phase 3, all planned Practice page panels are implemented:

| Phase | Panel | Status | Key Metric |
|-------|-------|--------|-----------|
| 1 | Long Run Pace (Violin Plot) | ✅ Complete | Average stint pace, degradation, clean air % |
| 2 | Short Run / Best Lap (Bar Chart) | ✅ Complete | Session-best lap, gap to P1, compound |
| 2b | Circuit Map (SVG Overlay) | ✅ Complete | Sector spatial context, fastest per sector |
| 2c | Sector Analysis (Table + Speed Trap) | ✅ Complete | Sector times, theoretical best, speed trap ranking |
| 3 | Session Progression (Connected Dots) | ✅ Complete | Gap-to-session-best evolution across FP1/FP2/FP3 |

### 9.2 Backend Pipeline — Shared Foundation

All 5 panels consume the same `get_processed_practice_data()` pipeline from Phase 1. The cache ensures each session's data is loaded and processed at most once per (session_id, fuel_effect) combination. Phase 3's progression endpoint extends this by loading multiple sessions, but each individual session load follows the same pipeline.

### 9.3 Frontend Patterns — Consistent Across Platform

The Practice page uses identical patterns to the Qualifying and Race pages:

| Pattern | Qualifying | Race | Practice |
|---------|-----------|------|----------|
| SSR + Suspense + Skeleton | ✅ | ✅ | ✅ |
| PlotlyLazy + plotlyTheme | ✅ | ✅ | ✅ |
| React Query + staleTime: Infinity | ✅ | ✅ | ✅ |
| ErrorBoundary (sessionId-keyed) | — | ✅ | ✅ |
| useVisibility (deferred loading) | — | ✅ | ✅ |
| content-defer (paint containment) | — | ✅ | ✅ |
| CompoundTabs | — | ✅ | ✅ |
| DriverChipSelector + Mode Toggle | — | ✅ | ✅ |
| URL state persistence | ✅ | ✅ | ✅ |
| "How to read" collapsible guides | — | ✅ | ✅ |

### 9.4 Test Coverage — Comprehensive

The complete test suite now spans 313+ API tests across 18 files and 167+ ML tests. The Practice page alone contributes 233 tests across 5 files, covering transforms, data service pipeline, short runs, sector analysis, and session progression.

---

*Documentation Version 1.0 — March 2026*
