# Minimal ML Features

## Overview

This document outlines the lightweight machine learning and AI features to be implemented in the F1 Engineering App. The focus is on practical, computationally efficient features that provide real value without requiring complex ML infrastructure.

## Philosophy

- **Heuristic-first:** Use rule-based systems where possible
- **Interpretable:** All insights should be explainable
- **Fast:** No model training required at runtime
- **Incremental:** Start simple, add complexity as needed
- **No black boxes:** Users should understand how insights are generated

## Feature Categories

### 1. Lap Similarity Detection

**Purpose:** Find laps with similar characteristics for comparison.

**Implementation:**
```typescript
function calculateLapSimilarity(lap1: TelemetryPoint[], lap2: TelemetryPoint[]): number {
  // Extract features
  const features1 = {
    avgSpeed: average(lap1.map(p => p.speed)),
    avgThrottle: average(lap1.map(p => p.throttle)),
    avgBrake: average(lap1.map(p => p.brake)),
    speedVariance: variance(lap1.map(p => p.speed)),
  }
  
  const features2 = { /* same for lap2 */ }
  
  // Calculate euclidean distance
  const distance = euclideanDistance(features1, features2)
  
  // Convert to similarity (0-1)
  return 1 / (1 + distance)
}
```

**Use Cases:**
- Find laps with similar driving style
- Identify setup similarities
- Recommend reference laps

**Complexity:** O(n) where n = telemetry points

### 2. Performance Anomaly Detection

**Purpose:** Identify outlier laps that deviate from normal performance.

**Method:** Statistical outlier detection using standard deviation.

```python
def detect_outliers(lap_times: List[float], threshold: float = 3.0) -> List[bool]:
    """
    Flag laps more than `threshold` standard deviations from mean.
    """
    times = np.array(lap_times)
    mean = np.mean(times)
    std = np.std(times)
    
    z_scores = np.abs((times - mean) / std)
    return z_scores > threshold
```

**Insights Generated:**
- "Lap 23 was 3.2σ slower than average (possible traffic or mistake)"
- "Driver showed consistent pace (σ = 0.12s)"

**Complexity:** O(n)

### 3. Tyre Degradation Modeling

**Purpose:** Estimate pace loss over stint age.

**Method:** Linear regression on lap time vs. tyre age.

```python
from scipy.stats import linregress

def calculate_degradation(stint_laps: pd.DataFrame) -> Dict:
    """
    Fit linear model: lap_time = baseline + degradation_rate * tyre_age
    """
    x = stint_laps['tyre_age'].values
    y = stint_laps['lap_time'].values
    
    slope, intercept, r_value, p_value, std_err = linregress(x, y)
    
    return {
        'baseline_pace': intercept,
        'degradation_rate': slope,  # seconds per lap
        'r_squared': r_value ** 2,
        'confidence': 'high' if r_value > 0.8 else 'medium'
    }
```

**Insights:**
- "Tyre degradation: +0.08s per lap (high confidence)"
- "Optimal stint length: 15 laps before crossover"

**Complexity:** O(n)

### 4. Braking Point Comparison

**Purpose:** Identify where drivers brake differently.

**Method:** Detect brake application points and compare.

```python
def find_braking_points(telemetry: pd.DataFrame, threshold: int = 10) -> List[float]:
    """
    Find distance points where brake > threshold.
    """
    braking = telemetry['Brake'] > threshold
    brake_starts = telemetry[braking & ~braking.shift(1)]['Distance'].values
    return brake_starts

def compare_braking(driver1_telem, driver2_telem, corner_distances) -> List[Dict]:
    """
    Compare braking points at each corner.
    """
    brake1 = find_braking_points(driver1_telem)
    brake2 = find_braking_points(driver2_telem)
    
    comparisons = []
    for corner_dist in corner_distances:
        # Find nearest brake point to corner
        bp1 = find_nearest(brake1, corner_dist)
        bp2 = find_nearest(brake2, corner_dist)
        
        delta = bp2 - bp1
        comparisons.append({
            'corner': corner_dist,
            'driver1_brake': bp1,
            'driver2_brake': bp2,
            'delta_meters': delta,
            'driver1_earlier': delta > 5  # 5m threshold
        })
    
    return comparisons
```

