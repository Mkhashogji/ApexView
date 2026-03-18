# Corner Analysis Architecture Revision — Implementation Report

## Document Information

| Field | Value |
|-------|-------|
| **Phase** | Phase 3 - Deceleration-Based Architecture |
| **Status** | Complete |
| **Date** | 2026-01-26 |
| **Branch** | `feature/ai-insights-v2` |

---

## 1. Overview

### 1.1 Objectives

The Corner Analysis Architecture Revision aimed to replace the boolean brake-based corner detection system with a more accurate deceleration-based, dynamically-zoned system. The primary objectives were:

1. **Replace boolean brake dependency** - FastF1 provides brake data as 0/1 (on/off), not pressure percentage. This limits accuracy in detecting braking intensity and timing.

2. **Implement dynamic corner zones** - Static apex positions from track JSON are approximate. Dynamic detection from speed minimum provides per-driver accuracy.

3. **Add two-stage braking detection** - Combine fast boolean detection with accurate deceleration refinement for robust braking point identification.

4. **Enable sector-time validation** - Validate corner delta sums against official sector times to catch systematic errors.

5. **Support per-circuit tuning** - Different circuits have different characteristics (Monaco's tight corners vs Monza's heavy braking zones).

### 1.2 Key Achievements

| Achievement | Description |
|-------------|-------------|
| **Deceleration Calculation** | Physics-based deceleration from speed using kinematic equation |
| **Dynamic Apex Detection** | Speed minimum detection within configurable search window |
| **Two-Stage Braking** | Boolean candidate + deceleration threshold refinement |
| **Dynamic Exit Detection** | Sustained acceleration OR speed recovery detection |
| **Sector Validation** | Corner delta sums validated against official timing |
| **Per-Circuit Config** | 15+ circuit-specific configurations with tunable parameters |
| **Backward Compatibility** | V1 functions unchanged; V2 is additive |
| **Automatic V2 Usage** | Endpoints automatically use V2 when speed data is available |

### 1.3 Files Created/Modified

| File | Type | Description |
|------|------|-------------|
| `apps/analysis_service/core/corner_config.py` | **NEW** | Per-circuit configuration dataclasses |
| `apps/analysis_service/core/comparison_logger.py` | **NEW** | V1/V2 comparison logging utilities |
| `apps/analysis_service/services/corner_analysis.py` | Modified | Added V2 detection functions |
| `apps/analysis_service/main.py` | Modified | Updated endpoints to support V2 |
| `apps/analysis_service/models/schemas.py` | Modified | Added `circuit_id` field to requests |
| `apps/analysis_service/tests/test_corner_analysis_v2.py` | **NEW** | 25 comprehensive tests for V2 |

---

## 2. Sequential Implementation Steps

### Step 1: Create Configuration Module

**File**: `apps/analysis_service/core/corner_config.py`

**Purpose**: Provide per-circuit tunable parameters for the V2 corner analysis system.

**Technical Details**:

```python
@dataclass
class CornerAnalysisConfig:
    # Deceleration thresholds (m/s²)
    braking_decel_threshold: float = -5.0     # Heavy braking onset
    trail_braking_threshold: float = -1.0     # Trail braking
    acceleration_threshold: float = 2.0       # Exit acceleration

    # Smoothing (higher for bumpy tracks)
    decel_smoothing_window: int = 5

    # Distance tolerances (meters)
    braking_point_tolerance: float = 20.0     # ±20m at ~5 Hz
    apex_search_margin: float = 50.0          # Search window

    # Exit detection
    exit_speed_recovery_pct: float = 0.85     # Exit when ≥85% pre-brake speed
    exit_sustained_points: int = 3            # Sustained accel required
```

**Circuit-Specific Overrides**:

| Circuit | Braking Threshold | Smoothing | Notes |
|---------|------------------|-----------|-------|
| Monza | -6.0 m/s² | 5 | Heavy braking from high speeds |
| Monaco | -4.0 m/s² | 7 | Lighter braking, bumpy surface |
| Singapore | -4.5 m/s² | 7 | Bumpy street circuit |
| Baku | -6.5 m/s² | 5 | Very heavy braking zones |

**Logical Reasoning**: Different circuits have vastly different characteristics. A one-size-fits-all threshold would misclassify corners at Monaco (where -5.0 m/s² is heavy braking) versus Monza (where drivers regularly exceed -6.0 m/s²).

---

### Step 2: Add Deceleration Calculation

**Function**: `compute_deceleration(distance, speed, smoothing_window)`

