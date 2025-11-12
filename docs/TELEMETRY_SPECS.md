# Telemetry Specifications

## Overview

Telemetry data contains high-frequency measurements from car sensors during laps. This document specifies the data structure, sources, transformations, and visualization requirements.

## Data Sources

### Primary: FastF1
FastF1 provides telemetry data through the `get_telemetry()` method on lap objects.

**Available Channels:**
- `Distance` - Distance from start line (meters)
- `Speed` - Car speed (km/h)
- `Throttle` - Throttle position (0-100%)
- `Brake` - Brake pressure (0-100% or binary)
- `nGear` - Current gear (1-8)
- `RPM` - Engine RPM
- `DRS` - DRS status (0-14, where ≥10 is active)
- `Time` - Session time
- `X`, `Y`, `Z` - Position coordinates

### Sampling Rate
- FastF1 telemetry: ~240Hz interpolated to lap distance
- Typical data points per lap: 2000-5000 depending on circuit length

## Data Model

### TypeScript

```typescript
interface TelemetryPoint {
  distance: number      // meters from start line
  speed: number         // km/h
  throttle: number      // 0-100%
  brake: number         // 0-100%
  gear: number          // 1-8
  rpm?: number          // revolutions per minute
  drs?: number          // 0-14 (≥10 = active)
  time?: number         // seconds from lap start
  x?: number            // track position X
  y?: number            // track position Y
}

interface LapTelemetry {
  driver: string
  lapNumber: number
  lapTime: number
  compound?: string
  data: TelemetryPoint[]
}
```

### Python (Pydantic)

```python
from pydantic import BaseModel
from typing import Optional, List

class TelemetryPoint(BaseModel):
    distance: float
    speed: float
    throttle: float
    brake: float
    gear: int
    rpm: Optional[int] = None
    drs: Optional[int] = None
    time: Optional[float] = None
    x: Optional[float] = None
    y: Optional[float] = None

class LapTelemetry(BaseModel):
    driver: str
    lap_number: int
    lap_time: float
    compound: Optional[str] = None
    data: List[TelemetryPoint]
```

## API Endpoints

### Get Telemetry Data

```
GET /telemetry?session={id}&drivers={list}&lap_type={type}

Parameters:
- session: Session identifier
- drivers: Comma-separated driver abbreviations
- lap_type: "fastest" | "average" | "specific"
- lap_number: Required if lap_type="specific"

Response:
{
  "telemetry": [
    {
      "driver": "VER",
      "lapNumber": 15,
      "lapTime": 92.837,
      "compound": "SOFT",
      "data": [
        {
          "distance": 0,
          "speed": 295.4,
          "throttle": 100,
          "brake": 0,
          "gear": 7,
          "rpm": 11500,
          "drs": 12
        },
        ...
      ]
    },
    ...
  ]
}
```

## Data Processing

### Backend Transformations

#### 1. Interpolation
Align telemetry from different laps to common distance points.

```python
import numpy as np
from scipy.interpolate import interp1d

def interpolate_telemetry(telemetry_df, target_distances):
    """
    Interpolate telemetry to common distance grid.
    """
    interpolator = interp1d(
        telemetry_df['Distance'],
        telemetry_df['Speed'],
        kind='linear',
        fill_value='extrapolate'
    )
    return interpolator(target_distances)
```

#### 2. Smoothing
Apply moving average for cleaner visualization.

```python
def smooth_telemetry(data, window_size=5):
    """
    Apply moving average smoothing.
    """
    return data.rolling(window=window_size, center=True).mean()
```

#### 3. Downsampling
Reduce data points for performance.

```python
def downsample_telemetry(telemetry, factor=10):
    """
    Reduce data points by factor.
    """
    return telemetry[::factor]
```

### Delta Calculation

Calculate time delta between laps over distance.

```python
def calculate_delta(reference_telemetry, compare_telemetry):
    """
    Calculate time delta at each distance point.
    
    Returns:
        Array of delta times (seconds)
    """
    # Interpolate to common distances
    distances = np.linspace(0, max_distance, 1000)
    
    ref_time = interpolate_telemetry(reference_telemetry['Time'], distances)
    cmp_time = interpolate_telemetry(compare_telemetry['Time'], distances)
    
    delta = cmp_time - ref_time
    return distances, delta
```

## Visualization

### Chart Types

#### 1. Speed Trace
Line chart showing speed over distance.

**Configuration:**
- X-axis: Distance (meters or % of lap)
- Y-axis: Speed (km/h)
- Multiple lines for driver comparison
- Color-coded by driver/team
- DRS zones highlighted as background regions

#### 2. Throttle/Brake Trace
Overlaid area charts.

