# Track Page Specification

## Overview

The track page provides comprehensive circuit information including layout, sectors, DRS zones, corners, and elevation profile. It helps users understand the track characteristics and their impact on performance.

## Layout Structure

```
┌─────────────────────────────────────────────────────┐
│ Header: Circuit Name                                │
│ Location, First race, Length, Lap record           │
├─────────────────────────────────────────────────────┤
│ Track Layout Visualization                         │
│ SVG/3D circuit with turn numbers and DRS zones    │
├─────────────────────────────────────────────────────┤
│ Elevation Profile                                  │
│ Height changes over lap distance                   │
├─────────────────────────────────────────────────────┤
│ Sector Information Cards (3 cards)                │
│ [Sector 1] [Sector 2] [Sector 3]                  │
├─────────────────────────────────────────────────────┤
│ DRS Zones Detail                                   │
│ Detection and activation points                    │
├─────────────────────────────────────────────────────┤
│ Corner-by-Corner Analysis                         │
│ Table of all corners with characteristics          │
├─────────────────────────────────────────────────────┤
│ Track Statistics                                   │
│ Records, characteristics, trivia                   │
└─────────────────────────────────────────────────────┘
```

## Components

### 1. Circuit Header

**Information Displayed:**
- Circuit full name
- Location (city, country) with flag
- First F1 race year
- Track length (meters/kilometers)
- Number of turns
- Lap record (time, driver, year)
- Circuit type (Street, Permanent, Hybrid)

**Example:**
```
┌─────────────────────────────────────────┐
│ 🏁 Circuit de Monaco                    │
│ 📍 Monte Carlo, Monaco 🇲🇨               │
│ 🗓️  First Race: 1950                     │
│ 📏 Length: 3,337 m (2.074 mi)           │
│ 🔄 Turns: 19                             │
│ ⏱️  Lap Record: 1:12.909                │
│    Lewis Hamilton, 2021                 │
│ 🏗️  Type: Street Circuit                 │
└─────────────────────────────────────────┘
```

### 2. Track Layout Visualization

Interactive 2D or 3D visualization of the circuit.

**Rendering Options:**

**Option A: SVG 2D Map**
- Vector graphics for scalability
- Color-coded sections
- Turn numbers
- DRS zones highlighted
- Start/finish line marked

**Option B: Three.js 3D View**
- Rotate and zoom
- True elevation representation
- Camera fly-through
- Realistic track surface

**Interactive Elements:**
- Click turn: Show corner details
- Hover DRS zone: Show activation/detection points
- Click sector: Highlight that sector
- Zoom controls

**Data Points Displayed:**
```javascript
interface TrackLayout {
  points: { x: number; y: number; z?: number }[]
  turns: Turn[]
  sectors: SectorBoundary[]
  drsZones: DRSZone[]
  startFinishLine: { x: number; y: number }
}
```

**Visual Layers:**
- Base track line (white/gray)
- Sector colors (red, yellow, green)
- DRS zones (green overlay)
- Turn numbers (white labels)
- Runoff areas (light gray)

### 3. Elevation Profile

2D chart showing height changes over lap distance.

**X-axis:** Distance (meters or lap %)
**Y-axis:** Elevation (meters above sea level)
**Visual Elements:**
- Area chart with gradient fill
- Uphill sections (red gradient)
- Downhill sections (blue gradient)
- Flat sections (gray)

**Example: Spa-Francorchamps**
```
Elevation (m)
    600 │     ╱╲
        │    ╱  ╲___
    580 │   ╱       ╲
        │  ╱         ╲___
    560 │─╱─────────────╲────
        0  1km  2km  3km  4km  5km
```

**Features:**
- Hover: Show exact elevation
- Click: Show which corner
- Gradient percentage displayed
- Max/min elevation marked

**Data Structure:**
```typescript
interface ElevationData {
  distance: number  // meters
  elevation: number // meters above base
  gradient?: number // percentage incline/decline
}
```

### 4. Sector Information Cards

Three cards describing each sector's characteristics.

