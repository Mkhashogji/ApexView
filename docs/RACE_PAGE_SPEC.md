# Race Page Specification

## Overview

The race page focuses on strategy analysis, tyre management, and pace evolution throughout the race. It provides insights into stint performance, pit stop strategies, and fuel-adjusted pace.

## Layout Structure

```
┌─────────────────────────────────────────────────────┐
│ Header: "Race Analysis"                             │
│ Subtitle: Circuit, Race distance, Winner            │
├─────────────────────────────────────────────────────┤
│ Filters Panel                                       │
│ [Drivers] [Compounds] [Lap Range]                  │
├─────────────────────────────────────────────────────┤
│ Strategy Timeline                                   │
│ Horizontal view of stints and compounds            │
├─────────────────────────────────────────────────────┤
│ Stint Pace Evolution Chart                         │
│ Lap time progression with pit stops marked         │
├─────────────────────────────────────────────────────┤
│ Tyre Degradation Chart                             │
│ Pace loss vs tyre age by compound                 │
├─────────────────────────────────────────────────────┤
│ Pit Stop Analysis Grid                             │
│ Stop times, durations, compound changes            │
├─────────────────────────────────────────────────────┤
│ Fuel-Adjusted Pace Chart                          │
│ Corrected performance comparison                   │
├─────────────────────────────────────────────────────┤
│ AI Strategy Insights                               │
│ Optimal windows, tyre management, anomalies        │
└─────────────────────────────────────────────────────┘
```

## Components

### 1. Filters Panel

**Driver Selection**
- Multi-select dropdown
- Team presets
- Position presets (Top 5, Points finishers)
- Default: Top 3 finishers

**Compound Filter**
- Multi-select for tyre compounds
- Color-coded buttons
- Options: Soft, Medium, Hard, Intermediate, Wet
- Default: All compounds

**Lap Range Slider**
- Select specific lap range for analysis
- Useful for isolating stints or periods
- Default: Full race

### 2. Strategy Timeline

Visual timeline showing each driver's race strategy.

```
VER │███████████║═══════════║░░░░░░░░│
    │   SOFT    │  MEDIUM   │  HARD  │
    │ Lap 1-14  │ Lap 15-32 │ Lap 33-58
    
HAM │═══════════║░░░░░░░░░░░║         │
    │  MEDIUM   │   HARD    │         │
    │ Lap 1-18  │ Lap 19-58 │         │
```

**Legend:**
- █ Soft (red)
- ═ Medium (yellow)
- ░ Hard (white)
- ▒ Intermediate (green)
- ▓ Wet (blue)

**Features:**
- Hover shows stint details
- Click to filter charts to that stint
- Pit stop markers (‖)
- Safety car periods (gray background)
- VSC periods (yellow background)

### 3. Stint Pace Evolution Chart

Line chart showing lap times over lap number.

**X-axis:** Lap number
**Y-axis:** Lap time (seconds)
**Lines:** One per driver
**Visual Elements:**
- Pit stop markers (dashed vertical lines)
- Safety car laps (gray shading)
- In/out laps (lighter opacity)
- Compound changes (line color changes)

**Interactions:**
- Hover: Show lap time, compound, stint lap
- Click pit stop marker: Show pit stop details
- Zoom to stint
- Toggle fuel correction

**Configuration:**
```javascript
{
  data: drivers.map(driver => ({
    x: driver.laps.map(l => l.lapNumber),
    y: driver.laps.map(l => l.lapTime),
    mode: 'lines+markers',
    name: driver.code,
    line: { color: driver.color },
    marker: { 
      size: 4,
      color: driver.laps.map(l => compoundColor[l.compound])
    }
  }))
}
```

### 4. Tyre Degradation Chart

Scatter plot with trend lines showing pace loss over tyre age.

**X-axis:** Tyre age (laps)
**Y-axis:** Lap time delta from stint start (seconds)
**Series:** One per compound
**Trend Lines:** Linear regression for each compound

**Example View:**
```
Δ Lap Time
    +2s │        ○ Soft
        │      ○   ○
    +1s │    ○   ○   ○  Medium
        │  ○   ○   ○   ○
     0s │○───────────────────→
        0   5   10  15  20  25
                Tyre Age (laps)
```

**Features:**
- Filter by driver
- Compare compounds
- Extrapolate for strategy planning
- Show confidence intervals

**Insights:**
```
Soft: +0.08s/lap degradation
Medium: +0.04s/lap degradation
Hard: +0.02s/lap degradation

Optimal Soft stint: 12-15 laps
Optimal Medium stint: 20-25 laps
```

### 5. Pit Stop Analysis Grid

Table comparing pit stop performance.

**Columns:**
- Driver
- Stop number
- Lap in
- Time loss (total)
- Pit duration (stationary)
- Tyre in → out
- Position change

**Example Row:**
```
VER | Stop 1 | Lap 14 | 22.3s | 2.1s | SOFT→MED | P1→P1
```

**Aggregations:**
- Average pit duration by team
- Fastest pit stop
- Most time-efficient strategy
- Undercut/overcut success rate

