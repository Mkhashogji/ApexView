# Phase 6: Performance Insights Orchestrator

## Document Information
- **Phase**: 6 of 8 (Refined AI Insights Architecture)
- **Implementation Date**: January 2026
- **Author**: ApexView Engineering Team
- **Status**: Complete
- **Test Coverage**: 28 unit tests (195 total across all phases)

---

## 1. Overview of Phase 6

### 1.1 Purpose

Phase 6 implements a **Performance Insights Orchestrator** - a unified API endpoint that chains Phases 2-5 into a single API call. This follows the **Backend-for-Frontend (BFF)** architectural pattern, reducing frontend complexity from 4 separate API calls to just 1.

### 1.2 Problem Statement

Prior to Phase 6, the frontend had to make sequential API calls to:
1. `/ml/scaled-delta` (Phase 2) - Get time delta analysis
2. `/ml/corner-analysis` (Phase 3) - Get corner-by-corner breakdown
3. `/ml/technique-profile` (Phase 4) - Get technique classification
4. `/ml/generate-insight` (Phase 5) - Get natural language insights

This created several issues:
- **Network Overhead**: 4 round-trips per analysis request
- **Complex State Management**: Frontend had to coordinate multiple async calls
- **Error Handling Complexity**: Each call could fail independently
- **Duplicate Data Fetching**: Telemetry was fetched multiple times internally

### 1.3 Solution

The Performance Insights Orchestrator provides:
- **Single Endpoint**: `POST /ml/performance-insights`
- **Complete Analysis**: All phases executed and results aggregated
- **Unified Response**: One response object with all driver data
- **Phase Timing**: Execution metrics for debugging and monitoring
- **Graceful Degradation**: Partial results returned even if some drivers fail

### 1.4 Key Benefits

| Benefit | Before Phase 6 | After Phase 6 |
|---------|---------------|---------------|
| API Calls | 4 sequential | 1 unified |
| Frontend Code | Complex orchestration | Simple fetch |
| Error Handling | Multiple try/catch | Single handler |
| Response Time | Sum of all phases + overhead | Optimized pipeline |
| Telemetry Fetch | Repeated per phase | Single fetch, shared |

---

## 2. Sequential Implementation Steps

### 2.1 Step 1: Design Pydantic Schemas

**File**: `apps/ml_service/models/schemas.py`

#### 2.1.1 Request Schema

```python
class PerformanceInsightsRequest(BaseModel):
    """Unified request for performance insights."""
    session_id: str           # e.g., "2025_24_Qualifying"
    reference_driver: str     # e.g., "NOR"
    compare_drivers: List[str]  # e.g., ["PIA", "VER"]
    corners: List[CornerInput]  # Track corner definitions
    mode: str = "engineer"    # "engineer" or "driver"
    session_part: Optional[str]  # "Q1", "Q2", or "Q3"
    circuit_name: Optional[str]  # For context in insights
    include_telemetry: bool = True  # Control response size
```

**Design Rationale**:
- Reuses existing `CornerInput` schema from Phase 3
- `include_telemetry` flag allows frontend to reduce payload size
- `mode` parameter propagates to Phase 5 for audience-specific output

#### 2.1.2 Driver Result Schema

```python
class DriverPerformanceResult(BaseModel):
    """Complete analysis for one driver comparison."""
    driver: str

    # Phase 2: Delta
    official_gap: float
    scaling_confidence: float
    delta: Optional[List[float]]
    distance: Optional[List[float]]

    # Phase 3: Corners
    corners_gaining: int
    corners_losing: int
    total_corner_delta: float
    corner_results: List[CornerResultSchema]

    # Phase 4: Technique
    technique_profile: Optional[TechniqueProfileSchema]

    # Phase 5: Insight
    insight: Optional[NaturalLanguageInsightSchema]
```

**Design Rationale**:
- Aggregates all phase outputs into single driver object
- Optional fields allow partial results if phases fail
- Reuses existing schemas where possible for consistency

#### 2.1.3 Timing Schema

```python
class PhaseTimingInfo(BaseModel):
    """Execution timing for debugging."""
    phase: str          # "telemetry_fetch", "delta_analysis", etc.
    duration_ms: int    # Execution time
    success: bool       # Whether phase completed
    error: Optional[str]  # Error message if failed
```

**Design Rationale**:
- Enables performance monitoring and optimization
- Helps identify bottlenecks in the pipeline
- Provides debugging information without exposing internals

#### 2.1.4 Response Schema

