# Data Handling Rules

## FastF1 Library

### Overview
FastF1 is the primary data source for F1 session, lap, and telemetry data. It downloads data from the official F1 API and provides a pandas-based interface.

### Installation
```bash
pip install fastf1
```

### Basic Usage

```python
import fastf1
from fastf1 import plotting

# Enable cache (ALWAYS do this)
fastf1.Cache.enable_cache('path/to/cache')

# Load a session
session = fastf1.get_session(2024, 'Bahrain', 'Q')
session.load()  # Downloads data if not cached

# Access data
laps = session.laps
results = session.results
telemetry = laps.pick_driver('VER').pick_fastest().get_telemetry()
```

## Data Structure

### Event Hierarchy
```
Season (2024)
└── Event (Round 1 - Bahrain)
    ├── Practice 1
    ├── Practice 2
    ├── Practice 3
    ├── Qualifying
    │   ├── Q1
    │   ├── Q2
    │   └── Q3
    └── Race
```

### Session Object

```python
session = fastf1.get_session(2024, 1, 'Q')
session.load()

# Attributes
session.name           # 'Qualifying'
session.date           # datetime object
session.event          # Event object
session.laps           # DataFrame of all laps
session.results        # DataFrame of final results
session.weather_data   # DataFrame of weather conditions
```

### Laps DataFrame

```python
laps = session.laps

# Important columns:
laps['Driver']         # 3-letter abbreviation
laps['LapNumber']      # int
laps['LapTime']        # timedelta
laps['Sector1Time']    # timedelta
laps['Sector2Time']    # timedelta
laps['Sector3Time']    # timedelta
laps['Compound']       # 'SOFT', 'MEDIUM', 'HARD', etc.
laps['TyreLife']       # Tyre age in laps
laps['IsPersonalBest'] # bool
laps['IsAccurate']     # bool (valid lap time)

# Filtering
ver_laps = laps.pick_driver('VER')
fastest_lap = ver_laps.pick_fastest()
clean_laps = laps[laps['IsAccurate']]
```

### Telemetry DataFrame

```python
lap = laps.pick_driver('VER').pick_fastest()
telemetry = lap.get_telemetry()

# Available channels:
telemetry['Time']      # Time since lap start (timedelta)
telemetry['Distance']  # Distance from start line (meters)
telemetry['Speed']     # km/h
telemetry['Throttle']  # 0-100%
telemetry['Brake']     # 0-100% or binary
telemetry['nGear']     # Current gear (1-8)
telemetry['RPM']       # Engine RPM
telemetry['DRS']       # 0-14 (≥10 = active)
telemetry['X']         # Track position X
telemetry['Y']         # Track position Y
telemetry['Z']         # Track position Z
```

## Common Operations

### Get Fastest Laps

```python
# Single driver
ver_fastest = session.laps.pick_driver('VER').pick_fastest()

# All drivers
fastest_laps = session.laps.groupby('Driver').apply(
    lambda df: df[df['LapTime'] == df['LapTime'].min()]
)
```

### Filter by Compound

```python
# Get all laps on soft tyres
soft_laps = session.laps[session.laps['Compound'] == 'SOFT']

# Get stint data
def get_stints(driver_laps):
    stints = []
    current_compound = None
    stint_start = 0
    
    for idx, lap in driver_laps.iterrows():
        if lap['Compound'] != current_compound:
            if current_compound is not None:
                stints.append({
                    'compound': current_compound,
                    'start_lap': stint_start,
                    'end_lap': lap['LapNumber'] - 1
                })
            current_compound = lap['Compound']
            stint_start = lap['LapNumber']
    
    # Add final stint
    stints.append({
        'compound': current_compound,
        'start_lap': stint_start,
        'end_lap': driver_laps.iloc[-1]['LapNumber']
    })
    
    return stints
```

### Compare Telemetry

