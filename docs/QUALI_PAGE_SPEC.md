# Qualifying Page Specification

## Overview

The qualifying page provides detailed lap-by-lap analysis with multi-driver comparison, delta charts, and sector breakdowns. It supports both traditional qualifying and sprint qualifying formats.

## Layout Structure

```
┌─────────────────────────────────────────────────────┐
│ Header: "Qualifying Analysis"                       │
│ Subtitle: Circuit name, date, format               │
├─────────────────────────────────────────────────────┤
│ Filters Panel                                       │
│ [Drivers] [Q1/Q2/Q3] [Traditional/Sprint]          │
├─────────────────────────────────────────────────────┤
│ Sector Performance Cards (3 cards)                 │
│ [Sector 1] [Sector 2] [Sector 3]                   │
├─────────────────────────────────────────────────────┤
│ Speed Trace Chart                                   │
│ Multi-driver telemetry overlay                     │
├─────────────────────────────────────────────────────┤
│ Delta Plot Chart                                    │
│ Time delta to reference driver                     │
├─────────────────────────────────────────────────────┤
│ Lap Times Table                                     │
│ All laps with sectors and compound                 │
├─────────────────────────────────────────────────────┤
│ AI Insights Panel                                   │
│ Automated analysis and observations                │
└─────────────────────────────────────────────────────┘
```

## Components

### 1. Filters Panel

**Driver Multi-Select**
- Dropdown with checkbox selection
- Maximum 6 drivers selectable
- Team color indicators
- Quick presets:
  - "Top 3" - P1, P2, P3
  - "Ferrari" - Both Ferrari drivers
  - "Red Bull" - Both RB drivers

**Session Sub-Select (Q1/Q2/Q3)**
- Radio buttons or tabs
- Show eliminated drivers in each session (grayed out if not participated)
- Default: Q3 (or highest available)

**Format Toggle (Traditional vs Sprint)**
- Toggle switch
- Auto-detected from weekend format
- Manual override allowed

### 2. Sector Performance Cards

Three cards showing best performance in each sector.

**Card Content:**
```
┌──────────────────┐
│ SECTOR 1         │
│ 24.532s          │ ← Best time
│ ● VER            │ ← Driver with color dot
│ +0.012 HAM       │ ← 2nd best with delta
│ +0.045 LEC       │ ← 3rd best with delta
└──────────────────┘
```

