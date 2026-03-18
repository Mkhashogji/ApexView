# Race Page Phase 4: Pit Stop Analysis

**Status:** Complete
**Implemented:** February 2026
**TypeScript:** Zero compilation errors
**Next.js Build:** Compiled successfully (8/8 static pages generated)
**Qualifying Regression:** Zero modified qualifying files
**Docker Validation:** All 3 containers running; endpoint verified with live Abu Dhabi 2025, Baku 2025, and Monaco 2025 data
**Test Coverage:** 15 unit tests (all passing), full backend suite 109/109 passing
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

### What Phase 4 Delivers

Phase 4 implements the **Pit Stop Analysis** panel — the operational performance dimension of the Race page. Unlike Phases 2 and 3, which measure car pace and tyre management (outcomes influenced by car design, setup, and driver skill), pit stop performance is one of the few areas where **team execution is directly measurable in seconds**. The panel answers: "Which pit crew was fastest, which was most consistent, and how much time did each team gain or lose through pit stop execution?"

The panel provides three chart views (By Team, By Driver, Gap to Fastest), two template-based insight cards (Quickest on Average, Most Consistent), and anomaly detection that automatically excludes unusually long stops from calculations while keeping them visible to users.

### Why It Matters

**Pit stops are operationally distinct from all other race metrics.** Race pace depends on car aerodynamics, power unit, tyre strategy, and driving skill — complex, interrelated factors. Pit stop performance depends on crew coordination, equipment reliability, and procedural execution. A team with the slowest car can still have the fastest pit crew. This independence makes pit stop analysis a unique dimension that enriches the Race page beyond pure pace metrics.

**It introduces the anti-hallucination insight pattern to the Race page.** The Telemetry Analysis Pipeline established template-based text generation in Phase 5 (Insight Generation) for the qualifying page. Phase 4 brings this pattern to the Race page for the first time, with two deterministic insight cards where every word traces to specific computed data. No AI speculation, no generated text — only template placeholders filled from calculated values.

**It validates the single-API-response, client-side-switch pattern.** Phase 3 required backend refetches for mode toggling (individual vs pooled regression). Phase 4 demonstrates that when all chart views can be derived from the same data, a single API call with instant client-side view switching provides a faster, simpler user experience. This pattern informs decisions for Phase 5 and beyond.

### Position in the Race Page Architecture

| Phase | Name | Depends On | Status |
|-------|------|-----------|--------|
| 1 | Race Data Foundation | — | Complete |
| 2 | Race Pace Distribution (Box Plot) | Phase 1 | Complete |
| 3 | Tyre Degradation Analysis | Phase 1 | Complete |
| **4** | **Pit Stop Analysis** | **Phase 1** | **Complete** |
| 5 | Team Performance Quadrant | Phase 1 | Planned |
| 6 | Performance Optimization & Integration | Phases 1-5 | Planned |

Phase 4 consumes the Phase 1 enriched dataset through the shared `get_processed_race_data()` service, specifically the `pit_stops` field — a `List[PitStopResponse]` produced by Phase 1's `extract_pit_stops()` function. It introduces a new aggregation service (`pit_stop_analysis.py`), a new API endpoint (`GET /race/pit-stops`), and seven new frontend components, all following the patterns established by Phases 2 and 3.

---

## 2. Theoretical and Logical Background

### 2.1 What Pit Stop Analysis Communicates

The panel answers three questions at different levels of granularity:

1. **By Team:** "Which pit crew performed best overall?" — Averages all non-anomalous stops per team, revealing crew-level execution quality.
2. **By Driver:** "How did each individual driver's pit stops compare?" — Breaks down to per-driver granularity, exposing within-team differences and cross-grid ranking.
3. **Gap to Fastest:** "How much time did each team lose relative to the best?" — Quantifies the competitive cost of slower pit stops in seconds, directly relatable to on-track gaps.

### 2.2 Pit Lane Time as the Metric

The metric used is **pit lane time** — the total time from pit entry to pit exit. This includes the drive through the pit lane, the stationary stop where the crew changes tyres, and the drive out. It is the broadest measure of pit stop cost, capturing not just crew execution speed but also pit lane navigation.

Pit lane time was chosen over stationary time (the narrower measure of just the wheel-change duration) because:
- FastF1 provides pit lane time reliably across all sessions
- Pit lane time captures the full time cost the driver experiences
- Stationary time extraction from FastF1 requires additional processing with less consistent data availability

### 2.3 Anomaly Detection and Exclusion

Not all pit stops represent normal crew execution. Incidents, penalties, drive-through penalties, mechanical failures, and first-lap emergency pits produce artificially long stop times that would distort averages. Phase 4 uses a two-tier anomaly detection system inherited from Phase 1's `extract_pit_stops()`:

| Condition | Threshold | Rationale |
|-----------|-----------|-----------|
| Absolute threshold | > 35 seconds | Any stop above 35s is clearly non-representative of crew execution |
| Relative threshold | > 2× team median | A stop more than double the team's typical time indicates an unusual event |

