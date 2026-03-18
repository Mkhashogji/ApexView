# Features Specification

## 1. Home / Weekend Overview

### Purpose
Central dashboard showing current race weekend status and quick access to all sessions.

### Features
- **Current Weekend Info**: Circuit name, country, dates
- **Session Status**: List of completed and upcoming sessions
- **Quick Stats**: Fastest lap, pole position, top speed
- **Recent Activity**: Latest analyzed sessions
- **Navigation Cards**: Quick links to Qualifying, Race, Practice, Track pages

### Data Requirements
- Current season and round
- Session schedule
- Session results summary

## 2. Qualifying Analysis Page

**Updated:** December 2025 - ML integration, 2x2 grid layout, React Query

### Purpose
Detailed lap-by-lap analysis with multi-driver comparison, ML-powered insights, and synchronized chart interactions.

### Layout
2x2 grid on desktop, single column on mobile:
- Top Left: Speed Trace (TelemetryLine)
- Top Right: Delta to Reference (DeltaPlot)
- Bottom Left: Sector Breakdown (SectorCards)
- Bottom Right: AI Insights (ML-powered)

### Features

#### Driver Selection (`DriverMultiSelect`)
- Multi-select dropdown for up to 6 drivers
- Team color-coded chips with remove button
- Quick presets: Top 3, Ferrari, McLaren, Mercedes, Red Bull
- Drivers grouped by team in dropdown
- Full name tooltip on hover
- ARIA labels for accessibility

#### Session Tabs (`QualifyingSessionTabs`)
- Traditional: Q1, Q2, Q3 tabs
- Sprint: SQ1, SQ2, SQ3 tabs (auto-detected)
- Red underline with glow for active tab
- Keyboard navigation support
- Disabled state for unavailable sessions

#### Telemetry Chart (`TelemetryLine`)
- **Channels:** Speed, Throttle, Brake, Gear, RPM, DRS
- Team-colored driver traces
- DRS zone shading (light green from track data)
- Corner annotations on x-axis (T1, T2, etc.)
- Synchronized zoom/pan with Delta Plot
- Export to PNG with 2x scale
- ARIA label for screen readers

#### Delta Plot (`DeltaPlot`)
- Time delta vs reference driver over distance
- Positive (red) = slower, Negative (green) = faster
- Sector boundary vertical lines
- Final delta annotations at lap end
- Synchronized zoom/pan with Telemetry
- Auto-scaling Y-axis

#### Sector Cards (`SectorCards`)
- Three cards with fastest sector time + driver
- Purple indicator for fastest sectors
- **Theoretical Best Lap** calculation (sum of fastest sectors)
- Delta to pole position display
- Detailed comparison table with color-coded deltas
- Purple highlighting for best sector times in table

#### AI Insights Panel (`AnalysisInsights`) - **Analysis Integrated**
- Fetches from Analysis service endpoints:
  - `/analysis/insights/{session_id}` - Combined insights
  - `/analysis/lap-similarity` - Pairwise driver similarity
  - `/analysis/driver-style-clustering` - Driving style groups
- **Insight Types:**
  - Similarity: "VER & NOR: 92% similar, main difference in braking"
  - Cluster: "VER, LEC grouped: aggressive throttle application"
  - Sector: "HAM +0.156s vs VER, time loss in S2"
  - Braking: "NOR brakes ~18m earlier into T12"
- Loading skeleton state
- **Automatic fallback** to rule-based insights if ML unavailable
- Confidence indicators (high/medium/low)
- Driver color badges

### Data Fetching (React Query)

```typescript
// Session metadata
useSessionsQuery(season, round)

// Telemetry for selected drivers  
useTelemetryQuery(sessionId, selectedDrivers)

// Sector times
useSectorsQuery(sessionId, selectedDrivers)

// Delta analysis
useDeltaQuery(sessionId, referenceDriver, compareDrivers)

// Track info (DRS, corners, sectors)
useTrackQuery(round, season)

// ML insights
useMLInsightsQuery(sessionId, selectedDrivers)
useLapSimilarityQuery(sessionId, driver1, driver2)
useDriverClusteringQuery(sessionId, drivers)
```

### URL State (Shareable)
```
/qualifying?season=2025&round=24&drivers=VER,NOR,PIA&session=Q3&ref=VER
```

### User Workflows
1. Select 2-3 drivers to compare (or use presets)
2. Switch between Q1/Q2/Q3 to see session progression
3. View sector cards for overall performance + theoretical best
4. Examine telemetry traces (zoom syncs with delta plot)
5. Analyze delta plot to identify corners where time is gained/lost
6. Read ML-powered AI insights for automated analysis

## 3. Race Analysis Page

### Purpose
Strategy and pace analysis focusing on stints, tyres, and race evolution.

### Features

