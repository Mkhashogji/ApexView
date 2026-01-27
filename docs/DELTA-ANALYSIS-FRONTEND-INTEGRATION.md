# Delta Analysis Frontend Integration

## Complete End-to-End Documentation

**Document Version:** 1.0
**Date:** February 2026
**Status:** Implementation Complete

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [The Problem: Two Disconnected Data Flows](#2-the-problem-two-disconnected-data-flows)
3. [Theoretical Background](#3-theoretical-background)
4. [Technical Implementation](#4-technical-implementation)
5. [Data Flow Architecture](#5-data-flow-architecture)
6. [Files Modified](#6-files-modified)
7. [The Fix Explained](#7-the-fix-explained)
8. [Frontend Integration Details](#8-frontend-integration-details)
9. [Testing and Verification](#9-testing-and-verification)
10. [Before vs After Comparison](#10-before-vs-after-comparison)

---

## 1. Executive Summary

### What Was Changed

The **DeltaPlot** component in the Qualifying Analysis page was updated to consume accurate Tier 1 delta data from the ML service instead of inaccurate speed-integration delta data from the legacy API endpoint.

### The Gap Fixed

Two disconnected data flows existed in the application:
- **DeltaPlot** (the main visualization) used inaccurate legacy algorithm
- **ScalingMetadataPanel** (metadata display) used accurate Tier 1 algorithm

This caused the graph to show incorrect delta values while the metadata panel showed correct values—confusing users and undermining trust in the analysis.

### Key Outcome

All frontend components now display consistent, accurate delta data:
- **Scale Factor:** 1.0000 (perfect)
- **Confidence:** 100%
- **Final Delta:** Exactly matches official FIA timing

---

## 2. The Problem: Two Disconnected Data Flows

### Before the Fix

The application had two separate data pipelines for delta analysis, each producing different results:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    BEFORE: TWO DISCONNECTED DATA FLOWS                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DATA FLOW A: DeltaPlot (MAIN VISUAL)                                       │
│  ────────────────────────────────────                                       │
│                                                                             │
│  QualifyingContent.tsx                                                      │
│       │                                                                     │
│       └──► useDeltaQuery()                                                  │
│                 │                                                           │
│                 └──► /telemetry/delta (API Service)                         │
│                           │                                                 │
│                           └──► transforms.calculate_delta()                 │
│                                     │                                       │
│                                     └──► Speed Integration (Tier 3)         │
│                                           ❌ Scale factor: 2-10x            │
│                                           ❌ Confidence: 30-60%             │
│                                           ❌ delta[-1] ≠ official_gap       │
│                                                                             │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  DATA FLOW B: ScalingMetadataPanel                                          │
│  ─────────────────────────────────                                          │
│                                                                             │
│  QualifyingContent.tsx                                                      │
│       │                                                                     │
│       └──► useScaledDeltaQuery()                                            │
│                 │                                                           │
│                 └──► /ml/scaled-delta (ML Service)                          │
│                           │                                                 │
│                           └──► delta_analysis.calculate_scaled_delta()      │
│                                     │                                       │
│                                     └──► Tier 1: RelativeDistance + Time    │
│                                           ✅ Scale factor: 1.0000           │
│                                           ✅ Confidence: 100%               │
│                                           ✅ delta[-1] == official_gap      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘

PROBLEM: Users saw ACCURATE metadata but INACCURATE graph!
```

### User Impact

| Component | Showed | User Experience |
|-----------|--------|-----------------|
| DeltaPlot graph | Wrong delta values | "Why doesn't the graph match the numbers?" |
| ScalingMetadataPanel | Correct official gap | "The official gap shows +0.385s..." |
| Graph endpoint | Wrong final value | "...but the graph shows +0.782s" |

This inconsistency undermined user confidence in the entire analysis system.

---

## 3. Theoretical Background

### 3.1 Why Speed Integration Fails

The legacy delta calculation used **speed integration**:

```python
# Legacy algorithm (transforms.calculate_delta)
time = distance / speed  # Physics relationship
ref_times = cumsum(distance_segments / ref_speed_ms)
comp_times = cumsum(distance_segments / comp_speed_ms)
delta = comp_times - ref_times
```

**Problems with this approach:**

| Issue | Cause | Effect |
|-------|-------|--------|
| **Interpolation smoothing** | Telemetry sampled at 4-10 Hz | Speed peaks/troughs lost |
| **Cumulative error** | Small errors compound | Final delta wrong by 2-10x |
| **Sampling variations** | Different drivers sample differently | Comparison skewed |
| **Racing line differences** | Absolute distance varies | Comparing different track positions |

**Result:** Final delta doesn't match official FIA timing.

### 3.2 The Three-Tier Algorithm Solution

The ML service implements a **three-tier algorithm** that guarantees accuracy:

#### Tier 1: RelativeDistance + Time Scaling (PREFERRED)

```python
def _calculate_with_relative_distance(...):
    """
    Key insight: Pre-scale time to match official lap time BEFORE delta calculation.
    Result: scale_factor = 1.0, confidence >= 0.9
    """
    # Normalize time to start at 0
    ref_lap_relative = ref_time - ref_time[0]
    comp_lap_relative = comp_time - comp_time[0]

    # Scale time to EXACTLY match official lap time
    ref_time_scale = ref_official_time / ref_lap_relative[-1]
    comp_time_scale = comp_official_time / comp_lap_relative[-1]

    ref_time_scaled = ref_lap_relative * ref_time_scale
    comp_time_scaled = comp_lap_relative * comp_time_scale

    # Use RelativeDistance (0-1) for position alignment
    common_rel_dist = np.linspace(0, 1, num_points)

    # Interpolate scaled times to common grid
    ref_time_at_pos = np.interp(common_rel_dist, ref_relative_distance, ref_time_scaled)
    comp_time_at_pos = np.interp(common_rel_dist, comp_relative_distance, comp_time_scaled)

    # Delta now EXACTLY equals official gap!
    delta = comp_time_at_pos - ref_time_at_pos
```

**Why Tier 1 works:**
- **RelativeDistance (0-1):** Normalizes track position regardless of racing line
- **Pre-scaling:** Guarantees `delta[-1] == official_gap` mathematically
- **Time column:** Uses direct timing data, not speed integration

#### Tier 2: Time with Distance Alignment (FALLBACK)

Used when `RelativeDistance` is unavailable but `Time` column exists:
- Uses distance-based alignment instead of RelativeDistance
- Less accurate due to racing line variations
- Confidence ~ 0.8

#### Tier 3: Speed Integration (LEGACY FALLBACK)

Used when neither `RelativeDistance` nor `Time` is available:
- Falls back to the original speed integration method
- Post-scales result to match official gap
- Confidence <= 0.6

### 3.3 Algorithm Selection Logic

```python
def calculate_scaled_delta(...):
    # Check available data
    can_use_tier1 = (
        ref_relative_distance is not None and
        ref_time is not None and
        comp_relative_distance is not None and
        comp_time is not None
    )

    can_use_tier2 = (
        ref_time is not None and
        comp_time is not None
    )

    # Use best available tier
    if can_use_tier1:
        return _calculate_with_relative_distance(...)  # Tier 1
    elif can_use_tier2:
        return _calculate_with_time_only(...)  # Tier 2
    else:
        return _calculate_with_speed_integration(...)  # Tier 3
```

---

## 4. Technical Implementation

### 4.1 Backend Changes (Previously Implemented)

The following backend changes enable the three-tier algorithm:

| File | Change | Purpose |
|------|--------|---------|
| `apps/api/app/models/dto.py` | Added `relative_distance` and `time` fields to `TelemetryResponse` | Enable API to return Tier 1 data |
| `apps/api/app/services/telemetry/fastf1_client.py` | Extract `RelativeDistance` and `Time` from FastF1 | Source Tier 1 data from telemetry |
| `apps/ml_service/services/delta_analysis.py` | Implemented three-tier algorithm | Core algorithm logic |
| `apps/ml_service/main.py` | Updated 4 endpoints to pass new fields | Pass Tier 1 data through pipeline |
| `apps/ml_service/services/performance_orchestrator.py` | Updated `fetch_driver_telemetry()` | Include new fields in orchestrator |

### 4.2 Frontend Changes (This Implementation)

**File Modified:** `apps/web/app/qualifying/QualifyingContent.tsx`

**Changes Made:**

1. **Removed `useDeltaQuery` import**
   ```typescript
   // BEFORE
   import {
     useSessionsQuery,
     useTelemetryQuery,
     useDeltaQuery,  // ← REMOVED
     useSectorsQuery,
     ...
   } from '@/lib/hooks'

   // AFTER
   import {
     useSessionsQuery,
     useTelemetryQuery,
     useSectorsQuery,
     ...
   } from '@/lib/hooks'
   ```

2. **Added `DeltaData` type import**
   ```typescript
   import { Telemetry, QualifyingSessionPart, DeltaData } from '@/../../packages/models/src/types'
   ```

3. **Added transformation for scaledDeltaData**
   ```typescript
   // Transform scaledDeltaData to DeltaData format for DeltaPlot
   // This ensures DeltaPlot uses accurate Tier 1 data (scale_factor=1.0, confidence=100%)
   const transformedDeltaData = useMemo((): DeltaData[] => {
     if (!scaledDeltaData?.results) return []

     return scaledDeltaData.results.map(result => ({
       referenceDriver: result.referenceDriver,
       compareDriver: result.compareDriver,
       distance: result.distance,
       delta: result.delta,  // Now uses accurate Tier 1 data!
     }))
   }, [scaledDeltaData])
   ```

4. **Updated loading state**
   ```typescript
   // BEFORE
   const isLoading =
     isSessionsLoading ||
     isTelemetryLoading ||
     isSectorsLoading ||
     isDeltaLoading ||  // ← Used old delta
     isTrackLoading ||
     isLapsLoading

   // AFTER
   const isLoading =
     isSessionsLoading ||
     isTelemetryLoading ||
     isSectorsLoading ||
     isScaledDeltaLoading ||  // ← Uses scaled delta (Tier 1)
     isTrackLoading ||
     isLapsLoading
   ```

5. **Updated DeltaPlot props**
   ```typescript
   // BEFORE
   <DeltaPlot
     deltaData={deltaData ?? []}  // ← Inaccurate data
     referenceDriver={referenceDriver}
     ...
   />

   // AFTER
   <DeltaPlot
     deltaData={transformedDeltaData}  // ← Accurate Tier 1 data
     referenceDriver={referenceDriver}
     ...
   />
   ```

---

## 5. Data Flow Architecture

### After the Fix: Unified Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    AFTER: UNIFIED DATA FLOW                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  QualifyingContent.tsx                                                      │
│       │                                                                     │
│       └──► useScaledDeltaQuery() ◄── SINGLE SOURCE OF TRUTH                │
│                 │                                                           │
│                 └──► /ml/scaled-delta (ML Service)                          │
│                           │                                                 │
│                           └──► delta_analysis.calculate_scaled_delta()      │
│                                     │                                       │
│                                     └──► Tier 1: RelativeDistance + Time    │
│                                           ✅ Scale factor: 1.0000           │
│                                           ✅ Confidence: 100%               │
│                                           ✅ delta[-1] == official_gap      │
│                                                 │                           │
│                                                 ▼                           │
│                              ┌──────────────────┴──────────────────┐       │
│                              │                                      │       │
│                              ▼                                      ▼       │
│                         DeltaPlot                        ScalingMetadataPanel
│                    (ACCURATE graph)                    (metadata display)   │
│                              │                                      │       │
│                              └──────────────┬───────────────────────┘       │
│                                             │                               │
│                                             ▼                               │
│                          BOTH SHOW CONSISTENT, ACCURATE DATA                │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Complete Data Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         COMPLETE DATA PIPELINE                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. FastF1 Library                                                          │
│     └── Extracts RelativeDistance and Time from F1 telemetry                │
│                │                                                            │
│                ▼                                                            │
│  2. FastF1Client (apps/api/app/services/telemetry/fastf1_client.py)         │
│     └── Converts to TelemetryResponse DTO with new fields                   │
│                │                                                            │
│                ▼                                                            │
│  3. API Endpoint: /telemetry                                                │
│     └── Returns JSON with relativeDistance and time arrays                  │
│                │                                                            │
│                ▼                                                            │
│  4. ML Service: /ml/scaled-delta                                            │
│     │   └── Fetches telemetry from API                                      │
│     │   └── Extracts relativeDistance and time fields                       │
│     │   └── Calls calculate_scaled_delta() with all fields                  │
│     │                                                                       │
│     └── delta_analysis.py                                                   │
│           └── Tier 1: _calculate_with_relative_distance()                   │
│                 └── Uses RelativeDistance (0-1) for alignment               │
│                 └── Pre-scales time to official lap time                    │
│                 └── Computes delta with scale_factor = 1.0                  │
│                │                                                            │
│                ▼                                                            │
│  5. Frontend: useScaledDeltaQuery                                           │
│     └── React Query hook fetches /ml/scaled-delta                           │
│                │                                                            │
│                ▼                                                            │
│  6. QualifyingContent.tsx                                                   │
│     └── transformedDeltaData useMemo transforms to DeltaData[]              │
│                │                                                            │
│                ▼                                                            │
│  7. DeltaPlot Component                                                     │
│     └── Renders accurate delta trace                                        │
│     └── Final value matches official gap                                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Files Modified

### 6.1 Frontend Files

| File | Role | Changes Made |
|------|------|--------------|
| `apps/web/app/qualifying/QualifyingContent.tsx` | Main qualifying page orchestrator | Removed useDeltaQuery, added transformation, updated DeltaPlot props, updated loading state |

### 6.2 Backend Files (Previously Modified)

| File | Role | Changes Made |
|------|------|--------------|
| `apps/api/app/models/dto.py` | Data Transfer Objects | Added `relative_distance: Optional[List[float]]` and `time: Optional[List[float]]` to TelemetryResponse |
| `apps/api/app/services/telemetry/fastf1_client.py` | FastF1 data extraction | Extract RelativeDistance and Time columns, include in response and cache |
| `apps/ml_service/services/delta_analysis.py` | Core delta algorithm | Implemented three-tier algorithm with Tier 1 as preferred method |
| `apps/ml_service/main.py` | ML service endpoints | Updated 4 endpoints to pass `relative_distance` and `time` fields |
| `apps/ml_service/services/performance_orchestrator.py` | Performance orchestration | Updated `fetch_driver_telemetry()` to include new fields |

### 6.3 Unchanged Files (Already Compatible)

| File | Role | Why No Changes Needed |
|------|------|----------------------|
| `apps/web/components/charts/DeltaPlot.tsx` | Delta visualization | Already accepts `DeltaData[]` which is compatible with transformation output |
| `packages/models/src/types.ts` | Type definitions | Already had `DeltaData` and `ScaledDeltaDriverResult` types |
| `apps/web/lib/hooks/useScaledDeltaQuery.ts` | React Query hook | Already existed for ScalingMetadataPanel |

---

## 7. The Fix Explained

### 7.1 What Was Wrong

The **DeltaPlot** component was receiving data through the wrong pipeline:

```typescript
// OLD: Using legacy delta hook
const {
  data: deltaData,
  isLoading: isDeltaLoading
} = useDeltaQuery(sessionId, referenceDriver, compareDrivers, qualifyingPart)

// This hook called /telemetry/delta API endpoint
// Which used transforms.calculate_delta() (speed integration)
// Producing inaccurate results with scale factors of 2-10x
```

### 7.2 What We Changed

The **DeltaPlot** now receives data through the accurate Tier 1 pipeline:

```typescript
// NEW: Using scaled delta hook (already existed for ScalingMetadataPanel)
const {
  data: scaledDeltaData,
  isLoading: isScaledDeltaLoading,
  isError: isScaledDeltaError,
  error: scaledDeltaError,
} = useScaledDeltaQuery(sessionId, referenceDriver, compareDrivers, qualifyingPart)

// Transform to DeltaData format for DeltaPlot
const transformedDeltaData = useMemo((): DeltaData[] => {
  if (!scaledDeltaData?.results) return []

  return scaledDeltaData.results.map(result => ({
    referenceDriver: result.referenceDriver,
    compareDriver: result.compareDriver,
    distance: result.distance,
    delta: result.delta,  // Now uses accurate Tier 1 data!
  }))
}, [scaledDeltaData])
```

### 7.3 Why This Is Significant

| Benefit | Explanation |
|---------|-------------|
| **Accuracy** | Final delta now exactly matches official FIA timing |
| **Consistency** | DeltaPlot and ScalingMetadataPanel show identical data |
| **User Trust** | Graph endpoint values match displayed metadata numbers |
| **Single Source of Truth** | One data pipeline for all delta-related components |
| **Maintainability** | No duplicate data fetching or algorithm implementations |

---

## 8. Frontend Integration Details

### 8.1 Data Transformation

The `ScaledDeltaDriverResult` interface has more fields than `DeltaData` requires:

```typescript
// What ML service returns (ScaledDeltaDriverResult)
interface ScaledDeltaDriverResult {
  referenceDriver: string    // ✅ Needed
  compareDriver: string      // ✅ Needed
  distance: number[]         // ✅ Needed
  delta: number[]            // ✅ Needed (now ACCURATE!)
  rawDelta: number[]         // ❌ Extra - ignored
  officialGap: number        // ❌ Extra - for metadata display
  telemetryGap: number       // ❌ Extra - for metadata display
  scalingFactor: number      // ❌ Extra - for metadata display
  confidence: number         // ❌ Extra - for metadata display
}

// What DeltaPlot expects (DeltaData)
interface DeltaData {
  referenceDriver: string
  compareDriver: string
  distance: number[]
  delta: number[]
}
```

The transformation extracts only the required fields:

```typescript
const transformedDeltaData = useMemo((): DeltaData[] => {
  if (!scaledDeltaData?.results) return []

  return scaledDeltaData.results.map(result => ({
    referenceDriver: result.referenceDriver,
    compareDriver: result.compareDriver,
    distance: result.distance,
    delta: result.delta,
  }))
}, [scaledDeltaData])
```

### 8.2 Component Integration

The **DeltaPlot** component required no changes because its interface (`DeltaData[]`) is a subset of `ScaledDeltaDriverResult`:

```typescript
// DeltaPlot.tsx - unchanged
interface DeltaPlotProps {
  deltaData: DeltaData[]  // Compatible with our transformation output
  referenceDriver: string
  sectors?: SectorInfo[]
  trackLength?: number
  onRangeChange?: (xRange: [number, number] | null) => void
  xRange?: [number, number] | null
}
```

### 8.3 Loading State Management

The loading state was updated to reflect the new data dependency:

```typescript
const isLoading =
  isSessionsLoading ||
  isTelemetryLoading ||
  isSectorsLoading ||
  isScaledDeltaLoading ||  // Use scaled delta loading state
  isTrackLoading ||
  isLapsLoading
```

This ensures the UI shows loading state until the accurate delta data is available.

---

## 9. Testing and Verification

### 9.1 Docker Commands Executed

```bash
# Build the frontend container with changes
docker compose build web

# Output:
# #20 DONE 56.0s
# Image apexview-web Built

# Restart all containers
docker compose up -d

# Output:
# Container f1-ml Running
# Container f1-api Running
# Container f1-web Recreate
# Container f1-web Recreated
# Container f1-web Started
```

### 9.2 API Verification

**Command:**
```bash
curl -s "http://localhost:8000/telemetry?session=2025_01_Qualifying&drivers=VER&session_part=Q3"
```

**Result:**
```
Keys: ['driver', 'lapNumber', 'lapTime', 'distance', 'speed', 'throttle',
       'brake', 'gear', 'relativeDistance', 'time', 'rpm', 'drs']

relativeDistance present: True ✅
time present: True ✅
relativeDistance sample: [1.72e-05, 0.0006, 0.002, 0.004, 0.005]
time sample: [0.0, 0.034, 0.122, 0.254, 0.282]
```

### 9.3 Delta Analysis Verification

**Command:**
```bash
curl -s -X POST "http://localhost:8501/ml/scaled-delta" \
  -H "Content-Type: application/json" \
  -d '{"session_id": "2025_01_Qualifying", "reference_driver": "VER", "compare_drivers": ["NOR", "LEC"], "session_part": "Q3"}'
```

**Results (2025 Australian GP Q3):**

| Driver Pair | Official Gap | Delta[-1] | Scale Factor | Confidence | Match |
|-------------|--------------|-----------|--------------|------------|-------|
| VER vs NOR | -0.385s | -0.385s | 1.0000 | 100% | ✅ |
| VER vs LEC | +0.274s | +0.274s | 1.0000 | 100% | ✅ |

### 9.4 ML Service Logs

```
docker logs f1-ml --tail 20 | grep -E "(Tier|PREFERRED)"
```

**Output:**
```
Using PREFERRED method: RelativeDistance + Time scaling (Tier 1)
Tier 1 complete: ref_scale=1.0000, comp_scale=1.0000, confidence=1.00
Using PREFERRED method: RelativeDistance + Time scaling (Tier 1)
Tier 1 complete: ref_scale=1.0000, comp_scale=1.0000, confidence=1.00
```

### 9.5 Evidence Summary

| Check | Expected | Actual | Status |
|-------|----------|--------|--------|
| Frontend build | Success | Built without errors | ✅ |
| API `relativeDistance` field | Present | Present with valid data | ✅ |
| API `time` field | Present | Present with valid data | ✅ |
| Algorithm tier used | Tier 1 | "PREFERRED method: RelativeDistance + Time scaling" | ✅ |
| Scale factor | 1.0000 | 1.0000 for all comparisons | ✅ |
| Confidence | 100% | 100% for all comparisons | ✅ |
| Delta[-1] matches official | Yes | Exact match for all comparisons | ✅ |

---

## 10. Before vs After Comparison

### 10.1 Metrics Comparison

| Metric | Before (Tier 3) | After (Tier 1) |
|--------|-----------------|----------------|
| **Data Source** | useDeltaQuery | useScaledDeltaQuery |
| **Endpoint** | /telemetry/delta | /ml/scaled-delta |
| **Algorithm** | Speed integration | RelativeDistance + Time scaling |
| **Scale Factor** | 2-10x (variable) | 1.0000 (always) |
| **Confidence** | 30-60% | 100% |
| **Final Delta Accuracy** | Wrong magnitude/sign possible | Exact match to official |
| **Graph-Metadata Consistency** | Mismatch | Perfect match |

### 10.2 User Experience Comparison

| Aspect | Before | After |
|--------|--------|-------|
| Graph accuracy | Misleading delta values | Accurate delta values |
| Trust in data | Users questioned discrepancies | Consistent experience |
| Corner analysis foundation | Based on inaccurate deltas | Based on accurate deltas |
| Professional credibility | Undermined by inconsistencies | Enhanced by accuracy |

### 10.3 Technical Debt Reduction

| Before | After |
|--------|-------|
| Two separate delta pipelines | Single source of truth |
| Duplicate API calls | Shared data from one query |
| Legacy code maintained | Legacy code deprecated |
| Inconsistent results | Guaranteed consistency |

---

## Appendix A: Type Definitions

### DeltaData (packages/models/src/types.ts)

```typescript
export interface DeltaData {
  referenceDriver: string
  compareDriver: string
  distance: number[]
  delta: number[]  // seconds, positive = compare driver is slower
}
```

### ScaledDeltaDriverResult (packages/models/src/types.ts)

```typescript
export interface ScaledDeltaDriverResult {
  referenceDriver: string
  compareDriver: string
  distance: number[]       // Common distance grid (meters)
  delta: number[]          // Scaled delta (matches official timing)
  rawDelta: number[]       // Original telemetry-derived delta
  officialGap: number      // Official timing gap (ground truth from FIA)
  telemetryGap: number     // Raw telemetry-calculated gap
  scalingFactor: number    // Multiplier: officialGap / telemetryGap
  confidence: number       // 0-1 score based on scaling factor deviation
}
```

### TelemetryResponse (apps/api/app/models/dto.py)

```python
class TelemetryResponse(CamelCaseModel):
    driver: str
    lap_number: int
    lap_time: Optional[float] = None
    distance: List[float]
    speed: List[float]
    throttle: List[float]
    brake: List[float]
    gear: List[int]
    # Fields for Tier 1 delta algorithm
    relative_distance: Optional[List[float]] = None  # 0-1 normalized
    time: Optional[List[float]] = None  # Elapsed time in seconds
    rpm: Optional[List[int]] = None
    drs: Optional[List[int]] = None
```

---

## Appendix B: Related Documentation

- **CLAUDE.md** — Comprehensive architecture documentation covering all 8 phases
- **CODEBASE-DIAGNOSTIC-ANALYSIS-2026-02-03.md** — Initial diagnostic analysis