```python
class PerformanceInsightsResponse(BaseModel):
    """Complete orchestrator response."""
    session_id: str
    reference_driver: str
    circuit_name: Optional[str]
    mode: str

    results: List[DriverPerformanceResult]
    session_percentiles: Optional[SessionPercentilesSchema]

    total_drivers_requested: int
    total_drivers_processed: int
    total_corners: int

    phase_timing: List[PhaseTimingInfo]
    total_duration_ms: int

    errors: List[str]
    warnings: List[str]
```

**Design Rationale**:
- Separates driver-specific results from session-wide context
- Timing breakdown enables SLA monitoring
- Error/warning lists enable graceful degradation reporting

---

### 2.2 Step 2: Create Orchestrator Module

**File**: `apps/ml_service/services/performance_orchestrator.py`

#### 2.2.1 Module Structure

```
performance_orchestrator.py
├── Constants
│   └── API_SERVICE_URL, TELEMETRY_TIMEOUT_SECONDS
├── Data Classes
│   ├── PerformanceInsightsConfig
│   ├── PhaseTimingInfo
│   ├── DriverPerformanceResult
│   └── PerformanceInsightsResult
├── Utility Functions
│   ├── _safe_array()
│   ├── _technique_profile_to_dict()
│   ├── _session_percentiles_to_dict()
│   ├── _insight_to_dict()
│   └── _corner_result_to_dict()
├── Telemetry Fetching
│   ├── fetch_driver_telemetry()
│   └── fetch_all_telemetry()
├── Phase Execution
│   ├── run_phase2_delta()
│   ├── run_phase3_corner()
│   ├── run_phase4_technique()
│   └── run_phase5_insight()
└── Main Orchestration
    └── orchestrate_performance_insights()
```

#### 2.2.2 Configuration Dataclass

```python
@dataclass
class PerformanceInsightsConfig:
    """Orchestrator configuration."""
    session_id: str
    reference_driver: str
    compare_drivers: List[str]
    corners: List[CornerInput]
    mode: str = "engineer"
    session_part: Optional[str] = None
    circuit_name: Optional[str] = None
    include_telemetry: bool = True
```

**Technical Note**: Uses `dataclass` internally rather than Pydantic for performance - Pydantic validation overhead is only needed at API boundaries.

#### 2.2.3 Telemetry Fetching

```python
async def fetch_driver_telemetry(
    client: httpx.AsyncClient,
    session_id: str,
    driver: str,
    session_part: Optional[str] = None
) -> Tuple[Optional[Dict], Optional[str]]:
    """Fetch telemetry from API service."""
```

**Implementation Details**:
- Uses `httpx.AsyncClient` for async HTTP
- Returns tuple of (data, error) for explicit error handling
- Validates required fields (distance, speed) before returning
- Includes lap_time for Phase 2 scaling

```python
async def fetch_all_telemetry(
    client: httpx.AsyncClient,
    session_id: str,
    reference_driver: str,
    compare_drivers: List[str],
    session_part: Optional[str] = None
) -> Tuple[Dict[str, Dict], List[str]]:
    """Fetch telemetry for all drivers concurrently."""
```

**Concurrency Strategy**:
```python
tasks = [
    fetch_driver_telemetry(client, session_id, driver, session_part)
    for driver in all_drivers
]
results = await asyncio.gather(*tasks)
```

This fetches all telemetry in parallel, reducing latency from O(n) to O(1) for n drivers.

#### 2.2.4 Phase Execution Functions

Each phase is wrapped in a function that:
1. Accepts phase-specific inputs
2. Calls the underlying phase module
3. Returns tuple of (result, error) for explicit error handling
4. Logs phase-specific context

**Phase 2: Delta Analysis**
```python
def run_phase2_delta(
    ref_telemetry: Dict,
    comp_telemetry: Dict,
    reference_driver: str,
    compare_driver: str
) -> Tuple[Optional[DeltaResult], Optional[str]]:
    """Execute Phase 2 delta calculation."""
    result = calculate_scaled_delta(
        ref_telemetry=ref_telemetry,
        comp_telemetry=comp_telemetry,
        ref_official_time=ref_telemetry.get("lap_time", 90.0),
        comp_official_time=comp_telemetry.get("lap_time", 90.0),
        ref_driver=reference_driver,
        comp_driver=compare_driver
    )
    return result, None
```

**Phase 3: Corner Analysis**
```python
def run_phase3_corner(
    delta_result: DeltaResult,
    ref_telemetry: Dict,
    corners: List[CornerInput]
) -> Tuple[Optional[CornerAnalysisResult], Optional[str]]:
    """Execute Phase 3 corner analysis."""
    result = analyze_corners(
        delta_result=delta_result,
        ref_distance=ref_telemetry["distance"],
        ref_brake=ref_telemetry["brake"],
        corners=corners
    )
    return result, None
```