**Physics Formula**:
```
a = (v₂² - v₁²) / (2 × Δd)
```

This is the distance-based kinematic equation, which is more accurate than time-based calculation for telemetry with variable sampling rates.

**Implementation**:

```python
def compute_deceleration(distance, speed, smoothing_window=5):
    speed_ms = speed / 3.6  # km/h to m/s
    delta_distance = np.diff(distance)
    delta_distance = np.where(delta_distance == 0, 0.001, delta_distance)

    v1_sq = speed_ms[:-1] ** 2
    v2_sq = speed_ms[1:] ** 2
    decel = (v2_sq - v1_sq) / (2 * delta_distance)

    # Smooth to reduce noise from ~5 Hz sampling
    if smoothing_window > 1:
        kernel = np.ones(smoothing_window) / smoothing_window
        decel = np.convolve(decel, kernel, mode='same')

    return decel
```

**Why Distance-Based**: FastF1 telemetry is sampled at ~5 Hz (~17m between samples at 300 km/h). Time-based calculations accumulate errors; distance-based calculations are more stable.

---

### Step 3: Add Dynamic Apex Detection

**Function**: `detect_apex_from_speed_v2(distance, speed, nominal_apex, search_margin)`

**Purpose**: Detect the actual apex position as the speed minimum within a search window around the nominal apex.

**Algorithm**:
1. Define search window: `[nominal_apex - margin, nominal_apex + margin]`
2. Find indices within window
3. Locate minimum speed index
4. Calculate confidence based on deviation from nominal

**Confidence Levels**:

| Deviation | Confidence | Interpretation |
|-----------|------------|----------------|
| < 20m | HIGH | Apex matches expected position |
| 20-40m | MEDIUM | Slight variation in driver line |
| > 40m | LOW | Significant deviation, may indicate corner misidentification |

**Theoretical Basis**: The apex is defined as the point of minimum speed through a corner. While track maps provide nominal apex positions, drivers take different lines, making dynamic detection more accurate.

---

### Step 4: Add Two-Stage Braking Detection

**Function**: `detect_braking_zone_v2(distance, brake, speed, decel, apex_distance, config)`

**Two-Stage Process**:

**Stage 1 - Boolean Candidate (Fast)**:
```python
brake_candidates = zone_idx[brake_normalized[zone_idx] >= 0.5]
boolean_brake_dist = distance[brake_candidates[0]]
```

**Stage 2 - Deceleration Refinement (Accurate)**:
```python
refined_idx = boolean_brake_idx
while refined_idx > zone_idx[0]:
    if decel[refined_idx - 1] > config.braking_decel_threshold:
        break  # Found where decel is not yet heavy
    refined_idx -= 1
```

**Why Two-Stage**:
- Boolean brake is fast but imprecise (only tells us brake is on/off)
- Deceleration is physics-based but computationally expensive
- Combining both gives speed and accuracy

**Confidence Based on Alignment**:

| Alignment Diff | Confidence | Meaning |
|---------------|------------|---------|
| ≤ 20m | HIGH | Boolean and decel agree |
| 20-40m | MEDIUM | Slight disagreement |
| > 40m | LOW | Significant disagreement, possible sensor lag |

---

### Step 5: Add Dynamic Exit Detection

**Function**: `detect_exit_zone_v2(distance, speed, decel, apex_idx, entry_speed, config)`

**Detection Criteria** (either condition triggers exit):

1. **Sustained Acceleration**:
   ```python
   if decel[exit_idx] >= config.acceleration_threshold:
       sustained_count += 1
       if sustained_count >= config.exit_sustained_points:
           return distance[exit_idx], "high"
   ```

2. **Speed Recovery**:
   ```python
   if speed[exit_idx] >= entry_speed * config.exit_speed_recovery_pct:
       return distance[exit_idx], "high"
   ```

