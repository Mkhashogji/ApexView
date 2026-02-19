# Race Page Phase 5: Team Performance Quadrant

**Status:** Complete
**Implemented:** February 2026
**TypeScript:** Zero compilation errors
**Next.js Build:** Compiled successfully (8/8 static pages generated)
**Qualifying Regression:** Zero modified qualifying files
**Docker Validation:** All 3 containers running; endpoint verified with live Abu Dhabi 2025, Baku 2025, and Monaco 2025 data
**Test Coverage:** 21 unit tests (all passing), full backend suite passing
**Document Version:** 1.0

---

## Table of Contents

1. [Purpose and Significance](#1-purpose-and-significance)
2. [Theoretical and Logical Background](#2-theoretical-and-logical-background)
3. [End-to-End Workflow and Data Flow](#3-end-to-end-workflow-and-data-flow)
4. [Technical Implementation Breakdown](#4-technical-implementation-breakdown)
5. [Critical Path Corrections](#5-critical-path-corrections)
6. [Docker Integration Validation](#6-docker-integration-validation)
7. [Learnings and How They Influenced Decisions](#7-learnings-and-how-they-influenced-decisions)
8. [Alignment with Broader Race Page Plan](#8-alignment-with-broader-race-page-plan)

---

## 1. Purpose and Significance

### What Phase 5 Delivers

Phase 5 implements the **Team Performance Quadrant** panel — the car-characterisation dimension of the Race page. Unlike Phases 2-4, which measure individual driver pace, tyre management, and pit crew execution, Phase 5 answers a fundamentally different question: **"What aerodynamic setup philosophy did each team use, and where are the car's strengths and weaknesses?"**

The panel provides three chart views (Top Speed Divergence, Mean Speed Divergence, Quadrant Scatter), two template-based insight cards (Fastest on Straights, Highest Mean Speed), and an expandable explanation guide. All three views are derived from a single API response — switching views is instant with no network request.

### Why It Matters

**Phase 5 introduces team-level aggregation — a new granularity.** All prior Race page features operate at the driver level (per-driver pace, per-driver degradation, per-driver pit times). Phase 5 aggregates upward to the team level, averaging both drivers' metrics to reveal the car's characteristics rather than the driver's. This requires a multi-stage aggregation pipeline: per-lap values → per-driver means → per-team means → field averages → deltas.

**It encodes the fundamental aerodynamic trade-off in F1.** The quadrant chart plots two axes that represent the core tension in car design: downforce increases cornering speed (raising mean speed) but increases drag (reducing top speed). Teams that solve this trade-off appear in the top-right "High Efficiency" quadrant; teams that accept it appear in opposite corners. This single visualisation communicates each team's design philosophy more directly than any pace metric.

**It validates the single-API-response, client-side-switch pattern at scale.** Phase 4 (Pit Stop Analysis) established this pattern with three bar chart views. Phase 5 extends it to three fundamentally different chart types — two horizontal divergence bars and a scatter plot with crosshair overlays — all from the same endpoint. This confirms the pattern's generality beyond bar chart variants.

**It completes the analytical story of the Race page.** With Phase 5, the Race page answers four distinct questions: Who was fastest (Phase 2), how did tyres degrade (Phase 3), how did the crew perform (Phase 4), and why was the car fast or slow (Phase 5). These four dimensions cover pace, strategy, operations, and engineering — the full spectrum of race performance analysis.

### Position in the Race Page Architecture

| Phase | Name | Depends On | Status |
|-------|------|-----------|--------|
| 1 | Race Data Foundation | — | Complete |
| 2 | Race Pace Distribution (Box Plot) | Phase 1 | Complete |
| 3 | Tyre Degradation Analysis | Phase 1 | Complete |
| 4 | Pit Stop Analysis | Phase 1 | Complete |
| **5** | **Team Performance Quadrant** | **Phase 1** | **Complete** |
| 6 | Performance Optimization & Integration | Phases 1-5 | Planned |

Phase 5 consumes the Phase 1 enriched dataset through the shared `get_processed_race_data()` service, specifically the `laps` array containing all classified, fuel-corrected race laps. It additionally requires circuit length in metres, resolved server-side from Track Intelligence via `get_track_info()`. It introduces a new aggregation service (`team_performance.py`), a new API endpoint (`GET /race/team-performance`), and eight new frontend components, all following the patterns established by Phases 2-4.

---

## 2. Theoretical and Logical Background

### 2.1 Decomposing Race Pace into Two Speed Dimensions

A car's race lap time is the product of two fundamentally different performance characteristics:

**Top Speed (Straight-Line Performance):**
The maximum speed reached on straights, measured by F1's speed trap — a fixed sensor point on the main straight. Top speed is determined primarily by aerodynamic drag, power unit output, and energy deployment strategy. It is NOT significantly affected by fuel weight because straight-line speed is drag-limited, not mass-limited. At 300+ km/h, the car reaches terminal velocity where engine power equals aerodynamic drag force. Extra fuel mass adds minimal drag.

**Mean Speed (Overall Lap Performance):**
The average speed over a complete lap, computed as `circuit_length / lap_time * 3.6` (converting m/s to km/h). Mean speed captures everything — straights, corners, braking zones, acceleration phases. It IS affected by fuel weight because heavier cars corner slower (less grip relative to mass) and accelerate slower. Therefore, mean speed uses the fuel-corrected lap time to isolate car performance from fuel load variation.

This asymmetric treatment — raw values for top speed, fuel-corrected values for mean speed — reflects the underlying physics. It emerged as a key design decision during planning and is one of the most technically significant aspects of Phase 5.

### 2.2 The Four Quadrants

When both dimensions are plotted on a scatter chart with field averages as crosshair reference lines, four quadrants emerge:

| Quadrant | Position | Meaning | Typical Cause |
|----------|----------|---------|---------------|
| **High Efficiency** | Top-right | Fast everywhere | Strong power unit + efficient aerodynamics |
| **High Downforce** | Bottom-right | Fast in corners, slow on straights | High downforce setup that sacrifices drag |
| **Low Downforce** | Top-left | Fast on straights, slow in corners | Low drag setup that sacrifices cornering grip |
| **Low Efficiency** | Bottom-left | Slow everywhere | Below-average in both dimensions |

The quadrant classification is not computed or stored — it is purely visual. Users read the team's position relative to the crosshairs and intuitively understand the characterisation. This avoids brittle categorical labels that might misclassify teams near the boundary.

### 2.3 The Multi-Stage Aggregation Hierarchy

The aggregation pipeline transforms ~1,200 individual lap records into 10 team-level data points through four stages:

```
Stage 1: Per-Lap Values
  Each RACING lap contributes:
    - speed_trap (raw SpeedST from FastF1)
    - mean_speed_kmh = circuit_length_m / fuel_corrected_time * 3.6

Stage 2: Per-Driver Means
  For each driver, compute:
    - top_speed = mean(all speed_trap values across their racing laps)
    - mean_speed = mean(all mean_speed_kmh values across their racing laps)

Stage 3: Per-Team Means
  For each team, average both drivers' means:
    - team_top_speed = mean(driver_1.top_speed, driver_2.top_speed)
    - team_mean_speed = mean(driver_1.mean_speed, driver_2.mean_speed)
  (If one driver DNF'd, single driver still contributes)

Stage 4: Field Averages and Deltas
  - field_top_speed = mean(all team top_speeds)  [mean-of-team-means]
  - field_mean_speed = mean(all team mean_speeds)
  - team_delta = team_value - field_average
```

**Why mean-of-team-means, not mean-of-all-drivers?**

Teams are the unit of analysis in Phase 5 (car characterisation, not driver performance). If Red Bull has 2 laps and Mercedes has 1 lap, a naive mean of all 3 laps would weight Red Bull 2:1. The mean-of-team-means approach weights each team equally — each team is one vote in the field average, regardless of how many laps or drivers contributed. This is a deliberate design choice that prevents teams with more data from skewing the reference lines.

### 2.4 Warm-Up Lap Inclusion

Unlike Phase 3 (tyre degradation), where the first 2 laps of each stint are excluded from regression because tyre warm-up causes non-representative lap times (~1-2s slower), Phase 5 includes warm-up laps. The reasoning:

- Aerodynamic configuration does not change between laps. Downforce level, wing angles, and drag coefficient are fixed for the race.
- The warm-up speed variation (~0.5 km/h on mean speed, negligible on top speed) is small relative to inter-team differences (~3-8 km/h).
- Including more laps per driver improves the statistical reliability of per-driver means.

This decision is documented in the service module's docstring and validated by the `test_warm_up_laps_included` unit test.

### 2.5 Missing Speed Trap Handling

Not all laps have `SpeedST` data. Speed trap readings can be missing when the timing loop sensor fails, when a driver pits before the speed trap point, or when FastF1's data parser encounters incomplete timing data. The service handles this asymmetrically:

- **Top speed:** Only laps with valid `speed_trap` values contribute. If a driver has zero valid speed trap readings, they are excluded from the team's top speed (but not from mean speed).
- **Mean speed:** Uses `fuel_corrected_time` (falling back to raw `lap_time` if fuel correction is unavailable). This is almost always present for RACING laps.
- **Team-level:** If no driver on any team has speed trap data, the endpoint returns an empty response rather than displaying a chart with only one axis of data.

### 2.6 Field Averages as Reference Lines

The crosshair reference lines on the quadrant chart use field averages (mean of team values) rather than median. This is a deliberate choice:

- With only 10 teams, median and mean are very similar; statistical robustness against outliers (the usual argument for median) is less important than interpretive clarity.
- The mean has the mathematical property that positive and negative deltas sum to zero, making the crosshairs a true balance point.
- The scatter chart shows all 10 data points, so any outlier is visually obvious to the user.

### 2.7 Server-Side Circuit Length Resolution

The mean speed formula requires circuit length in metres. Rather than passing this from the frontend (which would require Track Intelligence data to flow through the API query), the endpoint resolves it server-side:

```python
parts = session.split('_')       # '2025_17_Race' → ['2025', '17', 'Race']
season = int(parts[0])            # 2025
round_num = int(parts[1])        # 17
track_info = await get_data_service().get_track_info(season, round_num)
circuit_length_m = track_info.length
```

This keeps the frontend API simple (session + fuel_effect only) and ensures the circuit length is always correct — the backend is the single source of truth for track data.

---

## 3. End-to-End Workflow and Data Flow

### 3.1 Initial Page Load

```
User navigates to /race?season=2025&round=17
       |
       v
RaceContent.tsx hydrates
  - Derives sessionId = "2025_17_Race"
  - Derives fuelEffect from Track Intelligence (circuit-specific)
       |
       v
TeamPerformancePanel mounts
  - Initialises activeView = 'quadrant' (default)
  - showGuide = false (collapsed)
       |
       v
useTeamPerformanceQuery fires
  - Query key: ['race', 'teamPerformance', '2025_17_Race', { fuelEffect: 0.033 }]
  - Calls fetchTeamPerformance('2025_17_Race', 0.033)
       |
       v
GET /race/team-performance?session=2025_17_Race&fuel_effect=0.033
       |
       v
get_team_performance() route handler
  - Calls await get_processed_race_data('2025_17_Race', 0.033)
    [Phase 1 pipeline: classify -> fuel correct -> traffic -> stints -> pit stops]
  - Parses session_id → season=2025, round=17
  - Calls await get_data_service().get_track_info(2025, 17)
  - Extracts circuit_length_m from track_info.length
  - Calls compute_team_performance(race_data['laps'], circuit_length_m, session_id)
       |
       v
compute_team_performance()
  - Filters to RACING classification laps (includes warm-up)
  - Per-driver: mean of speed_trap → top_speed; mean of (length/fct*3.6) → mean_speed
  - Per-team: average both drivers' means
  - Field averages: mean of all team values (weights teams equally)
  - Deltas: team_value - field_average
  - Insights: highest top speed team, highest mean speed team
  - Sorts by mean speed descending
       |
       v
TeamPerformanceResponse JSON (camelCase via CamelCaseModel)
  - sessionId, teams[], fieldAverages{}, insights{}
       |
       v
TeamPerformancePanel receives data
  - Renders header with TeamPerfViewTabs
  - Renders active chart (TeamQuadrantScatter by default)
  - Renders TeamPerfInsights (two template-based cards)
  - Renders "How to read this chart" expandable guide
```

### 3.2 View Switching Flow (Client-Side Only)

```
User clicks "Top Speed" tab
       |
       v
setActiveView('topSpeed')
  - React state update only
  - NO backend refetch (same data, different slice)
       |
       v
TopSpeedDivergence renders with data.teams
  - Horizontal divergence bars from zero
  - Positive = above field average, negative = below
  - Team-coloured bars, dynamic height
```

```
User clicks "Mean Speed" tab
       |
       v
setActiveView('meanSpeed')
  - React state update only
       |
       v
MeanSpeedDivergence renders with data.teams
  - Same pattern as TopSpeedDivergence but with 2dp precision
```

```
User clicks "Quadrant" tab
       |
       v
setActiveView('quadrant')
  - React state update only
       |
       v
TeamQuadrantScatter renders with data.teams + data.fieldAverages
  - 10 team dots positioned by meanSpeed (x) and topSpeed (y)
  - Crosshair lines at field averages via layout.shapes
  - Quadrant labels via layout.annotations
```

### 3.3 GP Switching Flow

```
User selects Abu Dhabi GP from navigation selector
       |
       v
URL changes: /race?season=2025&round=24
       |
       v
RaceContent re-renders with new round
  - New sessionId = "2025_24_Race"
  - New fuelEffect from Track Intelligence
       |
       v
useTeamPerformanceQuery fires with new query key
  - ['race', 'teamPerformance', '2025_24_Race', { fuelEffect: 0.032 }]
  - placeholderData: keepPreviousData -> old Baku data remains at 50% opacity
       |
       v
New Abu Dhabi data arrives
  - isPlaceholderData = false -> opacity transitions to 100%
  - Charts render with Abu Dhabi 2025 team performance data
  - activeView preserved (user stays on whichever tab they were viewing)
```

### 3.4 Data Flow Through the Aggregation Service

```
List[Dict] (enriched laps from Phase 1 pipeline)
       |
       v
Filter: classification == 'RACING' AND lap_time is not None
       |
       v
Per-Driver Aggregation:
  For each driver:
    +---> speed_traps[] = all valid SpeedST values
    +---> lap_speeds[] = all valid (circuit_length / fct * 3.6) values
       |
       v
Per-Driver Means:
  For each driver:
    +---> top_speed = mean(speed_traps) or None if empty
    +---> mean_speed = mean(lap_speeds)
       |
       v
Per-Team Means:
  For each team:
    +---> team_top_speed = mean(drivers' top_speeds) [excludes None drivers]
    +---> team_mean_speed = mean(drivers' mean_speeds)
       |
       v
Field Averages (mean-of-team-means):
  +---> field_top_speed = mean(all team top_speeds)
  +---> field_mean_speed = mean(all team mean_speeds)
       |
       v
Deltas:
  +---> top_speed_delta = team_top_speed - field_top_speed
  +---> mean_speed_delta = team_mean_speed - field_mean_speed
       |
       v
Insights:
  +---> fastest_on_straights = team with max top_speed
  +---> highest_mean_speed = team with max mean_speed
       |
       v
Sort by mean_speed descending → TeamPerformanceResponse
```

---

## 4. Technical Implementation Breakdown

### 4.1 Files Created

| File | Lines | Purpose | Key Exports |
|------|-------|---------|-------------|
| `services/race/team_performance.py` | 200 | Aggregation service | `compute_team_performance()` |
| `components/race/TeamPerformancePanel.tsx` | 204 | Main orchestrator panel | `TeamPerformancePanel` |
| `components/race/TeamPerfViewTabs.tsx` | 47 | Three-tab switcher | `TeamPerfViewTabs`, `TeamPerfView` |
| `components/race/TopSpeedDivergence.tsx` | ~100 | Horizontal divergence bar chart | `TopSpeedDivergence` |
| `components/race/MeanSpeedDivergence.tsx` | ~100 | Horizontal divergence bar chart | `MeanSpeedDivergence` |
| `components/race/TeamQuadrantScatter.tsx` | 206 | Scatter with crosshairs + quadrant labels | `TeamQuadrantScatter` |
| `components/race/TeamPerfInsights.tsx` | ~80 | Template-based insight cards | `TeamPerfInsights` |
| `lib/hooks/useTeamPerformanceQuery.ts` | ~20 | React Query hook | `useTeamPerformanceQuery` |
| `tests/test_team_performance.py` | 359 | 21 unit tests | `TestComputeTeamPerformance` |

### 4.2 Files Modified

| File | Change | Impact |
|------|--------|--------|
| `services/telemetry/fastf1_client.py` | Added 4 speed column extractions (SpeedST, SpeedI1, SpeedI2, SpeedFL) | Data foundation for Phase 5 |
| `services/mock_data.py` | Added matching speed columns to mock data | Test/fallback parity |
| `routes/race.py` | Added `GET /team-performance` endpoint with server-side circuit length resolution | New API surface for Phase 5 |
| `models/dto.py` | Added 5 DTOs: `TeamPerformanceData`, `TeamPerformanceFieldAverages`, `TeamPerfInsightEntry`, `TeamPerformanceInsights`, `TeamPerformanceResponse` | Backend response schema |
| `packages/models/src/types.ts` | Added 5 matching TypeScript interfaces | Frontend type safety |
| `lib/api.ts` | Added `fetchTeamPerformance()` | API client function |
| `lib/hooks/queryKeys.ts` | Added `race.teamPerformance()` key factory | Cache key for React Query |
| `app/race/RaceContent.tsx` | Added `<TeamPerformancePanel>` section | Panel integration |

### 4.3 Speed Column Extraction (`fastf1_client.py`)

The data foundation for Phase 5 was added to the existing `get_race_laps()` method in the FastF1 client. Four speed columns were extracted from FastF1's laps DataFrame:

```python
'speed_trap': float(lap['SpeedST']) if pd.notna(lap.get('SpeedST')) else None,
'speed_i1': float(lap['SpeedI1']) if pd.notna(lap.get('SpeedI1')) else None,
'speed_i2': float(lap['SpeedI2']) if pd.notna(lap.get('SpeedI2')) else None,
'speed_fl': float(lap['SpeedFL']) if pd.notna(lap.get('SpeedFL')) else None,
```

These are added to the per-lap dict construction (lines 432-435) that builds each lap record during race session loading. Only `speed_trap` (SpeedST) is used by Phase 5's aggregation service; the other three (SpeedI1, SpeedI2, SpeedFL) are extracted proactively for potential future use (sector-level speed analysis).

**No pipeline changes were needed.** The three transform functions (`classify_race_laps`, `apply_fuel_correction`, `derive_traffic`) modify dicts in-place and preserve unknown keys — verified by reading `transforms.py` before implementation. New keys flow through the pipeline without modification.

**Cache implication:** Parquet files written before this change lack speed columns. The service handles this gracefully — if no lap has `speed_trap` data, `compute_team_performance()` returns `_empty_response()`. Users need to clear old Parquet cache files to get speed data for sessions cached before this extraction was added.

### 4.4 Backend Aggregation Service (`team_performance.py`)

The service implements a six-step aggregation pipeline that transforms a flat list of enriched lap dicts into the team performance response:

```python
def compute_team_performance(
    laps: List[Dict],
    circuit_length_m: float,
    session_id: str,
) -> Dict[str, Any]:
```

**Input:** `List[Dict]` — enriched race laps from `get_processed_race_data()['laps']`, plus circuit length from `get_track_info()`.

**Processing stages:**

**Stage 1 — RACING Lap Filtering:**
```python
racing_laps = [
    lap for lap in laps
    if lap.get('classification') == 'RACING'
    and lap.get('lap_time') is not None
]
```
Only RACING classification laps with valid lap times enter the pipeline. IN_LAP, OUT_LAP, SAFETY_CAR, VSC, RED_FLAG, FORMATION, and ANOMALY laps are excluded. Warm-up laps (first 2 of each stint) are included — they have classification RACING and the `is_warm_up` flag is ignored by this service.

**Stage 2 — Per-Driver Data Collection:**
```python
driver_data[driver] = {
    'team': None,
    'speed_traps': [],     # raw SpeedST values
    'lap_speeds': [],      # computed mean speed per lap
}
```
Each lap contributes its `speed_trap` to the list (if not None) and its computed mean speed (`circuit_length_m / fct * 3.6`). The `fuel_corrected_time` is preferred; raw `lap_time` is used as fallback if fuel correction is unavailable.

**Stage 3 — Per-Driver Means:**
For each driver: `top_speed = mean(speed_traps)` or None if no speed trap data; `mean_speed = mean(lap_speeds)`. Drivers with no lap speed data (empty `lap_speeds` list) are dropped entirely.

**Stage 4 — Per-Team Means:**
Drivers are grouped by team. Team top speed averages only drivers who have speed trap data; team mean speed averages all drivers. This asymmetric treatment ensures a missing speed trap for one driver doesn't reduce the team to zero when the other driver has valid data.

**Stage 5 — Field Averages and Deltas:**
Field averages are mean-of-team-means. Deltas are `team_value - field_average`. Top speed rounded to 1 decimal place; mean speed rounded to 2 decimal places. Teams sorted by mean speed descending (fastest overall team first).

**Stage 6 — Insight Computation:**
```python
fastest_straight = max(teams, key=lambda t: t['top_speed'])
highest_mean = max(teams, key=lambda t: t['mean_speed'])
```
Deterministic selection — no heuristics or thresholds. Each insight includes the team name, the absolute value, and the delta above field average.

**Edge case handling:**
- Empty input → `_empty_response(session_id)` with empty teams list and zero field averages
- Zero or negative circuit length → `_empty_response()` (prevents division by zero)
- No RACING laps → `_empty_response()`
- All speed traps missing → `_empty_response()` (can't construct meaningful quadrant)
- Zero `fuel_corrected_time` → excluded from mean speed calculation (prevents infinity)
- Single driver per team → that driver's means become the team's means (no averaging needed)
- None lap_time laps → filtered in Stage 1

### 4.5 Data Transfer Objects (`dto.py`)

Five Pydantic models define the response schema, all extending `CamelCaseModel`:

```
TeamPerformanceResponse
  ├── session_id: str
  ├── teams: List[TeamPerformanceData]
  │     ├── team: str
  │     ├── top_speed: float              # Average SpeedST across team's drivers
  │     ├── mean_speed: float             # Average lap speed (fuel-corrected)
  │     ├── top_speed_delta: float        # vs field average
  │     └── mean_speed_delta: float       # vs field average
  ├── field_averages: TeamPerformanceFieldAverages
  │     ├── top_speed: float              # Mean of all team top speeds
  │     └── mean_speed: float             # Mean of all team mean speeds
  └── insights: TeamPerformanceInsights
        ├── fastest_on_straights: Optional[TeamPerfInsightEntry]
        │     ├── team: str
        │     ├── value: float
        │     └── delta: float
        └── highest_mean_speed: Optional[TeamPerfInsightEntry]
              ├── team: str
              ├── value: float
              └── delta: float
```

The schema is intentionally flat compared to Phase 4's pit stop DTOs. There are no per-stop arrays, no anomaly notes, no tiered metric types — team performance aggregation produces a single value per team per metric, making the data structure simpler.

### 4.6 API Endpoint (`race.py`)

```python
@router.get("/team-performance", response_model=TeamPerformanceResponse)
async def get_team_performance(
    session: str = Query(..., description="Session ID, e.g. 2025_17_Race"),
    fuel_effect: float = Query(0.032, description="Fuel effect per kg in seconds"),
):
    race_data = await get_processed_race_data(session, fuel_effect)
    parts = session.split('_')
    season = int(parts[0])
    round_num = int(parts[1])
    from app.services.data_service import get_data_service
    track_info = await get_data_service().get_track_info(season, round_num)
    circuit_length_m = track_info.length
    return compute_team_performance(race_data['laps'], circuit_length_m, session)
```

Key design decisions:
- **Circuit length resolved server-side:** The frontend never sends circuit length. The endpoint parses the session_id, looks up the track via `get_track_info()`, and extracts the length. This keeps the API contract clean and avoids frontend-backend coupling on track data.
- **Fuel effect parameter:** Passed to `get_processed_race_data()` for fuel correction. The fuel-corrected times flow through to the mean speed calculation. Top speed is unaffected (uses raw SpeedST).
- **Shared data service:** Same Phase 1 pipeline as all other race endpoints. The enriched dataset is cached — no redundant session loading.
- **Lazy import of `get_data_service`:** The import is inside the function body to avoid circular import issues with the data service factory pattern.

### 4.7 Frontend Panel Orchestrator (`TeamPerformancePanel.tsx`)

The orchestrator manages two pieces of state:
- `activeView: TeamPerfView` — which chart is visible (`'topSpeed'` | `'meanSpeed'` | `'quadrant'`)
- `showGuide: boolean` — whether the explanation section is expanded

**Progressive rendering states:**
1. **Loading (no prior data):** `TeamPerformanceSkeleton` — matches panel dimensions (header bar + 400px chart + 2 insight card placeholders)
2. **Error:** Clear error message with error details
3. **Empty data (no teams):** "No speed data available for this session. Try clearing the cache and reloading."
4. **Placeholder data:** Previous GP data at 50% opacity during transition (`isPlaceholderData`)
5. **Ready:** Full panel with tab switcher, active chart, insight cards, and expandable guide

**Component tree:**
```
TeamPerformancePanel
  ├── TeamPerfViewTabs (three-tab switcher)
  ├── [Active chart view]
  │     ├── TopSpeedDivergence (horizontal divergence bars)
  │     ├── MeanSpeedDivergence (horizontal divergence bars)
  │     └── TeamQuadrantScatter (scatter + crosshairs + quadrant labels)
  ├── TeamPerfInsights (two template-based insight cards)
  └── "How to read this chart" (expandable guide, 3 sections)
```

### 4.8 Chart Components

**`TopSpeedDivergence` — Horizontal Divergence Bar Chart**

Plotly horizontal bars showing each team's top speed delta relative to field average. Bars extend left (negative delta, below-average) or right (positive delta, above-average) from a zeroline. Teams sorted by delta ascending, then reversed for Plotly's bottom-to-top rendering (highest delta at top). Team colours via `getTeamColorForMode(team, 'team')`. Dynamic height computed from team count. All Plotly configuration wrapped in `useMemo` to prevent zoom-reset bugs on re-render.

**`MeanSpeedDivergence` — Horizontal Divergence Bar Chart**

Same structural pattern as TopSpeedDivergence but using `meanSpeedDelta` and `meanSpeed` fields. 2 decimal place precision on labels (vs 1dp for top speed) reflects the higher granularity of mean speed differences.

**`TeamQuadrantScatter` — Scatter Plot with Crosshairs and Quadrant Labels**

The most complex chart in Phase 5, combining three Plotly features:

1. **Scatter trace:** 10 team markers positioned at `(meanSpeed, topSpeed)`. Marker size 12px, team colours, 3-letter abbreviation labels above each dot. Custom hover templates show team name and both speed values.

2. **Crosshair reference lines** via `layout.shapes`:
   ```javascript
   shapes = [
     { type: 'line', xref: 'x', yref: 'paper',
       x0: fieldAverages.meanSpeed, x1: fieldAverages.meanSpeed,
       y0: 0, y1: 1,
       line: { color: 'rgba(255,255,255,0.2)', dash: 'dash' } },
     { type: 'line', xref: 'paper', yref: 'y',
       x0: 0, x1: 1,
       y0: fieldAverages.topSpeed, y1: fieldAverages.topSpeed,
       line: { color: 'rgba(255,255,255,0.2)', dash: 'dash' } },
   ]
   ```
   Using `layout.shapes` instead of trace data prevents crosshair lines from appearing in the legend or producing hover tooltips — a design lesson established from the qualifying page's `DeltaPlot.tsx`.

3. **Quadrant labels** via `layout.annotations`:
   Four corner labels using `xref/yref: 'paper'` coordinates (0-1 range, independent of data scale). Each label is colour-coded: green (High Efficiency), yellow (Low Downforce), blue (High Downforce), red (Low Efficiency). All at 60% opacity to avoid competing with the data points.

**Team Abbreviation Map:**
A `TEAM_ABBR` lookup converts full team names to 3-letter codes (e.g., "Red Bull Racing" → "RBR", "McLaren" → "MCL") to prevent label overlap on the scatter plot. A fallback `team.slice(0, 3).toUpperCase()` handles any unknown team names.

### 4.9 Insight Cards (`TeamPerfInsights.tsx`)

Two cards in a responsive grid (`grid-cols-1 sm:grid-cols-2`):

**Fastest on Straights card:**
- Team-coloured left border (3px) via `getTeamColorForMode`
- Shows team name, top speed value (1dp), and delta above field average
- Template: "Fastest on straights at {value} km/h (+{delta} km/h vs field)"

**Highest Mean Speed card:**
- Same styling pattern with team-coloured left border
- Shows team name, mean speed value (2dp), and delta above field average
- Template: "Highest mean speed at {value} km/h (+{delta} km/h vs field)"

Both cards include a null guard — if the insight is null (no data), the card is not rendered. This handles the edge case where the response has teams but insight computation returned null.

### 4.10 Expandable User Guide

An expandable "How to read this chart" section following the exact pattern from Phases 2-4:

- `useState(false)` for collapse/expand state
- Rotating arrow indicator (`▶` → rotated 90° when expanded)
- `aria-expanded` for accessibility
- Container: `border border-white/10 bg-white/[0.02]`
- Three sections:
  1. **What does this panel show?** — Explains the decomposition into top speed and mean speed
  2. **Three chart views** — Describes Top Speed, Mean Speed, and Quadrant views
  3. **The four quadrants** — Explains each quadrant with colour coding matching the chart labels

### 4.11 React Query Hook (`useTeamPerformanceQuery.ts`)

```typescript
export function useTeamPerformanceQuery(
  sessionId: string | undefined,
  fuelEffect?: number,
) {
  return useQuery<TeamPerformanceResponse>({
    queryKey: queryKeys.race.teamPerformance(sessionId ?? '', fuelEffect),
    queryFn: () => fetchTeamPerformance(sessionId!, fuelEffect),
    enabled: !!sessionId,
    placeholderData: keepPreviousData,
  })
}
```

Design decisions:
- **Query key includes fuelEffect:** Unlike Phase 4's pit stop hook (session only), team performance depends on fuel correction. Different fuel_effect values produce different mean speed values, so the key must include it to avoid serving stale data.
- **`keepPreviousData`:** Enables smooth opacity transition during GP switching. The old data is shown at 50% opacity while the new data loads.
- **TODO (Phase 6):** Wrap with `useVisibilityQuery` for Intersection Observer deferred loading. The Team Performance panel is the lowest panel on the page — it should only begin fetching when the user scrolls near it.

### 4.12 API Client and Query Keys

**`fetchTeamPerformance()`** in `api.ts`:
```typescript
export async function fetchTeamPerformance(
  sessionId: string,
  fuelEffect?: number,
): Promise<TeamPerformanceResponse> {
  const params = new URLSearchParams({ session: sessionId })
  if (fuelEffect !== undefined) {
    params.set('fuel_effect', fuelEffect.toString())
  }
  return fetchApi<TeamPerformanceResponse>(
    `${API_BASE_URL}/race/team-performance?${params}`
  )
}
```

**Query key factory** in `queryKeys.ts`:
```typescript
teamPerformance: (sessionId: string, fuelEffect?: number) =>
  ['race', 'teamPerformance', sessionId, { fuelEffect }] as const,
```

The structured `{ fuelEffect }` object at the end follows the same pattern as the tyre degradation key, ensuring React Query treats different fuel correction values as different cache entries.

### 4.13 Integration in RaceContent

The panel mounts as the final analytical section in `RaceContent.tsx`:

```tsx
{/* Phase 5: Team Performance Quadrant */}
<section>
  <TeamPerformancePanel sessionId={sessionId} fuelEffect={fuelEffect} />
</section>
```

Two props are passed: `sessionId` (derived from URL state) and `fuelEffect` (derived from Track Intelligence's `fuelEffectPerKg` value for the current circuit, or 0 if fuel correction is toggled off). The panel manages all internal state (active view, guide toggle). No state leaks to the parent.

### 4.14 Unit Test Coverage

21 tests in `test_team_performance.py` covering:

| Test | What It Validates |
|------|-------------------|
| `test_empty_laps_returns_empty_response` | Graceful handling of no data |
| `test_zero_circuit_length_returns_empty` | Zero circuit length prevention |
| `test_negative_circuit_length_returns_empty` | Negative circuit length prevention |
| `test_no_racing_laps_returns_empty` | Only IN_LAP/OUT_LAP laps |
| `test_racing_laps_with_none_lap_time_excluded` | None lap_time handling |
| `test_single_team_deltas_are_zero` | Delta = 0 when only one team exists |
| `test_two_team_aggregation` | Full pipeline with two teams: deltas, field averages |
| `test_mean_speed_formula` | Verifies `circuit_length / fct * 3.6` computation |
| `test_mean_speed_falls_back_to_lap_time` | Fallback when fuel_corrected_time is None |
| `test_non_racing_laps_excluded` | IN_LAP, SAFETY_CAR classification filtering |
| `test_warm_up_laps_included` | Warm-up laps contribute (unlike Phase 3) |
| `test_missing_speed_trap_excluded_from_top_speed` | None speed_trap handling |
| `test_all_speed_traps_missing_returns_empty` | No speed data → empty response |
| `test_single_driver_per_team` | DNF teammate scenario |
| `test_field_averages_weight_teams_equally` | Mean-of-team-means, not mean-of-all-laps |
| `test_teams_sorted_by_mean_speed_descending` | Sort order correctness |
| `test_insight_fastest_on_straights` | Insight data accuracy for top speed |
| `test_insight_highest_mean_speed` | Insight data accuracy for mean speed |
| `test_multiple_laps_per_driver_averaged` | Multi-lap driver averaging |
| `test_rounding_precision` | Top speed 1dp, mean speed 2dp |
| `test_zero_fuel_corrected_time_excluded` | Prevents division by zero |

All tests use a `_make_racing_lap()` helper that creates minimal lap dicts matching the structure produced by Phase 1's pipeline. All float assertions use `pytest.approx()` with appropriate tolerances — a lesson carried forward from earlier phases.

---

## 5. Critical Path Corrections

Phase 5 benefited from the diagnostic-first workflow formalised during Phase 4. Two categories of corrections were applied:

### 5.1 Corrections Carried Forward from Phase 4 Diagnostics

These corrections were already known from Phase 4 and applied from the start:

| # | Issue | Correction Applied |
|---|---|---|
| 1 | DTOs centralised in `apps/api/app/models/dto.py`, not service-local | All 5 DTOs added to centralised file |
| 2 | Types in `packages/models/src/types.ts`, not `apps/web/types.ts` | All 5 interfaces added to shared package |
| 3 | PlotlyLazy at `@/components/charts/PlotlyLazy` | Correct import in all 3 chart components |
| 4 | Team colours via `getTeamColorForMode(team, 'team')` | Used in all chart components and insight cards |
| 5 | Hooks in `apps/web/lib/hooks/` directory | Correct path for hook and queryKeys |
| 6 | Panel styling via `card-panel` CSS class | Used in orchestrator component |

### 5.2 Phase 5-Specific Corrections

| # | Issue | Discovery | Correction |
|---|---|---|---|
| 1 | Stale Parquet cache lacking speed columns returned empty teams | Docker validation — endpoint returned valid but empty response | Documented cache invalidation requirement; service returns clear empty state |
| 2 | Two-layer cache (Parquet + in-memory) required sequential invalidation | After deleting Parquet files, in-memory cache still served stale data | Delete Parquet files, then restart API container to clear in-memory `_race_data_cache` |
| 3 | `get_processed_race_data()` laps are dicts (not Pydantic objects) | Verified by reading `race_data_service.py` — laps stay as dicts through pipeline | Service uses `lap.get('classification')` dict access (not attribute access) |

The Parquet cache issue (corrections #1 and #2) was the primary challenge during Docker validation and is documented in detail in Section 6.

---

## 6. Docker Integration Validation

### 6.1 Validation Process

After unit tests passed (21/21 local, full suite passing), Docker-based integration validation exercised the endpoint with live FastF1 data across three races:

| Race | Characteristics | Purpose |
|------|----------------|---------|
| Baku 2025 (R17) | Street circuit, mix of high-speed and low-speed | Primary validation target |
| Abu Dhabi 2025 (R24) | Season finale, comprehensive data | Cross-reference and cache debugging |
| Monaco 2025 (R8) | Slowest circuit, unique aero setups | Extreme case validation |

### 6.2 The Stale Cache Discovery

**Initial test (Abu Dhabi):** The endpoint returned HTTP 200 with a valid JSON structure — but `teams` was an empty array and `field_averages` showed `0.0` for both values. The graceful degradation was working correctly (no crash, structurally valid response), but no team data was present.

**Root cause analysis:**
1. The Abu Dhabi Parquet cache file (`2025_24_Race_race_laps.parquet`) was written before the speed column extraction was added.
2. When the Phase 1 pipeline loaded this cached file, the lap dicts had no `speed_trap` key.
3. `compute_team_performance()` found zero valid speed trap values → returned `_empty_response()`.
4. This is exactly the correct behaviour — the service cannot produce team performance data without speed trap readings.

**Resolution — Two-Layer Cache Invalidation:**
1. **Delete Parquet files:** `docker exec f1-api bash -c "rm -f /app/data/cache/parquet/*Race_race_laps.parquet"` — removes the serialised cache layer.
2. **Restart API container:** `docker restart f1-api` — clears the in-memory `_race_data_cache` dict that held the stale processed data.

After both layers were invalidated, the next API call triggered a fresh FastF1 session load, which included the new speed columns. All subsequent tests returned full data.

### 6.3 Validation Results

**Baku 2025 (First successful test):**
- 10 teams, all with valid top speed and mean speed data
- Field averages: top_speed ~330 km/h, mean_speed ~195 km/h (physically realistic for a long-straight street circuit)
- Highest top speed: Haas (low downforce setup) — consistent with known Baku characteristics
- Highest mean speed: McLaren — consistent with their strong overall 2025 form
- All deltas sum to approximately zero (mathematical property of mean-based field averages)

**Abu Dhabi 2025 (After cache clear):**
- 10 teams, full data
- Mean speed values lower than Baku (shorter straights, more technical corners)
- Team rankings shifted from Baku, reflecting different track characteristics

**Monaco 2025:**
- 10 teams, full data
- Lowest top speeds (~280 km/h vs Baku's ~330 km/h) — physically correct for Monaco's short tunnel straight
- Highest mean speed teams different from Baku/Abu Dhabi — reflects Monaco-specific setup requirements

### 6.4 Cross-Endpoint Regression Check

All existing endpoints verified working alongside the new endpoint:
- `GET /race/pace?session=2025_24_Race` → 200, 20 drivers
- `GET /race/tyre-degradation?session=2025_24_Race` → 200
- `GET /race/pit-stops?session=2025_24_Race` → 200
- `GET /race/team-performance?session=2025_24_Race` → 200, 10 teams
- API logs confirmed the web frontend calls all 4 race endpoints in parallel, including the new team-performance endpoint

### 6.5 Frontend Build Verification

- TypeScript compilation: `npx tsc --noEmit` — zero errors
- Next.js build: compiled successfully (8/8 static pages)
- `TeamPerformance` references confirmed present in compiled race page JavaScript bundle
- Race page serves HTTP 200 from web container

---

## 7. Learnings and How They Influenced Decisions

### 7.1 Multi-Stage Aggregation Pipeline Design

**Learning:** When aggregating from individual records to group-level summaries, the hierarchy of aggregation stages must be deliberate. Averaging "per-driver means into per-team means" produces a different result than "averaging all laps across the team." The choice between these approaches has mathematical and semantic implications.

**Influence:** The mean-of-team-means approach was chosen because it weights teams equally in the field average. Without this, a team that completed more laps (e.g., no retirements, more pit stops) would have disproportionate influence on the crosshair reference lines. The test `test_field_averages_weight_teams_equally` explicitly validates this: Red Bull with 2 laps and Mercedes with 1 lap both contribute equally to the field average.

### 7.2 Asymmetric Metric Treatment Based on Domain Modelling

**Learning:** Not all metrics in a system should be processed identically. Top speed and mean speed look similar on the surface (both measured in km/h), but the underlying physics dictates different treatment. Top speed is drag-limited and fuel-insensitive; mean speed is mass-sensitive and requires fuel correction. Applying fuel correction to both, or neither, would produce misleading results.

**Influence:** This principle extended to other asymmetries in the service: missing speed trap data excludes a driver from top speed but not from mean speed. A team can appear in the mean speed divergence chart without having a top speed value. The service's handling of partial data reflects the domain reality that these are independent measurements with different failure modes.

### 7.3 Schema Evolution in Cached Systems (The Stale Cache Problem)

**Learning:** When a data pipeline writes intermediate results to a persistent cache (Parquet files), the schema is frozen at write time. Adding new columns to the extraction layer does not retroactively update cached files. If the consuming service expects the new columns, it will find them absent in old cache entries.

**Influence:** The two-layer cache architecture (Parquet + in-memory dict) required sequential invalidation — deleting the files alone was insufficient because the in-memory layer still held the stale processed data. This was the primary debugging challenge during Docker validation. Future schema-changing modifications to the extraction layer should include a cache version mechanism or proactive documentation of the invalidation procedure.

### 7.4 Graceful Degradation as a Correctness Property

**Learning:** The `_empty_response()` pattern — returning a structurally valid but empty response rather than crashing — is not just a defensive coding practice. It is a correctness property. When the stale Parquet cache returned laps without speed columns, the service correctly determined that no valid team performance data could be computed and returned an empty response. The frontend correctly rendered "No speed data available" rather than crashing or showing misleading data.

**Influence:** The chain of correct empty responses — from service to API to frontend — validated that the error boundary design works end-to-end. Each layer handled the empty data case independently: the service returned `_empty_response()`, the API serialised it as valid JSON, the frontend checked `data.teams.length === 0` and showed the appropriate empty state message.

### 7.5 Pattern Replication as an Engineering Strategy

**Learning:** Phase 5 was implemented significantly faster than Phase 4 because the patterns were already established. The tab switcher (`TeamPerfViewTabs`) was copied from `PitStopViewTabs` with type changes. The divergence charts were adapted from `PitStopByTeam`. The insight cards followed `PitStopInsights`. The panel orchestrator followed `PitStopPanel`. The hook followed `usePitStopsQuery`. Each component required domain-specific adjustments (different data fields, different chart configurations), but the structural skeleton was reusable.

**Influence:** This validates the architectural decision to invest heavily in Phase 4's patterns. The effort to get pit stop analysis right — with its tiered consistency, anomaly handling, and expandable guide — paid dividends in Phase 5, where the focus could shift entirely to the domain-specific logic (aggregation pipeline, quadrant layout) rather than structural concerns.

### 7.6 Server-Side Circuit Length Resolution Simplifies the API Contract

**Learning:** The original plan considered passing circuit length as a frontend query parameter. This would have required the frontend to look up the circuit length, add it to every API call, and trust the frontend to send the correct value. Resolving it server-side from the session_id keeps the API contract simple (session + fuel_effect only) and ensures correctness.

**Influence:** The server-side resolution pattern (`parse session_id → get_track_info() → extract length`) adds one async call per request, but the data is already cached by the data service. The marginal cost is near-zero, and the benefit is a cleaner separation of concerns: the frontend doesn't need to know about circuit metadata when calling the team performance endpoint.

### 7.7 Plotly layout.shapes and layout.annotations for Overlay Elements

**Learning:** Reference lines and labels that are part of the chart's visual framework (not data) should use Plotly's `layout.shapes` and `layout.annotations` rather than additional trace data. Traces produce hover tooltips, legend entries, and interact with zoom in ways that reference elements should not.

**Influence:** The crosshair lines on the quadrant scatter use `layout.shapes` with mixed coordinate references (`xref: 'x', yref: 'paper'` for the vertical line; `xref: 'paper', yref: 'y'` for the horizontal line). This ensures the lines span the full plot area while intersecting at the correct data values. The quadrant labels use `layout.annotations` with `xref/yref: 'paper'` so they stay in the corners regardless of zoom level. This pattern was established in the qualifying page's `DeltaPlot.tsx` and applied consistently in Phase 5.

### 7.8 End-to-End Type Safety Across Service Boundaries

**Learning:** The chain from Python DTOs (`CamelCaseModel` with snake_case fields) → JSON serialisation (automatic camelCase conversion) → TypeScript interfaces (camelCase fields) requires manual alignment. There is no automated check that `top_speed_delta` in Python corresponds to `topSpeedDelta` in TypeScript. The `CamelCaseModel` base class handles the conversion, but if a field name is misspelled in either language, the error only surfaces at runtime.

**Influence:** The 5 Python DTOs and 5 TypeScript interfaces were written in parallel, with field names cross-checked manually. The TypeScript compilation step (`npx tsc --noEmit`) catches frontend-side type errors, but backend-side naming errors require the Docker validation step to catch. Future consideration: a codegen tool that generates TypeScript interfaces from Pydantic models would eliminate this class of errors.

---

## 8. Alignment with Broader Race Page Plan

### 8.1 Patterns Validated and Extended

| Pattern | Origin | Phase 5 Validation |
|---------|--------|--------------------|
| React Query hook per panel | Phase 2 | Hook with fuelEffect in query key (most parameterised race hook) |
| `keepPreviousData` for GP switching | Phase 2 | Smooth opacity transition works with scatter plot |
| PlotlyLazy for all charts | Phase 2 | Three new chart types rendered correctly (divergence bars + scatter) |
| `card-panel` CSS class | Phase 2 | Panel styling consistent across all five race panels |
| Server-side computation | Phase 2/3 | Full aggregation pipeline on backend |
| Anti-hallucination insights | Qualifying P5 | Two deterministic insight cards with data-only placeholders |
| Single API response, client-side switch | Phase 4 | Three chart types (not just bar variants) from one response |
| `getTeamColorForMode` for team-level data | Phase 4 | Used in all chart components and insight cards |
| Pre-implementation diagnostics | Phase 4 | Applied corrections from Phase 4 before writing code |
| Expandable user guide | Phase 2/3/4 | Same pattern, three domain-specific sections |
| `layout.shapes` for reference lines | Qualifying DeltaPlot | Crosshair lines without hover/legend artifacts |
| `layout.annotations` for chart labels | Qualifying DeltaPlot | Quadrant labels anchored to paper coordinates |

### 8.2 Infrastructure Extended for Phase 6

| Asset | Created/Extended | Available To |
|-------|-----------------|-------------|
| `queryKeys.race.teamPerformance()` | Phase 5 | Phase 6 performance optimisation |
| `fetchTeamPerformance()` | Phase 5 | Phase 6 prefetch on hover |
| Team abbreviation map (`TEAM_ABBR`) | Phase 5 | Any future team-level chart |
| Divergence bar pattern (from zero) | Phase 5 | Reusable for any delta-based comparison |
| Server-side circuit length resolution | Phase 5 | Pattern for any endpoint needing track metadata |
| Speed column extraction | Phase 5 | SpeedI1/I2/FL available for future sector speed analysis |

### 8.3 Deferred to Phase 6

| Feature | Deferred To | Reason |
|---------|------------|--------|
| `useVisibilityQuery` (Intersection Observer) | Phase 6 | Below-fold deferred loading for team performance panel |
| `staleTime: Infinity` for query | Phase 6 | Performance optimisation, not functional |
| `gcTime: 30min` for query | Phase 6 | Memory management, not functional |
| Prefetch on Race nav hover | Phase 6 | Performance optimisation |
| Lighthouse audit | Phase 6 | Performance validation |
| Track Segment Map (stretch goal) | Not planned | Requires 24 per-circuit SVGs — deferred indefinitely |

### 8.4 Shared Data Service Efficiency

Phase 5 continues the shared data service pattern. The `get_processed_race_data()` pipeline runs once per session and caches the enriched dataset. All five race endpoints consume different slices of the same cached output:

| Endpoint | Slice Consumed | Processing |
|----------|---------------|------------|
| `/race/pace` | `laps` (filtered RACING) | Box plot statistics |
| `/race/tyre-degradation` | `laps` (fuel-corrected) | Per-compound regression |
| `/race/pit-stops` | `pit_stops` | Team/driver aggregation |
| **`/race/team-performance`** | **`laps` (RACING + speed_trap)** | **Multi-stage team aggregation** |

Phase 5's additional server-side call (`get_track_info()`) adds minimal overhead — the track data is already loaded and cached by the data service singleton.

### 8.5 Race Page Feature Completion

With Phase 5 complete, five of six phases are delivered:

| Phase | Feature | Charts | Status |
|-------|---------|--------|--------|
| 1 | Data Foundation | — | Complete |
| 2 | Race Pace Distribution | 1 (box plot) | Complete |
| 3 | Tyre Degradation | 2 (scatter + bar) | Complete |
| 4 | Pit Stop Analysis | 3 (horiz x2 + vert x1) | Complete |
| **5** | **Team Performance Quadrant** | **3 (divergence x2 + scatter x1)** | **Complete** |
| 6 | Performance & Integration | — | Planned |

The Race page now delivers the full analytical story: pace distribution, tyre management, pit crew execution, and car characterisation. Phase 6 will optimise the complete page for performance (Intersection Observer deferred loading, cache tuning, Lighthouse audit) and perform integration testing across all five panels.

The total chart count across the Race page is now **9 interactive Plotly charts** across 4 panels, all loaded progressively through independent React Query hooks from 4 separate API endpoints, all consuming the same shared Phase 1 data pipeline. This validates the architectural patterns established during the qualifying page performance optimisation journey.

---

*Documentation Version 1.0 — February 2026*