**Visual Enhancements:**
- Green: Faster than average
- Red: Slower than average
- Bold: Fastest stop of the race

### 6. Fuel-Adjusted Pace Chart

Remove fuel load effect to show true car performance.

**Calculation:**
```python
# Assume 0.035s per lap fuel effect
fuel_kg_per_lap = 1.5
fuel_effect_per_kg = 0.023  # seconds
total_fuel = 110  # kg at start

fuel_at_lap_n = total_fuel - (lap_number * fuel_kg_per_lap)
fuel_correction = fuel_at_lap_n * fuel_effect_per_kg

adjusted_time = lap_time - fuel_correction
```

**Display:**
- Line chart similar to stint pace
- But with fuel correction applied
- Shows which driver truly had faster car

**Use Cases:**
- Compare different strategies
- Identify when driver pushed vs. conserved
- Detect performance issues vs. strategy

### 7. AI Strategy Insights

Automated analysis of race strategies.

**Insight Categories:**

**Optimal Pit Windows**
```
🎯 VER's first stop on lap 14 was optimal.
   Window calculation: Lap 12-16
   Track position protected, tyre delta exploited.
```

**Tyre Management**
```
🔧 HAM showed excellent tyre management in final stint.
   Degradation rate 40% lower than field average.
```

**Strategy Effectiveness**
```
⚡ One-stop strategy cost ALO ~8s vs two-stop.
   Medium→Hard not ideal for this track.
```

**Anomaly Detection**
```
⚠️ PER's lap 23 outlier (5.2s slower).
   Possible: Traffic, mistake, or issue.
```

**What-If Analysis**
```
💭 If HAM had stopped lap 18 instead of lap 20:
   Estimated gain: 2.1s (more aggressive undercut)
```

## Data Loading

### Initial Load
```typescript
// 1. Race result summary
const results = await fetchRaceResults(season, round)

// 2. All lap times
const laps = await fetchLaps(sessionId, 'all')

// 3. Pit stop data
const pitStops = await fetchPitStops(sessionId)

// 4. Strategy timeline data
const stints = computeStints(laps, pitStops)
```

### Computed Data
```typescript
interface Stint {
  driver: string
  stintNumber: number
  compound: TyreCompound
  startLap: number
  endLap: number
  lapCount: number
  averagePace: number
  degradationRate: number
}

function computeStints(laps: Lap[], pitStops: PitStop[]): Stint[] {
  // Group consecutive laps on same compound
  // Calculate average pace and degradation
}
```

## User Workflows

### Workflow 1: Strategy Comparison
1. User selects two drivers with different strategies
2. Views strategy timeline to see pit stop timings
3. Analyzes stint pace to see pace differences
4. Compares tyre degradation rates
5. Determines which strategy was more effective

### Workflow 2: Tyre Analysis
1. User filters to single compound (e.g., Medium)
2. Views degradation chart for all drivers on that compound
3. Identifies who managed tyres best
4. Reads AI insights for management techniques

### Workflow 3: Pit Stop Evaluation
1. User checks pit stop analysis grid
2. Sorts by pit duration
3. Compares team performance
4. Identifies slow stops that cost positions

### Workflow 4: Performance Diagnosis
1. User notices driver finished lower than expected
2. Checks fuel-adjusted pace
3. Compares with teammate
4. Determines if issue was pace, strategy, or incidents

## State Management

### URL State
```
/race?
  season=2024
  &round=1
  &drivers=VER,HAM,LEC
  &compounds=SOFT,MEDIUM
  &lapStart=1
  &lapEnd=58
```

### Local State
```typescript
interface RacePageState {
  selectedDrivers: string[]
  selectedCompounds: TyreCompound[]
  lapRange: [number, number]
  fuelAdjusted: boolean
  highlightedStint: StintId | null
  sortConfig: { column: string; direction: 'asc' | 'desc' }
}
```

## Responsive Design

### Desktop
- Multi-column layout
- All charts visible simultaneously
- Full pit stop table

### Tablet
- Two-column layout
- Charts stacked
- Scrollable pit stop table

### Mobile
- Single column
- Simplified strategy timeline
- Most important chart (stint pace) prioritized
- Pit stop summary (not full table)

## Performance Considerations

- Race data is large (20 drivers × 60 laps = 1200+ data points)
- Virtualize lap table if showing all data
- Downsample telemetry for performance
- Compute stints and degradation on backend
- Cache processed race data

## Testing Checklist

- [ ] Load race data correctly
- [ ] Strategy timeline shows all stints
- [ ] Pit stop markers align with timeline
- [ ] Tyre degradation calculation accurate
- [ ] Fuel adjustment computation correct
- [ ] Compound filter works
- [ ] Lap range slider functional
- [ ] AI insights generate
- [ ] Responsive on mobile
- [ ] Handle safety car periods
- [ ] Handle DNFs and retirements

## Future Enhancements

- Live strategy predictions during race
- Compare with previous races at same circuit
- Optimal strategy calculator
- Team radio integration
- Weather impact analysis
- Position change animation