Both conditions use OR logic — either alone is sufficient to flag an anomaly. Flagged stops are:
- **Excluded** from team averages, driver averages, grid average, and consistency calculations
- **Preserved** in the pass-through stops array and displayed in the anomaly notes section
- Users can see what happened without those outliers distorting the performance picture

### 2.4 The Tiered Consistency Metric

Consistency — how repeatable a team's pit stops are — is the second insight dimension alongside speed. The original design used IQR (Interquartile Range) universally, but this proved problematic: IQR requires at least three data points for meaningful computation, and many teams in one-stop races have only two stops total.

The solution is a **tiered consistency metric** that adapts to the available data:

| Team Stop Count | Metric | Type Label | Rationale |
|-----------------|--------|------------|-----------|
| ≥ 3 stops | IQR (Q3 − Q1) | `'iqr'` | Standard robust measure; captures spread of the middle 50% |
| 2 stops | Absolute difference | `'range'` | The only meaningful spread measure for a pair |
| 1 stop | null | null | Consistency is undefined for a single observation |

Both IQR and absolute difference are measured in seconds and represent "spread of stop times," making them directly comparable when selecting the most consistent team for the insight card. A team with 0.029s IQR (from 3 stops) is more consistent than a team with 0.200s range (from 2 stops) — the units and meaning align.

This tiered design emerged as a key learning during planning. The initial specification used IQR universally, which would have silently excluded all 2-stop teams from the consistency insight — potentially the majority of teams in a one-stop race like Baku. The tiered approach ensures the "Most Consistent" insight card is populated for any race with at least one team having two or more stops.

### 2.5 Template-Based Insights (Anti-Hallucination)

The two insight cards use deterministic text templates with data placeholders. No natural language generation, no LLM, no speculation:

**Quickest on Average template:**
```
"{team} was the quickest team in the pit lane, with an average total time of {averageTime}s.
This is {percentageFaster}% faster than the grid's overall average of {gridAverage}s."
```

**Most Consistent template (IQR variant, ≥3 stops):**
```
"{team} was the most consistent, with an Interquartile Range (IQR) of just {consistency}s.
This means the middle 50% of their pit stop times fall within this very narrow window."
```

**Most Consistent template (range variant, 2 stops):**
```
"{team} was the most consistent, with just {consistency}s separating their two pit stops."
```

The template selection is automatic based on `consistencyType`. The IQR template explains what "middle 50%" means; the range template uses plain language about "two pit stops." Both avoid assuming the reader understands statistical terminology.

### 2.6 Single-Response, Client-Side View Switching

Unlike Phase 3 (where mode toggling requires a backend refetch because individual and pooled regressions are fundamentally different computations), all three pit stop chart views derive from the same dataset:

- **By Team** uses `teamAggregates`
- **By Driver** uses `driverAggregates`
- **Gap to Fastest** uses `gapToFastest`

All three arrays are computed in a single aggregation pass and returned in one API response. Switching views is instant — a React state change with no network request. This design was a deliberate simplification informed by the Phase 3 experience, where the refetch-on-toggle pattern added latency and complexity.

---

## 3. End-to-End Workflow and Data Flow

### 3.1 Initial Page Load

```
User navigates to /race?season=2025&round=24
       |
       v
RaceContent.tsx hydrates
  - Derives sessionId = "2025_24_Race"
       |
       v
PitStopPanel mounts
  - Initialises activeView = 'byTeam' (default)
  - showGuide = false (collapsed)
       |
       v
usePitStopsQuery fires
  - Query key: ['race', 'pitStops', '2025_24_Race']
  - Calls fetchPitStops('2025_24_Race')
       |
       v
GET /race/pit-stops?session=2025_24_Race
       |
       v
get_pit_stops() route handler
  - Calls await get_processed_race_data('2025_24_Race')
    [Phase 1 pipeline: classify -> fuel correct -> traffic -> stints -> pit stops]
  - Extracts pit_stops from cached pipeline output
  - Calls analyse_pit_stops(pit_stops)
       |
       v
analyse_pit_stops()
  - Separates normal stops from anomalies (is_anomaly flag from Phase 1)
  - Computes team_aggregates (avg time, count, tiered consistency)
  - Computes driver_aggregates (avg time, count)
  - Computes gap_to_fastest (delta from fastest team)
  - Computes grid_average (mean of all normal stop times)
  - Computes insights (quickest team, most consistent team)
  - Collects anomaly_notes (flagged stops with metadata)
       |
       v
PitStopAnalysisResponse JSON (camelCase via CamelCaseModel)
  - stops, teamAggregates, driverAggregates, gapToFastest,
    gridAverage, fastestTeam, insights, anomalyNotes
       |
       v
PitStopPanel receives data
  - Renders header with PitStopViewTabs
  - Renders active chart (PitStopByTeam by default)
  - Conditionally renders PitStopAnomalyNote (if anomalies exist)
  - Renders PitStopInsights (two template-based cards)
  - Renders "How to read this chart" expandable guide
```