**Configuration:**
- Throttle: Green area (0-100%)
- Brake: Red area (0-100%)
- Stacked or overlaid
- Semi-transparent for overlap visibility

#### 3. Multi-Channel View
Synchronized subplots.

**Channels:**
- Speed
- Throttle
- Brake
- Gear (stepped line)
- RPM

**Features:**
- Shared X-axis (distance)
- Vertical cursor for synchronization
- Zoom applies to all subplots

#### 4. Delta Plot
Time delta visualization.

**Configuration:**
- X-axis: Distance
- Y-axis: Delta time (seconds)
- Zero line as reference
- Positive area (slower) in red
- Negative area (faster) in green
- Cumulative delta annotation

### Plotly Configuration

```typescript
const plotlyConfig = {
  data: [{
    x: telemetry.map(p => p.distance),
    y: telemetry.map(p => p.speed),
    type: 'scatter',
    mode: 'lines',
    name: driver,
    line: {
      color: driverColor,
      width: 2
    }
  }],
  layout: {
    title: 'Speed Trace',
    xaxis: {
      title: 'Distance (m)',
      gridcolor: '#333'
    },
    yaxis: {
      title: 'Speed (km/h)',
      gridcolor: '#333'
    },
    plot_bgcolor: '#15151E',
    paper_bgcolor: '#15151E',
    font: { color: '#fff' },
    hovermode: 'x unified'
  },
  config: {
    responsive: true,
    displayModeBar: true,
    modeBarButtonsToRemove: ['lasso2d', 'select2d']
  }
}
```

## Performance Optimization

### Data Size Management

**Problem:** Full telemetry can be 2-5MB per lap.

**Solutions:**
1. **Downsampling:** Reduce to 500-1000 points for visualization
2. **Compression:** Use gzip for API responses
3. **Lazy Loading:** Load on-demand, not upfront
4. **Caching:** Cache processed telemetry

### Frontend Optimization

```typescript
// Lazy load telemetry when chart becomes visible
const [telemetry, setTelemetry] = useState(null)

useEffect(() => {
  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting && !telemetry) {
      fetchTelemetry().then(setTelemetry)
    }
  })
  
  observer.observe(chartRef.current)
  return () => observer.disconnect()
}, [])
```

### Backend Caching

```python
from functools import lru_cache

@lru_cache(maxsize=128)
def get_processed_telemetry(session_id: str, driver: str, lap_number: int):
    """
    Cache processed telemetry in memory.
    """
    # Load and process telemetry
    return processed_data
```

## Special Considerations

### DRS Detection

DRS status interpretation:
- `0-9`: DRS not available or not active
- `10-14`: DRS active (levels vary by source)

Convert to binary:
```python
telemetry['DRS_Active'] = (telemetry['DRS'] >= 10).astype(int)
```

### Gear Shifts

Detect gear changes for analysis:
```python
telemetry['GearShift'] = telemetry['nGear'].diff() != 0
```

### Brake Points

Identify braking zones:
```python
telemetry['Braking'] = telemetry['Brake'] > 10  # 10% threshold
brake_zones = telemetry[telemetry['Braking']].groupby(
    (telemetry['Braking'] != telemetry['Braking'].shift()).cumsum()
)
```

### Corner Detection

Identify corners from speed minima:
```python
from scipy.signal import find_peaks

# Find local speed minima (corners)
speed = telemetry['Speed'].values
minima, _ = find_peaks(-speed, distance=100)
corners = telemetry.iloc[minima]
```

## Testing

### Test Cases

1. **Data Loading:** Verify telemetry loads for all drivers
2. **Interpolation:** Aligned distances match across drivers
3. **Delta Calculation:** Reference delta to itself is zero
4. **Downsampling:** Maintains overall shape/characteristics
5. **Chart Rendering:** Performance with 5+ drivers
6. **Error Handling:** Missing telemetry data

### Mock Data

For development without FastF1:

```typescript
function generateMockTelemetry(lapLength: number): TelemetryPoint[] {
  const points = []
  for (let d = 0; d <= lapLength; d += 10) {
    const progress = d / lapLength
    points.push({
      distance: d,
      speed: 150 + 150 * Math.sin(progress * Math.PI * 4),
      throttle: Math.random() * 100,
      brake: Math.random() > 0.7 ? Math.random() * 100 : 0,
      gear: Math.floor(3 + Math.random() * 4)
    })
  }
  return points
}
```

## Future Enhancements

1. **3D Track View:** Plot telemetry on 3D track model
2. **Predictive Traces:** ML-predicted optimal lap
3. **Real-time Streaming:** Live telemetry during sessions
4. **Custom Channels:** User-defined calculated channels
5. **Audio Playback:** Synthesized engine sound from RPM