```python
# Get two drivers' fastest laps
ver_lap = session.laps.pick_driver('VER').pick_fastest()
ham_lap = session.laps.pick_driver('HAM').pick_fastest()

# Get telemetry
ver_tel = ver_lap.get_telemetry()
ham_tel = ham_lap.get_telemetry()

# Interpolate to common distance
from scipy.interpolate import interp1d

common_distance = np.linspace(0, 5000, 1000)

ver_speed = interp1d(ver_tel['Distance'], ver_tel['Speed'])(common_distance)
ham_speed = interp1d(ham_tel['Distance'], ham_tel['Speed'])(common_distance)

# Calculate delta
speed_delta = ham_speed - ver_speed
```

### Weekend Format Detection

```python
def is_sprint_weekend(event):
    """Check if event has sprint format."""
    try:
        event.get_session('Sprint Qualifying')
        return True
    except:
        return False

# Usage
event = fastf1.get_event(2024, 'Brazil')
if is_sprint_weekend(event):
    sessions = ['FP1', 'Sprint Qualifying', 'Sprint', 'Qualifying', 'Race']
else:
    sessions = ['FP1', 'FP2', 'FP3', 'Qualifying', 'Race']
```

## Data Quality Issues

### Missing Data

```python
# Check for missing lap times
laps_with_times = laps[laps['LapTime'].notna()]

# Check for missing telemetry
try:
    telemetry = lap.get_telemetry()
    if len(telemetry) == 0:
        print("Empty telemetry")
except Exception as e:
    print(f"Telemetry unavailable: {e}")
```

### Invalid Laps

```python
# Filter out invalid laps
valid_laps = laps[laps['IsAccurate'] == True]

# Remove in/out laps for race pace analysis
clean_laps = laps[
    (laps['PitInTime'].isna()) &  # Not pit in lap
    (laps['PitOutTime'].isna())   # Not pit out lap
]
```

### Outlier Detection

```python
import numpy as np

def remove_outliers(lap_times, threshold=3.0):
    """Remove laps beyond threshold standard deviations."""
    times = lap_times.dropna()
    mean = times.mean()
    std = times.std()
    
    z_scores = np.abs((times - mean) / std)
    return lap_times[z_scores < threshold]

# Usage
clean_times = remove_outliers(laps['LapTime'].dt.total_seconds())
```

## Performance Optimization

### Cache Strategy

```python
from pathlib import Path

# Set up cache
CACHE_DIR = Path('data/cache')
CACHE_DIR.mkdir(parents=True, exist_ok=True)
fastf1.Cache.enable_cache(str(CACHE_DIR))

# Cache is permanent - data downloaded once
# Clear cache if corrupted:
# rm -rf data/cache/*
```

### Lazy Loading

```python
# Don't load full session if only need results
session = fastf1.get_session(2024, 1, 'Q')
# session.load()  # Skip this if not needed

# Just get results without full lap data
results = session.results  # Lightweight
```

### Downsampling Telemetry

```python
# Original: ~240Hz, 3000-5000 points per lap
telemetry = lap.get_telemetry()

# Downsample for visualization
downsampled = telemetry[::10]  # Every 10th point

# Or resample to specific frequency
import pandas as pd
telemetry_resampled = telemetry.set_index('Time').resample('100ms').mean()
```

## Data Transformations

### Time Conversions

```python
# Convert timedelta to seconds
lap_time_seconds = lap['LapTime'].total_seconds()

# Format for display
def format_lap_time(timedelta):
    """Format timedelta as MM:SS.mmm"""
    total_seconds = timedelta.total_seconds()
    minutes = int(total_seconds // 60)
    seconds = total_seconds % 60
    return f"{minutes}:{seconds:06.3f}"

# Usage
print(format_lap_time(lap['LapTime']))  # "1:32.837"
```

### Distance Normalization

```python
# Normalize distance to percentage
def normalize_distance(telemetry, lap_length):
    """Convert distance to lap percentage."""
    telemetry['DistancePct'] = telemetry['Distance'] / lap_length * 100
    return telemetry
```

### Speed Units

```python
# FastF1 provides km/h
# Convert to mph if needed
telemetry['SpeedMPH'] = telemetry['Speed'] * 0.621371

# Convert to m/s
telemetry['SpeedMS'] = telemetry['Speed'] / 3.6
```

## Static Circuit Data

### Circuit Information Format

Store in `data/static/circuits/{circuit-name}.json`:

```json
{
  "circuitName": "Bahrain International Circuit",
  "round": 1,
  "season": 2024,
  "length": 5412,
  "turns": 15,
  "sectors": [
    {
      "sectorNumber": 1,
      "startDistance": 0,
      "endDistance": 1804
    }
  ],
  "drsZones": [
    {
      "zoneNumber": 1,
      "detectionPoint": 5180,
      "activationPoint": 5281,
      "endPoint": 200
    }
  ],
  "corners": [
    {
      "cornerNumber": 1,
      "name": "Turn 1",
      "distance": 235,
      "type": "right",
      "gear": 2,
      "speed": 95
    }
  ],
  "elevationData": [
    { "distance": 0, "elevation": 0 },
    { "distance": 500, "elevation": 2 }
  ]
}
```

### Loading Circuit Data

```python
import json
from pathlib import Path

def load_circuit_data(season: int, round: int):
    """Load static circuit data."""
    # Get circuit name from FastF1
    event = fastf1.get_event(season, round)
    circuit_name = event.Location.lower().replace(' ', '-')
    
    # Load static data
    circuit_file = Path(f'data/static/circuits/{circuit_name}.json')
    if circuit_file.exists():
        with open(circuit_file) as f:
            return json.load(f)
    
    return None
```

## Error Handling

### Common Errors

```python
from fastf1.core import SessionNotAvailableError

try:
    session = fastf1.get_session(2024, 1, 'Q')
    session.load()
except SessionNotAvailableError:
    print("Session not available (future or cancelled)")
except Exception as e:
    print(f"Error loading session: {e}")

# Check if data is available before accessing
if session.laps is not None and len(session.laps) > 0:
    fastest = session.laps.pick_fastest()
else:
    print("No lap data available")
```

### Timeout Handling

```python
import asyncio

async def load_session_with_timeout(season, round, session_name, timeout=30):
    """Load session with timeout."""
    try:
        session = fastf1.get_session(season, round, session_name)
        # Run blocking load in executor
        loop = asyncio.get_event_loop()
        await asyncio.wait_for(
            loop.run_in_executor(None, session.load),
            timeout=timeout
        )
        return session
    except asyncio.TimeoutError:
        raise Exception(f"Session load timed out after {timeout}s")
```

## Testing with Mock Data

### Create Mock Telemetry

```python
import pandas as pd
import numpy as np

def create_mock_telemetry(lap_length=5000, num_points=1000):
    """Generate mock telemetry for testing."""
    distance = np.linspace(0, lap_length, num_points)
    
    # Simulate speed profile
    speed = 150 + 150 * np.sin(distance / lap_length * np.pi * 4)
    
    # Simulate throttle/brake
    throttle = np.where(speed > 200, 100, speed / 3)
    brake = np.where(speed < 150, 50, 0)
    
    return pd.DataFrame({
        'Distance': distance,
        'Speed': speed,
        'Throttle': throttle,
        'Brake': brake,
        'nGear': np.random.randint(2, 8, num_points),
        'Time': pd.to_timedelta(distance / speed * 3.6, unit='s')
    })
```

## Best Practices

### Do's

✅ Always enable cache before any FastF1 operations
✅ Check for data availability before accessing
✅ Handle missing/incomplete data gracefully
✅ Use `IsAccurate` flag to filter valid laps
✅ Downsample telemetry for frontend performance
✅ Convert timedeltas to seconds for JSON serialization
✅ Normalize data before comparison
✅ Cache processed results
✅ Use appropriate interpolation for alignment
✅ Document data assumptions

### Don'ts

❌ Don't call `session.load()` multiple times
❌ Don't return raw pandas DataFrames to frontend
❌ Don't assume all sessions have full data
❌ Don't ignore outliers in analysis
❌ Don't forget to handle sprint weekends differently
❌ Don't send full telemetry without downsampling
❌ Don't hardcode circuit-specific values
❌ Don't skip validation of FastF1 data
❌ Don't forget timezones in date handling
❌ Don't assume consistent data format across seasons

## References

- [FastF1 Documentation](https://docs.fastf1.dev/)
- [FastF1 GitHub](https://github.com/theOehrly/Fast-F1)
- [F1 Technical Regulations](https://www.fia.com/regulations)