### 3.2 View Switching Flow (Client-Side Only)

```
User clicks "By Driver" tab
       |
       v
setActiveView('byDriver')
  - React state update only
  - NO backend refetch (same data, different slice)
       |
       v
PitStopByDriver renders with data.driverAggregates
  - ~20 horizontal bars, team-colour-coded
  - Dynamic height: Math.min(600, Math.max(200, count * 28 + 80))
```

```
User clicks "Gap to Fastest" tab
       |
       v
setActiveView('gapToFastest')
  - React state update only
       |
       v
PitStopGapToFastest renders with data.gapToFastest
  - Vertical bars, fastest team shows "Fastest" label at 0.000s
  - All others show "+X.XXXs" labels
```

### 3.3 GP Switching Flow

```
User selects Baku GP from navigation selector
       |
       v
URL changes: /race?season=2025&round=17
       |
       v
RaceContent re-renders with new round
  - New sessionId = "2025_17_Race"
       |
       v
usePitStopsQuery fires with new query key
  - ['race', 'pitStops', '2025_17_Race']
  - placeholderData: keepPreviousData -> old Abu Dhabi data remains at 50% opacity
       |
       v
New Baku data arrives
  - isPlaceholderData = false -> opacity transitions to 100%
  - Charts render with Baku 2025 pit stop data
  - activeView preserved (user stays on whichever tab they were viewing)
```

### 3.4 Data Flow Through the Aggregation Service

```
List[PitStopResponse]               (from Phase 1 extract_pit_stops)
       |
       v
Split: normal_stops / anomalies     (filter on is_anomaly flag)
       |
       +---> Team Aggregates
       |       Group by team -> avg, count, tiered consistency
       |       Sort ascending by average time
       |
       +---> Driver Aggregates
       |       Group by driver -> avg, count
       |       Sort ascending by average time
       |
       +---> Gap to Fastest
       |       fastest_avg = team_aggregates[0].average
       |       gap = each_team.average - fastest_avg
       |
       +---> Grid Average
       |       mean(all normal stop times)
       |
       +---> Insights
       |       quickest: team_aggregates[0] with pct_faster
       |       most_consistent: min(consistency) across all teams with non-null value
       |
       +---> Anomaly Notes
               metadata for each flagged stop
```

---

## 4. Technical Implementation Breakdown

### 4.1 Files Created

| File | Lines | Purpose | Key Exports |
|------|-------|---------|-------------|
| `services/race/pit_stop_analysis.py` | 210 | Aggregation service | `analyse_pit_stops()` |
| `components/race/PitStopPanel.tsx` | 209 | Main orchestrator panel | `PitStopPanel` |
| `components/race/PitStopViewTabs.tsx` | 46 | Three-tab switcher | `PitStopViewTabs`, `PitStopView` |
| `components/race/PitStopByTeam.tsx` | 82 | Horizontal bar chart (teams) | `PitStopByTeam` |
| `components/race/PitStopByDriver.tsx` | 83 | Horizontal bar chart (drivers) | `PitStopByDriver` |
| `components/race/PitStopGapToFastest.tsx` | 82 | Vertical bar chart (gap) | `PitStopGapToFastest` |
| `components/race/PitStopInsights.tsx` | 86 | Template-based insight cards | `PitStopInsights` |
| `components/race/PitStopAnomalyNote.tsx` | 33 | Anomaly note text | `PitStopAnomalyNote` |
| `lib/hooks/usePitStopsQuery.ts` | 24 | React Query hook | `usePitStopsQuery` |
| `tests/test_pit_stop_analysis.py` | 267 | 15 unit tests | `TestAnalysePitStops` |

### 4.2 Files Modified

| File | Change | Impact |
|------|--------|--------|
| `routes/race.py` | Added `GET /pit-stops` endpoint with `PitStopAnalysisResponse` | New API surface for Phase 4 |
| `models/dto.py` | Added 8 DTOs: `TeamPitStopAggregate`, `DriverPitStopAggregate`, `GapToFastest`, `PitStopQuickestInsight`, `PitStopConsistencyInsight`, `PitStopInsights`, `AnomalyNote`, `PitStopAnalysisResponse` | Backend response schema |
| `packages/models/src/types.ts` | Added 8 matching TypeScript interfaces | Frontend type safety |
| `lib/api.ts` | Added `fetchPitStops()` | API client function |
| `lib/hooks/queryKeys.ts` | Added `race.pitStops()` key factory | Cache key for React Query |
| `app/race/RaceContent.tsx` | Added `<PitStopPanel>` section | Panel integration |

### 4.3 Backend Aggregation Service (`pit_stop_analysis.py`)

The service implements a single-pass aggregation pipeline that transforms a flat list of `PitStopResponse` objects into the full analysis response. The core function signature:

```python
def analyse_pit_stops(pit_stops: List[PitStopResponse]) -> Dict[str, Any]:
```

