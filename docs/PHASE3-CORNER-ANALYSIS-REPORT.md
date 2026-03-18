# Phase 3: Corner Analysis Module - Implementation Report

## Executive Summary

**Date:** January 19, 2026
**Feature Branch:** `feature/ai-insights-v2`
**Status:** ✅ COMPLETE

Phase 3 implements the Corner Analysis Module, which analyzes WHERE and WHY time is gained or lost at each corner. This builds on Phase 2's `get_delta_change_in_range()` function from `delta_analysis.py`.

### Key Capabilities
- Detects braking zones using telemetry (brake percentage + gradient)
- Defines corner zones with hybrid approach (fixed offsets + brake refinement)
- Computes delta change within each corner zone
- Attributes cause (braking, apex, exit, multiple, unknown)
- Provides confidence levels (high, medium, low)

---

## Architecture Decisions

### Design Questions & Answers (User-Approved)

| Question | Decision |
|----------|----------|
| **Corner zone definition** | Hybrid approach: Fixed offsets (apex - 200m / apex + 100m) + brake telemetry refinement |
| **Multiple compare_drivers** | YES - Efficient I/O batching (one telemetry fetch, multiple comparisons) |
| **Corner data source** | Pass from frontend (already available via `useTrackQuery`) |

### Algorithm Overview

```
1. Search zone: apex - 250m to apex - 50m
2. Find braking point: first point where brake > 20% AND gradient > 5%/10m
3. If found: brake_start = detected point, confidence = HIGH
4. Fallback: brake_start = apex - 200m, confidence = MEDIUM
5. Corner zone: brake_start to apex + 100m
6. Get delta change using Phase 2's get_delta_change_in_range()
7. Determine cause: braking/apex/exit/multiple based on where gain occurs
```

---

## Files Created (5 new files)

### 1. `apps/analysis_service/services/corner_analysis.py` (~400 lines)

**Purpose:** Core analysis module with hybrid zone detection algorithm

**Key Components:**
```python
# Data Classes
@dataclass
class CornerInput:
    corner_number: int
    apex_distance: float
    corner_type: str  # "left" or "right"
    name: Optional[str] = None

@dataclass
class CornerResult:
    corner_number: int
    name: Optional[str]
    apex_distance: float
    brake_distance: float
    zone_start: float
    zone_end: float
    delta_change: float  # seconds, positive = compare driver slower
    cause: CauseType  # "braking" | "apex" | "exit" | "multiple" | "unknown"
    confidence: ConfidenceLevel  # "high" | "medium" | "low"

@dataclass
class CornerAnalysisResult:
    reference_driver: str
    compare_driver: str
    corner_results: List[CornerResult]
    total_delta_change: float
    corners_gaining: int
    corners_losing: int
```

**Key Functions:**
```python
def detect_braking_zone(distance, brake, apex_distance, ...) -> Tuple[float, ConfidenceLevel]:
    """Detect braking point using threshold + gradient analysis."""

def determine_cause(delta_result, zone_start, zone_end, apex_distance) -> CauseType:
    """Attribute cause by analyzing delta change in braking/apex/exit phases."""

def analyze_single_corner(delta_result, ref_distance, ref_brake, corner) -> CornerResult:
    """Analyze time gained/lost at a single corner."""

def analyze_corners(delta_result, ref_distance, ref_brake, corners) -> CornerAnalysisResult:
    """Main entry point: analyze all corners for a driver comparison."""
```

**Constants:**
```python
DEFAULT_BRAKE_SEARCH_START = 250  # Search zone starts apex - 250m
DEFAULT_BRAKE_SEARCH_END = 50     # Search zone ends apex - 50m
DEFAULT_ZONE_BEFORE_APEX = 200    # Fallback: zone starts apex - 200m
DEFAULT_ZONE_AFTER_APEX = 100     # Zone ends apex + 100m
BRAKE_THRESHOLD_PERCENT = 20.0   # Minimum brake % to consider "braking"
BRAKE_GRADIENT_THRESHOLD = 5.0   # Minimum gradient (%/10m) for detection
```

---

### 2. `apps/analysis_service/tests/test_corner_analysis.py` (~350 lines)

**Purpose:** 31 unit tests covering all functions

**Test Classes:**
```python
class TestSafeArray:           # 6 tests - array handling edge cases
class TestDetectBrakingZone:   # 6 tests - braking detection
class TestDetermineCause:      # 5 tests - cause attribution
class TestAnalyzeSingleCorner: # 5 tests - single corner analysis
class TestAnalyzeCorners:      # 4 tests - full analysis
class TestIntegration:         # 1 test - full pipeline
class TestEdgeCases:           # 4 tests - edge cases
```

