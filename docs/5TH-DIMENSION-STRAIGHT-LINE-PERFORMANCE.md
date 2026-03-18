# 5th Dimension: Straight-Line Performance Enhancement

## Document Overview

This document provides comprehensive documentation of the **5th Dimension: Straight-Line Performance** feature, its integration with the Corner Analysis component, and its role in completing the Telemetry Analysis Pipeline's lap time analysis pipeline.

**Document Version:** 1.1  
**Last Updated:** February 4, 2026  
**Status:** Implementation Complete (UI Fix Applied)  
**Related Phase:** Phase 4 (Technique Profiling) & Phase 5 (Insight Generation)

---

## Table of Contents

1. [Purpose and Significance](#1-purpose-and-significance)
2. [Logical and Theoretical Background](#2-logical-and-theoretical-background)
3. [Full Workflow and Data Flow](#3-full-workflow-and-data-flow)
4. [Technical Implementation](#4-technical-implementation)
5. [Testing and Evaluation Phase](#5-testing-and-evaluation-phase)
6. [Obstacles/Issues Encountered](#6-obstaclesissues-encountered)

---

## 1. Purpose and Significance

### 1.1 The Reconciliation Problem

Before the 5th dimension was implemented, the Corner Analysis (Phase 3) calculated time deltas for each corner zone, but these deltas did not account for **straight sections between corners**. This created a reconciliation gap:

| Component | Value | Issue |
|-----------|-------|-------|
| Corner Total (Σ corner deltas) | +0.876s | Sum of all corner zones |
| Official Gap | +0.109s | From F1 timing |
| **Missing Time** | **-0.767s** | Where did this time go? |

Users would ask: *"If my driver lost 0.876s in corners, why is the official gap only 0.109s?"*

The answer: **The driver gained 0.767s on the straights**, but this wasn't being captured.

### 1.2 The 5th Dimension Solution

The Straight-Line Performance dimension provides **mathematical closure**:

```
corner_total + straight_total = official_gap
  +0.876s    +    -0.767s     =   +0.109s ✓
```

### 1.3 Educational Value

Beyond reconciliation, the 5th dimension adds significant analytical value:

| Insight Type | Example |
|--------------|---------|
| **Setup Trade-offs** | High downforce loses time on straights but gains in corners |
| **Technique Correlation** | Strong exit traction → faster straight-line acceleration |
| **Aero Efficiency** | Low-drag configuration → top speed advantage |
| **Cross-Dimension Analysis** | Exit → Straight chain identifies compound opportunities |

### 1.4 User-Facing Improvements

| Before 5th Dimension | After 5th Dimension |
|---------------------|---------------------|
| 4-dimension profile (braking, apex, exit, consistency) | 5-dimension profile with straight-line |
| Corner analysis only | Corners + Straights = Official (visual equation) |
| No setup insight | Primary factor badges (Aero, Traction, Drag) |
| No cross-dimension analysis | Exit → Straight opportunity insights |

---

## 2. Logical and Theoretical Background

### 2.1 What is Straight-Line Performance?

Straight-line performance captures the time delta accumulated in the **non-corner portions** of the lap. These sections represent:

1. **Main straights** — Long, full-throttle sections where top speed matters
2. **Connecting straights** — Shorter sections between corner complexes
3. **Acceleration zones** — The transition from corner exit to full speed

### 2.2 Factors Affecting Straight-Line Performance

The primary factors that determine straight-line performance are classified as:

| Factor | Description | Performance Implication |
|--------|-------------|------------------------|
| `aero_efficiency` | Low-drag aerodynamic configuration | Higher top speed, gaining time |
| `exit_traction` | Strong traction from corner exits | Better acceleration, gaining time |
| `high_drag` | High-downforce setup with more drag | Lower top speed, losing time |
| `poor_traction` | Traction deficit limiting acceleration | Slower acceleration, losing time |
| `balanced` | No dominant factor | Neutral performance |

### 2.3 The Exit → Straight Chain

Corner exit performance and straight-line performance are **physically connected**:

```
Corner Exit → Acceleration Phase → Top Speed → Braking Phase → Next Corner
     ↑                                                              ↑
     └────────── Exit technique affects straight-line speed ────────┘
```

A driver with excellent exit traction will:
1. Get on throttle earlier
2. Accelerate faster out of corners
3. Carry more speed onto straights
4. Potentially achieve higher top speeds (or equal speeds with less time)

This correlation is captured in the cross-dimension analysis:

| Exit Level | Straight Level | Classification | Meaning |
|------------|----------------|----------------|---------|
| STRONG | STRONG | **OPTIMAL** | Exit technique maximizing straight-line gains |
| STRONG | WEAK | **ANOMALY** | Good exits not converting (suggests high drag setup) |
| WEAK | STRONG | **ANOMALY** | Straight-line gains despite poor exits (suggests low drag) |
| WEAK | WEAK | **CRITICAL** | Compounding losses — priority fix area |

### 2.4 Session-Relative Classification

Like the original 4 dimensions, straight-line performance uses **session-relative percentile classification**:

```
All drivers' straight-line totals: [-0.30, -0.15, 0.00, +0.10, +0.25]

P30 threshold = -0.15s (top 30% boundary)
P70 threshold = +0.10s (bottom 30% boundary)

Classification:
  straight_total <= P30 → STRONG (gaining time, top 30%)
  P30 < straight_total < P70 → NEUTRAL (middle 40%)
  straight_total >= P70 → WEAK (losing time, bottom 30%)
```

**Important:** For straight-line performance, **negative delta = better** (gaining time). This inverts the "lower is better" percentile interpretation — drivers with the most negative totals are STRONG.

---

## 3. Full Workflow and Data Flow

### 3.1 End-to-End Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    5TH DIMENSION DATA FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│ PHASE 2: Delta Analysis                                                     │
│   └── DeltaResult with distance-indexed delta array                         │
│            │                                                                │
│            ▼                                                                │
│ PHASE 3: Corner Analysis                                                    │
│   ├── CornerResult[] (per-corner delta breakdown)                          │
│   ├── StraightSegment[] (per-straight delta breakdown)                     │
│   └── LapBreakdown (corner_total + straight_total = official_gap)          │
│            │                                                                │
│            ▼                                                                │
│ PHASE 4: Technique Profiling                                               │
│   ├── aggregate_straight_line_performance()                                │
│   │     └── Extracts: straight_total, top_gaining, top_losing, factor      │
│   ├── classify_straight_line_dimension()                                   │
│   │     └── Returns: StraightLineDimension (STRONG/NEUTRAL/WEAK)           │
│   └── TechniqueProfile.straight_line (5th dimension attached)              │
│            │                                                                │
│            ▼                                                                │
│ PHASE 5: Insight Generation                                                │
│   ├── generate_straight_line_insight()                                     │
│   │     └── Mode-aware insight text with factor explanation                │
│   ├── generate_lap_breakdown_insight()                                     │
│   │     └── Reconciliation explanation text                                │
│   └── generate_exit_straight_opportunity()                                 │
│         └── Cross-dimension correlation insight                            │
│            │                                                                │
│            ▼                                                                │
│ PHASE 6: Performance Orchestrator                                          │
│   └── Serializes straight_line dimension into API response                 │
│            │                                                                │
│            ▼                                                                │
│ PHASE 7: Frontend Components                                               │
│   ├── TechniqueProfileDisplay (5th dimension bar)                          │
│   ├── LapBreakdownPanel (Corners + Straights = Official)                   │
│   ├── StraightFocusAreas (top gaining/losing straights)                    │
│   └── DriverInsightCard (dimension insights including straight-line)       │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 Data Structures

#### LapBreakdown (from Corner Analysis)

```python
@dataclass
class LapBreakdown:
    corner_total: float          # Sum of all corner deltas (seconds)
    straight_total: float        # Sum of all straight deltas (seconds)
    official_gap: float          # Official timing gap (seconds)
    track_coverage: float        # Corner distance / track length (0-1)
    straight_segments: List[StraightSegment]
    reconciliation_valid: bool   # corners + straights ≈ official_gap
    reconciliation_error: float  # Absolute error (seconds)
```

#### StraightSegment (from Corner Analysis)

```python
@dataclass
class StraightSegment:
    segment_number: int          # Sequential segment number
    name: str                    # e.g., "T1→T2" or "Main Straight"
    start_distance: float        # Start distance (meters)
    end_distance: float          # End distance (meters)
    delta_change: float          # Time delta in segment (seconds)
    length: float                # Segment length (meters)
    primary_factor: str          # 'aero_efficiency', 'traction', etc.
```

#### StraightLineDimension (from Technique Profiling)

```python
@dataclass
class StraightLineDimension:
    level: TechniqueLevel        # STRONG, NEUTRAL, or WEAK
    descriptor: str              # Human-readable description
    percentile: float            # Session percentile (0-100)
    raw_delta: float             # Total straight-line delta (seconds)
    primary_factor: str          # Dominant cause
    segment_count: int           # Number of segments analyzed
    top_gaining_straights: List[str]  # Best 3 straights
    top_losing_straights: List[str]   # Worst 3 straights
    avg_confidence: float        # Average confidence (0-1)
```

### 3.3 Function Call Sequence

```
profile_drivers() [Phase 4 entry point]
    │
    ├── For each driver:
    │   ├── aggregate_by_cause() → Corner dimensions
    │   └── aggregate_straight_line_performance() → Straight-line data
    │
    ├── calculate_session_percentiles() → P30/P70 boundaries
    │   └── Include straight_line_p30, straight_line_p70
    │
    └── For each driver:
        ├── classify_dimension() × 4 → braking, apex, exit, consistency
        ├── classify_straight_line_dimension() → 5th dimension
        └── TechniqueProfile (complete with straight_line)

generate_insights() [Phase 5 entry point]
    │
    ├── generate_dimension_insight_*() × 4 → Corner insights
    ├── generate_straight_line_insight() → 5th dimension insight
    ├── generate_lap_breakdown_insight() → Reconciliation text
    └── generate_exit_straight_opportunity() → Cross-dimension insight
```

---

## 4. Technical Implementation

### 4.1 Key Functions

#### 4.1.1 determine_straight_line_primary_factor()

Determines the dominant factor explaining straight-line performance.

```python
def determine_straight_line_primary_factor(
    straight_segments: List[StraightSegment],
    top_speed_delta: Optional[float] = None,
    avg_exit_delta: Optional[float] = None
) -> str:
    """
    Logic priority:
    1. If top_speed_delta > +2 km/h → 'aero_efficiency'
    2. If top_speed_delta < -2 km/h → 'high_drag'
    3. If avg_exit_delta < -0.02s AND gaining → 'exit_traction'
    4. If avg_exit_delta > +0.02s AND losing → 'poor_traction'
    5. Otherwise → 'balanced' or most common segment factor
    """
```

#### 4.1.2 aggregate_straight_line_performance()

Extracts aggregated straight-line data from LapBreakdown.

```python
def aggregate_straight_line_performance(
    lap_breakdown: Optional[LapBreakdown],
    exit_dimension: Optional[TechniqueDimension] = None
) -> Dict[str, any]:
    """
    Returns:
        - straight_total: Total time delta on straights
        - segment_count: Number of straight segments
        - primary_factor: Dominant performance factor
        - top_gaining_straights: Best 3 straights
        - top_losing_straights: Worst 3 straights
        - avg_confidence: Average confidence
    """
```

#### 4.1.3 classify_straight_line_dimension()

Classifies straight-line performance into STRONG/NEUTRAL/WEAK.

```python
def classify_straight_line_dimension(
    straight_total: float,
    all_straight_totals: List[float],
    primary_factor: str,
    segment_count: int,
    top_gaining: List[str],
    top_losing: List[str],
    avg_confidence: float = 0.8
) -> StraightLineDimension:
    """
    Note: For straight-line, negative delta = faster = better.
    STRONG = low percentile (most negative)
    WEAK = high percentile (most positive)
    """
```

#### 4.1.4 generate_straight_line_insight()

Generates natural language insights for the 5th dimension.

```python
def generate_straight_line_insight(
    straight_line: Optional[StraightLineDimension],
    mode: InsightMode = InsightMode.ENGINEER
) -> Optional[DimensionInsight]:
    """
    ANTI-HALLUCINATION: All text comes from templates with data binding.
    
    Engineer mode: "Straight-Line: STRONG (P18) — -267ms. Low-drag configuration..."
    Driver mode: "Your straight-line speed is a major strength — you're 267ms faster..."
    """
```

### 4.2 Files Modified

| File | Changes |
|------|---------|
| `apps/analysis_service/services/technique_profiling.py` | +`StraightLineDimension` dataclass, +`determine_straight_line_primary_factor()`, +`aggregate_straight_line_performance()`, +`classify_straight_line_dimension()`, updated `profile_drivers()` |
| `apps/analysis_service/services/insight_generation.py` | +`STRAIGHT_LINE_ENGINEER` templates, +`STRAIGHT_LINE_DRIVER` templates, +`PRIMARY_FACTOR_*` templates, +`LAP_BREAKDOWN_*` templates, +`EXIT_STRAIGHT_OPPORTUNITY` templates, +`generate_straight_line_insight()`, +`generate_lap_breakdown_insight()`, +`generate_exit_straight_opportunity()`, updated `generate_insights()` |
| `apps/analysis_service/services/corner_analysis.py` | `LapBreakdown` and `StraightSegment` dataclasses (pre-existing, used by 5th dimension) |
| `apps/analysis_service/services/performance_orchestrator.py` | Updated `_technique_profile_to_dict()` to serialize `straight_line`, updated `_session_percentiles_to_dict()` |
| `apps/analysis_service/models/schemas.py` | +`StraightLineDimensionSchema`, updated `TechniqueProfileSchema`, updated `SessionPercentilesSchema` |
| `packages/models/src/types.ts` | +`StraightLineDimension` interface, +`StraightLinePrimaryFactor` type, updated `TechniqueProfile`, updated `SessionPercentiles`, updated `DimensionType` |
| `apps/web/components/panels/PerformanceInsightsPanel/TechniqueProfileDisplay.tsx` | Added 5th dimension bar with separator and factor badge |
| `apps/web/components/panels/PerformanceInsightsPanel/DimensionBar.tsx` | Added `'straight_line': 'Straight-Line'` label |
| `apps/web/components/panels/PerformanceInsightsPanel/DriverInsightCard.tsx` | +`StraightFocusAreas` component for top gaining/losing straights |
| `apps/web/components/panels/LapBreakdownPanel.tsx` | Updated factor badge colors to match new primary factor names |

### 4.3 Template System (Anti-Hallucination)

All insight text is generated from pre-defined templates with data binding:

**Engineer Mode Templates:**

```python
STRAIGHT_LINE_ENGINEER = {
    TechniqueLevel.STRONG: (
        "Straight-Line: STRONG (P{percentile:.0f}) — {raw_ms:+d}ms. "
        "{factor_text} Gaining on {segment_count} straight segments."
    ),
    TechniqueLevel.WEAK: (
        "Straight-Line: WEAK (P{percentile:.0f}) — {raw_ms:+d}ms. "
        "{factor_text} Losing time on {segment_count} straight segments."
    ),
}
```

**Driver Mode Templates:**

```python
STRAIGHT_LINE_DRIVER = {
    TechniqueLevel.STRONG: (
        "Your straight-line speed is a major strength — you're {raw_ms_abs}ms faster "
        "on the straights. {factor_advice}"
    ),
    TechniqueLevel.WEAK: (
        "You're losing {raw_ms_abs}ms on straights. {factor_advice} "
        "Focus on {improvement_focus} to recover time between corners."
    ),
}
```

---

## 5. Testing and Evaluation Phase

### 5.1 Test File

**File:** `apps/analysis_service/tests/test_straight_line_integration.py`

**Coverage:** 32 tests across 7 test classes

### 5.2 Test Classes

| Test Class | Tests | Purpose |
|------------|-------|---------|
| `TestPrimaryFactorDetermination` | 6 | Tests `determine_straight_line_primary_factor()` logic |
| `TestStraightLineAggregation` | 5 | Tests `aggregate_straight_line_performance()` |
| `TestStraightLineClassification` | 5 | Tests `classify_straight_line_dimension()` for STRONG/NEUTRAL/WEAK |
| `TestStraightLineInsightGeneration` | 4 | Tests `generate_straight_line_insight()` in both modes |
| `TestLapBreakdownInsight` | 4 | Tests `generate_lap_breakdown_insight()` for reconciliation |
| `TestExitStraightOpportunity` | 5 | Tests `generate_exit_straight_opportunity()` cross-dimension |
| `TestEndToEndIntegration` | 3 | Tests complete `profile_drivers()` flow with 5th dimension |

### 5.3 Test Commands

```bash
# Run all straight-line integration tests
docker exec f1-analysis python -m pytest tests/test_straight_line_integration.py -v

# Run with coverage
docker exec f1-analysis python -m pytest tests/test_straight_line_integration.py -v --cov=services

# Run full test suite (301+ tests)
docker exec f1-analysis python -m pytest tests/ -v

# Run specific test class
docker exec f1-analysis python -m pytest tests/test_straight_line_integration.py::TestPrimaryFactorDetermination -v
```

### 5.4 Expected Test Output

```
==================== test session starts ====================
collected 32 items

tests/test_straight_line_integration.py::TestPrimaryFactorDetermination::test_aero_efficiency_with_high_top_speed PASSED
tests/test_straight_line_integration.py::TestPrimaryFactorDetermination::test_high_drag_with_low_top_speed PASSED
tests/test_straight_line_integration.py::TestPrimaryFactorDetermination::test_exit_traction_correlation PASSED
tests/test_straight_line_integration.py::TestPrimaryFactorDetermination::test_poor_traction_correlation PASSED
tests/test_straight_line_integration.py::TestPrimaryFactorDetermination::test_balanced_with_no_clear_factor PASSED
tests/test_straight_line_integration.py::TestPrimaryFactorDetermination::test_empty_segments_returns_balanced PASSED
tests/test_straight_line_integration.py::TestStraightLineAggregation::test_aggregation_with_valid_breakdown PASSED
tests/test_straight_line_integration.py::TestStraightLineAggregation::test_aggregation_identifies_gaining_straights PASSED
tests/test_straight_line_integration.py::TestStraightLineAggregation::test_aggregation_identifies_losing_straights PASSED
tests/test_straight_line_integration.py::TestStraightLineAggregation::test_aggregation_with_none_breakdown PASSED
tests/test_straight_line_integration.py::TestStraightLineAggregation::test_aggregation_uses_exit_correlation PASSED
tests/test_straight_line_integration.py::TestStraightLineClassification::test_classification_strong_percentile PASSED
tests/test_straight_line_integration.py::TestStraightLineClassification::test_classification_weak_percentile PASSED
tests/test_straight_line_integration.py::TestStraightLineClassification::test_classification_neutral_percentile PASSED
tests/test_straight_line_integration.py::TestStraightLineClassification::test_classification_with_insufficient_data PASSED
tests/test_straight_line_integration.py::TestStraightLineClassification::test_classification_preserves_metadata PASSED
tests/test_straight_line_integration.py::TestStraightLineInsightGeneration::test_engineer_mode_strong_includes_percentile PASSED
tests/test_straight_line_integration.py::TestStraightLineInsightGeneration::test_driver_mode_strong_is_actionable PASSED
tests/test_straight_line_integration.py::TestStraightLineInsightGeneration::test_weak_insight_includes_improvement_focus PASSED
tests/test_straight_line_integration.py::TestStraightLineInsightGeneration::test_none_input_returns_none PASSED
tests/test_straight_line_integration.py::TestLapBreakdownInsight::test_reconciled_breakdown_engineer PASSED
tests/test_straight_line_integration.py::TestLapBreakdownInsight::test_reconciled_breakdown_driver PASSED
tests/test_straight_line_integration.py::TestLapBreakdownInsight::test_not_reconciled_breakdown PASSED
tests/test_straight_line_integration.py::TestLapBreakdownInsight::test_none_breakdown_returns_none PASSED
tests/test_straight_line_integration.py::TestExitStraightOpportunity::test_strong_strong_is_optimal PASSED
tests/test_straight_line_integration.py::TestExitStraightOpportunity::test_weak_weak_is_critical PASSED
tests/test_straight_line_integration.py::TestExitStraightOpportunity::test_strong_exit_weak_straight_anomaly PASSED
tests/test_straight_line_integration.py::TestExitStraightOpportunity::test_driver_mode_is_actionable PASSED
tests/test_straight_line_integration.py::TestExitStraightOpportunity::test_none_inputs_return_none PASSED
tests/test_straight_line_integration.py::TestEndToEndIntegration::test_profile_drivers_includes_straight_line PASSED
tests/test_straight_line_integration.py::TestEndToEndIntegration::test_profile_without_lap_breakdown PASSED
tests/test_straight_line_integration.py::TestEndToEndIntegration::test_multiple_drivers_percentile_distribution PASSED

==================== 32 passed in 1.52s ====================
```

### 5.5 Verification Methods

| Verification | Method |
|--------------|--------|
| **Unit Tests** | 32 pytest tests covering all functions |
| **Type Safety** | TypeScript build (`pnpm build`) verifies frontend types |
| **API Contract** | Pydantic schemas validate response structure |
| **Full Suite** | 301+ tests across all modules ensure no regressions |
| **Visual Verification** | Frontend displays 5th dimension bar, LapBreakdown panel |

---

## 6. Obstacles/Issues Encountered

### 6.1 Issue #1: Dataclass Field Mismatches in Tests

**Severity:** Medium  
**Impact:** Test failures due to missing required fields

**Problem:**  
Initial tests created `StraightSegment` and `LapBreakdown` objects without all required fields:

```python
# FAILING - Missing required fields
StraightSegment(
    name="T1→T2",
    delta_change=-0.150,
    # Missing: segment_number, start_distance, end_distance, length, primary_factor
)
```

**Resolution:**  
Updated all test fixtures to include complete field sets:

```python
# FIXED - All required fields present
StraightSegment(
    segment_number=1,
    name="T1→T2",
    start_distance=0,
    end_distance=500,
    delta_change=-0.150,
    length=500,
    primary_factor="exit_traction",
)
```

### 6.2 Issue #2: CornerResult Field Confusion

**Severity:** Medium  
**Impact:** End-to-end tests failing

**Problem:**  
Tests attempted to use non-existent fields `braking_delta`, `apex_delta`, `exit_delta` on `CornerResult`:

```python
# FAILING - These fields don't exist
CornerResult(
    braking_delta=0.02,  # ❌ Not a real field
    apex_delta=0.01,     # ❌ Not a real field
)
```

**Resolution:**  
Used the correct fields (`delta_change`, `cause`, `brake_distance`) from the actual dataclass definition:

```python
# FIXED - Using actual fields
CornerResult(
    corner_number=1,
    name="Turn 1",
    apex_distance=100.0,
    brake_distance=80.0,
    zone_start=0.0,
    zone_end=200.0,
    delta_change=0.050,
    cause="braking",
    confidence="high",
)
```

### 6.3 Issue #3: Balanced Factor Test Failure

**Severity:** Low  
**Impact:** One test returning `'exit_traction'` instead of `'balanced'`

**Problem:**  
The `test_balanced_with_no_clear_factor` test failed because the sample segments had net gains, triggering exit_traction detection:

```python
# Original segments had net gain, so exit_traction was detected
segments = [
    StraightSegment(..., delta_change=-0.150),  # Gaining
    StraightSegment(..., delta_change=0.050),   # Losing
    # Net = -0.100 (gaining) → triggers exit_traction correlation
]
```

**Resolution:**  
Created truly balanced segments with near-zero net delta:

```python
# Fixed - Truly balanced segments
segments = [
    StraightSegment(..., delta_change=0.001, primary_factor="balanced"),
    StraightSegment(..., delta_change=-0.001, primary_factor="balanced"),
    # Net ≈ 0 → correctly returns 'balanced'
]
```

### 6.4 Issue #4: Docker Environment Setup

**Severity:** Low  
**Impact:** Initial test runs failed to find pytest

**Problem:**  
The Docker container did not have `pytest` installed, and the module import paths were incorrect:

```bash
# Failed - pytest not found
docker exec f1-analysis pytest tests/

# Failed - module not found
docker exec f1-analysis python tests/test_straight_line_integration.py
```

**Resolution:**  
Used proper Docker environment setup:

```bash
# Install pytest if missing
docker exec f1-analysis pip install pytest

# Run with correct PYTHONPATH
docker exec f1-analysis python -m pytest tests/test_straight_line_integration.py -v
```

### 6.5 Issue #5: Lap Breakdown Panel Not Displaying in UI

**Severity:** High  
**Impact:** Complete feature invisibility — Lap Breakdown panel not rendering despite backend implementation

**Problem:**  
After implementing the 5th Dimension feature (backend Analysis service + frontend components), the **LapBreakdownPanel** was not appearing in the Performance Insights card. The UI showed technique profiles and corner analysis, but the "Corners + Straights = Official" breakdown was completely missing.

**Symptoms Observed:**
- No visible Lap Breakdown panel in DriverInsightCard
- No straight-line segment table visible
- API response had `lap_breakdown: null` for all drivers
- Backend logs showed `calculate_lap_breakdown()` was never being called

**Investigation Steps:**

1. **Backend Data Structure Check** — Verified `StraightSegment`, `LapBreakdown`, and `calculate_lap_breakdown()` existed in `corner_analysis.py` ✅

2. **Schema Check** — Verified `LapBreakdownSchema` and `StraightSegmentSchema` existed in `schemas.py` ✅

3. **Orchestrator Check** — Verified `run_phase3_corner()` accepted `track_length` parameter and passed it to `analyze_corners_v2()` ✅

4. **API Endpoint Check** — **FOUND ROOT CAUSE** — `get_performance_insights()` in `main.py` was NOT passing `track_length` to `PerformanceInsightsConfig`:

   ```python
   # BROKEN - track_length missing from config
   config = PerformanceInsightsConfig(
       session_id=request.session_id,
       reference_driver=request.reference_driver,
       # ... other fields ...
       include_telemetry=request.include_telemetry,
       # track_length was NOT being passed!
   )
   ```

5. **Request Schema Check** — **SECOND ROOT CAUSE** — `PerformanceInsightsRequest` in `schemas.py` didn't include `track_length` field.

6. **Frontend Check** — **THIRD ROOT CAUSE** — The entire frontend stack (`api.ts`, `usePerformanceInsightsQuery.ts`, `PerformanceInsightsPanel.tsx`, `QualifyingContent.tsx`) was not passing `track_length` from track data to the API.

7. **Response Serialization Check** — **FOURTH ROOT CAUSE** — `get_performance_insights()` wasn't including `lap_breakdown` when constructing `DriverPerformanceResult`.

**Root Cause Summary:**

The `track_length` parameter was **required** for `calculate_lap_breakdown()` to execute (see `analyze_corners_v2()` line 1634), but the parameter was missing from the entire request/response flow:

```
Track Data (length) ──✗──> Frontend API call ──✗──> Request Schema ──✗──> Orchestrator Config
                                                                              │
                                                   track_length = None ◀──────┘
                                                              │
                                   analyze_corners_v2() skips lap breakdown calculation
                                                              │
                                             lap_breakdown = None in response
```

**Resolution:**

Four coordinated changes across the stack:

| Layer | File | Change |
|-------|------|--------|
| **Backend Schema** | `apps/analysis_service/models/schemas.py` | Added `track_length: Optional[float]` to `PerformanceInsightsRequest` |
| **Backend API** | `apps/analysis_service/main.py` | Added `track_length=request.track_length` to config; Added `lap_breakdown` serialization in response |
| **Frontend Types** | `packages/models/src/types.ts` | Added `track_length?: number` to `PerformanceInsightsRequest` |
| **Frontend API** | `apps/web/lib/api.ts` | Added `trackLength` parameter to `fetchPerformanceInsights()` |
| **Frontend Hook** | `apps/web/lib/hooks/usePerformanceInsightsQuery.ts` | Added `trackLength` option and pass to API function |
| **Frontend Component** | `apps/web/components/panels/PerformanceInsightsPanel/PerformanceInsightsPanel.tsx` | Added `trackLength` prop and pass to hook |
| **Frontend Page** | `apps/web/app/qualifying/QualifyingContent.tsx` | Added `trackLength={trackData?.length}` to panel props |

**Verification:**

```powershell
# API test with track_length parameter
$body = @{
    session_id = "2025_24_Qualifying"
    reference_driver = "VER"
    compare_drivers = @("NOR")
    corners = @(@{corner_number = 1; name = "T1"; apex_distance = 180; corner_type = "right"})
    mode = "engineer"
    track_length = 5281
} | ConvertTo-Json -Depth 5

$response = Invoke-RestMethod -Uri "http://localhost:8501/analysis/performance-insights" `
    -Method POST -Body $body -ContentType "application/json"

$response.results[0].lap_breakdown
# Output:
# corner_total         : 0.014
# straight_total       : 0.187
# official_gap         : 0.201
# reconciliation_valid : True
# insight_text         : "Corner zones cover 2.8% of the circuit..."
```

**Data Flow After Fix:**

```
Track Data (trackData.length = 5281)
  │
  ▼
QualifyingContent.tsx
  │ trackLength={trackData?.length}
  ▼
PerformanceInsightsPanel.tsx
  │ trackLength prop
  ▼
usePerformanceInsightsQuery.ts
  │ trackLength option
  ▼
fetchPerformanceInsights()
  │ track_length in request body
  ▼
ML API /analysis/performance-insights
  │ request.track_length
  ▼
PerformanceInsightsConfig
  │ config.track_length = 5281
  ▼
run_phase3_corner(track_length=5281)
  │
  ▼
analyze_corners_v2(track_length=5281)
  │
  ▼
calculate_lap_breakdown() ← NOW EXECUTES!
  │
  ▼
LapBreakdown in CornerAnalysisResult
  │
  ▼
_lap_breakdown_to_dict() serialization
  │
  ▼
DriverPerformanceResult.lap_breakdown in API response
  │
  ▼
LapBreakdownPanel renders correctly! ✅
```

### 6.6 Lessons Learned

| Issue | Root Cause | Prevention |
|-------|------------|------------|
| Missing dataclass fields | Test fixtures not matching actual definitions | Always reference actual dataclass definitions when creating test data |
| Non-existent fields | Assumed field names instead of checking | Read source code before writing tests |
| Logic test failures | Test data triggered unintended code paths | Design test data carefully for specific scenarios |
| Docker environment | Missing dependencies | Include test dependencies in requirements.txt |
| **Lap Breakdown not displaying** | **Required parameter not passed through full stack** | **Trace data flow end-to-end when adding new required parameters; ensure all layers (schema, API, hook, component, page) are updated** |

---

## Appendix A: TypeScript Type Definitions

```typescript
// packages/models/src/types.ts

/** 5th Dimension: Straight-line performance analysis */
export interface StraightLineDimension {
  level: DimensionLevel
  descriptor: string
  percentile: number
  raw_delta: number  // Total straight-line delta (negative = faster)
  primary_factor: StraightLinePrimaryFactor
  segment_count: number
  top_gaining_straights: string[]
  top_losing_straights: string[]
  avg_confidence: number
}

/** Primary factors explaining straight-line performance */
export type StraightLinePrimaryFactor = 
  | 'aero_efficiency'
  | 'exit_traction'
  | 'high_drag'
  | 'poor_traction'
  | 'balanced'

/** Updated TechniqueProfile with 5th dimension */
export interface TechniqueProfile {
  driver: string
  reference_driver: string
  braking: TechniqueDimension
  apex: TechniqueDimension
  exit: TechniqueDimension
  consistency: TechniqueDimension
  straight_line?: StraightLineDimension  // 5th dimension (optional for backward compat)
  top_gaining_corners: string[]
  top_losing_corners: string[]
  style_summary: string
  overall_confidence: number
  total_corners_analyzed: number
}
```

---

## Appendix B: Frontend Component Structure

```
DriverInsightCard
├── Header (driver vs reference, official gap badge)
├── Summary text (from insight.summary)
├── LapBreakdownPanel (5th Dimension)
│   ├── Visual equation: [Corners] + [Straights] = [Official]
│   ├── Track coverage bar (corners vs straights)
│   ├── Reconciliation indicator (✓ or ⚠)
│   └── Collapsible straight segments table
├── TechniqueProfileDisplay (5 Dimensions)
│   ├── DimensionBar (Braking)
│   ├── DimensionBar (Apex)
│   ├── DimensionBar (Exit)
│   ├── DimensionBar (Consistency)
│   ├── Separator
│   ├── DimensionBar (Straight-Line)
│   └── Primary Factor Badge
├── FocusAreas (Corner gaining/losing)
└── StraightFocusAreas (Straight gaining/losing)
```

---

*Documentation Version 1.1 — February 4, 2026*

---

## Changelog

| Version | Date | Changes |
|---------|------|--------|
| 1.0 | February 2026 | Initial implementation documentation |
| 1.1 | February 4, 2026 | Added Issue #5: Lap Breakdown UI visibility fix (track_length parameter flow) |