**Why Dynamic Exit**: The previous V1 system used a fixed `apex + 100m` exit. This fails for:
- Long corners (Suzuka's 130R)
- Short corners (Monaco's hairpin)
- Corners followed by immediate braking

---

### Step 6: Add Sector Validation

**Function**: `validate_against_sectors(corner_results, sector_boundaries, ref_sectors, comp_sectors, tolerance)`

**Purpose**: Validate that corner delta sums align with official sector time differences.

**Algorithm**:
```python
# Group corners by sector
for cr in corner_results:
    if cr.apex_distance < s1_end:
        sectors[0].append(cr)
    elif cr.apex_distance < s2_end:
        sectors[1].append(cr)
    else:
        sectors[2].append(cr)

# Validate each sector
for i in range(3):
    corner_sum = sum(cr.delta_change for cr in sectors[i])
    official_delta = comp_sectors[i] - ref_sectors[i]
    diff = corner_sum - official_delta
    is_valid = abs(diff) <= tolerance
```

**Confidence Adjustment**:
```python
confidence_adj = 0.5 + (valid_count / 3) * 0.5
# 0/3 valid → 0.5, 3/3 valid → 1.0
```

**Logical Reasoning**: Official sector times are ground truth from FIA timing. If corner deltas don't sum to sector deltas, there's a systematic error in corner detection.

---

### Step 7: Create `analyze_single_corner_v2()`

**Orchestration Function** that combines all V2 components:

```python
def analyze_single_corner_v2(...):
    # Step 1: Compute deceleration for both drivers
    ref_decel = compute_deceleration(ref_distance, ref_speed, ...)
    comp_decel = compute_deceleration(comp_distance, comp_speed, ...)

    # Step 2: Detect apex from speed minimum
    detected_apex, apex_speed, apex_conf = detect_apex_from_speed_v2(...)

    # Step 3: Two-stage braking detection for both drivers
    ref_brake_dist, ref_conf, ref_meta = detect_braking_zone_v2(...)
    comp_brake_dist, comp_conf, comp_meta = detect_braking_zone_v2(...)

    # Step 4: Use earlier braking point with margin
    earliest_brake = min(ref_brake_dist, comp_brake_dist)
    zone_start = earliest_brake - APPROACH_MARGIN_METERS

    # Step 5: Dynamic exit detection
    exit_dist, exit_conf = detect_exit_zone_v2(...)
    zone_end = exit_dist

    # Step 6: Calculate delta change
    delta_change = get_delta_change_in_range(delta_result, zone_start, zone_end)

    return CornerResultV2(...)
```

---

### Step 8: Update Endpoints

**Modified Endpoints**:
- `/analysis/corner-analysis`
- `/analysis/technique-profile`
- `/analysis/generate-insight`

**V2 Selection Logic**:
```python
ref_has_speed = "speed" in ref_telemetry and len(ref_telemetry["speed"]) > 0
comp_has_speed = "speed" in comp_telemetry and len(comp_telemetry["speed"]) > 0

if ref_has_speed and comp_has_speed:
    corner_result = analyze_corners_v2(
        ...,
        circuit_id=request.circuit_id if hasattr(request, "circuit_id") else ""
    )
else:
    corner_result = analyze_corners(...)  # V1 fallback
```

**Schema Updates**:
```python
class CornerAnalysisRequest(BaseModel):
    # ... existing fields ...
    circuit_id: Optional[str] = Field(
        None,
        description="Circuit identifier for v2 config lookup"
    )
```

---

### Step 9: Add Comparison Logging

**File**: `apps/analysis_service/core/comparison_logger.py`

**Purpose**: Log V1 vs V2 comparisons during transition period.

**Functions**:
- `log_v1_v2_comparison()` - Per-corner delta differences
- `log_v2_metrics()` - V2-specific statistics
- `log_deceleration_stats()` - Deceleration distribution

**Output Format** (JSON for easy parsing):
```json
{
  "session_id": "2025_24_Qualifying",
  "driver": "NOR",
  "total_v1_delta": 0.123,
  "total_v2_delta": 0.115,
  "total_diff": 0.008,
  "corners": [...]
}
```

---

## 3. Implementation Workflow

### 3.1 Development Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                    DEVELOPMENT WORKFLOW                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  1. Create Configuration Module                                  │
│     └── corner_config.py with CornerAnalysisConfig              │
│         └── Circuit-specific overrides (15+ circuits)           │
│                                                                  │
│  2. Add V2 Functions to corner_analysis.py                      │
│     ├── compute_deceleration()                                  │
│     ├── detect_apex_from_speed_v2()                             │
│     ├── detect_braking_zone_v2()                                │
│     ├── detect_exit_zone_v2()                                   │
│     ├── validate_against_sectors()                              │
│     ├── analyze_single_corner_v2()                              │
│     └── analyze_corners_v2()                                    │
│                                                                  │
│  3. Update Endpoints in main.py                                 │
│     └── Add V2 selection logic with V1 fallback                 │
│                                                                  │
│  4. Update Schemas in schemas.py                                │
│     └── Add circuit_id field to request models                  │
│                                                                  │
│  5. Add Comparison Logging                                      │
│     └── comparison_logger.py for V1/V2 analysis                 │
│                                                                  │
│  6. Create Test Suite                                           │
│     └── test_corner_analysis_v2.py (25 tests)                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Testing Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                      TESTING WORKFLOW                            │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LOCAL TESTS (Outside Docker)                                   │
│  ├── pytest tests/test_corner_analysis_v2.py -v                 │
│  │   └── Result: 25/25 passed                                   │
│  ├── pytest tests/test_corner_analysis.py -v                    │
│  │   └── Result: 38/38 passed (V1 backward compatibility)       │
│  └── python -m py_compile (all modified files)                  │
│      └── Result: Syntax OK                                      │
│                                                                  │
│  DOCKER BUILD                                                   │
│  └── docker-compose build --no-cache ml                         │
│      └── Result: Image built successfully                       │
│                                                                  │
│  DOCKER TESTS                                                   │
│  ├── Container startup verification                             │
│  │   └── Result: Container healthy                              │
│  ├── Import verification                                        │
│  │   └── Result: All V2 imports successful                      │
│  ├── Functional tests                                           │
│  │   └── Result: All V2 functions working                       │
│  └── Endpoint tests                                             │
│      └── Result: /analysis/corner-analysis returns valid response     │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.3 Data Flow Workflow

```
┌─────────────────────────────────────────────────────────────────┐
│                      V2 DATA FLOW                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  REQUEST                                                        │
│  │                                                              │
│  ▼                                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Endpoint receives request with:                          │  │
│  │ - session_id, reference_driver, compare_drivers          │  │
│  │ - corners, session_part, circuit_id                      │  │
│  └──────────────────────────────────────────────────────────┘  │
│  │                                                              │
│  ▼                                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Fetch telemetry from API service:                        │  │
│  │ - distance[], speed[], brake[], throttle[]               │  │
│  └──────────────────────────────────────────────────────────┘  │
│  │                                                              │
│  ▼                                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Check if speed data available:                           │  │
│  │ - Yes → Use analyze_corners_v2()                         │  │
│  │ - No  → Fallback to analyze_corners() (V1)               │  │
│  └──────────────────────────────────────────────────────────┘  │
│  │                                                              │
│  ▼ (V2 Path)                                                   │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Get circuit config:                                      │  │
│  │ - get_config_for_circuit(circuit_id)                     │  │
│  │ - Returns circuit-specific or default config             │  │
│  └──────────────────────────────────────────────────────────┘  │
│  │                                                              │
│  ▼                                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ For each corner:                                         │  │
│  │ 1. compute_deceleration() for both drivers               │  │
│  │ 2. detect_apex_from_speed_v2()                           │  │
│  │ 3. detect_braking_zone_v2() for both drivers             │  │
│  │ 4. detect_exit_zone_v2()                                 │  │
│  │ 5. get_delta_change_in_range()                           │  │
│  │ 6. determine_cause()                                     │  │
│  └──────────────────────────────────────────────────────────┘  │
│  │                                                              │
│  ▼                                                              │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Return CornerAnalysisResult:                             │  │
│  │ - corner_results[] with CornerResultV2 objects           │  │
│  │ - total_delta_change, corners_gaining, corners_losing    │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 4. Test Execution and Results

### 4.1 Local Unit Tests

**Command**:
```bash
cd apps/analysis_service
python -m pytest tests/test_corner_analysis_v2.py -v --tb=short
```

**Output**:
```
============================= test session starts =============================
platform win32 -- Python 3.13.2, pytest-9.0.2

tests/test_corner_analysis_v2.py::TestComputeDeceleration::test_constant_speed_zero_deceleration PASSED
tests/test_corner_analysis_v2.py::TestComputeDeceleration::test_braking_negative_deceleration PASSED
tests/test_corner_analysis_v2.py::TestComputeDeceleration::test_acceleration_positive_deceleration PASSED
tests/test_corner_analysis_v2.py::TestComputeDeceleration::test_smoothing_reduces_noise PASSED
tests/test_corner_analysis_v2.py::TestComputeDeceleration::test_handles_empty_arrays PASSED
tests/test_corner_analysis_v2.py::TestDetectApexFromSpeedV2::test_finds_speed_minimum PASSED
tests/test_corner_analysis_v2.py::TestDetectApexFromSpeedV2::test_high_confidence_near_nominal PASSED
tests/test_corner_analysis_v2.py::TestDetectApexFromSpeedV2::test_low_confidence_far_from_nominal PASSED
tests/test_corner_analysis_v2.py::TestDetectApexFromSpeedV2::test_returns_nominal_when_no_data PASSED
tests/test_corner_analysis_v2.py::TestDetectBrakingZoneV2::test_two_stage_detection PASSED
tests/test_corner_analysis_v2.py::TestDetectBrakingZoneV2::test_decel_only_fallback PASSED
tests/test_corner_analysis_v2.py::TestDetectBrakingZoneV2::test_confidence_based_on_alignment PASSED
tests/test_corner_analysis_v2.py::TestDetectExitZoneV2::test_detects_exit_via_acceleration PASSED
tests/test_corner_analysis_v2.py::TestDetectExitZoneV2::test_detects_exit_via_speed_recovery PASSED
tests/test_corner_analysis_v2.py::TestValidateAgainstSectors::test_validates_matching_sectors PASSED
tests/test_corner_analysis_v2.py::TestValidateAgainstSectors::test_fails_on_mismatch PASSED
tests/test_corner_analysis_v2.py::TestValidateAgainstSectors::test_confidence_adjustment_range PASSED
tests/test_corner_analysis_v2.py::TestAnalyzeSingleCornerV2::test_returns_corner_result_v2 PASSED
tests/test_corner_analysis_v2.py::TestAnalyzeSingleCornerV2::test_dynamic_zone_detection PASSED
tests/test_corner_analysis_v2.py::TestAnalyzeCornersV2::test_analyzes_all_corners PASSED
tests/test_corner_analysis_v2.py::TestAnalyzeCornersV2::test_uses_circuit_config PASSED
tests/test_corner_analysis_v2.py::TestCornerConfig::test_default_config_values PASSED
tests/test_corner_analysis_v2.py::TestCornerConfig::test_circuit_specific_config PASSED
tests/test_corner_analysis_v2.py::TestCornerConfig::test_unknown_circuit_returns_default PASSED
tests/test_corner_analysis_v2.py::TestV2Integration::test_full_pipeline PASSED

======================== 25 passed, 1 warning in 0.16s ========================
```

### 4.2 V1 Backward Compatibility Tests

**Command**:
```bash
python -m pytest tests/test_corner_analysis.py -v --tb=short
```

**Output**:
```
======================== 38 passed, 1 warning in 0.16s ========================
```

### 4.3 Docker Build

**Command**:
```bash
docker-compose build --no-cache ml
```

**Output** (final lines):
```
#14 exporting to image
#14 naming to docker.io/library/f1-engineering-app-ml:latest done
 Image f1-engineering-app-ml Built
```

### 4.4 Docker Container Startup

**Command**:
```bash
docker-compose up -d ml
docker-compose logs ml --tail=10
```

**Output**:
```
f1-analysis  | INFO:     Started server process [1]
f1-analysis  | INFO:     Waiting for application startup.
f1-analysis  | INFO:     Application startup complete.
f1-analysis  | 2026-01-26 10:46:38 | INFO | F1 Analysis Service v0.1.0 starting
f1-analysis  | INFO:     Uvicorn running on http://0.0.0.0:8501 (Press CTRL+C to quit)
```

### 4.5 Docker Import Verification

**Command**:
```bash
docker-compose exec ml python -c "
from services.corner_analysis import (
    analyze_corners, analyze_corners_v2, compute_deceleration,
    detect_apex_from_speed_v2, detect_braking_zone_v2,
    detect_exit_zone_v2, validate_against_sectors
)
from core.corner_config import CornerAnalysisConfig, get_config_for_circuit
print('All v2 imports successful!')
print(f'Default braking threshold: {CornerAnalysisConfig().braking_decel_threshold}')
print(f'Monaco braking threshold: {get_config_for_circuit(\"monaco\").braking_decel_threshold}')
"
```

**Output**:
```
All v2 imports successful!
Default braking threshold: -5.0
Monaco braking threshold: -4.0
```

### 4.6 Docker Functional Test

**Command**:
```bash
docker-compose exec ml python -c "
import numpy as np
from services.corner_analysis import compute_deceleration, detect_apex_from_speed_v2
from core.corner_config import CornerAnalysisConfig

# Test data
distance = np.linspace(0, 500, 100)
speed = np.zeros(100)
for i, d in enumerate(distance):
    if d < 250: speed[i] = 300
    elif d < 350: speed[i] = 300 - (d - 250) * 2
    else: speed[i] = 100 + (d - 350) * 1.5

# Test deceleration
decel = compute_deceleration(distance, speed)
print(f'Deceleration range: [{decel.min():.1f}, {decel.max():.1f}] m/s²')

# Test apex detection
apex_dist, apex_speed, conf = detect_apex_from_speed_v2(distance, speed, 350, 50)
print(f'Apex: {apex_dist:.0f}m, speed={apex_speed:.0f} km/h, confidence={conf}')
"
```

**Output**:
```
Deceleration range: [-41.6, 35.4] m/s²
Apex: 348m, speed=103 km/h, confidence=high
```

### 4.7 Endpoint Test

**Command**:
```bash
curl -s -X POST "http://localhost:8501/analysis/corner-analysis" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "2025_1_Qualifying", "reference_driver": "VER",
       "compare_drivers": ["NOR"], "corners": [{"corner_number": 1,
       "apex_distance": 500, "corner_type": "left", "name": "Turn 1"}],
       "session_part": "Q3", "circuit_id": "monza"}'
```

**Output**:
```json
{
  "session_id": "2025_1_Qualifying",
  "reference_driver": "VER",
  "results": [{
    "compare_driver": "NOR",
    "corner_results": [{
      "corner_number": 1,
      "name": "Turn 1",
      "apex_distance": 500.0,
      "brake_distance": 251.09,
      "zone_start": 212.75,
      "zone_end": 460.96,
      "delta_change": 0.0688,
      "cause": "braking",
      "confidence": "low"
    }],
    "total_delta_change": 0.0688,
    "corners_gaining": 0,
    "corners_losing": 1
  }],
  "metadata": {
    "session_part": "Q3",
    "drivers_analyzed": 1,
    "corners_analyzed": 1,
    "drivers_failed": 0,
    "errors": null
  }
}
```

### 4.8 V2 Usage Confirmation (Logs)

**Command**:
```bash
docker-compose logs ml --tail=10
```

**Output**:
```
f1-analysis  | 2026-01-26 10:49:19 | INFO | Analyzing 1 corners (v2) for VER vs NOR
f1-analysis  | 2026-01-26 10:49:19 | INFO | Corner analysis (v2) complete: total_delta=+0.069s
```

**Key Evidence**: Log message `Analyzing 1 corners (v2)` confirms V2 is being used.

---

## 5. Technical Comparison: V1 vs V2

| Aspect | V1 (Original) | V2 (New) |
|--------|---------------|----------|
| **Brake Detection** | Boolean threshold + gradient | Two-stage: boolean + deceleration |
| **Apex Position** | Static from track JSON | Dynamic from speed minimum |
| **Exit Position** | Fixed `apex + 100m` | Dynamic via acceleration/speed recovery |
| **Per-Circuit Tuning** | None | 15+ circuit-specific configs |
| **Validation** | None | Sector-time validation |
| **Confidence** | Binary (detected/fallback) | Multi-factor (apex + brake + exit) |
| **Speed Data** | Not used | Required for V2 features |
| **Backward Compatible** | N/A | Yes, V1 unchanged |

---

## 6. Risk Mitigation

| Risk | Mitigation |
|------|------------|
| **V1 Breakage** | V1 functions unchanged; V2 is additive |
| **Missing Speed Data** | Automatic fallback to V1 |
| **Incorrect V2 Results** | Comparison logging for validation |
| **Circuit-Specific Issues** | Per-circuit config allows tuning |
| **Performance Regression** | Deceleration caching, vectorized operations |

---

## 7. Future Enhancements

1. **Integrate Sector Validation into Endpoints** - Currently available but not automatically invoked
2. **Add V2 Fields to Response Schema** - Expose `detected_apex`, `entry_speed`, `apex_speed`, `exit_distance`
3. **Implement V1/V2 A/B Testing** - Run both and compare results for same session
4. **Add More Circuit Configs** - Currently 15, expand to all 24 circuits
5. **Telemetry Analysis Refinement** - Use historical data to tune thresholds per corner

---

## 8. Conclusion

The Corner Analysis Architecture Revision successfully implements a deceleration-based, dynamically-zoned corner analysis system that addresses the limitations of the original boolean brake-based approach. Key achievements include:

- **Physics-based detection** using kinematic deceleration calculations
- **Dynamic zone boundaries** based on actual driver behavior
- **Per-circuit configurability** for optimal performance across different tracks
- **Full backward compatibility** with automatic V2 selection when speed data is available
- **Comprehensive testing** with 25 V2 tests and 38 V1 compatibility tests passing

The implementation is production-ready and verified in Docker with real endpoint responses showing V2 in use.
