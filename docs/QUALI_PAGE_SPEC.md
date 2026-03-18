# Qualifying Page Specification

## Overview

The qualifying page provides detailed lap-by-lap analysis with multi-driver comparison, delta charts, sector breakdowns, and ML-powered insights. It supports both traditional qualifying (Q1/Q2/Q3) and sprint qualifying (SQ1/SQ2/SQ3) formats.

**Updated:** December 2025 - React Query integration, Analysis service, 2x2 grid layout

## Layout Structure

```
┌─────────────────────────────────────────────────────┐
│ Header: "QUALIFYING ANALYSIS" (Montserrat, uppercase)│
│ Subtitle: Circuit name, Season, Round               │
├─────────────────────────────────────────────────────┤
│ [Q1] [Q2] [Q3] Tabs    │    Reference: [Dropdown]  │
├─────────────────────────────────────────────────────┤
│ Driver Chips: [VER] [NOR] [HAM] + [Add Drivers]    │
├──────────────────────┬──────────────────────────────┤
│ SPEED TRACE          │ DELTA TO REFERENCE           │
│ (TelemetryLine)      │ (DeltaPlot)                  │
│ - Multi-channel      │ - Sector boundaries          │
│ - DRS zone shading   │ - Final delta annotations    │
│ - Corner annotations │ - Chart sync with telemetry  │
├──────────────────────┼──────────────────────────────┤
│ SECTOR BREAKDOWN     │ AI INSIGHTS                  │
│ (SectorCards)        │ (AnalysisInsights - analysis powered)    │
│ - Theoretical best   │ - Lap similarity scores      │
│ - Purple sectors     │ - Driving style clusters     │
│ - Delta table        │ - Braking differences        │
└──────────────────────┴──────────────────────────────┘
```

### Responsive Behavior

- **Desktop (≥768px):** 2x2 grid layout (`md:grid-cols-2`)
- **Mobile (<768px):** Single column stack with collapsible sections

## Components

### 1. Session Tabs (`QualifyingSessionTabs`)

**Purpose:** Switch between Q1/Q2/Q3 (or SQ1/SQ2/SQ3 for sprint weekends)

**Features:**
- Auto-detect sprint weekend from session data
- Red underline with glow for active tab
- Gray out unavailable sessions
- Keyboard navigation (arrow keys, Home/End)
- ARIA attributes for accessibility

**Props:**
```typescript
interface QualifyingSessionTabsProps {
  selected: QualifyingSessionPart  // 'Q1' | 'Q2' | 'Q3' | 'SQ1' | 'SQ2' | 'SQ3'
  onChange: (session: QualifyingSessionPart) => void
  isSprintWeekend?: boolean
  availableSessions?: QualifyingSessionPart[]
}
```

### 2. Driver Multi-Select (`DriverMultiSelect`)

**Purpose:** Select up to 6 drivers for comparison

**Features:**
- Team-colored chips with remove button
- Team presets (Top 3, Ferrari, McLaren, etc.)
- Full driver name tooltip on hover
- Grouped dropdown by team
- ARIA labels for accessibility
- Click outside to close

**Props:**
```typescript
interface DriverMultiSelectProps {
  selected: string[]
  onChange: (drivers: string[]) => void
  maxDrivers?: number  // default: 6
}
```

### 3. Telemetry Chart (`TelemetryLine`)

**Purpose:** Multi-driver telemetry overlay with channel selection

**Channels:**
- Speed (km/h) - default
- Throttle (%)
- Brake (%)
- Gear (1-8)
- RPM
- DRS (0/1)

**Features:**
- DRS zone shading (light green from track data)
- Corner annotations on x-axis (T1, T2, etc.)
- Channel toggle buttons with red active state
- Zoom/pan synchronization with DeltaPlot
- Team-colored driver traces
- Unified hover tooltips
- Export as PNG

**Props:**
```typescript
interface TelemetryLineProps {
  telemetryData: Map<string, Telemetry>
  selectedDrivers: string[]
  drsZones?: DRSZone[]
  corners?: Corner[]
  trackLength?: number
  onRangeChange?: (xRange: [number, number] | null) => void
  xRange?: [number, number] | null
}
```

### 4. Delta Plot (`DeltaPlot`)

**Purpose:** Time delta to reference driver over lap distance

**Features:**
- Positive area (red) = slower than reference
- Negative area (green) = faster than reference
- Sector boundary vertical lines
- Final delta annotations per driver
- Synchronized zoom/pan with TelemetryLine
- Y-axis auto-scaling with padding

**Props:**
```typescript
interface DeltaPlotProps {
  deltaData: DeltaData[]
  referenceDriver: string
  sectors?: SectorInfo[]
  trackLength?: number
  onRangeChange?: (xRange: [number, number] | null) => void
  xRange?: [number, number] | null
}
```

### 5. Sector Cards (`SectorCards`)

**Purpose:** Sector time breakdown with theoretical best lap calculation

**Features:**
- Three sector cards with fastest time and driver
- Purple indicator for fastest sector
- Theoretical best lap calculation (sum of fastest sectors)
- Delta to pole position
- Detailed comparison table with color-coded deltas
- Purple highlighting for fastest sector times

**Props:**
```typescript
interface SectorCardsProps {
  sectorData: SectorComparison[]
  referenceDriver: string
  poleTime?: number
}
```

### 6. AI Insights Panel (`AnalysisInsights`)