**Phase 4: Technique Profiling**
```python
def run_phase4_technique(
    corner_results_by_driver: Dict[str, CornerAnalysisResult],
    reference_driver: str
) -> Tuple[List[TechniqueProfile], Optional[SessionPercentiles], Optional[str]]:
    """Execute Phase 4 technique profiling."""
    profiles, percentiles = profile_drivers(
        corner_results_by_driver=corner_results_by_driver,
        reference_driver=reference_driver,
        weight_by_confidence=True
    )
    return profiles, percentiles, None
```

**Phase 5: Insight Generation**
```python
def run_phase5_insight(
    profile: TechniqueProfile,
    mode: InsightMode,
    session_context: Optional[Dict] = None
) -> Tuple[Optional[NaturalLanguageInsight], Optional[str]]:
    """Execute Phase 5 insight generation."""
    result = generate_insights(
        profile=profile,
        mode=mode,
        session_context=session_context
    )
    return result.insight if result.success else None, None
```

#### 2.2.5 Conversion Functions

Dataclasses from phase modules must be converted to dictionaries for JSON serialization:

```python
def _technique_profile_to_dict(profile: TechniqueProfile) -> Dict:
    """Convert TechniqueProfile to serializable dict."""
    return {
        "driver": profile.driver,
        "reference_driver": profile.reference_driver,
        "braking": {
            "level": profile.braking.level.value,
            "descriptor": profile.braking.descriptor,
            "percentile": profile.braking.percentile,
            # ... other fields
        },
        # ... other dimensions
        "style_summary": profile.style_summary,
        "overall_confidence": profile.overall_confidence,
    }
```

**Why Manual Conversion?**
- Dataclasses don't automatically serialize enums (TechniqueLevel.STRONG → "strong")
- Allows selective field inclusion
- Decouples internal representation from API contract

#### 2.2.6 Main Orchestration Function

```python
async def orchestrate_performance_insights(
    config: PerformanceInsightsConfig,
    client: Optional[httpx.AsyncClient] = None
) -> PerformanceInsightsResult:
    """Main orchestration entry point."""
```

**Execution Flow**:

```
┌─────────────────────────────────────────────────────────────────────┐
│                    ORCHESTRATION PIPELINE                           │
├─────────────────────────────────────────────────────────────────────┤
│                                                                     │
│  Stage 1: Telemetry Fetch                                          │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  fetch_all_telemetry() - Concurrent for all drivers           │ │
│  │  └─► telemetry_by_driver: {driver: telemetry_dict}            │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              ↓                                      │
│  Stage 2: Phase 2 - Delta (per driver)                             │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  for driver in compare_drivers:                                │ │
│  │      run_phase2_delta(ref_telem, driver_telem, ...)           │ │
│  │  └─► delta_results: {driver: DeltaResult}                     │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              ↓                                      │
│  Stage 3: Phase 3 - Corner (per driver)                            │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  for driver in delta_results:                                  │ │
│  │      run_phase3_corner(delta_result, ref_telem, corners)      │ │
│  │  └─► corner_results: {driver: CornerAnalysisResult}           │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              ↓                                      │
│  Stage 4: Phase 4 - Technique (all drivers)                        │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  run_phase4_technique(corner_results, reference_driver)       │ │
│  │  └─► profiles: {driver: TechniqueProfile}                     │ │
│  │  └─► session_percentiles: SessionPercentiles                  │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              ↓                                      │
│  Stage 5: Phase 5 - Insights (per driver)                          │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  for driver in profiles:                                       │ │
│  │      run_phase5_insight(profile, mode, context)               │ │
│  │  └─► insights: {driver: NaturalLanguageInsight}               │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                              ↓                                      │
│  Stage 6: Assemble Results                                         │
│  ┌───────────────────────────────────────────────────────────────┐ │
│  │  Combine all phase outputs into DriverPerformanceResult       │ │
│  │  Add session_percentiles, phase_timing, errors                │ │
│  │  └─► PerformanceInsightsResult                                │ │
│  └───────────────────────────────────────────────────────────────┘ │
│                                                                     │
└─────────────────────────────────────────────────────────────────────┘
```

**Timing Collection**:

Each stage records its execution time:

```python
phase2_start = time.time()
# ... execute phase 2 ...
phase2_duration = int((time.time() - phase2_start) * 1000)
result.phase_timing.append(PhaseTimingInfo(
    phase="delta_analysis",
    duration_ms=phase2_duration,
    success=len(delta_results) > 0,
    error=phase2_errors[0] if phase2_errors else None
))
```

