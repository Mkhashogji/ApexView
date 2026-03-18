# Race Page Phase 2: Race Pace Distribution

**Status:** Complete (with post-initial visual refinements and interactivity enhancements)
**Implemented:** February 2026
**Test Baseline:** 61/61 backend tests passing (38 transform + 21 service + 2 integration)
**TypeScript:** Zero compilation errors
**Next.js Build:** Compiled successfully (8/8 static pages generated)
**Qualifying Regression:** Zero modified qualifying files
**Document Version:** 2.0

---

## Table of Contents

1. [Purpose and Significance](#1-purpose-and-significance)
2. [Theoretical and Logical Background](#2-theoretical-and-logical-background)
3. [End-to-End Workflow and Data Flow](#3-end-to-end-workflow-and-data-flow)
4. [Technical Implementation Breakdown](#4-technical-implementation-breakdown)
5. [Visual Refinement and Interactivity Enhancements](#5-visual-refinement-and-interactivity-enhancements)
6. [Issues Encountered and Resolved](#6-issues-encountered-and-resolved)
7. [Test Coverage and Verification](#7-test-coverage-and-verification)
8. [Alignment with Broader Race Page Plan](#8-alignment-with-broader-race-page-plan)

---

## Recent Changes (Since Document Version 1.0)

| Area | Status | Details |
|------|--------|---------|
| **Visual Refinement** | Complete | X-axis simplified to driver code only; enrichment moved to summary strip and custom tooltips |
| **Driver Summary Strip** | Complete | Two-section card design with team-coloured headers and F1-standard compound colours |
| **React Header + Team Legend** | Complete | Title/subtitle and colour-coded team legend rendered above chart in React (not inside Plotly) |
| **Two-Tier Custom Tooltips** | Complete | Summary (box hover) vs detailed (whisker hover) vs outlier; replaces Plotly built-in tooltips |
| **Brush-to-Zoom** | Complete | Click-drag rectangle zoom on both axes; scroll wheel zoom; double-click reset |
| **Zoom State Persistence** | Complete | `useMemo` for traces/layout/config prevents tooltip-driven re-renders from resetting zoom |
| **How to Read Guide** | Complete | Expanded to 4 structured sections: box plot anatomy, hover guide, zoom guide, fuel correction |
| **Plotly Box Rendering Bug Fix** | Complete | Removed `y` array that triggered Plotly case '11' invisible-box bug |
| **PlotlyLazy.tsx** | Modified | Added `onUnhover` prop to interface for custom tooltip dismissal |
| **Mode Bar** | Changed | Appears on hover (was hidden); includes zoom/pan/auto-scale/reset |

---

## 1. Purpose and Significance

### What Phase 2 Delivers

Phase 2 implements the **Race Pace Distribution** box plot — the primary analytical feature of the Race page and the first frontend deliverable for race analysis. It transforms the validated Phase 1 data pipeline into an interactive visual surface that users can explore and interact with.

The box plot shows every driver's fuel-corrected race pace distribution, sorted by mean lap time (fastest left to right), colour-coded by team, with enriched metadata including tyre strategy, finishing position, consistency score, traffic exposure, and gap-to-fastest. Each driver's box represents their fuel-corrected lap time spread across the race, with whiskers showing the realistic pace range and outlier dots representing anomalous laps.

Beyond the visualisation itself, Phase 2 establishes the complete Race page frontend architecture: the SSR page shell, Suspense boundaries, the React Query hook pattern, the query key namespace, the API client function, the sidebar, the skeleton, and the progressive rendering infrastructure that all subsequent phases inherit.

### Why It Matters

**It is the highest-value analytical feature.** Race pace distribution is the single most commonly referenced metric in professional F1 post-race analysis. Every major analyst (FDataAnalysis, F1-Tempo, Motorsport.com) publishes race pace distributions within hours of each race. This panel communicates more about race performance than any other single visualisation — it reveals who had genuine pace versus who benefited from strategy, track position, or circumstance.

**It validates the Phase 1 pipeline end-to-end.** Phase 1 was entirely backend with synthetic test data validation. Phase 2 renders Phase 1's output visually. If the lap classification, fuel correction, traffic derivation, or statistical aggregation have subtle issues, the box plot makes them visible immediately — a driver's box appearing in the wrong position, outliers that should have been filtered, or gap-to-fastest values that contradict published analysis.

**It establishes the Race page frontend architecture.** Phase 2 is to the Race page what the qualifying page's initial build was to qualifying — it sets every pattern that Phases 3-5 will inherit. The React Query hooks, the API client functions, the page shell, the sidebar, the skeleton loading, the progressive rendering, the error boundaries, the GP selector integration — all of these are created in Phase 2 and reused (not recreated) in subsequent phases.

### Position in the Race Page Architecture

Phase 2 is the second of six planned phases:

| Phase | Name | Depends On | Status |
|-------|------|-----------|--------|
| 1 | Race Data Foundation | — | Complete |
| **2** | **Race Pace Distribution (Box Plot)** | **Phase 1** | **Complete** |
| 3 | Tyre Degradation Analysis | Phase 1 | Planned |
| 4 | Pit Stop Analysis | Phase 1 | Planned |
| 5 | Team Performance Quadrant | Phase 1 | Planned |
| 6 | Performance Optimization & Integration | Phases 1-5 | Planned |

Phase 2 consumes the `GET /race/pace` endpoint built in Phase 1. Phases 3-5 will create their own endpoints but follow the identical hook, query key, and panel patterns established by Phase 2.

---

## 2. Theoretical and Logical Background

### 2.1 What the Box Plot Communicates

A race pace box plot answers the question: **"How fast was each driver's car on race day, independent of strategy, incidents, and track position?"**

Each driver's box represents their fuel-corrected lap time distribution from RACING laps only (excluding pit laps, safety car laps, formation laps, and anomalous laps). The key statistical elements:

- **Median line** — The central tendency of the driver's pace. More robust than mean for small samples with outliers.
- **Box (Q1 to Q3)** — The interquartile range containing the middle 50% of laps. A narrow box indicates consistency; a wide box indicates pace variation (often due to tyre degradation across stints).
- **Whiskers** — Extend to the furthest data point within 1.5 x IQR of the box edges (Tukey standard). These show the realistic pace range.
- **Outlier dots** — ANOMALY-classified laps that exceeded the whisker threshold. Each represents a lap where something unusual happened — traffic, a mistake, a safety car restart with cold tyres.
- **Mean marker** — A diamond marker showing the arithmetic mean, rendered by Plotly's `boxmean: true` property. When the mean differs significantly from the median, it indicates skew — typically a few slow laps pulling the average up.

### 2.2 Mean-Based Sorting Decision

Drivers are sorted by **mean** lap time (fastest left, slowest right). This was validated during Phase 1 against the FDataAnalysis Baku 2025 benchmark, which confirmed that mean-based ordering matches published rankings within +/-1 position for drivers separated by less than 0.05 seconds.

The mean is used instead of the median because ANOMALY laps are excluded from the calculation upstream — the RACING dataset is clean by the time statistics are computed. With outliers already removed, the mean provides a more sensitive ordering than the median, especially for drivers with asymmetric tyre strategies (e.g., a short soft stint followed by a long hard stint, which shifts the median toward the hard-stint pace).

### 2.3 Fuel Correction Toggle

The box plot offers two views toggled by the user:

1. **Fuel-corrected** (default) — Lap times normalised to empty-tank equivalent using the circuit-specific fuel effect factor. This removes the approximately 3.5-second spread that fuel mass introduces across a race distance, revealing true pace degradation and driver performance. The corrected time for each lap is `corrected = raw_time - (fuel_remaining * fuel_effect_per_kg)`.

2. **Raw lap times** — Uncorrected times showing what actually happened on track. Useful for understanding actual time gaps between drivers at specific race moments.

The toggle works by passing different `fuel_effect` values to the API: the circuit-specific factor (e.g., 0.034 for Bahrain) when fuel-corrected, or `0` when raw. When `fuel_effect=0`, the fuel correction formula computes `corrected = raw - 0 = raw`, so the same code path handles both modes. React Query caches each variant independently because `fuelEffect` is part of the query key.

**Fuel correction implementation detail:** The backend uses a linear fuel-burn model. F1 cars start with approximately 110 kg of fuel, consuming around 2 kg per lap. Each kilogram adds a circuit-specific time penalty (0.028-0.036 s/kg from the Track Intelligence database). The correction subtracts the estimated fuel-mass penalty from each lap, normalising to an equivalent empty-tank condition. It applies only to RACING and ANOMALY laps; pit laps, safety car laps, and formation laps receive `null`. The model does not account for non-linear effects such as fuel flow rate changes or engine mode variations — this limitation is documented in the user-facing guide.

### 2.4 The Pace vs Position Insight

The box plot explicitly separates "how fast you drove" from "where you finished." This is the core analytical value proposition. In Formula 1:

- A driver can have excellent pace but finish poorly (bad strategy, penalties, incidents, qualifying position limiting overtaking opportunity)
- A driver can finish well with mediocre pace (defensive driving from a strong qualifying, benefiting from others' misfortune, optimal pit stop timing)

By showing pace rank (x-axis ordering) AND finishing position (summary strip card and tooltip) together, users gain insights that a simple race results table cannot provide.

### 2.5 Enrichment Metadata

Beyond the core statistical distribution, each driver's entry includes supplementary data displayed in the custom tooltips and driver summary strip:

| Metric | Source | Display Location | Purpose |
|--------|--------|-----------------|---------|
| **Finishing position** | `session.results` (FastF1) | Summary strip card + detailed tooltip | Context: pace rank vs actual result |
| **Gap to fastest** | Mean difference from fastest driver | Summary strip card + both tooltip tiers | Quantifies pace deficit per lap |
| **Tyre strategy** | Stint compound sequence | Summary strip card (coloured letters) + detailed tooltip | Compound context for pace variation |
| **Consistency score** | Mean of per-stint standard deviations | Detailed tooltip only | Lap-to-lap repeatability |
| **Laps in traffic** | Count where gap-to-car-ahead < 1.5s | Detailed tooltip only | Why pace might be worse than potential |
| **Total racing laps** | Count of RACING-classified laps | Detailed tooltip only | Sample size transparency |
| **IQR** | Derived: Q3 - Q1 | Detailed tooltip only | Width of the core pace band |
| **Outlier count** | Length of outliers array | Detailed tooltip only (when > 0) | Anomalous lap frequency |

### 2.6 Fuel-Corrected Statistics Fix

During Phase 2 implementation, a bug was identified and fixed in `compute_race_pace_stats()`. The function was using raw `lap_time` for all statistics (mean, median, Q1, Q3, whiskers, outliers, consistency score) instead of `fuel_corrected_time`. This meant that even when the user requested fuel-corrected analysis via the API, the statistics were computed from uncorrected times.

The fix changes all lap time references in the statistics computation to use `fuel_corrected_time` when available, falling back to `lap_time` when absent. When `fuel_effect=0`, `fuel_corrected_time` equals `lap_time` (since the correction formula subtracts zero), so raw mode is unaffected. This ensures the statistics accurately reflect whichever correction mode the user selects.

### 2.7 Available Metrics Inventory

The `DriverPaceData` TypeScript interface documents exactly which fields are available from the server:

```typescript
interface DriverPaceData {
  driver: string
  team?: string
  minTime: number       // Whisker lower bound (server-computed)
  q1: number            // First quartile
  median: number        // Median lap time
  mean: number          // Arithmetic mean
  q3: number            // Third quartile
  maxTime: number       // Whisker upper bound (server-computed)
  outliers: number[]    // Lap times beyond 1.5x IQR
  gapToFastest: number  // Mean delta to fastest driver
  tyreStrategy: string[] // Compound sequence (e.g., ['MEDIUM', 'HARD', 'HARD'])
  consistencyScore?: number  // Mean of per-stint standard deviations
  lapsInTraffic: number      // Laps within 1.5s of car ahead
  totalRacingLaps: number    // Count of RACING-classified laps
  finishingPosition?: number // Official race result position
}
```

**Not available from the server (omitted from tooltips):**
- `lowerFence` / `upperFence` — not stored as separate fields; `minTime`/`maxTime` serve as whisker bounds because the server filters outliers beyond 1.5x IQR before computing these values.
- `IQR` — not pre-computed; derived client-side as `q3 - q1` for the detailed tooltip.

---

## 3. End-to-End Workflow and Data Flow

### 3.1 User Interaction Flow

```
User navigates to /race (or /race?season=2025&round=17)
       |
       v
Server Component (page.tsx) renders SSR shell immediately
  - <h1> "Race Analysis" paints within FCP (~0.2s)
  - <p> subtitle renders
  - Suspense boundary shows RacePageSkeleton
       |
       v
Client Component (RaceContent.tsx) hydrates
  - Reads ?season and ?round from URL (useSearchParams)
  - Derives sessionId = "2025_17_Race"
  - Reads fuelEffectPerKg from Track Intelligence (static, sync)
  - Default state: fuelCorrected = true
       |
       +-- Computes fuelEffect = 0.034 (Bahrain example)
       |
       v
useRacePaceQuery(sessionId, fuelEffect) fires
  - Query key: ['race', 'pace', '2025_17_Race', { fuelEffect: 0.034 }]
  - Calls fetchRacePace('2025_17_Race', 0.034)
       |
       v
GET /race/pace?session=2025_17_Race&fuel_effect=0.034
       |
       v
[Phase 1 Pipeline runs -- classify, fuel correct, traffic, stints, pits]
       |
       v
compute_race_pace_stats(race_data)
  - Uses fuel_corrected_time for all statistics
  - Includes finishing_positions from session.results
  - Returns DriverPaceResponse[] sorted by mean
       |
       v
RacePaceResponse JSON (camelCase) -> Frontend
       |
       v
RacePaceBoxPlot renders:
  - React header (title + GP subtitle + team colour legend)
  - Plotly chart (one box trace per driver, team-coloured)
  - Custom tooltip overlay (summary/detailed/outlier tiers)
  - Driver summary strip (scrollable cards)
  - Collapsible "How to read this chart" guide
```

### 3.2 GP Switching Flow

When the user selects a different Grand Prix via the navigation:

```
URL changes: /race?season=2025&round=6
       |
       v
RaceContent re-renders with new season/round
  - New sessionId = "2025_6_Race"
  - New fuelEffectPerKg from Track Intelligence (Miami = 0.033)
       |
       v
useRacePaceQuery fires with new key
  - placeholderData: keepPreviousData -> old data remains
  - isPlaceholderData = true -> opacity drops to 50%
       |
       v
New data arrives -> isPlaceholderData = false
  - opacity transitions to 100% (CSS transition-opacity duration-300)
  - Box plot re-renders with new drivers/data
  - useMemo dependencies [drivers, fuelCorrected] change -> traces/layout recreated
  - Zoom state resets (correct behaviour: new data = new chart)
```

This provides a smooth visual transition without blank states during loading, matching the pattern established by the qualifying page.

### 3.3 Fuel Toggle Flow

When the user toggles the fuel correction checkbox:

```
fuelCorrected state flips: true -> false
       |
       v
fuelEffect recalculates: 0.034 -> 0
       |
       v
useRacePaceQuery fires with new query key
  - ['race', 'pace', '2025_17_Race', { fuelEffect: 0 }]
  - Different key from corrected version -> separate cache entry
       |
       v
GET /race/pace?session=2025_17_Race&fuel_effect=0
  - fuel_corrected_time = raw_time (correction = 0)
  - Statistics computed from raw times
       |
       v
Box plot updates with raw lap times
  - Y-axis label changes: "Lap Time (s)"
  - Driver ordering may shift (fuel effect doesn't affect all drivers equally)
  - useMemo dependencies change -> layout recreated with new y-axis title
```

Both the corrected and raw versions are cached independently by React Query. Toggling back and forth serves from cache without re-fetching.

### 3.4 Finishing Position Data Flow

Finishing positions are extracted at the data source level and propagated through the entire pipeline:

```
fastf1_client.py: get_race_laps()
  |
  +-- Fresh load: session.results DataFrame
  |     for each row: finishing_positions[Abbreviation] = int(Position)
  |
  +-- Cache hit: _derive_finishing_positions_from_laps(records)
        for each driver: find last lap -> use position field
  |
  v
Returns: { 'laps': [...], 'finishing_positions': {'VER': 1, 'NOR': 2, ...} }
  |
  v
race_data_service.py: get_processed_race_data()
  - Unpacks dict: raw_laps = result['laps'], finishing_positions = result['finishing_positions']
  - Passes finishing_positions through to result dict
  |
  v
race_data_service.py: compute_race_pace_stats()
  - Reads finishing_positions from race_data dict
  - Adds to each DriverPaceResponse: finishing_position = finishing_positions.get(driver)
  |
  v
DriverPaceResponse -> JSON -> DriverPaceData (TypeScript)
  - finishingPosition?: number
  |
  v
RacePaceBoxPlot
  - Summary strip card: "P1"
  - Detailed tooltip: "P1" (top-right of header row)
```

This design keeps finishing position as a per-driver attribute (not per-lap), extracted once from the authoritative source (`session.results`) and propagated alongside lap data rather than embedded in each of the 1,200+ lap records.

---

## 4. Technical Implementation Breakdown

### 4.1 Files Created

| File | Purpose | Key Exports |
|------|---------|-------------|
| `apps/web/lib/hooks/useRacePaceQuery.ts` | React Query hook for race pace data | `useRacePaceQuery(sessionId, fuelEffect?)` |
| `apps/web/app/race/page.tsx` | SSR Server Component page shell | `RacePage` (default export) |
| `apps/web/app/race/RacePageSkeleton.tsx` | Loading skeleton matching layout dimensions | `RacePageSkeleton` (default export) |
| `apps/web/app/race/RaceContent.tsx` | Client component orchestrating data fetching and panel rendering | `RaceContent` (default export) |
| `apps/web/components/race/RaceSidebar.tsx` | Sidebar with fuel correction toggle | `RaceSidebar` |
| `apps/web/components/race/RacePaceBoxPlot.tsx` | Plotly box plot with custom tooltips, zoom, summary strip, guide | `RacePaceBoxPlot` |

### 4.2 Files Modified

| File | Change | Impact |
|------|--------|--------|
| `apps/api/app/services/race/race_data_service.py` | Fixed stats to use `fuel_corrected_time`; added `finishing_position` propagation | Statistics now reflect fuel correction mode; finishing position available in response |
| `apps/api/app/services/telemetry/fastf1_client.py` | `get_race_laps()` returns dict with `finishing_positions`; added `_derive_finishing_positions_from_laps()` helper | Return type changed from `list` to `dict`; backward-compatible unpacking in caller |
| `apps/api/app/models/dto.py` | Added `finishing_position: Optional[int] = None` to `DriverPaceResponse` | New optional field in API response |
| `apps/api/app/services/mock_data.py` | `get_race_laps()` returns dict format with `finishing_positions` | Mock data matches live data shape |
| `apps/api/tests/test_race_data_service.py` | Fixed median/outlier assertions for fuel-corrected times; added 2 finishing_position tests | Test suite adapted to fuel-correction fix; new coverage for finishing position |
| `packages/models/src/types.ts` | Added `finishingPosition?: number` to `DriverPaceData` | TypeScript type matches backend DTO |
| `apps/web/lib/api.ts` | Added `fetchRacePace(sessionId, fuelEffect?)` | New API client function for race pace endpoint |
| `apps/web/lib/hooks/queryKeys.ts` | Added `race` namespace with `pace(sessionId, fuelEffect?)` | Query key factory extended for race queries |
| `apps/web/components/charts/PlotlyLazy.tsx` | Added `onUnhover` prop to `PlotProps` interface | Enables custom tooltip dismissal via Plotly unhover callback |

### 4.3 Server Component Shell (`page.tsx`)

The Race page follows the identical SSR pattern established by the qualifying page for optimal performance:

```tsx
export default function RacePage() {
  return (
    <div className="space-y-6">
      <header className="border-l-4 border-f1red pl-4">
        <h1>Race Analysis</h1>           {/* LCP element -- renders server-side */}
        <p>Race pace distribution...</p>
      </header>
      <Suspense fallback={<RacePageSkeleton />}>
        <RaceContent />                    {/* Client component -- streams in */}
      </Suspense>
    </div>
  )
}
```

The `<h1>` renders immediately via SSR, ensuring the First Contentful Paint occurs within ~0.2 seconds. The Suspense boundary wraps the client component so the page shell appears instantly while JavaScript hydrates and data loads. This is the same pattern that achieved 94-97 Lighthouse scores on the qualifying page.

### 4.4 Client Component (`RaceContent.tsx`)

The client component orchestrates all state, data fetching, and rendering:

**State Management:**
- URL state: `season` and `round` from `useSearchParams()` — the single source of truth for GP selection
- Local state: `fuelCorrected` boolean (default `true`) — controls the fuel correction toggle
- Derived: `sessionId` = `${season}_${round}_Race`, `fuelEffect` = circuit-specific factor or `0`

**Track Intelligence Integration:**
```typescript
const trackIntel = getTrackIntelligence(round)
const fuelEffectPerKg = trackIntel?.fuelEffectPerKg ?? 0.032
const fuelEffect = fuelCorrected ? fuelEffectPerKg : 0
```

`getTrackIntelligence()` is a synchronous lookup into the static Track Intelligence database (24 circuits). No async operation needed — the data is bundled at build time.

**Four-State Rendering Pattern:**

| Condition | Render |
|-----------|--------|
| `isLoading && !racePaceData` | Skeleton placeholder (450px pulse block) |
| `isError` | Error message with details |
| `racePaceData` present | `<RacePaceBoxPlot>` with data |
| No data, no loading | Empty state prompt |

The `isLoading && !racePaceData` guard ensures the skeleton shows only on initial load, not during refetches. During GP switches, `isPlaceholderData` triggers the opacity transition instead.

**Layout:**
```
flex flex-col lg:flex-row gap-6
  +-- RaceSidebar (lg:w-72, sticky)
  +-- main (flex-1, min-w-0)
        +-- card-panel with opacity transition
```

### 4.5 React Query Hook (`useRacePaceQuery.ts`)

```typescript
export function useRacePaceQuery(sessionId: string | undefined, fuelEffect?: number) {
  return useQuery<RacePaceResponse>({
    queryKey: queryKeys.race.pace(sessionId ?? '', fuelEffect),
    queryFn: () => fetchRacePace(sessionId!, fuelEffect),
    enabled: !!sessionId,
    placeholderData: keepPreviousData,
  })
}
```

**Design decisions:**
- `enabled: !!sessionId` prevents queries from firing before GP selection
- `placeholderData: keepPreviousData` shows stale data during GP switches (opacity transition)
- `fuelEffect` in the query key means fuel-corrected and raw versions are cached independently
- Returns the standard React Query tuple with `isPlaceholderData` for transition detection

### 4.6 Box Plot Component (`RacePaceBoxPlot.tsx`)

The most substantial frontend component (806 lines), responsible for transforming pre-aggregated statistics into an interactive Plotly visualisation with custom React tooltips, zoom controls, a driver summary strip, and an educational guide.

**Component Layout Structure:**

```
<div ref={containerRef} className="relative">
  +-- React header (h3 title + GP subtitle + team colour legend)
  +-- PlotlyLazy (box traces + outlier scatter + custom hover/unhover)
  +-- CustomTooltip overlay (positioned absolutely within container)
  +-- Driver summary strip (horizontally scrollable cards)
  +-- Collapsible "How to read this chart" guide (4 sections)
</div>
```

**Trace Architecture:**

One box trace per driver is required for individual team colouring (Plotly's default applies one colour to all boxes). Each trace uses pre-computed statistics rather than raw data arrays:

```typescript
{
  type: 'box',
  x: [d.driver],
  // y intentionally omitted -- see Section 6.1 for why
  lowerfence: [d.minTime],    // Whisker lower bound
  upperfence: [d.maxTime],    // Whisker upper bound
  q1: [d.q1],
  median: [d.median],
  q3: [d.q3],
  mean: [d.mean],
  boxmean: true,               // Shows diamond marker at mean
  boxpoints: false,            // Outliers handled by separate scatter trace
  fillcolor: teamColor + '4D', // 30% opacity team colour fill
  line: { color: teamColor, width: 1.5 },
  hoverinfo: 'none',           // Custom React tooltips instead of Plotly's built-in
}
```

Using Plotly's pre-computed box properties (`lowerfence`, `upperfence`, `q1`, `median`, `q3`) bypasses Plotly's internal statistics computation. This is essential because the server-side statistics use fuel-corrected times, IQR-based whiskers with the specific RACING/ANOMALY separation that Plotly would not replicate from raw data.

**CRITICAL: The `y` array must NOT be included.** See Section 6.1 for the full explanation of the Plotly dimension detection bug.

**Outlier Scatter Overlay:**

ANOMALY laps are rendered as a separate scatter trace with `circle-open` markers at size 6, ensuring visual consistency with the server-side classification. The scatter trace is only included when outliers exist.

**Memoisation Strategy (Zoom State Preservation):**

All Plotly props (`traces`, `layout`, `config`) are wrapped in `useMemo` to ensure referential stability:

```typescript
const traces = useMemo(() => { ... }, [drivers])
const layout = useMemo(() => { ... }, [drivers, fuelCorrected])
const config = useMemo(() => { ... }, [])
```

This prevents tooltip state changes (`setTooltip`) from triggering React re-renders that would cause Plotly to receive new prop objects. Without memoisation, each hover event would create a new layout object, causing Plotly to reset the user's zoom state. See Section 6.2 for the full diagnosis of this issue.

**Dark Theme Styling:**
- `paper_bgcolor` and `plot_bgcolor`: transparent (inherits page background)
- Y-axis grid: `rgba(255,255,255,0.08)` (subtle white at 8% opacity)
- X-axis grid: hidden (`showgrid: false`)
- Font colour: `#9CA3AF` (Tailwind gray-400)
- Tick font: `rgba(255,255,255,0.85)` (bright white for driver codes)
- Font family: Inter (matching the global self-hosted font)
- `displayModeBar: 'hover'` — toolbar appears only when hovering over chart area
- Box fills: team colour at 30% opacity (`+ '4D'`), with team-coloured borders at `width: 1.5`

### 4.7 Sidebar Component (`RaceSidebar.tsx`)

The sidebar provides page-specific controls. GP selection is handled by the global `RaceWeekendSelector` in the navigation bar (not duplicated in the sidebar).

**Content:**
- Section header: "Pace Correction" (uppercase, tracking-wide, matching qualifying sidebar style)
- Checkbox: "Fuel-corrected lap times" (controlled component bound to `fuelCorrected` state)
- Helper text: Dynamic description that changes based on toggle state

**Layout:** Sticky on large screens (`lg:sticky lg:top-16`) with overflow scrolling for content exceeding viewport height. Matches the qualifying sidebar's responsive pattern of full-width on mobile, fixed-width on desktop.

### 4.8 Skeleton Component (`RacePageSkeleton.tsx`)

The skeleton mirrors the exact layout structure of `RaceContent` to prevent Cumulative Layout Shift (CLS) during the Suspense transition:

- Sidebar skeleton: `lg:w-72` with pulse blocks matching fuel toggle dimensions
- Main content skeleton: `flex-1` with a 450px height pulse block matching the Plotly chart area

Uses the established `animate-pulse`, `bg-f1gray/20`, and `bg-f1gray/30` classes from the qualifying skeleton.

### 4.9 API Client and Query Keys

**`fetchRacePace(sessionId, fuelEffect?)`** in `api.ts`:
- Constructs URLSearchParams with `session` (required) and `fuel_effect` (optional)
- Uses the existing `fetchApi<T>()` generic helper with `ApiError` handling
- Targets `${API_BASE_URL}/race/pace` — the Phase 1 endpoint

**Query key namespace** in `queryKeys.ts`:
```typescript
race: {
  all: ['race'] as const,
  pace: (sessionId: string, fuelEffect?: number) =>
    ['race', 'pace', sessionId, { fuelEffect }] as const,
}
```

Including `fuelEffect` as an object property in the key means that corrected and raw queries produce different keys and are cached independently. With React Query's default `staleTime` and `gcTime`, both versions remain cached during a session — toggling the checkbox serves from cache without re-fetching.

### 4.10 Backend Changes: Finishing Position Pipeline

**`get_race_laps()` return type change (`fastf1_client.py`):**

The method's return type changed from `list` to `dict`:
```python
# Before (Phase 1):
return result  # list of lap dicts

# After (Phase 2):
return {'laps': result, 'finishing_positions': finishing_positions}
```

Finishing positions are extracted from `session.results` (FastF1's official results DataFrame) on fresh loads. On cache hits (Parquet), where session results are not available, the helper method `_derive_finishing_positions_from_laps()` approximates by finding each driver's last lap and using its `position` field.

**`get_processed_race_data()` unpacking (`race_data_service.py`):**

The caller handles both return formats for backward compatibility:
```python
if isinstance(raw_result, dict):
    raw_laps = raw_result.get('laps', [])
    finishing_positions = raw_result.get('finishing_positions', {})
else:
    raw_laps = raw_result if raw_result else []
    finishing_positions = {}
```

The `finishing_positions` dict is passed through the result structure and consumed by `compute_race_pace_stats()`, which adds it to each `DriverPaceResponse`.

### 4.11 Backend Changes: Fuel-Corrected Statistics Fix

Three locations in `compute_race_pace_stats()` were updated to use fuel-corrected times:

```python
# Before (Phase 1 -- used raw times):
racing_times = [l['lap_time'] for l in d_laps if l['classification'] == 'RACING']
all_times = [l['lap_time'] for l in d_laps]
stint_laps_map[l['stint']].append(l['lap_time'])

# After (Phase 2 -- uses fuel-corrected times with fallback):
racing_times = [l.get('fuel_corrected_time') or l['lap_time'] for l in d_laps if l['classification'] == 'RACING']
all_times = [l.get('fuel_corrected_time') or l['lap_time'] for l in d_laps]
stint_laps_map[l['stint']].append(l.get('fuel_corrected_time') or l['lap_time'])
```

The `or` fallback ensures that if `fuel_corrected_time` is `None` (e.g., for laps that weren't corrected), the raw `lap_time` is used instead. This makes the fix safe for any data state.

---

## 5. Visual Refinement and Interactivity Enhancements

After the initial Phase 2 implementation, three rounds of visual refinement and interactivity enhancements were applied. These were motivated by comparing our output against professional F1 analysis tools (formula-insights.com) and identifying opportunities to improve clarity, usability, and information density.

### 5.1 X-Axis Simplification and Enrichment Relocation

**Context:** The initial implementation used Plotly's HTML-in-ticktext to render three-line stacked x-axis labels (driver code, finishing position, tyre strategy). This made labels dense and hard to read at 20 drivers, with small text compressed into narrow column widths.

**Change:** X-axis labels were simplified to the 3-character driver code only (e.g., "VER", "NOR", "LEC"). Enrichment data (gap, strategy, finishing position) was relocated to two new surfaces: the driver summary strip below the chart, and the custom two-tier tooltips on hover.

**Impact:** Cleaner x-axis that scales to 20 drivers without readability issues. Enrichment data is now more accessible through dedicated, purpose-built UI surfaces rather than cramped axis labels.

### 5.2 React Header with Team Colour Legend

**Context:** The chart title and any legend were previously handled inside Plotly's layout configuration, which offers limited styling control and renders in Plotly's SVG canvas rather than as DOM elements that can be styled with Tailwind.

**Change:** The title ("Race Pace Distribution by Driver"), GP subtitle (e.g., "2025 Yas Marina Circuit" from Track Intelligence `circuitOverview.circuitName`), and a colour-coded team legend are rendered in React above the Plotly chart. The legend uses `deduplicateTeams()` to show each team once with a coloured square swatch. Plotly's built-in legend is disabled (`showlegend: false` on all traces).

**Impact:** Full control over typography, layout, and responsive behaviour. The team legend wraps naturally on narrow viewports. The GP subtitle uses `formatGPTitle()` which looks up the circuit name from Track Intelligence, falling back to "Round N" if unavailable.

### 5.3 Driver Summary Strip

**Context:** After removing enrichment from x-axis labels, a dedicated surface was needed to display per-driver metadata (gap, strategy, position) in a scannable format.

**Change:** A horizontally scrollable strip of driver cards was added below the chart. Each card uses a two-section design:

1. **Header section** — Driver code in bold white text on a team-coloured background tint (`teamColor + '30'` = 19% opacity)
2. **Metadata section** — Gap to leader, tyre strategy with F1-standard compound colours, and finishing position

Card styling: 3px team-coloured top border, `border-white/10` sides/bottom, `rounded-md` corners, `min-width: 72px`. Strategy letters use the `COMPOUND_COLOR` map: Soft = `#FF3333` (red), Medium = `#FCD34D` (yellow), Hard = `#FFFFFF` (white), Intermediate = `#4ADE80` (green), Wet = `#60A5FA` (blue).

**Impact:** Users can scan all 20 drivers' strategies, gaps, and positions at a glance without hovering. The horizontal scroll handles overflow on smaller screens.

### 5.4 Two-Tier Custom Tooltips

**Context:** Plotly's built-in `hoverinfo: 'text'` provides a single tooltip per trace point. Professional F1 analysis tools (formula-insights.com) use context-sensitive tooltips that show different levels of detail depending on which part of the box the user hovers. Our implementation replaces Plotly's tooltip system entirely with a custom React-rendered overlay.

**Change:** Plotly's built-in hover is suppressed (`hoverinfo: 'none'` on all traces; `hoverlabel` set to transparent). Instead, the `onHover` and `onUnhover` Plotly callbacks drive a React tooltip state machine with three tiers:

**Tier Detection Logic:**
- The `onHover` callback receives `event.points[0]` which includes `curveNumber` (which trace) and `y` (the data-space y-value at the hover point)
- If `curveNumber === drivers.length` → the outlier scatter trace → **outlier tier**
- If `curveNumber < drivers.length` → a box trace → compare `point.y` against the driver's `q1`/`q3`:
  - `q1 <= y <= q3` → **summary tier** (hovering inside the box)
  - Otherwise → **detailed tier** (hovering on whiskers or outside the box)

**Summary Tooltip (box interior hover):**
Compact card showing driver name, team, median, mean, gap to leader, and fuel correction mode. Designed for quick scanning — 3 data rows.

**Detailed Tooltip (whisker/outer hover):**
Full breakdown with three grouped sections separated by dividers:
1. Distribution: Min, Q1, Median (highlighted), Q3, Max
2. Derived stats: Mean, IQR, Gap
3. Race context: Strategy, Consistency, Traffic, Outlier count

**Outlier Tooltip (scatter dot hover):**
Minimal card showing driver name, the specific outlier lap time, and "(outlier)" label.

**Tooltip Styling:**
- Dark background (`#111827`)
- 3px team-coloured left border stripe
- Team-coloured outer border at 38% opacity (`teamColor + '60'`)
- `pointer-events-none` to avoid interfering with chart interactions
- `absolute` positioning within the `relative` container
- Edge-collision avoidance: flips horizontally when near right edge, clamps vertically
- `z-50` ensures tooltip renders above all other elements

**Anti-Flicker:**
- 80ms debounced hide timeout (`hideTimeoutRef`) — cleared on each new hover event
- Prevents tooltip from disappearing momentarily when moving between adjacent box elements (e.g., median line to Q3 boundary)

**PlotlyLazy Interface Extension:**
The `onUnhover` prop was added to `PlotProps` in `PlotlyLazy.tsx` to enable the tooltip dismissal callback. This was a single-line interface change.

### 5.5 Zoom and Pan Controls

**Context:** The initial implementation had `fixedrange: true` on both axes, preventing any zoom interaction. Users needed the ability to focus on specific clusters of drivers or narrow lap-time bands.

**Implementation — Three zoom mechanisms:**

1. **Brush-to-zoom (click-and-drag rectangle):** Both axes set to `fixedrange: false` with `dragmode: 'zoom'`. Users draw a selection rectangle over any area of the chart and the view zooms to that region. This is the primary zoom interaction.

2. **Scroll wheel zoom:** Enabled via `scrollZoom: true` in the Plotly config. Provides smooth incremental zoom centred on the cursor position.

3. **Double-click to reset:** Plotly's built-in behaviour when `dragmode: 'zoom'` — restores both axes to their auto-computed initial range.

**Mode bar:** Set to `displayModeBar: 'hover'` (appears on chart hover). Retains zoom, pan, auto-scale, and reset buttons. Removed lasso and select tools (`modeBarButtonsToRemove: ['lasso2d', 'select2d']`) as they are not meaningful for box plots.

**Performance:** Zoom operations update only the Plotly axis domain state — no recomputation of distribution statistics occurs. The `useMemo` pattern ensures that zoom-triggered re-renders (if any) do not recreate the trace/layout objects.

### 5.6 Zoom State Persistence (useMemo Fix)

**Context:** After implementing zoom, the zoom level would reset every time the user hovered over a box. This made zoom unusable in practice.

**Root Cause:** Two compounding issues:
1. The layout object included `autorange: true` on the y-axis, which instructs Plotly to reset range on every layout application
2. Tooltip state changes (`setTooltip`) triggered React re-renders, which recreated the `traces`, `layout`, and `config` objects inline. `react-plotly.js` saw new prop references, called `Plotly.react()`, which applied the new layout with `autorange: true` — resetting zoom.

**Fix:**
1. **Removed `autorange: true`** from the y-axis configuration. When neither `autorange` nor `range` is specified, Plotly auto-ranges once on initial mount, then preserves whatever range the user sets via zoom/pan.
2. **Wrapped `traces`, `layout`, and `config` in `useMemo`** with appropriate dependency arrays:
   - `traces`: depends on `[drivers]`
   - `layout`: depends on `[drivers, fuelCorrected]`
   - `config`: depends on `[]` (static)
   - `teamEntries`: depends on `[drivers]`

Now when tooltip state changes trigger re-renders, these objects remain referentially identical, so `react-plotly.js` sees no prop change and Plotly does nothing — zoom is preserved. The memoised values only recompute when data or fuel mode changes, which correctly resets the chart for new content.

### 5.7 Enhanced "How to Read This Chart" Guide

**Context:** The initial guide was a flat list of 6 short sentences explaining box plot elements. Users needed more context, especially around the fuel correction toggle and the new two-tier tooltip system.

**Change:** Expanded to a structured, collapsible guide with 4 titled sections inside a bordered card (`rounded-lg border border-white/10 bg-white/[0.02] p-4`):

1. **Understanding the Box Plot** — Explains box, median (solid line), mean (dashed line / diamond), whiskers (1.5x IQR), outlier circles, and sort order (median pace, fastest first)
2. **Hover Tooltips** — Explains the two-tier system: box hover = summary, whisker hover = detailed
3. **Zoom and Pan** — Describes brush-to-zoom (primary), scroll wheel, double-click reset, and toolbar
4. **Fuel-Corrected Lap Times** — Technical explanation of the correction: 110 kg fuel, ~2 kg/lap burn, 0.028-0.036 s/kg circuit-specific penalty, subtraction to empty-tank equivalent. Explains what "enabled" vs "disabled" means visually. Notes limitation: linear model, no engine mode variation.

The guide uses `aria-expanded` on the toggle button for accessibility. Each section has a semi-bold gray-300 heading with gray-500 body text and gray-400 highlighted terms.

---

## 6. Issues Encountered and Resolved

### 6.1 Plotly Box Traces Rendering as Invisible (Critical)

**Severity:** Critical
**Impact:** All box traces were invisible — only the outlier scatter dots appeared.

**Root Cause:** Plotly's internal `box/defaults.js` has dimension detection logic using `switch(String(xDims) + String(yDims))`:
- Case `'10'` (x is 1D, no y): Sets `len = Math.min(sLen, xLen)` — works correctly with pre-computed stats
- Case `'11'` (x is 1D, y is 1D): Sets `len = 0` and `traceOut.visible = false; return;` — silently kills the trace

Our initial implementation had `y: [d.q1, d.median, d.q3]` alongside `x: [d.driver]`, triggering case `'11'`. Plotly classified the trace as "ill-defined" and made it invisible.

**Fix:** Removed the `y` array entirely from box traces. With only `x: [d.driver]` (case `'10'`), Plotly correctly renders one box per trace from the pre-computed stats (`q1`, `median`, `q3`, `lowerfence`, `upperfence`).

**Prevention:** A code comment documents this critical constraint so future developers don't re-introduce the `y` array.

### 6.2 Zoom State Resetting on Hover (High)

**Severity:** High
**Impact:** Zoom was unusable — any hover interaction snapped the chart back to default range.

**Root Cause Chain:**
1. User zooms in (Plotly updates internal axis range)
2. User hovers a box → `handleHover` fires → `setTooltip(...)` → React state update
3. React re-renders `RacePaceBoxPlot`
4. On re-render, `layout` object recreated with `yaxis.autorange: true` (new object reference)
5. `react-plotly.js` receives new layout prop → calls `Plotly.relayout()` → autorange resets zoom

**Fix:** Two changes:
1. Removed `autorange: true` from yaxis (Plotly auto-ranges once on mount without it)
2. Wrapped `traces`, `layout`, `config` in `useMemo` so tooltip re-renders don't create new object references

### 6.3 `circuitName` TypeScript Error

**Severity:** Low (build failure)
**Impact:** TypeScript compilation failed.

**Root Cause:** `formatGPTitle()` accessed `intel?.circuitName` but the field is nested at `intel.circuitOverview.circuitName` in the `TrackIntelligence` interface.

**Fix:** Changed to `intel?.circuitOverview?.circuitName` with optional chaining.

---

## 7. Test Coverage and Verification

### 7.1 Backend Test Results

**Command:**
```bash
cd apps/api && python -m pytest tests/test_race_transforms.py tests/test_race_data_service.py tests/test_race_integration.py -v
```

**Result:** 61/61 passed

| Test File | Tests | Status |
|-----------|-------|--------|
| `test_race_transforms.py` | 38 | All passing |
| `test_race_data_service.py` | 21 | All passing (19 original + 2 new) |
| `test_race_integration.py` | 2 | All passing |

### 7.2 New Tests Added

**`TestRacePaceStats::test_finishing_position_included`**
- Creates two-driver race data with explicit finishing positions (`VER: 1`, `NOR: 2`)
- Verifies that `DriverPaceResponse.finishing_position` is correctly populated per driver

**`TestRacePaceStats::test_finishing_position_none_when_missing`**
- Creates race data without finishing positions
- Verifies that `finishing_position` defaults to `None` (graceful degradation)

### 7.3 Modified Test Assertions

Two existing tests were updated to account for the fuel-corrected statistics fix:

**`test_median_computed_correctly`** — Assertion range shifted from `90.0 < median < 91.5` to `89.0 < median < 90.5` because the test fixture's `_make_lap()` helper sets `fuel_corrected_time = lap_time - 1.0`, and statistics now use the corrected value.

**`test_outliers_beyond_whiskers`** — Expected outlier value changed from `130.0` to `129.0` (the fuel-corrected equivalent of the 130.0 anomaly lap).

### 7.4 Frontend Verification

- **TypeScript compilation:** `npx tsc --noEmit` — zero errors across all iterations
- **Next.js build:** Compiled successfully, all 8 static pages generated (including the new Race page)
- **Race page bundle:** 5.78 KiB page chunk (First Load JS: 189 KiB)
- **Qualifying regression:** Zero qualifying page files modified — no regression risk
- **Live data verification:** API returning 20 drivers for Abu Dhabi 2025 (NOR leading), 19 for Baku 2025; fuel correction delta ~1.7s consistent with physics
- **Docker deployment:** All 3 containers healthy (f1-api, f1-analysis, f1-web); build successful on each iteration
- **Build error:** The EPERM symlink error during standalone output is the pre-existing Windows/OneDrive issue documented in MEMORY.md and does not indicate a code problem

### 7.5 Visual Verification

- Box traces render correctly with team-coloured fills and borders (Plotly case '10')
- Outlier dots appear above whiskers with `circle-open` markers
- Summary strip cards display team colours, coloured compound letters, gap values, and positions
- Two-tier tooltips appear at correct positions with team-coloured left borders
- Brush-to-zoom works (rectangle selection zooms; double-click resets)
- Scroll wheel zoom works incrementally
- Zoom state persists through hover interactions (no reset)
- GP switching triggers opacity transition and full chart re-render
- Fuel toggle switches y-axis label and recomputes statistics

---

## 8. Alignment with Broader Race Page Plan

### 8.1 Patterns Established for Phases 3-5

Phase 2 creates a reusable template that subsequent phases follow without structural changes:

**To add a new Race page panel (e.g., Tyre Degradation in Phase 3), a developer needs:**

1. **Backend endpoint** — e.g., `GET /race/tyre-degradation?session={id}&fuel_effect={factor}`
2. **API client function** — `fetchRaceTyreDeg()` in `api.ts` following `fetchRacePace` pattern
3. **Query key** — `queryKeys.race.tyreDeg(sessionId, ...)` in the `race` namespace
4. **React Query hook** — `useRaceTyreDegQuery()` following `useRacePaceQuery` pattern
5. **Panel component** — e.g., `TyreDegradationPanel.tsx` using PlotlyLazy
6. **Section in RaceContent** — A new `<section>` block with the four-state rendering pattern

No structural refactoring of the page shell, sidebar, skeleton, or query infrastructure is needed. This architectural efficiency is the primary reason Phase 2 was prioritised as the foundational frontend phase.

### 8.2 Reusable Infrastructure

| Asset | Created In | Available To |
|-------|-----------|-------------|
| `RaceContent.tsx` layout shell | Phase 2 | Phases 3-5 add `<section>` blocks |
| `RaceSidebar.tsx` | Phase 2 | Phases 3-5 add controls (compound filter, driver picker) |
| `RacePageSkeleton.tsx` | Phase 2 | Phases 3-5 extend with additional skeleton sections |
| `queryKeys.race` namespace | Phase 2 | Phases 3-5 add `.tyreDeg()`, `.pitStops()`, `.teamPerf()` |
| `useRacePaceQuery` pattern | Phase 2 | Phases 3-5 replicate for their hooks |
| `fetchRacePace` pattern | Phase 2 | Phases 3-5 replicate for their API functions |
| GP switching + opacity transition | Phase 2 | Phases 3-5 inherit automatically |
| Per-panel error isolation | Phase 2 | Each panel's `isError` state is independent |
| `PlotlyLazy` with `onHover`/`onUnhover` | Phase 2 | Future charts can implement custom tooltips |
| `useMemo` pattern for Plotly zoom | Phase 2 | Any Plotly chart with stateful overlays should follow |
| `COMPOUND_COLOR` map | Phase 2 | Tyre degradation panel (Phase 3) uses same colours |
| `deduplicateTeams()` / `shortCompound()` | Phase 2 | Reusable across race panels |

### 8.3 Deferred to Later Phases

| Feature | Deferred To | Reason |
|---------|------------|--------|
| Tyre degradation scatter + regression | Phase 3 | Separate analytical feature |
| Pit stop analysis (3 bar charts) | Phase 4 | Separate analytical feature |
| Team performance quadrant | Phase 5 | Requires telemetry data (most data-intensive) |
| `useVisibilityQuery` (Intersection Observer) | Phase 6 | Below-fold deferred loading |
| Prefetch on Race nav hover | Phase 6 | Performance optimisation |
| Lighthouse audit | Phase 6 | Performance validation |
| Track segment SVG map | Stretch goal | Disproportionate effort for 24 SVGs |

### 8.4 Shared Data Service Advantage

All Race page panels consume the same `get_processed_race_data()` cached result. The pipeline runs once per session (and fuel effect combination) and caches the enriched dataset. Phase 2's box plot queries the pace statistics slice; Phase 3's tyre degradation will query the per-lap fuel-corrected times grouped by stint; Phase 4's pit stops will query the pit stop extraction. No redundant computation occurs across panels.

---

*Documentation Version 2.0 — February 2026*
