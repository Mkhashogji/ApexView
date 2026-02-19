# Race Page Phase 3: Tyre Degradation Analysis

**Status:** Complete (with post-implementation fixes for layout, tooltip, URL persistence, and guide)
**Implemented:** February 2026
**TypeScript:** Zero compilation errors
**Next.js Build:** Compiled successfully (8/8 static pages generated)
**Qualifying Regression:** Zero modified qualifying files
**Docker Validation:** All 3 containers healthy; endpoint verified with live Abu Dhabi 2025 and Baku 2025 data
**Document Version:** 1.0

---

## Table of Contents

1. [Purpose and Significance](#1-purpose-and-significance)
2. [Theoretical and Logical Background](#2-theoretical-and-logical-background)
3. [End-to-End Workflow and Data Flow](#3-end-to-end-workflow-and-data-flow)
4. [Technical Implementation Breakdown](#4-technical-implementation-breakdown)
5. [Post-Implementation Fixes](#5-post-implementation-fixes)
6. [Issues Encountered and Resolved](#6-issues-encountered-and-resolved)
7. [Learnings and How They Influenced Decisions](#7-learnings-and-how-they-influenced-decisions)
8. [Alignment with Broader Race Page Plan](#8-alignment-with-broader-race-page-plan)

---

## 1. Purpose and Significance

### What Phase 3 Delivers

Phase 3 implements the **Tyre Degradation Analysis** panel — the deepest analytical feature of the Race page and the one most directly mirroring pit wall engineering. It transforms the Phase 1 enriched lap dataset into a dual-chart visualisation showing how quickly each driver or team consumed tyre life across a full race distance, with server-side linear regression quantifying wear rate per compound.

The panel provides two synchronised views: a scatter plot of fuel-adjusted lap times versus tyre age (with trend lines showing degradation slope), and a horizontal bar chart of wear rates sorted from lowest to highest (best tyre management first). Users can toggle between Driver and Team analysis modes, filter to specific drivers, and switch between tyre compounds (Hard, Medium, Soft) — with all selections persisted to the URL for shareability.

### Why It Matters

**Tyre degradation is the primary variable that determines race strategy.** It dictates pit windows, compound selection, and whether an aggressive or conservative approach is optimal. Every pit wall decision — when to pit, which compound to fit, how hard to push — traces back to real-time degradation assessment. Phase 3 makes this analysis accessible by computing fuel-corrected degradation trends and presenting them in the standard format used by professional F1 analysts.

**It validates the architecture at interaction scale.** Phase 2 established the Race page frontend patterns (React Query hooks, progressive rendering, PlotlyLazy, query key namespace) with a single chart and minimal interactivity. Phase 3 stress-tests these patterns with a multi-component interactive panel: mode toggle (backend refetch), driver chip selector (client-side filter), compound tabs (client-side switch), dual-chart layout, custom tooltip, URL state persistence, and session-change validation. Every pattern that worked simply in Phase 2 is now proven under real interaction complexity.

**It introduces the server-side regression pattern.** Phase 3 is the first feature to perform statistical modelling (linear regression via scipy) on the backend and deliver pre-computed results to the frontend. This establishes the principle that computation-heavy analytics live in FastAPI, not in the browser — the frontend receives coordinates to render, not data to compute. This pattern will be reused by Phase 5's team performance quadrant.

### Position in the Race Page Architecture

| Phase | Name | Depends On | Status |
|-------|------|-----------|--------|
| 1 | Race Data Foundation | — | Complete |
| 2 | Race Pace Distribution (Box Plot) | Phase 1 | Complete |
| **3** | **Tyre Degradation Analysis** | **Phase 1** | **Complete** |
| 4 | Pit Stop Analysis | Phase 1 | Planned |
| 5 | Team Performance Quadrant | Phase 1 | Planned |
| 6 | Performance Optimization & Integration | Phases 1-5 | Planned |

Phase 3 consumes the Phase 1 enriched lap dataset through the shared `get_processed_race_data()` service. It introduces a new computation service (`tyre_degradation.py`), a new API endpoint (`GET /race/tyre-degradation`), and five new frontend components, all following the patterns established by Phase 2.

---

## 2. Theoretical and Logical Background

### 2.1 What Tyre Degradation Analysis Communicates

The panel answers the question: **"How quickly did each driver or team lose tyre performance across each stint, and how does that compare across the field?"**

In a typical F1 race, lap times increase over a stint as tyre grip diminishes. The rate of this increase — measured in seconds lost per lap — is the degradation rate (or wear rate). A driver with 0.030 s/lap degradation is managing tyres better than one with 0.080 s/lap, all else being equal. This difference compounds over a 25-30 lap stint into multiple seconds, which can determine whether a pit strategy works or fails.

### 2.2 Fuel Correction: Isolating the Tyre Signal

Raw lap times during a race contain two competing effects:

1. **Fuel burn benefit** — The car gets lighter each lap (~1.8-2.2 kg/lap), which makes it faster. At a circuit-specific rate of 0.028-0.036 s/kg, this produces roughly 0.060 s/lap of improvement.
2. **Tyre degradation penalty** — Grip diminishes, making the car slower. Typical rates range from 0.020 s/lap (low-degradation circuits with hard compounds) to 0.100+ s/lap (high-degradation circuits with soft compounds).

These two effects partially cancel. A driver whose tyres are losing 0.035 s/lap might show flat raw lap times because fuel burn gives roughly 0.035 s/lap of offsetting benefit. Without fuel correction, the degradation trend is masked.

The correction formula normalises to empty tank:

```
corrected = raw_time - (fuel_remaining * fuel_effect_per_kg)
```

Where `fuel_remaining = total_fuel - (fuel_per_lap * lap_number)`, clamped to zero. This subtracts the fuel-mass penalty from each lap — early-race laps receive a larger subtraction (heavier car). The result reveals the underlying tyre degradation trajectory hidden by fuel mass reduction.

The `fuel_effect_per_kg` value is circuit-specific, drawn from the Track Intelligence database:

| Tier | Range (s/kg) | Circuits |
|------|-------------|----------|
| Low | 0.028-0.029 | Silverstone, Monza, Spa, Suzuka |
| Mid | 0.031-0.033 | Most circuits (16 of 24) |
| High | 0.034-0.036 | Monaco, Singapore, Hungary, Bahrain, Montreal |

### 2.3 Linear Regression as the Standard Approach

The scatter plot's trend line uses ordinary least squares linear regression (scipy `linregress`) on the (tyre_age, fuel_adjusted_time) pairs. The gradient (slope) represents the wear rate in seconds per lap. This is the standard approach used in published F1 tyre degradation analyses.

Linear regression was chosen over polynomial or non-linear fits because:
- Stint samples are typically 15-30 data points — insufficient for stable higher-order estimation
- The linear model provides a single interpretable number (s/lap) that directly compares across drivers
- Non-linear "cliff" effects (sudden grip loss) are rare in the filtered dataset and are documented as a limitation rather than modelled

### 2.4 Data Filtering for Regression Quality

Not all racing laps are suitable for regression. Several categories of laps are excluded:

**Warm-up laps (first 2 of each stint):** Tyres need 1-2 laps to reach operating temperature. Including these produces artificially steep initial slopes that misrepresent the underlying degradation rate.

**Non-racing laps:** In-laps, out-laps, safety car laps, VSC laps, red flag laps, and formation laps are excluded entirely — they represent non-representative driving conditions.

**Anomaly laps:** Laps detected as statistical outliers (IQR-based or >110% of driver median) appear in the scatter plot as visible dots but are excluded from the regression computation.

**Minimum sample threshold:** Groups with fewer than 7 usable laps after filtering do not receive a regression line or wear rate number. The response returns `regression: null` and `wearRate: null` rather than an unreliable estimate. This threshold balances statistical reliability against the reality that short stints (5-6 laps) are common in F1.

### 2.5 Driver Mode vs Team Mode

The panel supports two analysis perspectives:

**Driver mode** computes individual regression per driver per compound. This reveals within-team differences: one driver may manage tyres better than their teammate on the same compound, visible as different trend slopes.

**Team mode** pools both drivers' laps into a single dataset per team per compound. This reveals team-level strategy philosophy: a team that consistently runs lower degradation may have a more conservative setup or superior mechanical grip. Pooling also increases the sample size, producing more stable regression estimates for teams with short stints.

The mode toggle triggers a backend refetch because the regression computation fundamentally changes — individual slopes cannot be derived from a pooled regression or vice versa.

### 2.6 Compound-Tabbed Layout

The panel presents data through compound tabs (Hard, Medium, Soft) rather than vertically stacking all compounds. This keeps the viewport focused on one compound at a time while the wear rate bar chart provides a cross-compound summary visible alongside any tab.

The compound display order follows F1 convention: hardest first (HARD, MEDIUM, SOFT, INTERMEDIATE, WET). Compounds not used in the race are omitted from the tabs.

---

## 3. End-to-End Workflow and Data Flow

### 3.1 Initial Page Load

```
User navigates to /race?season=2025&round=24
       |
       v
RaceContent.tsx hydrates
  - Derives sessionId = "2025_24_Race"
  - Reads fuelEffectPerKg = 0.031 from Track Intelligence (Abu Dhabi)
  - fuelCorrected = true -> fuelEffect = 0.031
       |
       v
TyreDegradationPanel mounts
  - Reads URL params: ?tdMode, ?tdDrivers, ?tdCompound
  - Initialises state from URL (or defaults: driver mode, no filter, null compound)
       |
       v
useTyreDegradationQuery fires
  - Query key: ['race', 'tyreDeg', '2025_24_Race', { fuelEffect: 0.031, mode: 'driver' }]
  - Calls fetchTyreDegradation('2025_24_Race', 0.031, 'driver')
       |
       v
GET /race/tyre-degradation?session=2025_24_Race&fuel_effect=0.031&mode=driver
       |
       v
tyre_degradation.compute_tyre_degradation()
  - Calls get_processed_race_data('2025_24_Race', 0.031)
    [Phase 1 pipeline: classify -> fuel correct -> traffic -> stints -> pit stops]
  - Filters to: classification == 'RACING' AND is_warm_up == False AND fuel_corrected_time != None
  - Groups by compound -> groups by driver
  - For each driver on each compound with >= 7 usable laps:
      scipy.linregress(tyre_age, fuel_adjusted_time) -> regression line + wear rate
  - Enriches with warm-up counts from full lap set
       |
       v
TyreDegradationResponse JSON (camelCase via CamelCaseModel)
  - session_id, mode, compounds (each with drivers list), compound_order
       |
       v
TyreDegradationPanel receives data
  - Extracts all identifiers from all compounds
  - Auto-selects all identifiers (if user hasn't manually filtered)
  - Sets active compound to first in compoundOrder (unless URL specifies one)
  - Filters active compound data by selectedIdentifiers (client-side useMemo)
       |
       v
Renders:
  +-- AnalysisModeToggle (Driver/Team radio buttons)
  +-- DriverChipSelector (multi-select chips with team colours)
  +-- CompoundTabs (Hard/Medium/Soft tabs)
  +-- DegradationScatter
  |     +-- Scatter plot (PlotlyLazy): markers + regression lines
  |     +-- Wear rate bar chart (PlotlyLazy): sorted ascending
  |     +-- DegradationTooltip (container-relative, edge-detected)
  +-- "How to read this chart" (7-section collapsible guide)
```

### 3.2 Mode Toggle Flow

```
User clicks "Team Analysis"
       |
       v
handleModeChange('team')
  - setMode('team')
  - Clears selectedIdentifiers (teams differ from drivers)
  - Updates URL: ?tdMode=team (removes tdDrivers)
       |
       v
useTyreDegradationQuery fires with new query key
  - ['race', 'tyreDeg', '2025_24_Race', { fuelEffect: 0.031, mode: 'team' }]
  - Backend pools both drivers' laps per team for regression
       |
       v
New data arrives
  - 10 team identifiers (not 20 driver codes)
  - Regression computed on pooled per-team data
  - Auto-selects all 10 teams
```

### 3.3 Driver Filtering Flow (Client-Side Only)

```
User removes "HAM" chip from DriverChipSelector
       |
       v
handleSelectionChange([...all except HAM])
  - setSelectedIdentifiers(updated list)
  - Updates URL: ?tdDrivers=ALB,ALO,ANT,...,VER (without HAM)
  - NO backend refetch (driver selection not in query key)
       |
       v
activeCompoundData recomputes via useMemo
  - Filters compound.drivers to only those in selectedIdentifiers
       |
       v
DegradationScatter re-renders with 19 drivers instead of 20
  - HAM's scatter points and trend line disappear
  - HAM's wear rate bar disappears
```

### 3.4 Compound Tab Switch Flow (Client-Side Only)

```
User clicks "Soft" tab
       |
       v
handleCompoundChange('SOFT')
  - setActiveCompound('SOFT')
  - Updates URL: ?tdCompound=SOFT
  - NO backend refetch (all compounds returned in single response)
       |
       v
activeCompoundData recomputes via useMemo
  - Selects SOFT compound from data.compounds
       |
       v
DegradationScatter re-renders with Soft compound data
```

### 3.5 GP Switching Flow

```
User selects Baku GP from navigation selector
       |
       v
URL changes: /race?season=2025&round=17&tdMode=driver&tdCompound=SOFT&tdDrivers=VER,LEC
       |
       v
RaceContent re-renders with new round
  - New sessionId = "2025_17_Race"
  - New fuelEffect = 0.033 (Baku from Track Intelligence)
       |
       v
useTyreDegradationQuery fires with new key
  - placeholderData: keepPreviousData -> old Abu Dhabi data remains at 60% opacity
       |
       v
TyreDegradationPanel detects sessionId change
  - prevSessionIdRef.current !== data.sessionId
  - Resets activeCompound to first available (HARD)
  - Validates tdDrivers: VER and LEC exist in Baku data -> kept
  - Updates URL: removes stale tdCompound, keeps valid tdDrivers
       |
       v
New Baku data arrives
  - isPlaceholderData = false -> opacity transitions to 100%
  - Charts render with Baku 2025 degradation data
```

### 3.6 Refetch vs Client-Side Decision Matrix

| User Action | Backend Refetch? | Reason |
|---|---|---|
| Toggle Driver <-> Team | Yes | Different regression grouping (individual vs pooled) |
| Change fuel correction | Yes | Different fuel_corrected_time values |
| Remove/add driver chip | No | Same data, client-side `useMemo` filter |
| Switch compound tab | No | All compounds pre-fetched in single response |
| Switch GP | Yes | Entirely new session and data |

---

## 4. Technical Implementation Breakdown

### 4.1 Files Created

| File | Lines | Purpose | Key Exports |
|------|-------|---------|-------------|
| `services/race/tyre_degradation.py` | 237 | Regression computation service | `compute_tyre_degradation()` |
| `components/race/TyreDegradationPanel.tsx` | 428 | Main orchestrator panel | `TyreDegradationPanel` |
| `components/race/DegradationScatter.tsx` | 334 | Dual-chart (scatter + bar) | `DegradationScatter` |
| `components/race/AnalysisModeToggle.tsx` | 41 | Driver/Team radio toggle | `AnalysisModeToggle` |
| `components/race/DriverChipSelector.tsx` | 156 | Multi-select chip picker | `DriverChipSelector` |
| `components/race/CompoundTabs.tsx` | 53 | Compound tab switcher | `CompoundTabs` |
| `lib/hooks/useTyreDegradationQuery.ts` | 26 | React Query hook | `useTyreDegradationQuery` |
| `lib/compounds.ts` | 51 | Compound colours and names | `getCompoundColor`, `COMPOUND_DISPLAY_NAMES` |

### 4.2 Files Modified

| File | Change | Impact |
|------|--------|--------|
| `routes/race.py` | Added `GET /tyre-degradation` endpoint | New API surface for Phase 3 |
| `models/dto.py` | Added 5 DTOs: `RegressionLine`, `DegradationDataPoint`, `DriverDegradationData`, `CompoundDegradation`, `TyreDegradationResponse` | Backend response schema |
| `packages/models/src/types.ts` | Added matching TypeScript interfaces | Frontend type safety |
| `lib/api.ts` | Added `fetchTyreDegradation()` | API client function |
| `lib/hooks/queryKeys.ts` | Added `race.tyreDeg()` key factory | Cache key for React Query |
| `app/race/RaceContent.tsx` | Added `<TyreDegradationPanel>` section | Panel integration |
| `components/charts/PlotlyLazy.tsx` | Already had `onUnhover` from Phase 2 | No change needed |

### 4.3 Backend Computation Service (`tyre_degradation.py`)

The core service implements a four-stage pipeline:

**Stage 1 — Data Loading and Filtering:**
```python
race_data = get_processed_race_data(session_id, fuel_effect_per_kg)
eligible_laps = [
    lap for lap in race_data['laps']
    if lap['classification'] == 'RACING'
    and not lap.get('is_warm_up', False)
    and lap.get('fuel_corrected_time') is not None
]
```

This consumes the Phase 1 enriched dataset. The filter chain removes non-racing laps, warm-up laps (first 2 of each stint), and laps with missing fuel correction. The remaining set represents clean, representative racing data suitable for regression.

**Stage 2 — Grouping by Compound and Identifier:**

Laps are grouped first by compound (HARD, MEDIUM, SOFT), then within each compound by driver (in driver mode) or team (in team mode). Each group becomes a candidate for regression computation.

**Stage 3 — Regression Computation:**
```python
def _compute_regression(data_points):
    if len(data_points) < MIN_REGRESSION_LAPS:  # MIN_REGRESSION_LAPS = 7
        return None
    x = [p['tyre_age'] for p in data_points]
    y = [p['fuel_adjusted_time'] for p in data_points]
    result = linregress(x, y)
    return {
        'start_x': float(min(x)),
        'start_y': float(result.intercept + result.slope * min(x)),
        'end_x': float(max(x)),
        'end_y': float(result.intercept + result.slope * max(x)),
        'slope': float(result.slope),      # Wear rate in s/lap
        'intercept': float(result.intercept),
        'r_squared': float(result.rvalue ** 2),
    }
```

The regression returns pre-computed line coordinates (startX/Y, endX/Y) — the frontend renders a simple two-point line trace without any mathematical computation. The slope is the wear rate in seconds per lap, and R-squared indicates fit quality.

Groups with fewer than 7 usable laps return `None` for regression and wear rate, displayed as "Insufficient data" in the UI rather than an unreliable number.

**Stage 4 — Warm-Up Count Enrichment:**

A separate pass over the full (unfiltered) lap set counts total RACING laps and warm-up laps per driver per compound. These counts are attached to each `DriverDegradationData` entry so the frontend can show transparency about data filtering (e.g., "23 racing laps, 4 warm-up excluded, 19 used for regression").

### 4.4 Data Transfer Objects (`dto.py`)

Five Pydantic models define the response schema:

```
TyreDegradationResponse
  ├── session_id: str
  ├── mode: 'driver' | 'team'
  ├── compound_order: List[str]  # Display order: ['HARD', 'MEDIUM', 'SOFT']
  └── compounds: List[CompoundDegradation]
        ├── compound: str  # e.g., 'HARD'
        └── drivers: List[DriverDegradationData]
              ├── identifier: str          # Driver code or team name
              ├── team: str
              ├── data_points: List[DegradationDataPoint]
              │     ├── tyre_age: int
              │     ├── fuel_adjusted_time: float
              │     ├── raw_time: float
              │     ├── lap_number: int
              │     ├── driver: str
              │     ├── team: str
              │     └── stint_number: int
              ├── regression: Optional[RegressionLine]
              │     ├── start_x, start_y, end_x, end_y: float
              │     ├── slope: float       # Wear rate (s/lap)
              │     ├── intercept: float
              │     └── r_squared: float
              ├── wear_rate: Optional[float]
              ├── usable_lap_count: int
              ├── total_stint_laps: int
              └── warm_up_laps_excluded: int
```

All models extend `CamelCaseModel`, which automatically serialises snake_case Python fields to camelCase JSON (e.g., `fuel_adjusted_time` becomes `fuelAdjustedTime` in the response).

### 4.5 Frontend Panel Orchestrator (`TyreDegradationPanel.tsx`)

The panel manages three dimensions of state, all persisted to URL parameters:

**URL State Parameters:**
- `tdMode` — `'driver'` or `'team'` (always present)
- `tdDrivers` — comma-separated identifiers (only present when a subset is selected; omitted when all selected to keep URLs clean)
- `tdCompound` — active compound tab (e.g., `'MEDIUM'`)

**State Initialisation from URL:**
```typescript
const urlMode = (searchParams.get('tdMode') as 'driver' | 'team') || 'driver'
const urlDrivers = searchParams.get('tdDrivers')?.split(',').filter(Boolean) || []
const urlCompound = searchParams.get('tdCompound') || null
```

**URL Update Helper:**
```typescript
const updateTyreDegURL = useCallback((newMode, newDrivers, newCompound) => {
  const params = new URLSearchParams(searchParams.toString())
  params.set('tdMode', newMode)
  if (newDrivers.length > 0 && newDrivers.length < allIdentifiers.length) {
    params.set('tdDrivers', newDrivers.join(','))
  } else {
    params.delete('tdDrivers')  // All selected = default, keep URL clean
  }
  if (newCompound) params.set('tdCompound', newCompound)
  else params.delete('tdCompound')
  router.replace(`${pathname}?${params.toString()}`, { scroll: false })
}, [searchParams, pathname, router, allIdentifiers.length])
```

Three memoised handler callbacks (`handleModeChange`, `handleSelectionChange`, `handleCompoundChange`) each update local state and write to URL.

**Session-Change Reset with Mount Protection:**

A `useRef` tracks the previous session ID to distinguish initial mount from actual GP switches:

```typescript
const prevSessionIdRef = useRef<string | undefined>(undefined)

useEffect(() => {
  if (data && data.compoundOrder.length > 0) {
    if (prevSessionIdRef.current !== undefined && prevSessionIdRef.current !== data.sessionId) {
      setActiveCompound(data.compoundOrder[0])  // Reset on GP switch
    }
    prevSessionIdRef.current = data.sessionId    // Store for next comparison
  }
}, [data?.sessionId, data])
```

On initial mount, `prevSessionIdRef.current` is `undefined`, so the reset is skipped — preserving the URL-restored compound. On subsequent GP switches, the ref holds the old session ID, triggering the reset to the first available compound.

**Progressive Rendering States:**
- Loading: Skeleton placeholder matching panel dimensions
- Error: Clear error message with details
- No data: Informative message
- Placeholder data: Previous GP data at 60% opacity during transition

### 4.6 Dual-Chart Component (`DegradationScatter.tsx`)

**Layout:**
```
flex flex-col lg:flex-row gap-4
  +-- Scatter (lg:flex-[7], 70% desktop)
  |     +-- overflow-hidden wrapper (hard height constraint)
  |     |     +-- PlotlyLazy (scatter + regression lines, height: 400px)
  |     +-- DegradationTooltip (absolute, outside overflow-hidden)
  +-- Bar chart (lg:flex-[3], 30% desktop)
        +-- "TYRE WEAR (LOWER = BETTER)" header
        +-- PlotlyLazy (horizontal bars, clamped height)
```

**Scatter Plot Traces:**

For each driver/team, two traces are generated:
1. **Scatter markers:** Each data point plotted at (tyreAge, fuelAdjustedTime) with team colour, 70% opacity, size 5. Custom data array attached for tooltip.
2. **Regression line:** Two-point line trace from pre-computed (startX, startY) to (endX, endY) with solid team colour, width 2. Only rendered when regression data exists.

**Wear Rate Bar Chart:**

Drivers are filtered to those with a non-null `wearRate`, sorted ascending (lowest = best tyre management at top). Height is clamped: `Math.min(400, Math.max(200, count * 30 + 80))`. Text labels show the numeric value with "s/lap" suffix.

**Custom Tooltip (`DegradationTooltip`):**

A sub-component using container-relative absolute positioning with edge detection:
- Container dimensions read from `containerRef.current.offsetWidth/Height`
- Horizontal flip when tooltip would exceed container right edge
- Vertical clamping to prevent top/bottom overflow
- Displays: driver, team, tyre age, fuel-adjusted time, raw time, lap number, stint number

### 4.7 Supporting Components

**`AnalysisModeToggle`** — Two radio-style buttons ("Driver Analysis" / "Team Analysis"). Active state uses `bg-f1red` with white text. Mode change triggers the parent's `handleModeChange` callback, which updates state, clears driver selection, writes to URL, and — through the query key change — triggers a backend refetch.

**`DriverChipSelector`** — Multi-select chip picker with:
- Dismissible chips showing team-coloured left border
- "+ Add" button opening a dropdown of unselected identifiers with team colour dots
- "Select All" / "Clear" bulk actions
- Click-outside-to-close behaviour
- Label dynamically shows "DRIVERS" or "TEAMS" based on mode

**`CompoundTabs`** — Tab bar with compound-coloured dot indicators. Active tab has a coloured bottom border and white text; inactive tabs show gray text. Uses `getCompoundColor()` from `compounds.ts` and `COMPOUND_DISPLAY_NAMES` for display text.

### 4.8 React Query Hook (`useTyreDegradationQuery.ts`)

```typescript
export function useTyreDegradationQuery(
  sessionId: string | undefined,
  fuelEffect?: number,
  mode: string = 'driver',
) {
  return useQuery<TyreDegradationResponse>({
    queryKey: queryKeys.race.tyreDeg(sessionId ?? '', fuelEffect, mode),
    queryFn: () => fetchTyreDegradation(sessionId!, fuelEffect, mode),
    enabled: !!sessionId,
    placeholderData: keepPreviousData,
  })
}
```

Key design decisions:
- `mode` is in the query key — toggling Driver/Team triggers a refetch with different regression computation
- `fuelEffect` is in the query key — changing fuel correction triggers a refetch
- `selectedIdentifiers` is NOT in the query key — driver filtering is client-side only
- `keepPreviousData` enables smooth GP switching with opacity transition

**TODO (Phase 6):** Add `staleTime: Infinity` and `gcTime: 30 * 60 * 1000` for immutable race data caching.

### 4.9 API Client and Query Keys

**`fetchTyreDegradation()`** in `api.ts`:
```typescript
export async function fetchTyreDegradation(
  sessionId: string,
  fuelEffect?: number,
  mode: string = 'driver',
): Promise<TyreDegradationResponse> {
  const params = new URLSearchParams({ session: sessionId, mode })
  if (fuelEffect !== undefined) params.set('fuel_effect', fuelEffect.toString())
  return fetchApi<TyreDegradationResponse>(
    `${API_BASE_URL}/race/tyre-degradation?${params}`
  )
}
```

**Query key factory** in `queryKeys.ts`:
```typescript
race: {
  tyreDeg: (sessionId: string, fuelEffect?: number, mode?: string) =>
    ['race', 'tyreDeg', sessionId, { fuelEffect, mode }] as const,
}
```

Including both `fuelEffect` and `mode` as structured key components means that each unique combination is cached independently. Switching between driver mode with fuel correction and team mode without fuel correction produces four distinct cache entries, all served from cache on subsequent toggles without re-fetching.

### 4.10 Shared TypeScript Types

The TypeScript interfaces in `packages/models/src/types.ts` exactly mirror the Python DTOs with camelCase naming:

- `TyreDegradationResponse` — top-level with `sessionId`, `mode`, `compounds`, `compoundOrder`
- `CompoundDegradation` — compound name with array of `DriverDegradationData`
- `DriverDegradationData` — identifier, team, `dataPoints[]`, optional `regression`, optional `wearRate`, lap counts
- `DegradationDataPoint` — per-lap record with `tyreAge`, `fuelAdjustedTime`, `rawTime`, metadata
- `RegressionLineData` — pre-computed line coordinates with `slope`, `intercept`, `rSquared`

### 4.11 Integration in RaceContent

The panel mounts as a section in `RaceContent.tsx`:

```tsx
<section>
  <TyreDegradationPanel sessionId={sessionId} fuelEffect={fuelEffect} />
</section>
```

`sessionId` is derived from URL params (`${season}_${round}_Race`). `fuelEffect` is the circuit-specific fuel correction factor from Track Intelligence (or 0 if the user disables fuel correction via the sidebar toggle). The panel manages all its own internal state independently — mode, driver selection, compound tab, and guide toggle are encapsulated within `TyreDegradationPanel` and do not leak into the parent.

---

## 5. Post-Implementation Fixes

After the initial Phase 3 implementation and Docker-based live data validation, four issues were identified during local browser testing and resolved in a focused fix round.

### 5.1 Layout Overflow

**Problem:** The dual-chart layout broke when driver selection changed. The bar chart's dynamic height calculation (`count * 30 + 80`) was unbounded — 20 drivers produced 680px, far exceeding the scatter's 400px. The scatter chart could also render beyond its CSS container because Plotly's layout `height: 400` is advisory to the charting engine, not a hard constraint on the DOM element.

**Fix — Multi-layer containment:**
1. Clamped bar chart height: `Math.min(400, Math.max(200, barData.count * 30 + 80))`
2. Added `overflow-hidden` to the bar chart container
3. Wrapped the PlotlyLazy scatter in a `<div className="overflow-hidden">` with explicit `style={{ height: '400px' }}` — a hard DOM constraint that Plotly cannot exceed
4. The scatter's parent `relative` container remains without overflow-hidden so the tooltip can render on top

### 5.2 Tooltip Positioning

**Problem:** The tooltip used `position: fixed` with raw `clientX`/`clientY` viewport coordinates. When the chart was scrolled partway off-screen, the tooltip appeared far from the hovered point. Near chart edges, the tooltip overflowed the viewport entirely.

**Fix — Container-relative positioning with edge detection:**
1. Added `useRef<HTMLDivElement>` on the scatter container
2. Converted viewport coordinates to container-relative in `handleHover`: `cursorX = clientX - containerRect.left`
3. Extracted a `DegradationTooltip` sub-component that calculates position with edge detection: flip horizontally if tooltip would exceed container width, clamp vertically if it would exceed container height
4. Changed from `position: fixed` to `position: absolute`

### 5.3 URL State Persistence

**Problem:** Mode, driver selection, and compound tab were `useState` only. Refreshing the page reset everything to defaults.

**Fix — URL parameter persistence with namespaced params:**
1. Added `useRouter`, `useSearchParams`, `usePathname` from `next/navigation`
2. Three URL parameters namespaced with `td` prefix: `tdMode`, `tdDrivers`, `tdCompound`
3. Three memoised handler callbacks write state to URL via `router.replace()` with `{ scroll: false }`
4. State initialises from URL on mount
5. Validation effect checks persisted driver IDs exist in current session data
6. `tdDrivers` omitted when all selected (all = default, keep URL clean)

### 5.4 Compound Tab Race Condition

**Problem:** After implementing URL persistence, the compound tab showed Hard instead of the URL-persisted Medium on page load. A `useEffect` on `data?.sessionId` fired on initial mount and unconditionally reset `activeCompound` to `data.compoundOrder[0]` (HARD), overwriting the URL-restored MEDIUM.

**Fix — Mount-aware session tracking:**
1. Added `useRef<string | undefined>(undefined)` to track previous session ID
2. On initial mount (`prevSessionIdRef.current === undefined`): skip reset, store current session ID
3. On actual GP switch (`prevSessionIdRef.current !== data.sessionId`): reset compound to first available

---

## 6. Issues Encountered and Resolved

### 6.1 Plotly Layout Height is Advisory, Not Binding (Critical for Layout)

**Severity:** High
**Impact:** Chart overflowed its container, overlapping with content below.

Plotly's `height: 400` in the layout object tells the charting engine the intended height, but the DOM element can exceed it when legends, axis labels, or the mode bar push content outside the plot area. Setting `height` in layout is necessary for Plotly's internal calculations, but it does not create a CSS constraint.

**Resolution:** Dual constraint — `height: 400` in Plotly layout for internal calculations, plus `style={{ height: '400px' }}` on the container element and an `overflow-hidden` wrapper for hard DOM containment.

### 6.2 Fixed-Position Tooltips Fail in Scrollable Layouts

**Severity:** High
**Impact:** Tooltip appeared far from hovered data point when page was scrolled.

`position: fixed` with `clientX`/`clientY` places the element relative to the viewport. When the chart container has been scrolled away from the viewport origin, the tooltip's position diverges from the data point's visual position. The Phase 2 RacePaceBoxPlot already solved this with container-relative absolute positioning — the Phase 3 tooltip was initially implemented with a simpler (but incorrect) approach.

**Resolution:** Adopted the proven Phase 2 pattern: `position: absolute` within a `position: relative` container, with `getBoundingClientRect()` conversion and edge detection.

### 6.3 useEffect with Data-Derived Dependencies Fires on Mount

**Severity:** Medium
**Impact:** URL-persisted compound tab was overwritten on initial page load.

A `useEffect` intended to respond to session changes (GP switches) also fires on the initial render when `data?.sessionId` first becomes non-null. With the compound reset logic inside, it overwrote the URL-restored value.

**Resolution:** `useRef` pattern to track the previous session ID. The effect stores the current ID and only resets when the stored value differs from the incoming one. On first mount, the ref is `undefined`, so the reset is skipped.

### 6.4 Docker Build Cache Serves Stale Code

**Severity:** Low (development workflow)
**Impact:** Code changes not reflected in Docker-served application.

`docker compose build web` returned all CACHED layers even after source files changed. Docker BuildKit's cache invalidation for the `COPY . .` layer depends on file metadata that may not be detected on Windows/OneDrive.

**Resolution:** Use `docker compose build --no-cache web` when verifying code changes. This forces a complete rebuild including the `COPY . .` and `pnpm build` steps.

---

## 7. Learnings and How They Influenced Decisions

### 7.1 Reuse Proven Patterns, Don't Simplify Them

The Phase 2 RacePaceBoxPlot established a container-relative tooltip pattern with edge detection. For Phase 3, the initial implementation used a simpler `position: fixed` approach, reasoning that it would be adequate. It wasn't. The scrollable layout exposed the exact failure mode that the Phase 2 pattern was designed to handle.

**Influence:** The Phase 3 tooltip was rewritten to match the Phase 2 pattern exactly. Going forward, new components that need custom tooltips over Plotly charts should copy the container-relative pattern rather than inventing simpler alternatives.

### 7.2 Plotly Needs Hard DOM Constraints, Not Just Layout Hints

Plotly's layout `height` controls the charting engine's internal coordinate system, but the rendered SVG element can exceed these bounds. The Phase 2 box plot rendered in a full-width container where overflow wasn't noticeable. Phase 3's side-by-side dual-chart layout made overflow immediately visible.

**Influence:** The fix established a two-layer pattern: an outer `relative` container for positioning overlays (tooltips), and an inner `overflow-hidden` div with explicit CSS height for Plotly containment. This pattern should be applied to any future Plotly chart where layout containment is critical.

### 7.3 useEffect with Data Dependencies Needs Mount Awareness

React's `useEffect` with `[data?.sessionId]` fires both on mount (when data first arrives) and on change (when GP switches). Code that should only run on change — like resetting the compound tab — needs explicit mount detection. The `useRef` pattern (tracking previous value, skipping when `undefined`) is the standard solution.

**Influence:** All session-change effects in future panels should use the `prevSessionIdRef` pattern rather than assuming the effect only fires on changes.

### 7.4 URL State Should Be Namespaced Per Panel

The qualifying page uses root-level URL params (`session`, `ref`, `drivers`). For the race page with multiple independent panels, each panel's state needs its own namespace to avoid collisions. The `td` prefix (`tdMode`, `tdDrivers`, `tdCompound`) keeps tyre degradation state separate from other panels' future state.

**Influence:** Phase 4 (Pit Stops) should use a `ps` prefix, and Phase 5 (Team Performance) should use a `tp` prefix. Each panel manages its own URL params internally, without hoisting to the parent.

### 7.5 "All Selected" Should Not Appear in the URL

When all 20 drivers are selected, persisting `tdDrivers=ALB,ALO,ANT,...,VER` adds visual noise to the URL and increases the chance of stale references on GP switch. The design decision: `tdDrivers` is only persisted when the selection is a subset. "All selected" is the default, represented by the absence of the parameter.

**Influence:** Any future panel with a multi-select filter should follow this pattern: persist only subsets, treat absence as "all."

### 7.6 Server-Side Regression Prevents Computation Drift

Computing regression in Python (scipy) and sending pre-computed line coordinates eliminates the risk of frontend/backend calculation differences. The frontend renders a simple two-point line trace — no math library needed. The regression visualisation is guaranteed to match the wear rate number in the bar chart because both derive from the same server-side computation.

**Influence:** Phase 5's team performance metrics (top speed delta, mean speed delta) should follow the same pattern: compute on the backend, deliver pre-computed aggregates to the frontend.

### 7.7 Client-Side vs Backend Refetch Must Be Deliberate

Phase 3 draws a clear line: mode changes trigger refetch (fundamentally different regression), driver selection does not (same data, client-side filter). This decision is encoded in the query key structure — `mode` is a key component, `selectedIdentifiers` is not.

**Influence:** For Phase 4 (Pit Stops), all data should be fetched in one call and filtered client-side (by team, by driver). For Phase 5 (Team Performance), telemetry-derived metrics require a single backend call with no client-side filtering needed.

---

## 8. Alignment with Broader Race Page Plan

### 8.1 Patterns Validated Under Interaction Complexity

Phase 3 confirmed that the Phase 2 patterns scale to interactive, multi-component panels:

| Pattern | Phase 2 Usage | Phase 3 Validation |
|---------|--------------|-------------------|
| React Query hook per panel | Single hook, minimal options | Hook with mode in query key, triggering refetch on toggle |
| `keepPreviousData` | GP switching | GP switching + mode switching |
| PlotlyLazy | Single chart | Two charts side-by-side with shared data |
| Custom tooltip | Three-tier hover system | Container-relative with edge detection |
| URL state | Season/round from navigation | Panel-specific `td*` params with validation |
| Progressive rendering | Loading/error/data states | Same states plus opacity transition |
| Server-side computation | Pre-computed box stats | Pre-computed regression coordinates |

### 8.2 Infrastructure Extended for Phases 4-5

| Asset | Created/Extended | Available To |
|-------|-----------------|-------------|
| `queryKeys.race.tyreDeg()` | Phase 3 | Pattern for `race.pitStops()`, `race.teamPerf()` |
| `fetchTyreDegradation()` | Phase 3 | Pattern for `fetchPitStops()`, `fetchTeamPerformance()` |
| `AnalysisModeToggle` | Phase 3 | Reusable by any panel needing a mode switch |
| `DriverChipSelector` | Phase 3 | Reusable by any panel needing multi-select filtering |
| `CompoundTabs` | Phase 3 | Reusable by any compound-segmented analysis |
| `compounds.ts` utilities | Phase 3 | Shared across all tyre-related features |
| URL state namespace pattern | Phase 3 | Template for `ps*` (Phase 4) and `tp*` (Phase 5) |
| Container-relative tooltip | Phase 3 | Standard pattern for all future Plotly tooltips |
| Dual-chart overflow pattern | Phase 3 | Pattern for any multi-chart layout |
| `prevSessionIdRef` pattern | Phase 3 | Standard for all session-change effects |

### 8.3 Deferred to Later Phases

| Feature | Deferred To | Reason |
|---------|------------|--------|
| `staleTime: Infinity` for query | Phase 6 | Performance optimisation, not functional |
| `gcTime: 30min` for query | Phase 6 | Memory management, not functional |
| `useVisibilityQuery` (Intersection Observer) | Phase 6 | Below-fold deferred loading |
| Prefetch on Race nav hover | Phase 6 | Performance optimisation |
| Lighthouse audit | Phase 6 | Performance validation |
| Non-linear degradation modelling | Not planned | Insufficient data for stable polynomial fits |

### 8.4 Shared Data Service Efficiency

Phase 3 continues the shared data service pattern from Phase 1. The `get_processed_race_data()` pipeline runs once per session (and fuel effect combination) and caches the enriched dataset. Phase 2's box plot queries the pace statistics slice; Phase 3's tyre degradation queries the per-lap fuel-corrected times grouped by stint and compound. No redundant computation occurs — both features consume the same cached pipeline output through different aggregation paths.

---

*Documentation Version 1.0 — February 2026*