**Features:**
- Click to highlight that driver across all charts
- Hover shows full sector telemetry preview
- Purple sector indicators (driver's personal best)

### 3. Speed Trace Chart

Multi-driver telemetry overlay showing speed over distance.

**Data Displayed:**
- X-axis: Distance (m or lap %)
- Y-axis: Speed (km/h)
- Lines: One per selected driver
- Background: DRS zones (light green)

**Interactions:**
- Hover: Show all driver values at that point
- Click legend: Toggle driver visibility
- Zoom: Click and drag
- Pan: Shift + drag
- Reset: Double-click

**Annotations:**
- Turn numbers on X-axis
- Maximum speed markers
- Braking zones (subtle shading)

**Plotly Configuration:**
```javascript
{
  type: 'scatter',
  mode: 'lines',
  hovermode: 'x unified',
  showlegend: true,
  legend: { orientation: 'h', y: -0.2 }
}
```

### 4. Delta Plot Chart

Time delta relative to reference driver over distance.

**Data Displayed:**
- X-axis: Distance (m)
- Y-axis: Delta time (s)
- Zero line: Reference driver
- Positive area: Slower (red fill)
- Negative area: Faster (green fill)

**Reference Selection:**
- Dropdown above chart
- Default: Fastest driver in selected set
- Options: Any selected driver

**Features:**
- Cumulative delta annotation at finish line
- Sector boundaries marked
- Click to see detailed breakdown at that point

**Interpretation Helper:**
```
┌─────────────────────────────────────┐
│ +0.234s slower at T3               │
│ -0.112s faster at T7               │
│ Final delta: +0.122s               │
└─────────────────────────────────────┘
```

### 5. Lap Times Table

Sortable table of all laps for selected drivers.

**Columns:**
- Driver (color-coded)
- Lap number
- Lap time
- S1, S2, S3 times
- Compound (colored dot)
- Track status (🟢/🟡/🔴)
- Delta to fastest

**Features:**
- Sort by any column
- Filter by compound
- Highlight fastest in each sector (purple background)
- Show deleted laps (strikethrough)

**Row Colors:**
- Personal best: Green tint
- Deleted lap: Red tint
- Pit in/out: Gray

### 6. AI Insights Panel

Automated analysis based on telemetry and lap data.

**Insight Types:**

**Braking Analysis:**
```
🔍 VER brakes 12m later into Turn 1 compared to HAM,
   gaining 0.042s per lap.
```

**Sector Performance:**
```
⚡ HAM strongest in Sector 2 (-0.089s vs field avg),
   losing time in Sector 3 (+0.134s).
```

**Setup Hints:**
```
🔧 Similar telemetry patterns suggest LEC and SAI
   running comparable downforce levels.
```

**Consistency:**
```
📊 VER most consistent with σ=0.082s across 5 laps.
   HAM shows higher variance (σ=0.215s).
```

## Data Loading

### Initial Load
1. Fetch session metadata
2. Load fastest lap for each driver
3. Display sector cards and lap table
4. Lazy-load telemetry on scroll

### Progressive Enhancement
1. Show skeleton while loading
2. Render lap data first (fast)
3. Load telemetry for selected drivers (slower)
4. Generate AI insights last (background task)

### API Calls
```typescript
// 1. Session info
const session = await fetchSession(season, round, 'Q')

// 2. Lap data for all drivers
const laps = await fetchLaps(session.id, ['all'])

// 3. Telemetry for selected drivers (lazy)
const telemetry = await fetchTelemetry(
  session.id, 
  selectedDrivers, 
  'fastest'
)

// 4. Delta analysis
const deltas = await fetchDelta(
  session.id,
  referenceDriver,
  selectedDrivers
)
```

## User Workflows

### Workflow 1: Basic Comparison
1. User lands on page → Default shows top 3 qualifiers
2. Sector cards show who was fastest where
3. Speed trace shows where time was gained/lost
4. Delta plot quantifies the differences

### Workflow 2: Detailed Analysis
1. User selects 2 specific drivers (e.g., VER vs HAM)
2. Compares speed traces to find performance differences
3. Examines delta plot to see cumulative effect
4. Reads AI insights for interpretation

### Workflow 3: Teammate Comparison
1. User clicks "Ferrari" preset → Loads LEC and SAI
2. Analyzes sector cards for strengths
3. Reviews consistency in lap table
4. Checks setup similarities in AI insights

### Workflow 4: Q1/Q2/Q3 Progression
1. User switches between Q1, Q2, Q3 tabs
2. Tracks single driver's improvement
3. Sees tyre compound strategy
4. Identifies track evolution effects

## State Management

### URL State (Shareable)
```
/qualifying?
  season=2024
  &round=1
  &drivers=VER,HAM,LEC
  &session=Q3
  &reference=VER
```

### Local State
```typescript
interface QualifyingPageState {
  selectedDrivers: string[]
  sessionPart: 'Q1' | 'Q2' | 'Q3'
  referenceDriver: string
  telemetryLoaded: boolean
  sortColumn: string
  sortDirection: 'asc' | 'desc'
}
```

## Responsive Design

### Desktop (> 1024px)
- Full width charts
- Side-by-side sector cards
- Table with all columns

### Tablet (768-1024px)
- Stacked sector cards
- Simplified table (hide some columns)
- Charts remain full-featured

### Mobile (< 768px)
- Single column layout
- Sector cards in carousel
- Simplified speed trace (no delta plot)
- Condensed table (driver, time, delta only)

## Performance Targets

- Initial page load: < 2s
- Telemetry load: < 1s per driver
- Chart interaction: 60fps
- Delta calculation: < 500ms

## Error Handling

### No Data Available
```
┌─────────────────────────────────────┐
│ ⚠️ Qualifying data not yet available│
│                                     │
│ Session scheduled for:              │
│ Saturday, March 2, 2024 - 15:00 UTC│
└─────────────────────────────────────┘
```

### Partial Data
```
⚠️ Telemetry data not available for HAM lap 12.
   Showing fastest available lap (lap 15).
```

### API Errors
```
❌ Failed to load session data.
   [Retry Button]
```

## Testing Checklist

- [ ] Load qualifying data for traditional weekend
- [ ] Load sprint qualifying data
- [ ] Select/deselect drivers
- [ ] Switch between Q1/Q2/Q3
- [ ] Change reference driver
- [ ] Sort lap table by different columns
- [ ] Zoom/pan on charts
- [ ] Toggle driver visibility
- [ ] Share URL with state
- [ ] Handle missing telemetry
- [ ] Responsive layout on mobile
- [ ] Loading states display correctly
- [ ] AI insights generate successfully

## Future Enhancements

- Compare with previous years
- Overlay track map with telemetry
- Export comparison report
- Video playback synchronized with telemetry
- Compound strategy recommendations