**Insights:**
- "VER brakes 12m later into Turn 1 than HAM"
- "Consistent braking within ±2m across all corners"

**Complexity:** O(n + m) where m = corners

### 5. Sector Performance Clustering

**Purpose:** Group drivers by sector strengths.

**Method:** K-means clustering on sector time deltas.

```python
from sklearn.cluster import KMeans

def cluster_drivers_by_sectors(sector_times: pd.DataFrame) -> Dict:
    """
    Cluster drivers based on sector performance patterns.
    """
    # Normalize sector times to deltas from best
    best_times = sector_times.min()
    deltas = sector_times - best_times
    
    # Cluster into groups (e.g., 3 groups)
    kmeans = KMeans(n_clusters=3, random_state=42)
    labels = kmeans.fit_predict(deltas)
    
    return {
        'clusters': labels,
        'centers': kmeans.cluster_centers_,
        'groups': {
            0: 'High-speed specialists',
            1: 'Low-speed specialists',
            2: 'Balanced performers'
        }
    }
```

**Insights:**
- "VER and LEC are high-speed specialists (strong in S1)"
- "HAM shows balanced performance across all sectors"

**Complexity:** O(k * n * i) where k=clusters, n=drivers, i=iterations (typically small)

### 6. Optimal Strategy Suggestion

**Purpose:** Recommend pit stop windows based on race data.

**Method:** Rule-based with degradation and gap analysis.

```python
def suggest_pit_window(
    current_lap: int,
    tyre_age: int,
    gap_behind: float,
    gap_ahead: float,
    degradation_rate: float,
    avg_pit_loss: float = 22.0
) -> Dict:
    """
    Simple strategy advisor.
    """
    # Calculate pace loss due to tyres
    pace_loss = tyre_age * degradation_rate
    
    # Calculate undercut potential
    fresh_tyre_advantage = 1.5  # seconds per lap on fresh tyres
    undercut_viable = (fresh_tyre_advantage - avg_pit_loss / 3) > 0
    
    # Check if gaps allow pit stop
    can_pit = gap_behind > avg_pit_loss
    
    # Calculate optimal window
    if pace_loss > 1.0 and can_pit:
        return {
            'recommendation': 'Pit now',
            'reason': f'Tyre degradation critical ({pace_loss:.1f}s/lap loss)',
            'undercut_potential': undercut_viable
        }
    elif tyre_age > 20 and undercut_viable:
        return {
            'recommendation': 'Pit within 2 laps',
            'reason': 'Undercut opportunity available',
            'window': [current_lap, current_lap + 2]
        }
    else:
        return {
            'recommendation': 'Stay out',
            'reason': 'Pace still competitive',
            'estimated_laps_remaining': int((2.0 - pace_loss) / degradation_rate)
        }
```

**Insights:**
- "Optimal pit window: Lap 12-16 (undercut opportunity)"
- "Stay out 3 more laps to clear traffic"

**Complexity:** O(1)

### 7. Consistency Score

**Purpose:** Quantify driver lap time consistency.

**Method:** Coefficient of variation on clean laps.

```python
def calculate_consistency_score(lap_times: List[float]) -> Dict:
    """
    Calculate consistency metrics.
    """
    times = np.array(lap_times)
    mean = np.mean(times)
    std = np.std(times)
    cv = std / mean  # coefficient of variation
    
    # Score: 100 is perfect, lower is less consistent
    score = max(0, 100 - (cv * 1000))
    
    return {
        'score': score,
        'std_dev': std,
        'mean': mean,
        'rating': 'Excellent' if score > 95 else 'Good' if score > 90 else 'Average'
    }
```

**Insights:**
- "Consistency Score: 96.2/100 (Excellent)"
- "Most consistent driver in session"

**Complexity:** O(n)

### 8. Setup Similarity Detection

**Purpose:** Identify drivers running similar setups.

**Method:** Compare telemetry patterns in key corners.