**Card Structure:**
```
┌─────────────────────────────────┐
│ SECTOR 1                         │
│ Distance: 0 - 1,760 m           │
│ Duration: ~24.5s                │
│                                 │
│ Characteristics:                │
│ • High-speed straights          │
│ • Heavy braking into Turn 1     │
│ • Traction out of Turn 3        │
│                                 │
│ Key Corners: 1, 2, 3            │
│ DRS Zone: Yes (Main straight)   │
│                                 │
│ Fastest 2024: 24.532s (VER)     │
│ Avg Speed: 237 km/h             │
└─────────────────────────────────┘
```

**Data Requirements:**
- Start/end distance
- Average sector time
- Corner list
- DRS availability
- Speed characteristics
- Historical fastest times

### 5. DRS Zones Detail

List and visualization of all DRS zones.

**Table Format:**

| Zone | Detection | Activation | End | Length | Description |
|------|-----------|------------|-----|--------|-------------|
| 1 | Turn 16 | Finish Line | Turn 1 | 850m | Main Straight |
| 2 | Turn 9 | Turn 10 | Turn 11 | 420m | Back Straight |

**Visual Map:**
- Show on track layout
- Color-code zones
- Arrow showing direction
- Measurement annotations

**Zone Card:**
```
┌─────────────────────────────────┐
│ DRS ZONE 1 - Main Straight      │
│                                 │
│ Detection: 5,180m (Turn 16)     │
│ Activation: 5,281m (Start/Finish)│
│ End Point: 200m (Turn 1)        │
│                                 │
│ Available Distance: 850m        │
│ Speed Gain: ~10-15 km/h         │
│ Overtakes 2024: 23              │
└─────────────────────────────────┘
```

### 6. Corner-by-Corner Analysis

Comprehensive table of every corner.

**Columns:**
- Corner # and Name
- Type (Left/Right)
- Apex Distance (m)
- Gear
- Speed (km/h)
- Angle (degrees)
- Difficulty (1-5 ⭐)

**Example Rows:**

| # | Name | Type | Distance | Gear | Speed | Angle | Difficulty |
|---|------|------|----------|------|-------|-------|------------|
| 1 | Sainte Dévote | Right | 167m | 2 | 85 km/h | 120° | ⭐⭐⭐⭐ |
| 2 | Beau Rivage | Right | 280m | 5 | 180 km/h | 45° | ⭐⭐ |
| 3 | Massenet | Left | 450m | 3 | 115 km/h | 90° | ⭐⭐⭐ |

**Interactive Features:**
- Click corner: Highlight on track map
- Sort by any column
- Filter by corner type
- Search by name

**Corner Detail Modal:**
```
┌─────────────────────────────────────┐
│ TURN 1 - SAINTE DÉVOTE              │
├─────────────────────────────────────┤
│ Type: Right-hander                  │
│ Gear: 2nd                           │
│ Apex Speed: 85 km/h                 │
│ Entry Speed: 295 km/h               │
│ Braking Point: ~100m before apex    │
│ Difficulty: ⭐⭐⭐⭐                   │
│                                     │
│ Description:                        │
│ Tight right-hander immediately after│
│ the start. Heavy braking zone. Key  │
│ overtaking opportunity on Lap 1.    │
│                                     │
│ 2024 Incidents: 5                   │
│ [View Telemetry] [View Onboard]    │
└─────────────────────────────────────┘
```

### 7. Track Statistics

Additional circuit information and trivia.

**Categories:**

**Records**
- Lap record
- Race record
- Most wins (driver)
- Most wins (constructor)
- Most poles

**Characteristics**
- Track surface (asphalt type)
- Direction (clockwise/counter-clockwise)
- Average speed
- Minimum speed corner
- Maximum speed point
- Overtaking difficulty (1-10)

**Recent Changes**
- Layout modifications
- Safety improvements
- DRS zone adjustments

**Trivia**
- Unique features
- Historical moments
- Track nickname