#### Driver Selection
- Multi-select for driver comparison
- Filter by team or position

#### Compound Filter
- Filter analysis by tyre compound
- Compare pace on different compounds

#### Stint Pace Evolution Chart
- Lap time over lap number
- Grouped by stint (visual separators)
- Color-coded by compound
- Fuel-corrected pace option
- Pit stop markers

#### Tyre Degradation Chart
- Pace loss vs. tyre age
- Separate lines per compound
- Extrapolation for strategy planning
- Temperature and track condition context

#### Pit Stop Summary
- Stop times and durations
- Tyre changes (in/out compounds)
- Time loss in pit lane
- Comparative analysis (driver vs. field average)

#### Strategy Timeline
- Horizontal timeline view of entire race
- Stint blocks colored by compound
- Position changes marked
- Safety car / VSC periods highlighted

#### Fuel-Adjusted Pace
- Remove fuel load effect from lap times
- True performance comparison
- Adjustable fuel consumption rate

#### AI Insights
- Strategy effectiveness analysis
- Optimal pit window identification
- Tyre management observations
- Pace anomaly detection

### User Workflows
1. View stint pace to understand race evolution
2. Analyze tyre degradation for each compound
3. Compare pit stop strategies
4. Identify fuel-corrected pace for true performance

## 4. Practice Sessions Page

### Purpose
Free practice analysis focusing on consistency, setup work, and long run pace.

### Features

#### Session Selector
- Choose between FP1, FP2, FP3
- Show session duration and conditions

#### Driver Selection
- Standard multi-select

#### Lap Time Consistency Chart
- Scatter plot of lap times
- Standard deviation indicators
- Identify representative laps
- Filter out outliers (in/out laps)

#### Telemetry Overlay
- Similar to qualifying page
- Multiple lap comparison
- Run analysis (consecutive laps)

#### Long Run Analysis
- Pace degradation over stint
- High fuel simulation
- Race pace prediction

#### Setup Balance Analysis
- Understeer/oversteer detection from telemetry
- Corner entry vs. exit performance
- Brake stability indicators
- Turn-in characteristics

#### Run Breakdown
- Categorize runs by type (quali sim, race sim, aero test)
- Lap count and pace for each run
- Tyre compound and age

#### AI Insights
- Setup direction recommendations
- Balance issues identification
- Consistency patterns
- Preparation effectiveness

## 5. Track Page

### Purpose
Circuit-specific information and geographical/technical details.

### Features

#### Track Map Visualization
- SVG or Three.js rendered circuit
- Turn numbers and names
- Direction arrows
- Sector boundaries marked
- DRS zones highlighted
- Overtaking zones indicated

#### Elevation Profile
- Height variation over lap distance
- Synced with track map
- Gradient indicators
- Max/min elevation marked

#### Sector Information Cards
- Characteristics of each sector
- Average speeds
- Corner types
- Key challenges

#### DRS Zones Detail
- Detection points
- Activation points
- End points
- Zone length and effectiveness

#### Corner Analysis
- List of all corners with details
- Corner number, name, type (left/right)
- Gear used
- Typical speed
- Difficulty rating

#### Track Statistics
- Circuit length
- Number of turns
- Race distance (laps and km)
- Lap record with driver and year
- First race year
- Track layout variants

### User Workflows
1. Explore track layout with interactive map
2. Understand elevation changes
3. Study DRS zones for overtaking analysis
4. Learn corner characteristics

## 6. Cross-Page Features

### Common Components

#### Time Format
- Always show: MM:SS.mmm
- Delta format: +/- SS.mmm
- Consistent precision (3 decimal places)

#### Driver Identifiers
- Three-letter abbreviation (VER, HAM, etc.)
- Team color coding
- Hover shows full name and team

#### Session Context
- Always visible: Which session is being viewed
- Quick session switcher
- Weekend format indicator

#### Data Freshness
- Last updated timestamp
- Refresh button for latest data
- Loading states during fetch

### Filtering & Comparison

#### Global Filters (persistent across pages)
- Season and race selection
- Session selection
- Driver selection

#### Page-Specific Filters
- Lap type (all, clean, fastest)
- Tyre compound
- Weather conditions
- Track status (green, yellow, red)

### Export & Sharing

#### Export Options
- CSV export of filtered data
- PNG/SVG export of charts
- Session summary report

#### Sharing
- Shareable URLs with filter state
- Copy analysis link
- Social media preview cards

## 7. Future Features (Roadmap)

### Phase 2
- Historical comparison (multi-season)
- Weather impact analysis
- Driver rating algorithm
- Teammate comparison dashboard

### Phase 3
- Live timing integration
- Push notifications
- Mobile app
- Video synchronization with F1TV

### Phase 4
- Telemetry analysis predictions
- Community features
- Custom analysis tools
- API access for developers