**Sample Test:**
```python
def test_full_pipeline_realistic_data(self):
    """Test full pipeline with realistic telemetry data."""
    # Create brake trace with 3 braking zones
    # Create delta trace showing time lost at corners
    # Verify all corners analyzed correctly
    assert result.corners_losing == 3
    assert result.corners_gaining == 0
```

---

### 3. `apps/web/lib/hooks/useCornerAnalysisQuery.ts`

**Purpose:** React Query hook for fetching corner analysis

```typescript
export function useCornerAnalysisQuery(
  sessionId: string,
  referenceDriver: string,
  compareDrivers: string[],
  corners: Corner[] | undefined,
  sessionPart?: string
) {
  return useQuery<CornerAnalysisResponse>({
    queryKey: queryKeys.ml.cornerAnalysis(sessionId, referenceDriver, compareDrivers, sessionPart),
    queryFn: () => fetchCornerAnalysis(sessionId, referenceDriver, compareDrivers, corners!, sessionPart),
    staleTime: 60000, // 60 seconds cache
    enabled: Boolean(sessionId && referenceDriver && compareDrivers.length > 0 && corners?.length),
    retry: 1,
  })
}
```

---

### 4. `apps/web/components/panels/CornerBreakdownPanel.tsx`

**Purpose:** UI component with sortable table, color-coded deltas, confidence badges

**Features:**
- Sortable columns (Corner, Δ Time, Cause)
- Color-coded delta values (green = gaining, red = losing)
- Confidence badges (HIGH = green, MEDIUM = yellow, LOW = red)
- Cause badges (braking = orange, apex = blue, exit = purple, multiple = pink)
- Driver selector for multi-driver results
- Summary row with totals
- Loading/error states

**Component Structure:**
```tsx
<CornerBreakdownPanel
  results={cornerAnalysisData?.results ?? []}
  referenceDriver={referenceDriver}
  isLoading={isCornerAnalysisLoading}
  error={isCornerAnalysisError ? (cornerAnalysisError as Error)?.message : undefined}
/>
```

---

### 5. `apps/web/lib/hooks/useCornerAnalysisQuery.ts`