**Error Isolation**:

Each phase handles errors independently:

```python
for driver in config.compare_drivers:
    try:
        delta_result, error = run_phase2_delta(...)
        if error:
            phase2_errors.append(error)
        elif delta_result:
            delta_results[driver] = delta_result
    except Exception as e:
        phase2_errors.append(f"Phase 2 error for {driver}: {str(e)}")
```

This ensures one driver's failure doesn't abort the entire analysis.

---

### 2.3 Step 3: Add API Endpoint

**File**: `apps/ml_service/main.py`

#### 2.3.1 Imports

```python
from models.schemas import (
    # ... existing imports ...
    # Phase 6: Performance Insights Orchestrator
    PerformanceInsightsRequest,
    PerformanceInsightsResponse,
    DriverPerformanceResult,
    PhaseTimingInfo,
)
from services.performance_orchestrator import (
    orchestrate_performance_insights,
    PerformanceInsightsConfig,
    PerformanceInsightsResult,
    DriverPerformanceResult as OrchestratorDriverResult,
    PhaseTimingInfo as OrchestratorPhaseTimingInfo,
)
```

**Alias Pattern**: Internal dataclasses are aliased to avoid conflicts with Pydantic schemas of the same name.

#### 2.3.2 Endpoint Definition

```python
@app.post(
    "/ml/performance-insights",
    response_model=PerformanceInsightsResponse,
    summary="Unified performance insights (chains Phases 2-5)",
    tags=["Phase 6 - Performance Orchestrator"]
)
async def get_performance_insights(request: PerformanceInsightsRequest):
    """Orchestrate complete performance analysis pipeline."""
```

#### 2.3.3 Request Processing

```python
# Convert request corners to CornerInput dataclass
corner_inputs = [
    CACornerInputForOrchestrator(
        corner_number=c.corner_number,
        apex_distance=c.apex_distance,
        corner_type=c.corner_type,
        name=c.name
    )
    for c in request.corners
]

# Build orchestrator config
config = PerformanceInsightsConfig(
    session_id=request.session_id,
    reference_driver=request.reference_driver,
    compare_drivers=request.compare_drivers,
    corners=corner_inputs,
    mode=request.mode,
    session_part=request.session_part,
    circuit_name=request.circuit_name,
    include_telemetry=request.include_telemetry,
)
```

#### 2.3.4 Response Conversion

The orchestrator returns internal dataclasses that must be converted to Pydantic schemas:

```python
driver_results = []
for dr in result.results:
    driver_results.append(DriverPerformanceResult(
        driver=dr.driver,
        official_gap=dr.official_gap,
        scaling_confidence=dr.scaling_confidence,
        delta=dr.delta,
        distance=dr.distance,
        # ... corner results conversion ...
        technique_profile=TechniqueProfileSchema(
            driver=dr.technique_profile["driver"],
            # ... nested schema construction ...
        ) if dr.technique_profile else None,
        insight=NaturalLanguageInsightSchema(
            # ... insight schema construction ...
        ) if dr.insight else None,
    ))
```

**Why Not Return Dict Directly?**
- Pydantic provides response validation
- OpenAPI documentation auto-generated from schemas
- Type hints enable IDE support for consumers

---

### 2.4 Step 4: Create Unit Tests

**File**: `apps/ml_service/tests/test_performance_orchestrator.py`

#### 2.4.1 Test Categories

| Category | Tests | Purpose |
|----------|-------|---------|
| Config Tests | 2 | Validate config dataclass defaults/values |
| Phase 2 Tests | 2 | Test delta execution and edge cases |
| Phase 3 Tests | 2 | Test corner analysis execution |
| Phase 4 Tests | 3 | Test technique profiling with 1/2+ drivers |
| Phase 5 Tests | 3 | Test insight generation in both modes |
| Conversion Tests | 4 | Test dataclass → dict conversions |
| Dataclass Tests | 4 | Test result dataclass construction |
| Integration Tests | 2 | Test orchestration with mocked HTTP |
| Edge Case Tests | 4 | Test empty inputs, large deltas, etc. |
| Performance Tests | 2 | Verify execution completes quickly |

#### 2.4.2 Fixtures