```python
def detect_setup_similarity(driver1_telem, driver2_telem, corners) -> float:
    """
    Compare downforce levels and setup characteristics.
    """
    similarities = []
    
    for corner in corners:
        # Extract corner telemetry
        c1 = extract_corner_data(driver1_telem, corner)
        c2 = extract_corner_data(driver2_telem, corner)
        
        # Compare key metrics
        min_speed_diff = abs(c1['min_speed'] - c2['min_speed'])
        max_speed_diff = abs(c1['max_speed'] - c2['max_speed'])
        
        # Normalize and combine
        similarity = 1 - (min_speed_diff / 50 + max_speed_diff / 100) / 2
        similarities.append(similarity)
    
    return np.mean(similarities)
```

**Insights:**
- "LEC and SAI showing similar telemetry patterns (92% similarity)"
- "Setup appears to be high downforce configuration"

**Complexity:** O(c * n) where c = corners

## Implementation Priority

### Phase 1 (MVP)
1. ✅ Lap similarity (for reference lap suggestions)
2. ✅ Anomaly detection (outlier identification)
3. ✅ Consistency score (driver performance metric)

### Phase 2 (Enhanced)
4. Tyre degradation modeling
5. Braking point comparison
6. Sector performance clustering

### Phase 3 (Advanced)
7. Optimal strategy suggestion
8. Setup similarity detection

## Data Requirements

All features require:
- Lap times and sector times
- Telemetry data (speed, throttle, brake)
- Tyre compound and age
- Session metadata

No external data or trained models required.

## Performance Considerations

- Pre-compute features during data load
- Cache results for reuse
- Run heavy computations in web workers (frontend)
- Use numpy/pandas vectorization (backend)
- Limit scope (e.g., analyze top 10 drivers only)

## API Integration

### Backend Endpoint
```python
@router.post("/insights/generate")
async def generate_insights(
    session_id: str,
    drivers: List[str],
    analysis_types: List[str]
):
    """
    Generate requested insights.
    """
    insights = []
    
    if 'consistency' in analysis_types:
        insights.append(calculate_consistency(session_id, drivers))
    
    if 'outliers' in analysis_types:
        insights.append(detect_anomalies(session_id, drivers))
    
    # ... etc
    
    return {'insights': insights}
```

### Frontend Usage
```typescript
const insights = await fetch('/api/insights/generate', {
  method: 'POST',
  body: JSON.stringify({
    sessionId: '2024_1_Q',
    drivers: ['VER', 'HAM'],
    analysisTypes: ['consistency', 'braking', 'similarity']
  })
})
```

## Testing

### Unit Tests
- Test each feature with known input/output
- Verify edge cases (empty data, single lap, etc.)
- Check performance on large datasets

### Integration Tests
- Test API endpoints
- Verify insights generate correctly
- Check caching works

### Validation
- Compare with domain expert analysis
- Verify insights match video evidence
- Check consistency across sessions

## Future Directions

### Medium-term
- **Time series forecasting:** Predict lap times
- **Classification:** Identify driving styles
- **Clustering:** Group similar race strategies

### Long-term
- **Deep learning:** Neural network for lap time prediction
- **Reinforcement learning:** Optimal strategy learning
- **NLP:** Natural language generation for insights

But always maintain:
- Interpretability
- Speed
- Accuracy
- User trust

## Example Insights Output

```json
{
  "insights": [
    {
      "type": "consistency",
      "driver": "VER",
      "score": 96.2,
      "description": "Excellent consistency with σ=0.082s across 12 laps",
      "confidence": "high"
    },
    {
      "type": "anomaly",
      "driver": "HAM",
      "lap": 23,
      "description": "Lap 5.2s slower than average (3.8σ deviation)",
      "possible_causes": ["Traffic", "Mistake", "Technical issue"],
      "confidence": "high"
    },
    {
      "type": "braking",
      "comparison": "VER vs HAM",
      "corner": "Turn 1",
      "description": "VER brakes 12m later, gaining ~0.04s",
      "confidence": "medium"
    },
    {
      "type": "similarity",
      "drivers": ["LEC", "SAI"],
      "score": 0.92,
      "description": "Similar telemetry patterns suggest comparable setup",
      "confidence": "medium"
    }
  ]
}
```