**Purpose:** ML-powered analysis with rule-based fallback

**Data Sources:**
- `/analysis/insights/{session_id}` - Combined insights
- `/analysis/lap-similarity` - Pairwise driver similarity
- `/analysis/driver-style-clustering` - Driving style groups

**Insight Types:**
- **Similarity:** "VER & NOR: 92% similar, main difference in braking"
- **Cluster:** "VER, LEC grouped together: aggressive throttle application"
- **Sector:** "HAM +0.156s vs VER, time loss in S2"
- **Braking:** "NOR brakes ~18m earlier into T12"

**Features:**
- Loading skeleton state
- Error fallback to rule-based insights
- Confidence indicators (high/medium/low)
- Driver color badges

**Props:**
```typescript
interface AnalysisInsightsProps {
  sessionId: string
  sectorData: SectorComparison[]
  referenceDriver: string
  selectedDrivers: string[]
}
```

## Data Loading with React Query

### Hooks Used

```typescript
// Session metadata
const sessionsQuery = useSessionsQuery(season, round)

// Telemetry for selected drivers
const telemetryQuery = useTelemetryQuery(sessionId, selectedDrivers)

// Sector times
const sectorsQuery = useSectorsQuery(sessionId, selectedDrivers)

// Delta analysis
const deltaQuery = useDeltaQuery(sessionId, referenceDriver, compareDrivers)

// Track info (DRS zones, corners, sectors)
const trackQuery = useTrackQuery(round, season)

// ML insights
const mlInsightsQuery = useMLInsightsQuery(sessionId, selectedDrivers)
```

### Cache Strategy

| Data Type | Stale Time | Notes |
|-----------|------------|-------|
| Sessions | 2 minutes | Rarely changes during analysis |
| Telemetry | 30 seconds | Large datasets, aggressive caching |
| Sectors | 30 seconds | Semi-static for historical data |
| Delta | 30 seconds | Computed, cache to avoid recomputation |
| Track | 5 minutes | Static per season |
| ML Insights | 60 seconds | Expensive computation |

## URL State Management

### Shareable URL Format

```
/qualifying?season=2025&round=24&drivers=VER,NOR,PIA&session=Q3&ref=VER
```

### Parameters

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| season | number | 2025 | F1 season year |
| round | number | 24 | Race round number |
| drivers | string[] | VER,NOR,PIA | Comma-separated driver codes |
| session | string | Q3 | Qualifying part (Q1/Q2/Q3/SQ1/SQ2/SQ3) |
| ref | string | First driver | Reference driver for delta |

## Chart Synchronization

Charts share zoom/pan state via React state:

```typescript
const [chartXRange, setChartXRange] = useState<[number, number] | null>(null)

// TelemetryLine updates range
onRangeChange={setChartXRange}
xRange={chartXRange}

// DeltaPlot receives same range
onRangeChange={setChartXRange}
xRange={chartXRange}
```

On Plotly `relayout` event, both charts sync their x-axis range.

## Accessibility

### ARIA Attributes

- `role="tablist"` on session tabs container
- `role="tab"` and `aria-selected` on each tab
- `aria-label` on charts (e.g., "Telemetry speed chart comparing selected drivers")
- `aria-current="page"` on active navigation item
- `role="listbox"` on driver selection

### Keyboard Navigation

- Tab through interactive elements
- Arrow keys for session tab navigation
- Escape to close driver dropdown
- Enter/Space to toggle selections

### Color Contrast

- All text meets WCAG AA (4.5:1 ratio)
- Delta colors (red/green) supplemented with +/- signs
- Purple sector indicator has sufficient contrast

## Performance Optimizations

1. **Memoization:** `useMemo` for traces, processed data
2. **Dynamic Import:** Plotly loaded client-side only
3. **Query Deduplication:** React Query prevents duplicate requests
4. **Lazy Loading:** Charts only render when data available
5. **Telemetry Downsampling:** Consider for very long traces

## Error Handling

### No Data

```
┌─────────────────────────────────────┐
│ Select drivers above to begin       │
│ analysis                            │
└─────────────────────────────────────┘
```

### API Error

```
┌─────────────────────────────────────┐
│ Failed to load qualifying data.     │
│ Please try again.                   │
│                                     │
│        [Retry Button]               │
└─────────────────────────────────────┘
```

### Analysis Service Unavailable

AnalysisInsights automatically falls back to rule-based insights when ML endpoints fail.

## Testing Checklist

- [ ] Load qualifying data for traditional weekend
- [ ] Load sprint qualifying data (SQ1/SQ2/SQ3)
- [ ] Select/deselect drivers (max 6)
- [ ] Switch between Q1/Q2/Q3 tabs
- [ ] Change reference driver
- [ ] Verify chart zoom/pan sync
- [ ] Verify DRS zone shading appears
- [ ] Verify sector boundaries in delta plot
- [ ] Verify theoretical best lap calculation
- [ ] Test ML insights loading and fallback
- [ ] Verify URL state persistence
- [ ] Share URL and verify state restored
- [ ] Test responsive layout on mobile
- [ ] Keyboard navigation works
- [ ] Screen reader announcements
- [ ] Loading skeletons display

## Sprint Weekend Support

When `isSprintWeekend` is detected:
- Session tabs show SQ1, SQ2, SQ3
- Session ID format changes to `{season}_{round}_Sprint_Qualifying`
- Sprint badge displayed next to tabs