```python
@pytest.fixture
def sample_telemetry():
    """Create sample telemetry data."""
    distance = list(np.linspace(0, 5000, 100))
    return {
        "distance": distance,
        "speed": [200 + np.sin(i / 10) * 50 for i in range(100)],
        "brake": [50 if 20 < i < 40 else 0 for i in range(100)],
        "throttle": [100 if i < 20 or i > 50 else 50 for i in range(100)],
        "lap_time": 90.5,
    }

@pytest.fixture
def sample_corners():
    """Create sample corner definitions."""
    return [
        CornerInput(corner_number=1, apex_distance=500, corner_type="right", name="Turn 1"),
        CornerInput(corner_number=2, apex_distance=1200, corner_type="left", name="Turn 2"),
        # ... more corners
    ]
```

#### 2.4.3 Key Test Patterns

**Phase Execution Test**:
```python
def test_run_phase2_delta_success(self, sample_telemetry):
    """Test successful Phase 2 execution."""
    ref_telemetry = sample_telemetry.copy()
    comp_telemetry = sample_telemetry.copy()
    comp_telemetry["lap_time"] = 90.7  # 0.2s slower

    result, error = run_phase2_delta(
        ref_telemetry, comp_telemetry, "NOR", "PIA"
    )

    assert error is None
    assert result is not None
    assert result.official_gap == pytest.approx(0.2, abs=0.01)
```

**Conversion Test**:
```python
def test_technique_profile_to_dict(self, sample_technique_profile):
    """Test TechniqueProfile to dict conversion."""
    result = _technique_profile_to_dict(sample_technique_profile)

    assert result["driver"] == "PIA"
    assert result["braking"]["level"] == "strong"
    assert len(result["top_gaining_corners"]) == 2
```

**Integration Test (Mocked)**:
```python
@pytest.mark.asyncio
async def test_orchestration_handles_missing_reference_driver(self, sample_config):
    """Test orchestration handles missing reference driver."""
    mock_client = AsyncMock()
    mock_response = MagicMock()
    mock_response.status_code = 404
    mock_client.get.return_value = mock_response

    result = await orchestrate_performance_insights(sample_config, mock_client)

    assert len(result.errors) > 0
    assert result.total_drivers_processed == 0
```

**Performance Test**:
```python
def test_delta_calculation_performance(self, sample_telemetry):
    """Test delta calculation completes quickly."""
    import time
    start = time.time()
    for _ in range(10):
        run_phase2_delta(ref_telem, comp_telem, "NOR", "PIA")
    elapsed = time.time() - start

    assert elapsed < 1.0  # 10 calculations under 1 second
```

---

## 3. Phase 6 Workflow