**Input:** `List[PitStopResponse]` — Pydantic model objects (not dicts) with attribute access (`.pit_lane_time`, `.is_anomaly`, `.team`, `.driver`, `.stop_number`, `.lap_number`).

**Processing stages:**

**Stage 1 — Anomaly Separation:**
```python
normal_stops = [s for s in pit_stops if not s.is_anomaly]
```
The anomaly flag was already set by Phase 1's `extract_pit_stops()`. This service consumes it rather than re-computing it.

**Stage 2 — Team Aggregation with Tiered Consistency:**
```python
team_times: Dict[str, List[float]] = defaultdict(list)
for stop in normal_stops:
    if stop.pit_lane_time is not None:
        team_times[stop.team].append(stop.pit_lane_time)

for team, times in team_times.items():
    times_arr = np.array(times)
    count = len(times)
    if count >= 3:
        consistency = round(np.percentile(times_arr, 75) - np.percentile(times_arr, 25), 3)
        consistency_type = 'iqr'
    elif count == 2:
        consistency = round(abs(float(times_arr[0]) - float(times_arr[1])), 3)
        consistency_type = 'range'
    else:  # count == 1
        consistency = None
        consistency_type = None
```

The tiered logic maps directly to the theoretical model: IQR for statistically meaningful samples, absolute difference for pairs, null for singletons.

**Stage 3 — Driver Aggregation:**
Groups by driver, computes mean pit lane time per driver. Simpler than team aggregation because consistency is only computed at team level (crew performance is a team attribute).

**Stage 4 — Gap to Fastest:**
```python
fastest_team_avg = team_aggregates[0]['average_pit_lane_time']
gap = each_team_avg - fastest_team_avg
```
The fastest team always has `gap_to_fastest = 0.0`. All gaps are non-negative.

**Stage 5 — Insight Computation:**
Deterministic selection of quickest (always `team_aggregates[0]`, since sorted ascending) and most consistent (minimum `consistency` value across all teams with non-null consistency, regardless of whether computed via IQR or range).

**Stage 6 — Anomaly Notes:**
Metadata extraction from anomaly-flagged stops for display in the UI.

**Edge case handling:**
- Empty input → returns `_empty_response()` with all arrays empty and null fields
- All stops anomalous → empty aggregates, null `fastest_team`, null insights
- `None` pit lane times → filtered from aggregation without crashing
- Single-team data → grid average equals that team's average

### 4.4 Data Transfer Objects (`dto.py`)

Eight Pydantic models define the response schema, all extending `CamelCaseModel`:

```
PitStopAnalysisResponse
  ├── stops: List[PitStopResponse]              # All stops (pass-through)
  ├── team_aggregates: List[TeamPitStopAggregate]
  │     ├── team: str
  │     ├── average_pit_lane_time: float
  │     ├── stop_count: int
  │     ├── consistency: Optional[float]         # IQR or abs diff or null
  │     └── consistency_type: Optional[str]      # 'iqr' | 'range' | null
  ├── driver_aggregates: List[DriverPitStopAggregate]
  │     ├── driver: str
  │     ├── team: str
  │     ├── average_pit_lane_time: float
  │     └── stop_count: int
  ├── gap_to_fastest: List[GapToFastest]
  │     ├── team: str
  │     └── gap_to_fastest: float
  ├── grid_average: float
  ├── fastest_team: Optional[str]
  ├── insights: PitStopInsights
  │     ├── quickest: Optional[PitStopQuickestInsight]
  │     │     ├── team, average_time, percentage_faster, grid_average
  │     └── most_consistent: Optional[PitStopConsistencyInsight]
  │           ├── team, consistency, consistency_type
  └── anomaly_notes: List[AnomalyNote]
        ├── driver, team, stop_number, lap_number, pit_lane_time
```

### 4.5 API Endpoint (`race.py`)

```python
@router.get("/pit-stops", response_model=PitStopAnalysisResponse)
async def get_pit_stops(
    session: str = Query(..., description="Session ID, e.g. 2025_17_Race"),
):
    race_data = await get_processed_race_data(session)
    pit_stops = race_data.get('pit_stops', [])
    return analyse_pit_stops(pit_stops)
```

Key design decisions:
- **No parameters beyond session:** Unlike tyre degradation (which accepts `fuel_effect` and `mode`), pit stop analysis has no configurable dimensions. The single session parameter is sufficient.
- **Async handler:** `get_processed_race_data()` is async, so the handler must `await` it.
- **Shared data service:** The Phase 1 pipeline runs once and caches. This endpoint extracts the `pit_stops` slice from the cached result — no redundant computation.

### 4.6 Frontend Panel Orchestrator (`PitStopPanel.tsx`)

The orchestrator manages two pieces of state:
- `activeView: PitStopView` — which chart is visible (`'byTeam'` | `'byDriver'` | `'gapToFastest'`)
- `showGuide: boolean` — whether the explanation section is expanded