**Example:**
```
┌─────────────────────────────────────┐
│ 📊 TRACK STATISTICS                 │
├─────────────────────────────────────┤
│ Direction: Clockwise                │
│ Average Speed: 218 km/h             │
│ Top Speed Location: Main Straight   │
│ Slowest Corner: Fairmont (T6, 48km/h)│
│ Overtaking Difficulty: 9/10         │
│                                     │
│ 🏆 Most Successful Driver:          │
│ Ayrton Senna (6 wins)               │
│                                     │
│ 🏆 Most Successful Team:            │
│ McLaren (15 wins)                   │
│                                     │
│ 💡 Did You Know?                    │
│ Monaco is the shortest circuit on   │
│ the F1 calendar at just 3.337km.   │
└─────────────────────────────────────┘
```

## Data Loading

### Static Data
Track characteristics don't change often, so can be statically stored.

**File Structure:**
```
data/static/circuits/
  ├── bahrain.json
  ├── monaco.json
  ├── silverstone.json
  └── ...
```

**JSON Schema:**
```json
{
  "circuitName": "Circuit de Monaco",
  "location": {
    "city": "Monte Carlo",
    "country": "Monaco",
    "countryCode": "MC"
  },
  "metadata": {
    "firstRace": 1950,
    "length": 3337,
    "turns": 19,
    "lapRecord": {
      "time": "1:12.909",
      "driver": "HAM",
      "year": 2021
    }
  },
  "layout": {
    "coordinates": [...],
    "turns": [...],
    "sectors": [...]
  },
  "drsZones": [...],
  "corners": [...],
  "elevation": [...]
}
```

### API Endpoint
```
GET /track/{round}?season={year}

Response: TrackResponse (from DTO)
```

## User Workflows

### Workflow 1: Track Familiarization
1. User selects track from calendar
2. Views track layout to understand shape
3. Studies elevation profile
4. Reviews corner characteristics
5. Learns DRS zones for race strategy

### Workflow 2: Corner Study
1. User clicks specific corner on map
2. Views corner details (gear, speed, angle)
3. Reads description and characteristics
4. Optionally views telemetry from sessions

### Workflow 3: Strategy Planning
1. User checks DRS zones
2. Studies overtaking opportunities
3. Reviews sector characteristics
4. Plans where lap time can be gained

### Workflow 4: Historical Context
1. User reviews lap records
2. Checks most successful drivers/teams
3. Reads track trivia
4. Understands track evolution

## Interactive Features

### Track Map Interactions
- **Click turn:** Show turn details
- **Hover sector:** Highlight and show info
- **Click DRS zone:** Show activation details
- **Double-click:** Reset view
- **Scroll:** Zoom in/out
- **Drag:** Pan view

### Elevation Profile Sync
- Hover on elevation chart → Highlight position on track map
- Click on track map → Jump to that position in elevation chart
- Synchronized tooltips

### Corner Filter
- Filter by gear (show only 2nd gear corners)
- Filter by type (left/right)
- Filter by difficulty
- Search by name

## Responsive Design

### Desktop
- Side-by-side track map and elevation
- Full corner table
- All statistics visible

### Tablet
- Stacked track map and elevation
- Scrollable corner table
- Collapsed statistics (expandable)

### Mobile
- Single column
- Simplified track map
- Condensed corner list
- Priority info only

## Accessibility

- Alt text for track map
- ARIA labels for interactive elements
- Keyboard navigation for corner list
- High contrast mode support

## Testing Checklist

- [ ] Load track data correctly
- [ ] Track map renders properly
- [ ] Elevation profile displays
- [ ] DRS zones highlighted correctly
- [ ] Corner table sortable/filterable
- [ ] Interactive elements clickable
- [ ] Responsive on all screen sizes
- [ ] Data loads from static files
- [ ] Sector cards show accurate info
- [ ] Records and statistics display

## Future Enhancements

- **3D flythrough:** Animated camera tour
- **VR support:** Immersive track exploration
- **Telemetry overlay:** Show actual driver line on map
- **Weather zones:** Track different weather in sections
- **Historical layouts:** Show track evolution over years
- **User annotations:** Let users add notes to corners
- **Comparison view:** Compare two tracks side-by-side