### 3.1 Complete Data Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FRONTEND REQUEST                                     │
│  POST /ml/performance-insights                                              │
│  {                                                                          │
│    "session_id": "2025_24_Qualifying",                                      │
│    "reference_driver": "NOR",                                               │
│    "compare_drivers": ["PIA", "VER"],                                       │
│    "corners": [{"corner_number": 1, "apex_distance": 500, ...}],           │
│    "mode": "engineer",                                                      │
│    "include_telemetry": true                                                │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         FASTAPI ENDPOINT                                     │
│  main.py: get_performance_insights()                                        │
│  1. Validate request via Pydantic                                           │
│  2. Convert CornerInput schemas to dataclasses                              │
│  3. Build PerformanceInsightsConfig                                         │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ORCHESTRATOR                                         │
│  performance_orchestrator.py: orchestrate_performance_insights()            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STAGE 1: TELEMETRY FETCH                                           │   │
│  │  ├── fetch_all_telemetry() via httpx.AsyncClient                    │   │
│  │  ├── GET http://api:8000/api/telemetry/{session_id}?driver=NOR     │   │
│  │  ├── GET http://api:8000/api/telemetry/{session_id}?driver=PIA     │   │
│  │  ├── GET http://api:8000/api/telemetry/{session_id}?driver=VER     │   │
│  │  └── (concurrent execution via asyncio.gather)                      │   │
│  │  OUTPUT: telemetry_by_driver = {"NOR": {...}, "PIA": {...}, ...}   │   │
│  │  TIMING: ~200-500ms depending on API latency                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STAGE 2: PHASE 2 - SCALED DELTA                                    │   │
│  │  for each compare_driver:                                           │   │
│  │  ├── run_phase2_delta(ref_telem, comp_telem, ...)                  │   │
│  │  ├── calculate_scaled_delta() from delta_analysis.py               │   │
│  │  │   ├── calculate_raw_delta() - telemetry-based                   │   │
│  │  │   ├── Apply scaling: official_gap / telemetry_gap               │   │
│  │  │   └── Calculate confidence score                                 │   │
│  │  └── Store result: delta_results[driver] = DeltaResult             │   │
│  │  OUTPUT: delta_results = {"PIA": DeltaResult, "VER": DeltaResult}  │   │
│  │  TIMING: ~50-100ms per driver                                       │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STAGE 3: PHASE 3 - CORNER ANALYSIS                                 │   │
│  │  for each delta_result:                                             │   │
│  │  ├── run_phase3_corner(delta_result, ref_telem, corners)           │   │
│  │  ├── analyze_corners() from corner_analysis.py                     │   │
│  │  │   ├── detect_braking_zone() per corner                          │   │
│  │  │   ├── get_delta_change_in_range() per corner                    │   │
│  │  │   └── determine_cause() per corner                              │   │
│  │  └── Store: corner_results[driver] = CornerAnalysisResult          │   │
│  │  OUTPUT: corner_results = {"PIA": CornerAnalysisResult, ...}       │   │
│  │  TIMING: ~20-50ms per driver                                        │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STAGE 4: PHASE 4 - TECHNIQUE PROFILING                             │   │
│  │  run_phase4_technique(corner_results, reference_driver)             │   │
│  │  ├── aggregate_by_cause() per driver                                │   │
│  │  ├── calculate_session_percentiles() across all drivers            │   │
│  │  ├── classify_dimension() per dimension per driver                  │   │
│  │  └── generate_style_summary() per driver                           │   │
│  │  OUTPUT: profiles = {"PIA": TechniqueProfile, "VER": ...}          │   │
│  │          session_percentiles = SessionPercentiles                   │   │
│  │  TIMING: ~10-30ms total                                             │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STAGE 5: PHASE 5 - INSIGHT GENERATION                              │   │
│  │  for each profile:                                                  │   │
│  │  ├── run_phase5_insight(profile, mode, session_context)            │   │
│  │  ├── generate_insights() from insight_generation.py                │   │
│  │  │   ├── classify_confidence()                                     │   │
│  │  │   ├── generate_*_summary() based on mode                        │   │
│  │  │   ├── generate_dimension_insight_*() per dimension              │   │
│  │  │   └── generate_opportunity_insights()                           │   │
│  │  └── Store: insights[driver] = NaturalLanguageInsight              │   │
│  │  OUTPUT: insights = {"PIA": NaturalLanguageInsight, ...}           │   │
│  │  TIMING: ~5-10ms per driver                                         │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                              │                                              │
│                              ▼                                              │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │  STAGE 6: RESULT ASSEMBLY                                           │   │
│  │  for each compare_driver:                                           │   │
│  │  ├── Create DriverPerformanceResult                                 │   │
│  │  │   ├── delta + distance arrays (if include_telemetry)            │   │
│  │  │   ├── corner_results list (converted to dicts)                  │   │
│  │  │   ├── technique_profile (converted to dict)                     │   │
│  │  │   └── insight (converted to dict)                               │   │
│  │  └── Append to results list                                         │   │
│  │  Add: session_percentiles, phase_timing, errors, warnings          │   │
│  │  OUTPUT: PerformanceInsightsResult                                  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         RESPONSE CONVERSION                                  │
│  main.py: Convert dataclasses to Pydantic schemas                           │
│  ├── DriverPerformanceResult (dataclass) → DriverPerformanceResult (schema)│
│  ├── Nested: TechniqueProfileSchema, NaturalLanguageInsightSchema          │
│  └── PhaseTimingInfo (dataclass) → PhaseTimingInfo (schema)                │
└─────────────────────────────────────────────────────────────────────────────┘
                                    │
                                    ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                         JSON RESPONSE                                        │
│  {                                                                          │
│    "session_id": "2025_24_Qualifying",                                      │
│    "reference_driver": "NOR",                                               │
│    "circuit_name": "Bahrain International Circuit",                         │
│    "mode": "engineer",                                                      │
│    "results": [                                                             │
│      {                                                                      │
│        "driver": "PIA",                                                     │
│        "official_gap": 0.200,                                               │
│        "scaling_confidence": 0.95,                                          │
│        "delta": [0.0, 0.001, ...],                                         │
│        "distance": [0, 5, 10, ...],                                        │
│        "corners_gaining": 3,                                                │
│        "corners_losing": 2,                                                 │
│        "total_corner_delta": 0.150,                                         │
│        "corner_results": [...],                                             │
│        "technique_profile": {                                               │
│          "driver": "PIA",                                                   │
│          "braking": {"level": "strong", "percentile": 25, ...},            │
│          "style_summary": "Late braker with excellent traction"            │
│        },                                                                   │
│        "insight": {                                                         │
│          "summary": "PIA vs NOR: Strong under braking...",                 │
│          "dimension_insights": [...],                                       │
│          "opportunity_text": "Focus on apex speed..."                      │
│        }                                                                    │
│      },                                                                     │
│      {...}  // VER results                                                  │
│    ],                                                                       │
│    "session_percentiles": {...},                                            │
│    "total_drivers_requested": 2,                                            │
│    "total_drivers_processed": 2,                                            │
│    "total_corners": 15,                                                     │
│    "phase_timing": [                                                        │
│      {"phase": "telemetry_fetch", "duration_ms": 350, "success": true},    │
│      {"phase": "delta_analysis", "duration_ms": 120, "success": true},     │
│      {"phase": "corner_analysis", "duration_ms": 80, "success": true},     │
│      {"phase": "technique_profiling", "duration_ms": 25, "success": true}, │
│      {"phase": "insight_generation", "duration_ms": 15, "success": true}   │
│    ],                                                                       │
│    "total_duration_ms": 590,                                                │
│    "errors": [],                                                            │
│    "warnings": []                                                           │
│  }                                                                          │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Error Handling Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ERROR HANDLING STRATEGY                              │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Level 1: Telemetry Fetch Errors                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  IF reference driver telemetry missing:                               │ │
│  │    → Return early with error (can't proceed without reference)        │ │
│  │  IF comparison driver telemetry missing:                              │ │
│  │    → Add to errors list, skip driver, continue with others            │ │
│  │  IF timeout:                                                          │ │
│  │    → Add to errors list, skip driver, continue with others            │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Level 2: Phase Execution Errors                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  Each phase wrapped in try/except:                                    │ │
│  │    try:                                                               │ │
│  │      result, error = run_phase_X(...)                                │ │
│  │    except Exception as e:                                             │ │
│  │      errors.append(f"Phase X error for {driver}: {str(e)}")          │ │
│  │      continue  # Skip to next driver                                  │ │
│  │                                                                       │ │
│  │  Phase failures are ISOLATED - one driver's failure doesn't          │ │
│  │  prevent analysis of other drivers.                                   │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
│  Level 3: Result Assembly Errors                                           │
│  ┌───────────────────────────────────────────────────────────────────────┐ │
│  │  IF no drivers processed successfully:                                │ │
│  │    → Return result with errors list populated                         │ │
│  │  IF partial success:                                                  │ │
│  │    → Return results for successful drivers                            │ │
│  │    → Include errors/warnings for failed drivers                       │ │
│  └───────────────────────────────────────────────────────────────────────┘ │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Step Significance

| Stage | Significance | Impact if Skipped |
|-------|--------------|-------------------|
| **Telemetry Fetch** | Foundation - all phases depend on this data | Complete failure |
| **Phase 2 Delta** | Provides scaled delta trace and official gap | No corner analysis possible |
| **Phase 3 Corner** | Identifies WHERE time is gained/lost | No technique classification |
| **Phase 4 Technique** | Provides session-relative classification | Generic insights only |
| **Phase 5 Insight** | Human-readable output | Results without explanation |
| **Result Assembly** | Combines all data for frontend | Raw data, hard to consume |

---

## 4. Technical Details

### 4.1 Data Type Boundaries

```
API Boundary (Pydantic)        Internal Processing (Dataclass)
═══════════════════════════════════════════════════════════════
PerformanceInsightsRequest  →  PerformanceInsightsConfig
                           →  CornerInput (corner_analysis)

DeltaResult (dataclass)     ←  calculate_scaled_delta()
CornerAnalysisResult        ←  analyze_corners()
TechniqueProfile            ←  profile_drivers()
NaturalLanguageInsight      ←  generate_insights()

Dict[str, Any]              ←  _*_to_dict() conversions

PerformanceInsightsResponse ←  Final assembly
DriverPerformanceResult     ←  Per-driver conversion
```

**Why This Boundary?**
- Pydantic at API boundaries for validation
- Dataclasses internally for performance
- Dicts for JSON serialization flexibility

### 4.2 Async Patterns

```python
# Concurrent telemetry fetch
tasks = [fetch_driver_telemetry(...) for driver in drivers]
results = await asyncio.gather(*tasks)

# Sequential phase execution
# (Each phase depends on previous phase output)
for driver in compare_drivers:
    delta = run_phase2_delta(...)       # Needs telemetry
    corner = run_phase3_corner(delta)   # Needs delta
    # ... accumulate results

profiles = run_phase4_technique(corner_results)  # Needs all corners
for profile in profiles:
    insight = run_phase5_insight(profile)  # Needs profile
```

### 4.3 Memory Considerations

```python
# Telemetry arrays can be large (1000 points × 4 channels × n drivers)
# include_telemetry flag controls whether to include in response

if config.include_telemetry:
    driver_result.delta = delta.delta        # ~8KB per driver
    driver_result.distance = delta.distance  # ~8KB per driver
else:
    driver_result.delta = None
    driver_result.distance = None
```

### 4.4 Timeout Configuration

```python
# Telemetry fetch timeout
TELEMETRY_TIMEOUT_SECONDS = 30.0

# Endpoint-level timeout (httpx client)
async with httpx.AsyncClient(timeout=60.0) as client:
    result = await orchestrate_performance_insights(config, client)
```

---

## 5. Files Created/Modified

### 5.1 New Files

| File | Lines | Purpose |
|------|-------|---------|
| `services/performance_orchestrator.py` | ~450 | Main orchestration logic |
| `tests/test_performance_orchestrator.py` | ~400 | Unit tests |

### 5.2 Modified Files

| File | Changes | Purpose |
|------|---------|---------|
| `models/schemas.py` | +150 lines | Phase 6 request/response schemas |
| `main.py` | +180 lines | New endpoint and imports |

---

## 6. Testing Summary

### 6.1 Test Results

```
============================= test session starts ==============================
tests/test_performance_orchestrator.py ...................... [ 28 tests ]
============================= 28 passed in 0.34s ==============================

Full suite:
============================= 195 passed in 2.06s ==============================
```

### 6.2 Test Coverage by Category

| Category | Count | Description |
|----------|-------|-------------|
| Config | 2 | Dataclass initialization |
| Phase 2 | 2 | Delta calculation |
| Phase 3 | 2 | Corner analysis |
| Phase 4 | 3 | Technique profiling |
| Phase 5 | 3 | Insight generation |
| Conversion | 4 | Dict serialization |
| Dataclass | 4 | Result construction |
| Integration | 2 | Mocked HTTP |
| Edge Cases | 4 | Boundary conditions |
| Performance | 2 | Execution speed |

---

## 7. API Reference

### 7.1 Endpoint

```
POST /ml/performance-insights
```

### 7.2 Request Schema

```json
{
  "session_id": "string (required)",
  "reference_driver": "string (required, 3 letters)",
  "compare_drivers": ["string", "string", ...],
  "corners": [
    {
      "corner_number": "int (>= 1)",
      "apex_distance": "float (meters)",
      "corner_type": "string ('left' | 'right')",
      "name": "string (optional)"
    }
  ],
  "mode": "string ('engineer' | 'driver'), default: 'engineer'",
  "session_part": "string (optional, 'Q1' | 'Q2' | 'Q3')",
  "circuit_name": "string (optional)",
  "include_telemetry": "bool, default: true"
}
```

### 7.3 Response Schema

```json
{
  "session_id": "string",
  "reference_driver": "string",
  "circuit_name": "string | null",
  "mode": "string",
  "results": [
    {
      "driver": "string",
      "official_gap": "float (seconds)",
      "scaling_confidence": "float (0-1)",
      "delta": "[float] | null",
      "distance": "[float] | null",
      "corners_gaining": "int",
      "corners_losing": "int",
      "total_corner_delta": "float",
      "corner_results": [{...}],
      "technique_profile": {...} | null,
      "insight": {...} | null
    }
  ],
  "session_percentiles": {...} | null,
  "total_drivers_requested": "int",
  "total_drivers_processed": "int",
  "total_corners": "int",
  "phase_timing": [
    {
      "phase": "string",
      "duration_ms": "int",
      "success": "bool",
      "error": "string | null"
    }
  ],
  "total_duration_ms": "int",
  "errors": ["string"],
  "warnings": ["string"]
}
```

---

## 8. Conclusion

Phase 6 successfully implements the Performance Insights Orchestrator, providing:

1. **Unified API**: Single endpoint replacing 4 sequential calls
2. **Complete Analysis**: All phases chained with proper data flow
3. **Error Resilience**: Graceful degradation with partial results
4. **Performance Monitoring**: Phase timing for optimization
5. **Comprehensive Tests**: 28 unit tests covering all components

The implementation follows the Backend-for-Frontend pattern, significantly simplifying frontend integration while maintaining the modular architecture of the underlying phase modules.

---

## Appendix A: Code Locations

```
apps/ml_service/
├── services/
│   └── performance_orchestrator.py  # NEW: Orchestration logic
├── models/
│   └── schemas.py                   # MODIFIED: +Phase 6 schemas
├── tests/
│   └── test_performance_orchestrator.py  # NEW: Unit tests
└── main.py                          # MODIFIED: +Endpoint
```