**Progressive rendering states:**
1. **Loading (no prior data):** `PitStopSkeleton` — matches panel dimensions
2. **Error:** Clear error message with error details
3. **Empty data:** "No pit stop data available for this session"
4. **Placeholder data:** Previous GP data at 50% opacity during transition (`isPlaceholderData`)
5. **Ready:** Full panel with chart, anomaly notes, insights, and guide

**Component tree:**
```
PitStopPanel
  ├── PitStopViewTabs (three-tab switcher)
  ├── [Active chart view]
  │     ├── PitStopByTeam (horizontal bars, ~10 teams)
  │     ├── PitStopByDriver (horizontal bars, ~20 drivers)
  │     └── PitStopGapToFastest (vertical bars, ~10 teams)
  ├── PitStopAnomalyNote (conditional, only when anomalies exist)
  ├── PitStopInsights (two template-based cards)
  └── "How to read this chart" (expandable guide, 4 sections)
```

### 4.7 Chart Components

**`PitStopByTeam` — Horizontal Bar Chart (Teams)**

Plotly horizontal bars showing team-averaged pit lane times. Data arrives pre-sorted ascending from the API; the array is reversed because Plotly renders horizontal bars bottom-to-top (the fastest team appears at the top). Height is dynamically computed: `Math.min(400, Math.max(200, count * 35 + 80))`.

Colour coding uses `getTeamColorForMode(team, 'team')` — a critical correction discovered during implementation. The standard `getTeamColor()` function accepts driver abbreviations only. `getTeamColorForMode` accepts team names when called with `'team'` mode.

**`PitStopByDriver` — Horizontal Bar Chart (Drivers)**

Same pattern as By Team but for ~20 drivers. Height clamped to 600px: `Math.min(600, Math.max(200, count * 28 + 80))`. Left margin set to 80px (vs 120px for teams) since driver codes are shorter than team names.

**`PitStopGapToFastest` — Vertical Bar Chart**

Teams on x-axis, gap to fastest on y-axis. Fixed height of 350px. The fastest team shows "Fastest" as its text label; all others show "+X.XXXs". X-axis labels are rotated -45° for readability. A zeroline at y=0 provides visual anchoring.

### 4.8 Insight Cards (`PitStopInsights.tsx`)

Two cards in a responsive grid (`grid-cols-1 sm:grid-cols-2`):

**Quickest on Average card:**
- Team-coloured left border (3px) via `getTeamColorForMode`
- Displays team name, average time, percentage faster than grid, grid average
- All values from pre-computed `PitStopQuickestInsight` data

**Most Consistent card:**
- Template selection via `buildConsistencyText()` — branches on `consistencyType`
- IQR template: explains that "the middle 50% of their pit stop times fall within this very narrow window"
- Range template: plain language about "separating their two pit stops"
- No statistical jargon in the range variant since the user can intuitively understand "0.016s between two stops"

### 4.9 Anomaly Note (`PitStopAnomalyNote.tsx`)

Minimal component that renders only when `anomalies.length > 0`. Deliberately understated — faded text (`text-xs text-gray-500`), subtle top border — so it doesn't compete with the main charts. Lists each flagged stop with driver code, stop number, lap number, and pit lane time.

### 4.10 Expandable User Guide

An expandable "How to read this chart" section following the exact pattern established by `RacePaceBoxPlot.tsx` and `TyreDegradationPanel.tsx`:

- `useState(false)` for collapse/expand state
- Rotating arrow indicator (`▶` → rotated 90° when expanded)
- `aria-expanded` for accessibility
- Container: `border border-white/10 bg-white/[0.02]` for subtle background
- Four sections:
  1. **What is pit lane time?** — Defines the metric for non-F1 audiences
  2. **Three chart views** — Explains each tab's perspective
  3. **Insight cards** — Explains both cards including the tiered consistency logic
  4. **Anomalous stops** — Explains automatic detection and exclusion

### 4.11 React Query Hook (`usePitStopsQuery.ts`)

```typescript
export function usePitStopsQuery(sessionId: string | undefined) {
  return useQuery<PitStopAnalysisResponse>({
    queryKey: queryKeys.race.pitStops(sessionId ?? ''),
    queryFn: () => fetchPitStops(sessionId!),
    enabled: !!sessionId,
    placeholderData: keepPreviousData,
  })
}
```

Design decisions:
- **Simplest query key of all race hooks:** Only `sessionId` — no fuel effect, no mode. Pit stop data has no configurable dimensions, so the key has no structured parameters.
- **No refetch triggers beyond GP switching:** All view changes are client-side state.
- **`keepPreviousData`:** Enables smooth opacity transition during GP switching.
- **TODO (Phase 6):** Wrap with `useVisibilityQuery` for Intersection Observer deferred loading. The Pit Stop panel is below the fold — it should only begin fetching when the user scrolls near it.

### 4.12 API Client and Query Keys

**`fetchPitStops()`** in `api.ts`:
```typescript
export async function fetchPitStops(
  sessionId: string,
): Promise<PitStopAnalysisResponse> {
  const params = new URLSearchParams({ session: sessionId })
  return fetchApi<PitStopAnalysisResponse>(
    `${API_BASE_URL}/race/pit-stops?${params}`
  )
}
```