(Listed above in #3)

---

## Files Modified (7 files)

### 1. `apps/analysis_service/models/schemas.py`

**Added 5 Pydantic schemas:**

```python
class CornerInput(BaseModel):
    corner_number: int = Field(..., ge=1, description="Sequential corner number")
    name: Optional[str] = Field(None, description="Corner name")
    apex_distance: float = Field(..., ge=0, description="Distance to apex (meters)")
    corner_type: str = Field(..., description="'left' or 'right'")

class CornerResultSchema(BaseModel):
    corner_number: int
    name: Optional[str]
    apex_distance: float
    brake_distance: float
    zone_start: float
    zone_end: float
    delta_change: float
    cause: str  # 'braking', 'apex', 'exit', 'multiple', 'unknown'
    confidence: str  # 'high', 'medium', 'low'

class CornerAnalysisRequest(BaseModel):
    session_id: str
    reference_driver: str
    compare_drivers: List[str]
    corners: List[CornerInput]
    session_part: Optional[str] = None

class CornerAnalysisDriverResult(BaseModel):
    compare_driver: str
    corner_results: List[CornerResultSchema]
    total_delta_change: float
    corners_gaining: int
    corners_losing: int

class CornerAnalysisResponse(BaseModel):
    session_id: str
    reference_driver: str
    results: List[CornerAnalysisDriverResult]
    metadata: Dict[str, Any]
```

---

### 2. `apps/analysis_service/main.py`

**Added imports:**
```python
from models.schemas import (
    CornerAnalysisRequest,
    CornerAnalysisResponse,
    CornerAnalysisDriverResult,
    CornerResultSchema,
)
from services.corner_analysis import (
    analyze_corners,
    CornerInput as CACornerInput,
    CornerResult,
)
```

**Added endpoint:**
```python
@app.post(
    "/analysis/corner-analysis",
    response_model=CornerAnalysisResponse,
    summary="Analyze time gained/lost at each corner",
    tags=["Phase 3 - Corner Analysis"]
)
async def get_corner_analysis(request: CornerAnalysisRequest):
    """
    Analyze WHERE and WHY time is gained or lost at each corner.

    1. Fetches telemetry for all drivers
    2. Calculates scaled delta (Phase 2)
    3. Performs corner-by-corner analysis (Phase 3)
    4. Returns detailed results with cause and confidence
    """
```

**Updated startup logging:**
```python
logger.info("Endpoints: /health, /lap-similarity, /driver-style-clustering, /analysis/scaled-delta, /analysis/corner-analysis")
```

---

### 3. `packages/models/src/types.ts`

**Added 6 TypeScript types:**

```typescript
/** Input for a corner to analyze */
export interface CornerInput {
  cornerNumber: number
  name?: string
  apexDistance: number
  cornerType: 'left' | 'right'
}

/** Cause of time gain/loss at a corner */
export type CornerCause = 'braking' | 'apex' | 'exit' | 'multiple' | 'unknown'

/** Confidence level for corner analysis */
export type CornerConfidence = 'high' | 'medium' | 'low'

/** Result of analyzing a single corner */
export interface CornerResult {
  cornerNumber: number
  name?: string
  apexDistance: number
  brakeDistance: number
  zoneStart: number
  zoneEnd: number
  deltaChange: number  // positive = compare driver slower
  cause: CornerCause
  confidence: CornerConfidence
}

/** Corner analysis result for a single driver comparison */
export interface CornerAnalysisDriverResult {
  compareDriver: string
  cornerResults: CornerResult[]
  totalDeltaChange: number
  cornersGaining: int
  cornersLosing: int
}

/** Complete response from corner analysis endpoint */
export interface CornerAnalysisResponse {
  sessionId: string
  referenceDriver: string
  results: CornerAnalysisDriverResult[]
  metadata: {
    sessionPart?: string
    driversAnalyzed: number
    cornersAnalyzed: number
    driversFailed?: number
    errors?: string[]
  }
}
```

---

### 4. `apps/web/lib/api.ts`

**Added import:**
```typescript
import { Corner, CornerAnalysisResponse } from '@/../../packages/models/src/types'
```

**Added function:**
```typescript
export async function fetchCornerAnalysis(
  sessionId: string,
  referenceDriver: string,
  compareDrivers: string[],
  corners: Corner[],
  sessionPart?: string
): Promise<CornerAnalysisResponse> {
  const response = await fetch(`${ML_SERVICE_URL}/analysis/corner-analysis`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      session_id: sessionId,
      reference_driver: referenceDriver,
      compare_drivers: compareDrivers,
      corners: corners.map(c => ({
        corner_number: c.cornerNumber,
        name: c.name,
        apex_distance: c.distance,
        corner_type: c.type,
      })),
      session_part: sessionPart,
    }),
  })
  // ... error handling and camelCase transformation
}
```

---

### 5. `apps/web/lib/hooks/queryKeys.ts`

**Added query key:**
```typescript
ml: {
  // ... existing keys
  cornerAnalysis: (
    sessionId: string,
    refDriver: string,
    compareDrivers: string[],
    sessionPart?: string
  ) =>
    ['ml', 'cornerAnalysis', sessionId, refDriver, {
      compareDrivers: [...compareDrivers].sort(),
      sessionPart
    }] as const,
}
```

---

### 6. `apps/web/lib/hooks/index.ts`

**Added export:**
```typescript
export { useCornerAnalysisQuery } from './useCornerAnalysisQuery'
```

---

### 7. `apps/web/app/qualifying/QualifyingContent.tsx`

**Added imports:**
```typescript
import { useCornerAnalysisQuery } from '@/lib/hooks'
import { CornerBreakdownPanel } from '@/components/panels/CornerBreakdownPanel'
```

**Added query:**
```typescript
// Phase 3: Corner Analysis Query
const {
  data: cornerAnalysisData,
  isLoading: isCornerAnalysisLoading,
  isError: isCornerAnalysisError,
  error: cornerAnalysisError,
} = useCornerAnalysisQuery(
  sessionId,
  referenceDriver,
  compareDrivers,
  trackData?.corners,
  qualifyingPart
)
```

**Added component:**
```tsx
{/* Phase 3: Corner Analysis Breakdown */}
<CornerBreakdownPanel
  results={cornerAnalysisData?.results ?? []}
  referenceDriver={referenceDriver}
  isLoading={isCornerAnalysisLoading}
  error={isCornerAnalysisError ? (cornerAnalysisError as Error)?.message : undefined}
/>
```

---

## Testing & Verification

### Unit Tests

**Command:**
```bash
cd "C:/f1-engineering-app"
docker compose run --rm ml bash -c "pip install pytest -q && python -m pytest tests/test_corner_analysis.py -v --tb=short --cache-clear"
```

**Result:** ✅ 31/31 tests passing

```
tests/test_corner_analysis.py::TestSafeArray::test_safe_array_with_valid_list PASSED
tests/test_corner_analysis.py::TestSafeArray::test_safe_array_with_numpy_array PASSED
tests/test_corner_analysis.py::TestSafeArray::test_safe_array_handles_none PASSED
tests/test_corner_analysis.py::TestSafeArray::test_safe_array_handles_empty_list PASSED
tests/test_corner_analysis.py::TestSafeArray::test_safe_array_handles_nan_values PASSED
tests/test_corner_analysis.py::TestSafeArray::test_safe_array_all_nan PASSED
tests/test_corner_analysis.py::TestDetectBrakingZone::test_detect_braking_zone_clear_braking PASSED
tests/test_corner_analysis.py::TestDetectBrakingZone::test_detect_braking_zone_no_braking PASSED
tests/test_corner_analysis.py::TestDetectBrakingZone::test_detect_braking_zone_gradual_braking PASSED
tests/test_corner_analysis.py::TestDetectBrakingZone::test_detect_braking_zone_already_braking PASSED
tests/test_corner_analysis.py::TestDetectBrakingZone::test_detect_braking_zone_empty_arrays PASSED
tests/test_corner_analysis.py::TestDetectBrakingZone::test_detect_braking_zone_invalid_search_zone PASSED
tests/test_corner_analysis.py::TestDetermineCause::test_determine_cause_braking PASSED
tests/test_corner_analysis.py::TestDetermineCause::test_determine_cause_apex PASSED
tests/test_corner_analysis.py::TestDetermineCause::test_determine_cause_exit PASSED
tests/test_corner_analysis.py::TestDetermineCause::test_determine_cause_multiple PASSED
tests/test_corner_analysis.py::TestDetermineCause::test_determine_cause_unknown_minimal_delta PASSED
tests/test_corner_analysis.py::TestAnalyzeSingleCorner::test_analyze_single_corner_basic PASSED
tests/test_corner_analysis.py::TestAnalyzeSingleCorner::test_analyze_single_corner_gain_in_braking PASSED
tests/test_corner_analysis.py::TestAnalyzeSingleCorner::test_analyze_single_corner_gain_at_apex PASSED
tests/test_corner_analysis.py::TestAnalyzeSingleCorner::test_analyze_single_corner_gain_on_exit PASSED
tests/test_corner_analysis.py::TestAnalyzeSingleCorner::test_analyze_single_corner_invalid_zone PASSED
tests/test_corner_analysis.py::TestAnalyzeCorners::test_analyze_corners_multiple_corners PASSED
tests/test_corner_analysis.py::TestAnalyzeCorners::test_analyze_corners_summary_calculation PASSED
tests/test_corner_analysis.py::TestAnalyzeCorners::test_analyze_corners_empty_corners PASSED
tests/test_corner_analysis.py::TestAnalyzeCorners::test_analyze_corners_with_empty_telemetry PASSED
tests/test_corner_analysis.py::TestIntegration::test_full_pipeline_realistic_data PASSED
tests/test_corner_analysis.py::TestEdgeCases::test_corner_at_track_start PASSED
tests/test_corner_analysis.py::TestEdgeCases::test_corner_at_track_end PASSED
tests/test_corner_analysis.py::TestEdgeCases::test_very_short_corner_zone PASSED
tests/test_corner_analysis.py::TestEdgeCases::test_negative_delta_time_gained PASSED

======================== 31 passed, 1 warning in 0.20s =========================
```

---

### Endpoint Test

**Command:**
```bash
# Start services
docker compose up -d ml api

# Test endpoint
curl -s -X POST http://localhost:8501/analysis/corner-analysis \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "2025_24_Qualifying",
    "reference_driver": "NOR",
    "compare_drivers": ["VER"],
    "corners": [
      {"corner_number": 1, "name": "Turn 1", "apex_distance": 180, "corner_type": "left"},
      {"corner_number": 5, "name": "Turn 5", "apex_distance": 700, "corner_type": "right"}
    ],
    "session_part": "Q3"
  }'
```

**Response:** ✅ Working

```json
{
  "session_id": "2025_24_Qualifying",
  "reference_driver": "NOR",
  "results": [
    {
      "compare_driver": "VER",
      "corner_results": [
        {
          "corner_number": 1,
          "name": "Turn 1",
          "apex_distance": 180.0,
          "brake_distance": 0.34,
          "zone_start": 0.51,
          "zone_end": 280.0,
          "delta_change": -0.082,
          "cause": "multiple",
          "confidence": "medium"
        },
        {
          "corner_number": 5,
          "name": "Turn 5",
          "apex_distance": 700.0,
          "brake_distance": 500.0,
          "zone_start": 500.0,
          "zone_end": 800.0,
          "delta_change": 0.066,
          "cause": "multiple",
          "confidence": "medium"
        }
      ],
      "total_delta_change": -0.016,
      "corners_gaining": 1,
      "corners_losing": 1
    }
  ],
  "metadata": {
    "session_part": "Q3",
    "drivers_analyzed": 1,
    "corners_analyzed": 2,
    "drivers_failed": 0,
    "errors": null
  }
}
```

**Interpretation:**
- **Turn 1**: VER gained 0.082s (negative delta = compare driver faster)
- **Turn 5**: VER lost 0.066s (positive delta = compare driver slower)
- **Total**: VER gained 0.016s overall across these 2 corners
- **Summary**: 1 corner gaining, 1 corner losing

---

## Implementation Steps Completed

| Step | Description | Status |
|------|-------------|--------|
| 1 | Create `corner_analysis.py` module | ✅ |
| 2 | Create `test_corner_analysis.py` tests | ✅ |
| 3 | Add Pydantic schemas to `schemas.py` | ✅ |
| 4 | Add ML endpoint to `main.py` | ✅ |
| 5 | Add TypeScript types to `types.ts` | ✅ |
| 6 | Add `fetchCornerAnalysis()` to `api.ts` | ✅ |
| 7 | Create `useCornerAnalysisQuery` hook | ✅ |
| 8 | Update `queryKeys.ts` and `index.ts` | ✅ |
| 9 | Create `CornerBreakdownPanel` component | ✅ |
| 10 | Integrate into `QualifyingContent` | ✅ |
| 11 | Run tests and verify endpoint | ✅ |

---

## Commit Message

```
feat(ai-insights): Phase 3 - Corner Analysis Module

- Create corner_analysis.py with hybrid zone detection algorithm
- Add 31 unit tests for corner analysis (100% passing)
- Add POST /analysis/corner-analysis endpoint
- Add 5 Pydantic schemas and 6 TypeScript types
- Create CornerBreakdownPanel UI component with:
  - Sortable table (corner, delta, cause)
  - Color-coded deltas (green/red)
  - Confidence badges (high/medium/low)
  - Driver selector for multi-driver analysis
- Integrate into QualifyingContent page

Corner analysis shows:
- WHERE time is gained/lost at each corner
- WHY (braking/apex/exit cause detection)
- Confidence level based on brake detection quality

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
```

---

## Files Summary

| Action | File | Lines |
|--------|------|-------|
| CREATE | `apps/analysis_service/services/corner_analysis.py` | ~400 |
| CREATE | `apps/analysis_service/tests/test_corner_analysis.py` | ~350 |
| CREATE | `apps/web/lib/hooks/useCornerAnalysisQuery.ts` | ~35 |
| CREATE | `apps/web/components/panels/CornerBreakdownPanel.tsx` | ~200 |
| MODIFY | `apps/analysis_service/models/schemas.py` | +70 |
| MODIFY | `apps/analysis_service/main.py` | +180 |
| MODIFY | `packages/models/src/types.ts` | +60 |
| MODIFY | `apps/web/lib/api.ts` | +75 |
| MODIFY | `apps/web/lib/hooks/queryKeys.ts` | +8 |
| MODIFY | `apps/web/lib/hooks/index.ts` | +1 |
| MODIFY | `apps/web/app/qualifying/QualifyingContent.tsx` | +15 |

**Total:** 4 files created, 7 files modified, ~1,400 lines of code

---

## Dependencies

Phase 3 builds on:
- **Phase 2 `delta_analysis.py`**: Uses `get_delta_change_in_range()` for corner analysis
- **Track data**: Corner apex distances from `apps/api/app/data/tracks/*.json`
- **Telemetry**: Brake data available via existing API endpoints (`TelemetryResponse.brake`)

---

## Previous Phases

| Phase | Description | Status |
|-------|-------------|--------|
| Phase 1 | Lap filtering + logging infrastructure | ✅ COMPLETE |
| Phase 2 | Scaled delta analysis + UI integration | ✅ COMPLETE |
| **Phase 3** | **Corner analysis module** | **✅ COMPLETE** |

---

## Next Steps (Future Phases)

Potential Phase 4 features:
- Sector-by-sector analysis (similar to corner analysis but for sectors)
- Mini-sector analysis (10m increments)
- Comparative analysis across multiple sessions
- Historical trend analysis per corner