**Query key factory** in `queryKeys.ts`:
```typescript
pitStops: (sessionId: string) =>
  ['race', 'pitStops', sessionId] as const,
```

### 4.13 Integration in RaceContent

The panel mounts as a section in `RaceContent.tsx`:

```tsx
{/* Phase 4: Pit Stop Analysis */}
<section>
  <PitStopPanel sessionId={sessionId} />
</section>
```

Only `sessionId` is passed as a prop. The panel manages all its own internal state (active view, guide toggle). No state leaks to the parent, no URL parameters needed (pit stop views are transient — unlike Phase 3's mode/driver/compound selections which benefit from URL persistence for shareability).

### 4.14 Unit Test Coverage

15 tests in `test_pit_stop_analysis.py` covering:

| Test | What It Validates |
|------|-------------------|
| `test_empty_input_returns_empty_response` | Graceful handling of no data |
| `test_basic_aggregation_two_teams` | Team averages, sorting, gap to fastest |
| `test_anomalies_excluded_from_averages` | Anomaly flag respected in aggregation |
| `test_tiered_consistency_iqr_for_three_plus_stops` | IQR computed for ≥3 stops |
| `test_tiered_consistency_range_for_two_stops` | Absolute difference for exactly 2 stops |
| `test_tiered_consistency_null_for_one_stop` | Null for single observation |
| `test_tiered_consistency_mixed_strategies` | IQR and range teams compared correctly for insight |
| `test_insight_quickest_team` | Quickest insight data accuracy |
| `test_insight_most_consistent_one_stop_race` | Range-type consistency in one-stop race |
| `test_insight_most_consistent_null_when_all_single_stop` | No insight when every team has 1 stop |
| `test_driver_aggregates_sorted_by_time` | Driver sort order correctness |
| `test_none_pit_lane_time_handled` | Null pit_lane_time doesn't crash |
| `test_all_stops_anomalous` | Empty aggregates when all stops flagged |
| `test_grid_average_excludes_anomalies` | Grid average only uses normal stops |
| `test_stops_passthrough_includes_all` | Original stops preserved in response |

All tests use a `_make_stop()` helper that creates `PitStopResponse` Pydantic objects, ensuring tests exercise the actual attribute-access pattern used by the service.

---

## 5. Critical Path Corrections

During the planning phase, a thorough codebase diagnostic revealed eight discrepancies between the implementation specification and the actual codebase. These were identified before writing any code, preventing errors that would have required debugging:

| # | Specification Assumed | Actual Codebase | Correction Applied |
|---|---|---|---|
| 1 | DTOs in `apps/api/services/race/dto.py` | DTOs live in `apps/api/app/models/dto.py` | All DTOs added to the correct centralised file |
| 2 | Types in `apps/web/types.ts` | Types live in `packages/models/src/types.ts` | All interfaces added to the shared monorepo package |
| 3 | PlotlyLazy at `@/components/PlotlyLazy` | PlotlyLazy at `@/components/charts/PlotlyLazy` | Correct import path in all chart components |
| 4 | `getTeamColor(team)` for team colours | `getTeamColor()` accepts driver abbreviations only | Used `getTeamColorForMode(team, 'team')` throughout |
| 5 | Hooks in `apps/web/hooks/` | Hooks in `apps/web/lib/hooks/` | Correct directory for hook file and queryKeys |
| 6 | `bg-f1dark-800` for panel background | `f1dark` is a flat colour (no shade variants) | Used `card-panel` CSS class (existing pattern) |
| 7 | Pit stops as `List[Dict]` | Pit stops as `List[PitStopResponse]` (Pydantic objects) | Used attribute access (`.pit_lane_time`) not dict access (`['pit_lane_time']`) |
| 8 | `get_processed_race_data()` is synchronous | `get_processed_race_data()` is async | Added `await` in the route handler |

The diagnostic process — reading existing code to verify assumptions before implementing — is a pattern that Phase 3's learnings reinforced. The cost of a thorough pre-implementation diagnostic is far lower than the cost of debugging cascading type errors or import failures after hundreds of lines of code are written.

---

## 6. Docker Integration Validation

### 6.1 Validation Process

After all code was written and unit tests passed (15/15 local, 109/109 full suite), Docker-based integration validation exercised the endpoint with live FastF1 data across three races with different characteristics:

| Race | Characteristics | Purpose |
|------|----------------|---------|
| Abu Dhabi 2025 (R24) | Clean race, no anomalies, mixed strategy | Baseline validation |
| Baku 2025 (R17) | Street circuit, 1-stop race for most teams | Validates null consistency for 1-stop teams |
| Monaco 2025 (R8) | Long race, many pit stops, anomalies present | Validates anomaly detection and IQR consistency |

### 6.2 Validation Results

**Abu Dhabi 2025:**
- 27 stops, 10 teams, 20 drivers, 0 anomalies
- Fastest: McLaren (21.416s), Most consistent: Williams (IQR 0.029s)
- Tiered consistency: 4 teams with IQR (≥3 stops), 6 teams with range (2 stops)
- Grid average matched manual calculation within 0.0002s

**Baku 2025:**
- 21 stops, 10 teams, 0 anomalies
- McLaren had 1 stop → consistency = null, consistencyType = null ✓
- Fastest: Racing Bulls (20.248s), Most consistent: Red Bull Racing (range 0.016s)
- All sorting verified ascending across all three arrays

**Monaco 2025:**
- 41 stops, 10 teams, **2 anomalies detected:**
  - BOR Stop 1, Lap 1: 37.316s (flagged as anomaly, excluded from averages) ✓
  - BEA Stop 1, Lap 1: 50.169s (flagged as anomaly, excluded from averages) ✓
- BOR's team aggregate correctly uses only 2 non-anomalous stops (24.525s, 24.443s → avg 24.484s)
- GAS has a null `pitLaneTime` stop → handled gracefully, filtered from aggregates ✓
- All 10 teams use IQR consistency (most teams had ≥3 non-anomalous stops in this longer race)

### 6.3 Cross-Endpoint Regression Check

Existing endpoints verified working alongside the new endpoint:
- `GET /race/pace?session=2025_24_Race` → 200, 20 drivers ✓
- `GET /race/tyre-degradation?session=2025_24_Race` → 200 ✓
- `GET /race/pit-stops?session=2025_24_Race` → 200 ✓
- OpenAPI spec (`/openapi.json`) lists all three race endpoints ✓

### 6.4 Frontend Build Verification

- Next.js compilation: 0 errors ✓
- Race page bundle: 13.6 kB + 197 kB First Load JS ✓
- `PitStopPanel` references found in compiled race page chunk ✓
- `pitLaneTime`, `pitStops` tokens present in race page JavaScript bundle ✓
- Race page serves HTTP 200 from web container ✓

---

## 7. Learnings and How They Influenced Decisions

### 7.1 Pre-Implementation Diagnostics Prevent Cascading Errors

The eight critical path corrections (Section 5) were all discovered through a thorough codebase diagnostic before writing any code. Had these been discovered during implementation, each would have required tracing through already-written code to fix — import path errors cascade through every file, Pydantic attribute access vs dict access produces runtime errors only, and async/sync mismatches cause silent failures.

**Influence:** The diagnostic process is now an established step in the Phase workflow. For Phase 5 (Team Performance), the same pattern will be followed: read existing code, verify every assumption from the specification, document corrections, and only then begin implementation.

### 7.2 Pydantic Objects Require Attribute Access, Not Dict Access

The Phase 1 `extract_pit_stops()` function returns `List[PitStopResponse]` — Pydantic model instances. The initial specification treated these as dictionaries (`stop['pit_lane_time']`). The diagnostic caught this: Pydantic objects use attribute access (`stop.pit_lane_time`). This distinction is invisible in Python's duck typing until runtime, where `stop['pit_lane_time']` raises `TypeError: 'PitStopResponse' object is not subscriptable`.

**Influence:** All new services that consume Phase 1 data should verify the return types of the shared data service. The test helper `_make_stop()` creates actual `PitStopResponse` objects (not dicts), ensuring unit tests catch attribute-access issues.

### 7.3 getTeamColor vs getTeamColorForMode

The qualifying page exclusively uses `getTeamColor(driverAbbreviation)` because qualifying data is always indexed by driver. Pit stop analysis aggregates by team name, requiring `getTeamColorForMode(teamName, 'team')`. This function was already in the codebase (used by Phase 3's team mode) but not mentioned in the Phase 4 specification.

**Influence:** Any future component that displays team-level data (Phase 5's Team Performance Quadrant will be exclusively team-level) must use `getTeamColorForMode` from the start.

### 7.4 The Tiered Consistency Design Emerged from Edge Case Analysis

The original specification used IQR universally. During planning review, the question arose: "What happens in a one-stop race where most teams have only 2 stops?" The answer was that IQR would be undefined for all 2-stop teams, leaving the "Most Consistent" insight card empty for the majority of races. The tiered approach (IQR ≥3, range for 2, null for 1) was designed as a direct response to this edge case.

The Monaco validation proved the design correct in the opposite direction: in a long race with many stops, all teams had ≥3 non-anomalous stops, so all used IQR. The Baku validation proved the one-stop edge case: McLaren had exactly 1 stop, correctly receiving null consistency.

**Influence:** Edge case analysis during planning — particularly with real-world race scenarios in mind — catches design issues that synthetic test cases miss. Future phases should explicitly enumerate race types (one-stop, multi-stop, safety car, red flag) and verify the design handles each.

### 7.5 Single API Response with Client-Side Switching Simplifies Both Ends

Phase 3 taught that backend refetches add latency and complexity (different query keys, loading states during toggles, cache management). Phase 4's design deliberately avoids refetches: all three chart views consume different slices of the same response. Switching tabs is a React state change — instantaneous, no skeleton, no opacity transition.

**Influence:** Phase 5 (Team Performance) should follow the same pattern where possible. If the three sub-charts (top speed divergence, mean speed divergence, quadrant scatter) can all be derived from the same aggregated response, a single endpoint with client-side switching is preferable.

### 7.6 Template-Based Insights Scale to Multiple Metric Types

The anti-hallucination template pattern from the qualifying page's Phase 5 adapted cleanly to the Race page. The key extension was the dual template for consistency — different wording based on `consistencyType`. This shows that template-based insights can handle conditional logic (not just simple slot-filling) while remaining fully deterministic.

**Influence:** Phase 5's team performance insights (if any) should use the same template approach with branching logic based on computed classification (e.g., "High Efficiency" vs "High Downforce" quadrant).

### 7.7 Docker Build Cache Requires Explicit Invalidation on Windows

The web container's `docker compose build web` returned all CACHED layers even after source files changed. This was a repeat of the issue discovered in Phase 3. Docker BuildKit's cache invalidation for the `COPY . .` layer is unreliable on Windows/OneDrive. `docker compose build --no-cache web` is required when verifying code changes.

**Influence:** The Docker validation workflow should always use `--no-cache` for the web container. The API container was not affected (its `COPY` layer correctly detected changes).

---

## 8. Alignment with Broader Race Page Plan

### 8.1 Patterns Validated and Extended

| Pattern | Origin | Phase 4 Validation |
|---------|--------|--------------------|
| React Query hook per panel | Phase 2 | Simplest hook variant — session only, no params |
| `keepPreviousData` for GP switching | Phase 2 | Smooth opacity transition works with bar charts |
| PlotlyLazy for all charts | Phase 2 | Three chart types (horiz bars × 2, vert bars × 1) rendered correctly |
| `card-panel` CSS class | Phase 2 | Panel styling consistent across all four race panels |
| Server-side computation | Phase 2/3 | All aggregation in FastAPI, frontend renders only |
| Anti-hallucination insights | Qualifying P5 | Template-based cards with branching logic for consistency type |
| Single API response, client-side switch | **New in Phase 4** | Three views from one response, instant switching |
| Expandable user guide | Phase 2/3 | Same `useState` + rotating arrow pattern, 4 sections |

### 8.2 Infrastructure Extended for Phase 5

| Asset | Created/Extended | Available To |
|-------|-----------------|-------------|
| `queryKeys.race.pitStops()` | Phase 4 | Pattern for `race.teamPerf()` |
| `fetchPitStops()` | Phase 4 | Pattern for `fetchTeamPerformance()` |
| `PitStopViewTabs` pattern | Phase 4 | Tab switcher reusable for any multi-view panel |
| `getTeamColorForMode` usage | Phase 4 (validated) | Required by Phase 5's team-level charts |
| Pre-implementation diagnostic process | Phase 4 (formalised) | Standard workflow for Phase 5 |
| Single-response client-switching | Phase 4 (established) | Applicable if Phase 5 sub-charts share an endpoint |

### 8.3 Deferred to Phase 6

| Feature | Deferred To | Reason |
|---------|------------|--------|
| `useVisibilityQuery` (Intersection Observer) | Phase 6 | Below-fold deferred loading for pit stop panel |
| `staleTime: Infinity` for query | Phase 6 | Performance optimisation, not functional |
| `gcTime: 30min` for query | Phase 6 | Memory management, not functional |
| Prefetch on Race nav hover | Phase 6 | Performance optimisation |
| Lighthouse audit | Phase 6 | Performance validation |
| URL state for active view | Not planned | View selection is transient, not worth sharing |

### 8.4 Shared Data Service Efficiency

Phase 4 continues the shared data service pattern established in Phase 1. The `get_processed_race_data()` pipeline runs once per session and caches the enriched dataset. Phase 2 queries the pace statistics slice, Phase 3 queries the per-lap fuel-corrected data for regression, and Phase 4 queries the `pit_stops` list for aggregation. All three features consume the same cached pipeline output through different processing paths — no redundant session loading or lap classification occurs.

### 8.5 Race Page Feature Completion

With Phase 4 complete, four of six phases are delivered:

| Phase | Feature | Charts | Status |
|-------|---------|--------|--------|
| 1 | Data Foundation | — | Complete |
| 2 | Race Pace Distribution | 1 (box plot) | Complete |
| 3 | Tyre Degradation | 2 (scatter + bar) | Complete |
| **4** | **Pit Stop Analysis** | **3 (horiz × 2 + vert × 1)** | **Complete** |
| 5 | Team Performance Quadrant | 3 (div × 2 + scatter × 1) | Planned |
| 6 | Performance & Integration | — | Planned |

The Race page is now functionally rich with three independent analytical panels covering pace, tyre management, and operational execution. Phase 5 will add the final car-characterisation dimension, and Phase 6 will optimise the complete page for performance.

---

*Documentation Version 1.0 — February 2026*
