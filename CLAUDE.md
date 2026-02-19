# Refined AI Architecture: Complete Implementation Documentation

## Document Overview

This document provides comprehensive documentation of the Refined AI Architecture implementation for ApexView, covering all phases from data foundation through race page implementation. It details the context, reasoning, purpose, significance, outputs, and visible impact of each major implementation, with deep technical explanations covering logic, theory, and implementation.

**Document Version:** 3.0  
**Last Updated:** February 2026  
**Status:** Phases 1-7 Complete, Performance Optimization Complete, Race Page Phase 1 Implementation In Progress  
**Test Baseline:** 198+ tests passing  
**Lighthouse Performance:** 94-97 (up from 42)

---

## Table of Contents

1. [Architecture Overview](#1-architecture-overview)
2. [Phase 1: Data Foundation](#2-phase-1-data-foundation)
3. [Phase 2: Delta Analysis with RelativeDistance Alignment and Official Timing Scaling](#3-phase-2-delta-analysis)
4. [Phase 3: Corner Analysis with Physics-Based V2 Algorithm](#4-phase-3-corner-analysis)
5. [Phase 4: Technique Profiling with Session-Relative Percentiles](#5-phase-4-technique-profiling)
6. [Phase 5: Insight Generation with Anti-Hallucination Templates](#6-phase-5-insight-generation)
7. [Phase 6: API Orchestration and Performance Orchestrator](#7-phase-6-api-orchestration)
8. [Phase 7: Frontend Implementation and Component Integration](#8-phase-7-frontend-implementation)
9. [Straight-Line Performance Integration (5th Dimension)](#9-straight-line-performance-integration)
10. [End-to-End System Integration](#10-end-to-end-system-integration)
11. [Test Coverage Summary](#11-test-coverage-summary)
12. [Performance Optimization Journey](#12-performance-optimization-journey)
13. [Track Intelligence — Complete Circuit Database](#13-track-intelligence)
14. [Race Page Implementation Plan](#14-race-page-implementation-plan)
15. [Issues and Problems Encountered](#15-issues-and-problems-encountered)

---

## Recent Updates (Since Version 2.1)

### What Changed Between v2.1 (January 2026) and v3.0 (February 2026)

| Area | Status | Details |
|------|--------|---------|
| **Performance Optimization** | ✅ Complete | Lighthouse 42 → 94-97, JavaScript bundle 1.3 MiB → 472 KiB, 0ms TBT, 0.2s FCP |
| **Track Intelligence** | ✅ Complete | All 24 F1 circuits implemented with verified data, condensed descriptions (~60-80 chars) |
| **Sector Breakdown UI** | ✅ Complete | Per-sector fastest time display fix |
| **Straight-Line Integration** | ✅ Complete | 5th dimension achieving mathematical closure (corners + straights = official gap) |
| **Race Page Planning** | ✅ Complete | Full 6-phase implementation plan with research validation |
| **Fuel Sensitivity Research** | ✅ Complete | Per-circuit fuel correction factors established (0.028-0.036 s/kg) |
| **Race Page Diagnostic** | ✅ Complete | 17-item codebase diagnostic confirming 7 implementation gaps |
| **Race Page Phase 1 Prompt** | ✅ Complete | Detailed implementation prompt for Race Data Foundation |
| **Race Page Phase 1** | 🔄 In Progress | Backend data pipeline for race lap extraction and processing |

---

## 1. Architecture Overview

### 1.1 The Problem Being Solved

The original AI Insights implementation used **cosine similarity** to compare driver telemetry, which produced meaningless results:

| Driver Pair | Cosine Similarity | Actual Gap | Problem |
|-------------|-------------------|------------|---------|
| VER vs NOR | 99.87% | +0.200s | Looks nearly identical |
| VER vs TSU | 99.91% | +2.500s | Looks even more similar |
| VER vs LEC | 99.89% | +0.350s | No useful distinction |

**Why Cosine Similarity Failed:**

Cosine similarity measures the *angle* between vectors, not their magnitude:

```
cos(θ) = (A · B) / (||A|| × ||B||)
```

All F1 drivers brake at the same corners, accelerate on the same straights, and follow similar racing lines. Their telemetry *shapes* are nearly identical — the vectors point in almost the same direction. The 2-5 km/h speed differences that translate to 0.1-2.0 second lap time gaps are invisible to cosine similarity.

**The User Experience Problem:**

Users saw "99.9% similar" and asked: *"If they're so similar, why is one driver 2 seconds faster?"*

The metric answered the wrong question. Users wanted to know:
1. **WHERE** on track was time gained/lost?
2. **WHY** was time gained/lost (braking, apex speed, exit traction)?
3. **WHAT** can be improved?

### 1.2 The Refined AI Architecture Solution

The architecture replaces cosine similarity with a pipeline that answers these questions:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    REFINED AI ARCHITECTURE PIPELINE                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  Phase 1: Data Foundation                                                   │
│  └── Clean telemetry (filtered deleted laps, pit laps, invalid data)       │
│                              │                                              │
│                              ▼                                              │
│  Phase 2: Delta Analysis                                                    │
│  └── WHERE: Distance-indexed delta trace anchored to official timing       │
│                              │                                              │
│                              ▼                                              │
│  Phase 3: Corner Analysis                                                   │
│  └── WHY: Per-corner breakdown with braking/apex/exit attribution          │
│                              │                                              │
│                              ▼                                              │
│  Phase 4: Technique Profiling                                               │
│  └── CLASSIFY: 5-dimension profile with session-relative percentiles       │
│                              │                                              │
│                              ▼                                              │
│  Phase 5: Insight Generation                                                │
│  └── EXPLAIN: Natural language insights (anti-hallucination templates)     │
│                              │                                              │
│                              ▼                                              │
│  Phase 6: API Orchestration                                                 │
│  └── DELIVER: Unified endpoint with graceful degradation                   │
│                              │                                              │
│                              ▼                                              │
│  Phase 7: Frontend Implementation                                           │
│  └── VISUALIZE: React components, charts, interactive displays             │
│                              │                                              │
│                              ▼                                              │
│  Race Page: 6-Phase Implementation                                          │
│  └── EXTEND: Race pace, tyre degradation, pit stops, team performance      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 1.3 Key Design Principles

| Principle | Application |
|-----------|-------------|
| **Official Timing as Ground Truth** | All calculations anchor to official F1 lap times |
| **RelativeDistance Alignment** | Compare same track positions between drivers |
| **Session-Relative Classification** | Use percentiles within session, not absolute thresholds |
| **Anti-Hallucination** | Template-based text generation, no LLM speculation |
| **Graceful Degradation** | System functions when data quality is poor |
| **Lap-Specific Analysis** | No extrapolation to car characteristics or team trends |
| **Server-Side Computation** | All statistical calculations in FastAPI, frontend renders only |
| **Progressive Rendering** | Independent panel loading, deferred below-fold content |

---

## 2. Phase 1: Data Foundation

### 2.1 Context: What Was Implemented

Phase 1 establishes the **data quality gatekeeper** that ensures invalid, corrupted, or misleading data never enters the analysis pipeline.

**Components Implemented:**

| Component | File | Purpose |
|-----------|------|---------|
| `_filter_valid_laps()` | `fastf1_client.py` | Removes deleted/pit/invalid laps |
| `logging_config.py` | `core/logging_config.py` | Structured logging infrastructure |
| Updated callers | `fastf1_client.py` | All data access points use filtering |

### 2.2 Reasoning: Why This Was Needed

**Problem 1: Deleted Laps Corrupting Analysis**

When a driver's lap is deleted for track limits, the telemetry still exists in FastF1's data. Without filtering, a deleted lap might be selected as "fastest," causing comparisons to use invalid reference data.

**Problem 2: Pit Laps Skewing Results**

Pit in/out laps have artificially slow times (pit lane speed limit), incomplete telemetry (missing sections), and non-representative driving (cooling tires, fuel saving).

**Problem 3: Silent Failures**

Without logging, issues were invisible — why did a driver return no data? Which laps were being selected? Where did the pipeline fail?

### 2.3 Technical Implementation

The `_filter_valid_laps()` method applies filtering at all data access points with a fallback to return original data if all laps are filtered:

```python
def _filter_valid_laps(self, laps) -> "pd.DataFrame":
    # 1. Filter deleted laps (track limit violations)
    # 2. Filter pit in laps
    # 3. Filter pit out laps
    # 4. Fallback: return original if all filtered
```

Integration points: `get_telemetry()`, `get_delta_analysis()`, `get_laps()` — all call `_filter_valid_laps()`.

---

## 3. Phase 2: Delta Analysis with RelativeDistance Alignment and Official Timing Scaling

### 3.1 Context: What Was Implemented

Phase 2 implements accurate time delta calculation between drivers using two critical innovations:
1. **RelativeDistance Alignment** — Ensures same track positions are compared
2. **Official Timing Scaling** — Anchors telemetry to official F1 lap times

### 3.2 The Problem: Absolute Distance Misalignment

FastF1's `Distance` column represents cumulative meters traveled in the session, not position on track. Different drivers have different session start positions, different lap lengths (racing line variation), and arbitrary cutoff at overlap boundaries. The original approach compared **different parts of the lap** between drivers.

**The Solution: RelativeDistance (0-1 Normalized)**

```
RelativeDistance = 0.000 → Start/finish line
RelativeDistance = 0.250 → 25% through lap (same corner for all drivers)
RelativeDistance = 1.000 → Back at start/finish
```

By interpolating to RelativeDistance, position 0.25 for VER = position 0.25 for LEC = same track position. Racing line variations are normalized out and full lap coverage is guaranteed.

### 3.3 Official Timing Scaling

Instead of trusting integrated time (which accumulates errors), telemetry time is scaled to exactly match official lap time:

```python
scale = official_time / telemetry_span
scaled_time = lap_relative_time * scale
# Now: scaled_time[-1] == official_time (guaranteed)
```

### 3.4 Results

**Before Phase 2 (Absolute Distance + Speed Integration):**

| Driver Pair | Official Gap | Calculated Gap | Scale Factor | Status |
|-------------|--------------|----------------|--------------|--------|
| VER vs LEC | +0.229s | +1.145s | 5.0x | ❌ Wrong |
| VER vs RUS | +0.137s | -0.685s | -5.0x | ❌ Inverted! |

**After Phase 2 (RelativeDistance + Time Scaling):**

| Driver Pair | Official Gap | Calculated Gap | Scale Factor | Status |
|-------------|--------------|----------------|--------------|--------|
| VER vs LEC | +0.229s | +0.229s | **1.0000x** | ✅ Perfect |
| VER vs RUS | +0.137s | +0.137s | **1.0000x** | ✅ Perfect |

---

## 4. Phase 3: Corner Analysis with Physics-Based V2 Algorithm

### 4.1 Context

Phase 3 transforms Phase 2's "WHERE time was gained/lost" into "WHY time was gained/lost" through corner-by-corner analysis with cause attribution.

### 4.2 Physics-Based Brake Detection

The V1 algorithm used simple threshold detection (`brake > 20%`), which failed due to trail braking from previous corners and gradual brake buildup. The V2 algorithm uses gradient-based detection:

```python
# V2: Is brake pressure INCREASING RAPIDLY?
gradient = (brake_diff / distance_diff) × 10  # %/10m
brake_point = first index where:
  - brake[i+1] >= 20%           # Threshold reached
  - AND gradient[i] >= 5%/10m   # Sharp increase INTO that point
```

### 4.3 Corner Phase Boundaries

Each corner zone is split into three phases — braking (zone_start → apex approach), apex (around apex point), and exit (post-apex → zone_end) — with time delta attributed to each phase to identify the primary cause of time gain/loss.

---

## 5. Phase 4: Technique Profiling with Session-Relative Percentiles

### 5.1 Why Session-Relative Percentiles

Absolute thresholds (e.g., "0.1s is bad") fail because 0.1s means different things at Monaco vs Spa. Session-relative percentiles use the actual session distribution:

```python
all_braking_deltas = [driver.braking for driver in session_drivers]
p30 = np.percentile(all_braking_deltas, 30)
p70 = np.percentile(all_braking_deltas, 70)
# Top 30% → STRONG, Bottom 30% → WEAK, Middle 40% → NEUTRAL
```

### 5.2 The Five Dimensions

| Dimension | Source | Meaning |
|-----------|--------|---------|
| **Braking** | Sum of braking_delta across corners | Time gained/lost under braking |
| **Apex** | Sum of apex_delta across corners | Time gained/lost at corner apexes |
| **Exit** | Sum of exit_delta across corners | Time gained/lost on corner exits |
| **Consistency** | Standard deviation of lap times | Lap-to-lap repeatability |
| **Straight-Line** | Total straight segment delta | Time gained/lost on straights |

---

## 6. Phase 5: Insight Generation with Anti-Hallucination Templates

### 6.1 The Anti-Hallucination Principle

Every insight traces directly to specific calculated data. Template-based generation with data placeholders prevents speculation:

```python
# GOOD: Template with data placeholder
"Braking: WEAK (P{percentile:.0f}) — +{raw_ms:d}ms lost under braking."

# BAD: Generated speculation
"Your braking technique needs improvement because the car seems unstable."
```

---

## 7. Phase 6: API Orchestration and Performance Orchestrator

### 7.1 The Unified Endpoint

Phase 6 creates a single API endpoint that orchestrates all phases through `PerformanceOrchestrator`, chaining Phases 1-5 with graceful degradation. If corner analysis fails for a specific driver/session combination, the system returns available data (delta, technique profile) rather than failing entirely.

---

## 8. Phase 7: Frontend Implementation

### 8.1 Architecture Pattern

Server Component shell → Suspense boundary → Client Component with parallel React Query hooks. SSR header renders immediately (0.2s FCP), panels load progressively with skeleton states, and `isPlaceholderData` + opacity transitions provide smooth GP switching.

### 8.2 Component Hierarchy

```
PerformanceInsightsPanel
├── DeltaPlot                  # Delta-to-reference line chart
├── LapBreakdownPanel          # Corners + Straights = Official
├── CornerBreakdownPanel       # Per-corner table
├── TechniqueProfileDisplay    # 5-dimension bars
└── InsightsPanel              # Natural language text
```

---

## 9. Straight-Line Performance Integration (5th Dimension)

### 9.1 The Problem Solved — Mathematical Closure

Before: Corner analysis total (+0.876s) didn't match official gap (+0.109s). Users asked "Where did -0.767s go?"

After: Corners (+0.876s) + Straights (-0.767s) = Official (+0.109s). Complete reconciliation within 5ms tolerance.

### 9.2 Primary Factor Determination

Straight-line performance is classified by primary factor: aero_efficiency (top speed delta > 2 km/h), high_drag_setup (< -2 km/h), exit_traction (acceleration delta > 0.02), poor_traction (< -0.02), or balanced.

---

## 10. End-to-End System Integration

### 10.1 File Structure

```
apps/
├── api/app/
│   ├── services/telemetry/
│   │   └── fastf1_client.py              # Phase 1 + Race Data Extension
│   ├── services/race/
│   │   └── race_data_service.py          # Race Page Phase 1 (NEW)
│   ├── routes/
│   │   ├── laps.py                       # Qualifying endpoints
│   │   └── race.py                       # Race endpoints (NEW)
│   ├── models/dto.py                     # DTOs including race types
│   └── utils/transforms.py              # Fuel correction, lap classification
├── ml_service/
│   ├── services/
│   │   ├── delta_analysis.py             # Phase 2
│   │   ├── corner_analysis.py            # Phase 3
│   │   ├── technique_profiling.py        # Phase 4
│   │   ├── insight_generation.py         # Phase 5
│   │   └── performance_orchestrator.py   # Phase 6
│   └── tests/                            # 198+ tests
├── web/
│   ├── app/qualifying/                   # Qualifying page (complete)
│   ├── app/race/                         # Race page (in progress)
│   └── components/panels/               # Phase 7
└── packages/models/src/
    ├── types.ts                          # Shared types (qualifying + race)
    └── data/tracks/                      # Track Intelligence (24 circuits)
```

---

## 11. Test Coverage Summary

| Test File | Tests | Coverage |
|-----------|-------|----------|
| `test_delta_analysis.py` | 28 | Delta, scaling, utilities |
| `test_corner_analysis.py` | 38 | Corner detection, phases |
| `test_technique_profiling.py` | 36 | Aggregation, percentiles |
| `test_insight_generation.py` | 61 | Templates, modes |
| `test_straight_line_integration.py` | 31 | Reconciliation |
| `test_similarity.py` | 4 | Legacy compatibility |
| `test_fastf1_client.py` | 11 | Client methods, filtering |
| **Total** | **209+** | |

---

## 12. Performance Optimization Journey

### 12.1 The Transformation

The qualifying page underwent systematic performance optimization that took Lighthouse scores from 42 to consistently 94-97.

| Metric | Before | After | Improvement |
|--------|--------|-------|-------------|
| **Lighthouse Score** | 42 | 94-97 | +52 points |
| **JavaScript Bundle** | 1.3 MiB | 472 KiB | -64% |
| **First Contentful Paint** | ~2.0s | 0.2s | -90% |
| **Largest Contentful Paint** | ~4.0s | 0.5s | -88% |
| **Total Blocking Time** | ~800ms | 0ms | -100% |
| **Speed Index** | ~5.0s | ~2.5s | -50% |

### 12.2 Key Optimisations Applied

**Bundle Analysis and Reduction:**
- Identified plotly.js as the primary bottleneck (~900 KiB)
- Switched to `plotly.js-basic-dist-min` (~300 KiB)
- Eliminated barrel file re-exports that pulled unnecessary code
- Direct hook imports instead of index barrel imports

**Progressive Rendering Architecture:**
- SSR header renders immediately via Server Component (0.2s FCP)
- Suspense boundary wraps Client Component
- Each panel has an independent React Query hook
- `isPlaceholderData` + opacity transition for smooth GP switching
- Skeleton layouts matching exact panel dimensions prevent CLS

**Font Optimisation:**
- Self-hosted fonts via `next/font/google` (Inter)
- Eliminated critical path chain from external Google Fonts CSS
- Font display swap prevents FOIT

**Plotly Isolation:**
- `PlotlyLazy.tsx` uses `next/dynamic` with `ssr: false`
- Plotly loads in separate webpack chunk, not in main bundle
- Charts render only after hydration, with skeleton placeholder

### 12.3 Patterns Established for Race Page

These optimisation patterns are designed into the Race page architecture from the start:
- SSR header for immediate FCP
- Independent panel hooks for progressive loading
- `useVisibilityQuery` hook (Intersection Observer) for deferred below-fold panel fetching
- `staleTime: Infinity` with `gcTime: 30min` for immutable race data
- Prefetch on navigation hover

---

## 13. Track Intelligence — Complete Circuit Database

### 13.1 Coverage

All 24 circuits on the 2025 F1 calendar have comprehensive Track Intelligence data, verified against official F1 and Pirelli sources:

| # | Circuit | Round | Status |
|---|---------|-------|--------|
| 1 | Albert Park (Melbourne) | 1 | ✅ Complete |
| 2 | Shanghai International Circuit | 2 | ✅ Complete |
| 3 | Suzuka Circuit | 3 | ✅ Complete |
| 4 | Bahrain International Circuit | 4 | ✅ Complete |
| 5 | Jeddah Corniche Circuit | 5 | ✅ Complete |
| 6 | Miami International Autodrome | 6 | ✅ Complete |
| 7 | Autodromo Enzo e Dino Ferrari (Imola) | 7 | ✅ Complete |
| 8 | Circuit de Monaco | 8 | ✅ Complete |
| 9 | Circuit de Barcelona-Catalunya | 9 | ✅ Complete |
| 10 | Circuit Gilles Villeneuve (Montreal) | 10 | ✅ Complete |
| 11 | Red Bull Ring (Spielberg) | 11 | ✅ Complete |
| 12 | Silverstone Circuit | 12 | ✅ Complete |
| 13 | Circuit de Spa-Francorchamps | 13 | ✅ Complete |
| 14 | Hungaroring (Budapest) | 14 | ✅ Complete |
| 15 | Circuit Zandvoort | 15 | ✅ Complete |
| 16 | Autodromo Nazionale Monza | 16 | ✅ Complete |
| 17 | Baku City Circuit | 17 | ✅ Complete |
| 18 | Marina Bay Street Circuit (Singapore) | 18 | ✅ Complete |
| 19 | Circuit of the Americas (Austin) | 19 | ✅ Complete |
| 20 | Autódromo Hermanos Rodríguez (Mexico) | 20 | ✅ Complete |
| 21 | Interlagos (São Paulo) | 21 | ✅ Complete |
| 22 | Las Vegas Strip Circuit | 22 | ✅ Complete |
| 23 | Lusail International Circuit (Qatar) | 23 | ✅ Complete |
| 24 | Yas Marina Circuit (Abu Dhabi) | 24 | ✅ Complete |

### 13.2 Data Structure Per Circuit

Each circuit file contains:
- Circuit metadata (name, country, length, lap count, first GP year)
- Sector breakdowns with distances and characteristics
- DRS zones with activation and detection points
- Corner data (number, name, type, speed, gear, apex distance)
- Elevation data (min, max, total ascent/descent)
- Pirelli circuit characteristics (traction, braking, lateral, track evolution, asphalt grip — each 1-5)
- Defining characteristics (condensed to ~60-80 characters for layout compatibility)
- Strategic insights (typical strategy, pit windows, safety car likelihood)
- Weather profile (typical conditions, temperature ranges)
- **Fuel effect per kg** (circuit-specific fuel correction factor, 0.028-0.036 s/kg) — NEW for Race page

### 13.3 Fuel Sensitivity Values

Added as part of Race page planning. Research-validated per-circuit fuel correction factors based on circuit characteristics:

| Tier | Range (s/kg) | Circuit Type | Circuits |
|------|-------------|--------------|----------|
| **Low** | 0.028-0.029 | High-speed, flowing, low traction demand | Silverstone, Monza, Spa, Suzuka |
| **Mid** | 0.031-0.033 | Mixed speed profiles, balanced demands | Most circuits (16 of 24) |
| **High** | 0.034-0.036 | Stop-go, traction-limited, heavy braking | Monaco, Singapore, Hungary, Bahrain, Montreal |

Derivation heuristic: baseline 0.032, +0.002-0.003 if Pirelli braking severity ≥ 4 AND traction ≥ 4, -0.002-0.003 if high average speed with few low-speed corners. Values cross-referenced against Pirelli circuit characteristics already in Track Intelligence.

---

## 14. Race Page Implementation Plan

### 14.1 Overall Purpose and Significance

The Race page is the second major analytical surface of ApexView. The Qualifying page answers "who is fastest over one lap?" The Race page answers a far more complex set of questions: who had the best pace over a full race distance, why did the finishing order look the way it did, what role did strategy play, and where did operational execution help or hurt each team?

Qualifying analysis operates on approximately 20 data points (one best lap per driver). Race analysis operates on 1,000-1,400 data points (50-70 laps × 20 drivers), with additional complexity from pit stops, tyre compound changes, safety car interventions, fuel load variation, traffic effects, and strategic decisions.

The Race page validates the application's architectural patterns at scale. The progressive rendering architecture, the React Query hook-per-panel pattern, the server-side computation philosophy, and the Plotly chunking strategy were all designed to handle data-heavy pages. The Race page is the first true test of those patterns under heavier data loads.

### 14.2 Features Overview

The Race page delivers five core analytical features:

| Feature | Primary Question Answered | Visualisation |
|---------|---------------------------|---------------|
| **Race Pace Distribution** | Who had the fastest car on race day? | Box-and-whisker plots per driver, sorted by median |
| **Tyre Degradation Analysis** | How quickly did each driver/team consume tyre life? | Scatter plot with regression + wear rate bars, per compound |
| **Pit Stop Analysis** | How much time did each team's pit crew gain or lose? | Three bar chart views + template-generated insights |
| **Team Performance Quadrant** | What aerodynamic setup philosophy did each team use? | Divergence bars + four-quadrant scatter plot |
| **Track Segment Map** | Which team was fastest on each track section? | Static SVG circuit map (stretch goal, deferred) |

Two additional metrics are integrated as enrichments within the Race Pace Distribution panel rather than standalone features:
- **Lap Time Consistency** — mean of stint standard deviations, surfaced in tooltip
- **Traffic Analysis** — count of laps within 1.5s of car ahead, surfaced in tooltip

### 14.3 Key Decisions Registry

Decisions made through planning, research, and diagnostics that implementation must respect:

| Decision | Basis | Impact |
|---|---|---|
| Fuel correction: 0.028-0.036 s/kg per circuit, 0.032 default | Perplexity research (industry standard 0.03-0.04, TracingInsights uses 0.03) | Corrected from original 0.06-0.07 assumption |
| Fuel normalization: empty tank | Research (standard convention) | `corrected = raw - (fuel_remaining × factor)` |
| Outlier detection: IQR + 110% median (OR logic) | Research (IQR robust to skew, % cap as safety net) | Two-tier filter catches statistical and obvious anomalies |
| Exclude first 2 stint laps from regression | Research (warm-up period, non-representative) | Prevents artificially steep degradation slopes |
| Minimum 7 usable laps for wear rate | Research (short stints unreliable for gradient) | "Insufficient data" label instead of misleading number |
| Box plot whiskers: 1.5×IQR (Tukey standard) | Research (most recognized convention) | Consistent with Plotly default |
| Sort drivers by median, not mean | Research (median robust to outlier skew) | More defensible pace ranking |
| Median line only in box, mean as text below | Research (dual lines cause clutter at 20 drivers) | Cleaner visual |
| Compound layout: tabs, not vertical stack | Research (keeps viewport focused) | H/M/S tabs with cross-compound summary |
| Regression: server-side, pre-computed | Research (avoids client computation, guarantees consistency) | FastAPI computes, sends line coordinates |
| Quadrant crosshairs: Plotly layout.shapes | Research (no unwanted hover/legend artifacts) | Cleaner than trace-based approach |
| Deferred loading: Intersection Observer | Research (only fetch when panel nears viewport) | `useVisibilityQuery` hook pattern |
| Race data caching: staleTime Infinity | Research (immutable post-event) | `gcTime: 30min` prevents memory growth |
| Track segment map: deferred stretch goal | Planning (disproportionate effort for 24 SVGs) | Core quadrant delivers full value |
| Traffic threshold: 1.5s | Research (reasonable for 2022+ ground-effect cars) | Stored as parameter, not hardcoded |
| Pit stop anomalies: exclude from avg, flag | Research (prevents penalty distortion) | Visible but separated from metrics |
| Multiple API endpoints, not single payload | Qualifying architecture + research | Progressive panel loading, independent fetching |

### 14.4 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    RACE PAGE ARCHITECTURE                               │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌─── Phase 1: Data Foundation ───────────────────────────────────────┐ │
│  │  FastF1 Race Session                                                │ │
│  │    → get_race_laps() [ALL laps, not pick_fastest()]                │ │
│  │    → Lap Classification & Filtering Pipeline                        │ │
│  │    → Stint Detection (FastF1 Stint column)                          │ │
│  │    → Fuel Correction (per-circuit factor from Track Intelligence)   │ │
│  │    → Traffic Derivation (gap-to-car-ahead)                         │ │
│  │    → Pit Stop Extraction (PitInTime/PitOutTime delta)              │ │
│  │  Output: Clean, enriched race dataset consumed by all endpoints     │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
│           │              │              │              │                 │
│           ▼              ▼              ▼              ▼                 │
│  ┌──── Phase 2 ──┐ ┌── Phase 3 ──┐ ┌─ Phase 4 ─┐ ┌─ Phase 5 ──┐     │
│  │  Race Pace    │ │ Tyre Deg    │ │ Pit Stops  │ │ Team Perf  │     │
│  │  Distribution │ │ Analysis    │ │ Analysis   │ │ Quadrant   │     │
│  │  Box Plot     │ │ Scatter +   │ │ 3× Bar +   │ │ 2× Bar +  │     │
│  │  + metadata   │ │ Regression  │ │ Insights   │ │ Scatter   │     │
│  └───────────────┘ └─────────────┘ └────────────┘ └────────────┘     │
│           │              │              │              │                 │
│           └──────────────┴──────────────┴──────────────┘                 │
│                              │                                           │
│                              ▼                                           │
│  ┌──── Phase 6: Performance Optimization & Integration ───────────────┐ │
│  │  Lighthouse Audit → Deferred Loading Validation → Bundle Analysis  │ │
│  │  Integration Tests → Cross-Panel Consistency → Error Boundaries    │ │
│  └─────────────────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────────────────┘
```

---

### 14.5 Phase 1: Race Data Foundation

#### Purpose and Significance

Phase 1 builds the data extraction, processing, and serving pipeline that every Race page feature depends on. It is entirely backend-focused with no frontend deliverables. This phase is the single most critical phase in terms of data integrity — every number shown to users on the Race page originates from what Phase 1 delivers.

The existing codebase can load race sessions from FastF1 (`_get_session_type` maps "Race" → "Race"), but `get_laps()` calls `pick_fastest()`, collapsing to one row per driver. Race analysis needs ALL laps — typically 1,000-1,400 records per race.

#### Theoretical and Logical Background

**Race Data Model vs Qualifying:**
Qualifying produces one optimal lap per driver (clean, controlled). Race data contains 1,000+ laps with multiple categories of non-representative laps: formation laps, in-laps, out-laps, safety car laps, VSC laps, red flag laps, warm-up laps, and anomalous laps. Phase 1 must CLASSIFY laps rather than simply include or exclude them, because different downstream features need different subsets.

**Lap Classification Categories:**

| Classification | In Pace Analysis? | In Tyre Deg Regression? |
|---|---|---|
| `RACING` | Yes | Yes (unless warm-up) |
| `IN_LAP` | No | No |
| `OUT_LAP` | No | No |
| `SAFETY_CAR` | No | No |
| `VSC` | No | No |
| `RED_FLAG` | No | No |
| `FORMATION` | No | No |
| `ANOMALY` | Yes (as outlier dot) | No |

Additionally, a boolean `is_warm_up` flag marks the first 2 laps of each stint. These are `RACING` (they appear in pace analysis) but excluded from tyre degradation regression.

**Fuel Correction Model:**
F1 cars start with ~110 kg of fuel, burning ~1.8-2.2 kg/lap. Each kg adds 0.028-0.036 s/kg (circuit-dependent). The correction normalises to empty tank: `corrected = raw - (fuel_remaining × factor)`. This subtracts the fuel penalty — early-race laps get larger subtraction. The result reveals the tyre degradation trend hidden by fuel mass effect.

**Outlier Detection:**
Two-tier with OR logic: IQR-based (`> Q3 + 1.5 × IQR`) OR percentage cap (`> 1.10 × driver_median`). Either condition alone is sufficient.

**Traffic Derivation:**
`gap_to_car_ahead = gap_to_leader(driver_i) - gap_to_leader(driver_ahead)`, for same-lap cars ordered by position. Laps with gap < 1.5s flagged as in_traffic.

#### Key Technical Considerations

**Files to modify:**
- `apps/api/app/services/telemetry/fastf1_client.py` — add `get_race_laps()` alongside existing `get_laps()` (do NOT modify existing method)
- `apps/api/app/services/mock_data.py` — add matching mock method
- `apps/api/app/models/dto.py` — add RaceLapResponse, StintResponse, PitStopResponse, RacePaceResponse, DriverPaceResponse (all extend CamelCaseModel)
- `apps/api/app/utils/transforms.py` — implement `classify_race_laps()`, `apply_fuel_correction()`, `derive_traffic()`
- `apps/api/app/main.py` — register new race router
- `packages/models/src/types.ts` — add RaceLapData, StintData, PitStopData, RacePaceResponse, DriverPaceData
- `packages/models/src/data/tracks/types.ts` — add `fuelEffectPerKg` to TrackIntelligence interface
- All 24 circuit files — add `fuelEffectPerKg` value

**Files to create:**
- `apps/api/app/services/race/race_data_service.py` — shared processing service with in-memory cache
- `apps/api/app/routes/race.py` — race API endpoints
- `apps/api/tests/test_race_transforms.py` — unit tests for classification, fuel correction, traffic
- `apps/api/tests/test_race_data_service.py` — unit tests for stint extraction, pit stops, pace stats

**Critical constraints:**
- Use existing Parquet cache singleton for raw lap caching
- Use `CamelCaseModel` base class for all new DTOs
- Follow `get_data_service()` factory pattern for routes
- Handle NaN/NaT values defensively (FastF1 DataFrames have frequent NaN)
- FastF1 TrackStatus codes: '1'=green, '4'=SC, '5'=red, '6'=VSC — codes can be concatenated in strings
- Fuel correction SUBTRACTS from raw time (earlier laps get larger subtraction)

**Shared Race Data Service Pattern:**
A shared processing service loads and processes the race session once (with caching), producing the classified, enriched, fuel-corrected dataset. Each endpoint queries this service for the specific slice it needs. This avoids redundant computation when multiple panels request data.

**Validation gate:** Phase 1 is complete when filtered lap counts, box plot statistics, and fuel-corrected trends for a reference race (e.g., Azerbaijan 2025) broadly match what respected independent analysts publish for the same event.

---

### 14.6 Phase 2: Race Pace Distribution

#### Purpose and Significance

Phase 2 delivers the primary analytical view of the Race page — the feature that provides the highest user value with moderate effort. After Phase 2 is complete, the Race page is functional and informative. This phase also establishes the frontend architectural patterns (Server Component → Suspense → Client Component shell, race-specific React Query hooks, `useVisibilityQuery` for deferred loading, prefetch on navigation hover) that all subsequent phases follow.

#### Theoretical and Logical Background

The box-and-whisker plot is the standard visualisation for race pace distribution in professional F1 analysis. Each box encodes five summary statistics (min, Q1, median, Q3, max within whisker bounds) plus outlier dots.

Design decisions validated by research:
- Whisker convention: 1.5×IQR (Tukey standard)
- Primary statistic: Median (robust to outlier skew, better than mean for pace ranking)
- Mean treatment: Numeric text below x-axis (not a second line inside the box — avoids clutter at 20 drivers)
- Sorting: By median, ascending (fastest first)
- Dark-theme styling: Team colour fills at ~60% opacity, high-contrast borders and median lines, x-jittered outlier dots

Supplementary metrics integrated into this panel:
- **Consistency** — mean of stint standard deviations per driver, surfaced in tooltip
- **Traffic** — count of laps within 1.5s of car ahead, surfaced in tooltip

#### Key Technical Considerations

**API endpoint:** `GET /race/pace?session={session_id}` returning pre-computed per-driver statistics (min, Q1, median, mean, Q3, max, outliers, gapToFastest, tyreStrategy, consistencyScore, lapsInTraffic, totalRacingLaps). The frontend receives ready-to-render data, not raw laps.

**Frontend architecture:**
- `app/race/page.tsx` — Server Component with SSR header ("RACE ANALYSIS") for immediate LCP
- `RaceContent.tsx` — Client Component with URL state, parallel hooks, progressive panels
- `RacePacePanel.tsx` — Box plot using PlotlyLazy with pre-computed statistics
- `useRacePaceQuery` — React Query wrapper with `enabled` guard, `keepPreviousData`
- `useVisibilityQuery` — Intersection Observer wrapper (Race Pace overrides with `enabled: true` as above-fold; subsequent panels use deferred loading)
- `queryKeys.race.pace(sessionId)` in queryKeys.ts
- Prefetch trigger on Race navigation hover via `queryClient.prefetchQuery`

**Performance targets:** SSR header ≤0.5s LCP, `staleTime: Infinity` for race queries, `gcTime: 30min`.

**Directly reusable from qualifying:** PlotlyLazy.tsx, Plotly theme config, getTeamColor/getDriverInfo utilities, formatLapTime/formatDelta formatters, RaceWeekendSelector, keepPreviousData pattern, panel card wrapper styling.

---

### 14.7 Phase 3: Tyre Degradation Analysis

#### Purpose and Significance

Phase 3 delivers the deepest analytical feature and the one most directly mirroring pit wall engineering. Tyre degradation is the primary variable that determines race strategy: it dictates pit windows, compound selection, and whether an aggressive or conservative approach is optimal. This phase is the most technically demanding — it combines backend data science (fuel correction, linear regression), interactive UI (Driver/Team toggle, multi-select picker, compound tabs), and dual-chart composition.

#### Theoretical and Logical Background

**Fuel correction isolates tyre degradation:** Without correction, a driver whose tyres are losing 0.035 s/lap might show flat raw lap times because fuel burn gives roughly 0.035 s/lap of offsetting benefit. The correction formula (`corrected = raw - (fuel_remaining × factor)`) reveals the underlying pace trajectory.

**Linear regression is the standard approach** for public/semi-pro tyre degradation analysis. The gradient represents wear rate in seconds per lap. Non-linear "cliff" effects (sudden grip loss) are documented as a limitation rather than modelled with higher-order fits (which are sensitive to outliers in small samples).

**Processing rules:**
- Exclude first 2 laps of each stint from regression (warm-up period)
- Require minimum 7 usable laps before reporting numeric wear rate
- Track evolution (rubber buildup) treated as unmodelled background factor

**Compound-tabbed layout** (Hard, Medium, Soft tabs) recommended over vertically stacking all compounds. Cross-compound summary (degradation rate bars for all compounds) remains visible regardless of selected tab.

#### Key Technical Considerations

**API endpoint:** `GET /race/tyre-degradation?session={session_id}&mode=driver|team&drivers=` returning per-compound, per-driver/team: data points (tyreAge, fuelAdjustedTime, rawTime, lapNumber), pre-computed regression line coordinates, wear rate (s/lap or null), stint metadata.

**Server-side regression:** Computed in FastAPI using numpy/scipy. Frontend receives pre-computed line coordinates — avoids client-side computation and ensures backend calculation matches display exactly.

**Frontend components:**
- `TyreDegradationPanel.tsx` (replaces existing empty placeholder)
- `AnalysisModeToggle.tsx` — Driver/Team radio toggle (instant swap with brief skeleton)
- `DriverChipSelector.tsx` — multi-select chip picker with team colours
- `CompoundTabs.tsx` — Hard/Medium/Soft tab switcher
- `DegradationScatter.tsx` — Plotly scatter with regression trend lines
- `WearRateBar.tsx` — horizontal bar chart of wear rates
- `CompoundSummary.tsx` — compact cross-compound comparison

**Track Intelligence integration:** `fuelEffectPerKg` value flows from Track Intelligence → frontend → API query parameter → fuel correction function. The backend doesn't need to know about Track Intelligence directly.

---

### 14.8 Phase 4: Pit Stop Analysis

#### Purpose and Significance

Phase 4 introduces the operational performance dimension — analysis entirely independent of car pace or tyre management. Pit stops are one of the few areas where team execution is directly measurable in seconds. This phase follows proven patterns (template-based insights from Phase 5 of the Refined AI Architecture) and is positioned after the data-intensive Phases 2-3 because pit stop data is structurally simpler.

#### Theoretical and Logical Background

Pit stop analysis operates on discrete events rather than continuous data. Three chart views provide different granularity: by team (crew performance), by driver (within-team variation), and gap to fastest (competitive impact quantified).

The consistency metric uses IQR rather than standard deviation because pit stop distributions can be skewed by a single problematic stop (stuck wheel nut, unsafe release).

Anomalous stops (penalties, drive-throughs, mechanical issues) are excluded from average calculations but flagged separately. This prevents a single 30-second drive-through penalty from corrupting a team's average.

Template-based insights follow the anti-hallucination approach from Phase 5 of the Refined AI Architecture:
- "Quickest on Average" template: deterministic fill from computed data
- "Most Consistent" template: IQR-based assessment

#### Key Technical Considerations

**API endpoint:** `GET /race/pit-stops?session={session_id}` returning per-stop detail, team averages with IQR, driver averages, gap to fastest, grid average, and pre-computed insight data.

**Frontend:** `PitStopPanel.tsx` with three sub-chart components (by team, by driver, gap to fastest) plus `PitStopInsights.tsx` (two insight cards). Uses `useVisibilityQuery` for deferred loading (below-fold panel).

---

### 14.9 Phase 5: Team Performance Quadrant Chart

#### Purpose and Significance

Phase 5 delivers team-level car characterisation — what setup philosophy each team employed and where their car's strengths and weaknesses lie. This connects directly to the straight-line performance dimension integrated in Phase 4 of the Refined AI Architecture, now applied at team level across a full race.

Reduced risk compared to original plan because the track segment map is deferred as a stretch goal. The three remaining components (two divergence charts + scatter plot) deliver the full analytical story.

#### Theoretical and Logical Background

The quadrant chart encodes the fundamental aerodynamic trade-off in F1: downforce versus drag.

Two axes:
- **Mean Speed (x-axis):** Average speed over a full lap (lap distance / lap time, averaged across race). Higher = faster overall.
- **Top Speed (y-axis):** Maximum speed on straights (from telemetry speed traces, per-lap maxima averaged per team). Higher = lower drag / stronger power unit.

Four quadrants formed by dashed crosshairs at field averages:
1. **High Efficiency** (top-right) — fast everywhere, strong power unit + aero efficiency
2. **High Downforce** (bottom-right) — fast in corners despite straight-line deficit
3. **Low Downforce** (top-left) — fast on straights, slow in corners
4. **Low Efficiency** (bottom-left) — struggling across the board

#### Key Technical Considerations

**API endpoint:** `GET /race/team-performance?session={session_id}` returning per-team: topSpeed, meanSpeed, topSpeedDelta, meanSpeedDelta, plus field averages.

**Important:** This endpoint requires telemetry speed data for all race laps — the most data-intensive operation. The API computes and returns aggregated results only; raw telemetry never sent to frontend. Server-side caching essential.

**Frontend:** `TeamPerformancePanel.tsx` with `TopSpeedDivergence.tsx`, `MeanSpeedDivergence.tsx`, and `TeamQuadrantScatter.tsx`. Crosshair lines use `layout.shapes` (not additional traces). Uses `useVisibilityQuery` for deferred loading.

**Track Segment Map (Stretch Goal):** Requires per-circuit SVG assets for 24 tracks — deferred. Can be added progressively after core Race page delivery.

---

### 14.10 Phase 6: Performance Optimization and Integration Testing

#### Purpose and Significance

Phase 6 applies the performance optimisation methodology proven during the qualifying Lighthouse journey (42 → 94-97) and performs integration testing across all five features.

#### Theoretical and Logical Background

The qualifying performance journey established clear practices that apply directly:

| Qualifying Practice | Race Page Application |
|---|---|
| SSR header for instant FCP | Same — Race page header renders server-side |
| Progressive panel loading | Same — each panel loads independently |
| `isPlaceholderData` + opacity transition | Same — smooth GP switching |
| Plotly in separate webpack chunk | Reused — same chunk serves all charts |
| Self-hosted fonts | Already global |
| Skeleton layouts | New skeletons for Race panel sizes |

New pattern for Race page: **Intersection Observer deferred loading** — below-fold panels only begin fetching when they scroll into/near viewport. The `useVisibilityQuery` hook wraps this. Designed into Phase 2, not retrofitted.

#### Key Technical Considerations

**Performance targets:**
- Performance Score: ≥ 90 (targeting 94+)
- FCP: ≤ 0.3s
- LCP: ≤ 0.6s
- TBT: 0ms
- CLS: ≤ 0.05

**Integration test areas:**
- GP weekend switching: all panels update, no stale data
- Driver filtering: changes in Tyre Degradation don't affect other panels
- Panel error isolation: one panel failing doesn't crash others
- Data consistency: driver list, team names consistent across all panels
- Mobile responsiveness

**Per-panel error boundaries:** Each panel degrades independently. If telemetry is unavailable for Team Performance, that panel shows "data not available" while other four panels work perfectly. Same principle as confidence scoring in the Refined AI Architecture.

---

### 14.11 Codebase Diagnostic Findings (Pre-Implementation)

A comprehensive 17-item diagnostic confirmed the codebase state before Race page implementation:

**What exists and is directly reusable (~60%):**
- FastF1 session loading (Race session type already mapped)
- Lap DTO structure (compound, tyreAge fields exist but only populated from pick_fastest())
- Track Intelligence data (all 24 circuits)
- PlotlyLazy, React Query patterns, SSR+Suspense pattern
- Team colours, formatters, RaceWeekendSelector, Navigation
- Parquet cache singleton
- Docker 3-service stack

**What must be built (~40%):**
- `get_race_laps()` method (FastF1Client returns all laps, not just fastest)
- Race-specific DTOs (RaceLapResponse, StintResponse, PitStopResponse, etc.)
- Race-specific TypeScript types
- Lap classification service
- Fuel correction utility
- Traffic derivation utility
- Pit stop extraction
- Race data service (shared processing with caching)
- Race API endpoints
- All race-specific frontend components and hooks
- `fuelEffectPerKg` field in Track Intelligence (24 circuit files)

**Key gaps confirmed:**
1. `get_laps()` uses `pick_fastest()` — returns 1 lap/driver, race needs ALL laps
2. No race-specific DTOs or TypeScript types exist
3. No race-specific API endpoints exist
4. `calculate_tyre_degradation()` in transforms.py is a TODO stub
5. MockDataService needs matching updates for any new methods
6. Performance orchestrator is qualifying-only

---

## 15. Issues and Problems Encountered

This section documents the key issues and problems encountered during the implementation journey, including how they were diagnosed and resolved.

### 15.1 Issue #1: `.env` Configuration Override (Static Data Regression)

**Severity:** Critical  
**Impact:** All circuits showing identical data, complete feature failure

The Docker container was running with `LIVE_DATA=false` because `apps/api/.env` (outdated) overrode the correct value in root `.env`. `MockDataService` loaded fixture data and ignored the session parameter, returning identical data for all requests.

**Resolution:** Delete `apps/api/.env`, restart containers, verify `LIVE_DATA=true` in container environment.

**Prevention:** Single source of truth for environment config (root `.env` only), delete service-specific `.env` files.

### 15.2 Issue #2: ML Service Integration Gap (RelativeDistance Not Passed)

**Severity:** High  
**Impact:** Delta calculations falling back to least accurate method (Tier 3 speed integration)

The delta calculation was correctly implemented in `delta_analysis.py`, but ML service endpoints were not passing `relative_distance` and `time` fields to the calculation function, causing the three-tier algorithm to always fall back to Tier 3.

**Resolution:** Added `relative_distance` and `time` fields to all 5 locations (3 in `main.py`, 2 in `performance_orchestrator.py`). Note: uses `"relativeDistance"` (camelCase) because API response uses camelCase JSON.

**Results:** Scale factors went from -10.0x to 5.0x → ~1.0. Confidence went from 30% → 90-100%.

### 15.3 Issue #3: Off-by-One Indexing Bug in Brake Detection

**Severity:** Medium  
**Impact:** All corners showing "MEDIUM" confidence regardless of braking behavior

The gradient array represents changes BETWEEN points (`gradient[i]` = change FROM point `i` TO point `i+1`). The code checked `zone_brake[i]` against `gradient[i]`, but when braking starts abruptly at index `i`, the high gradient is at `gradient[i-1]` (leading INTO that point), not `gradient[i]`.

**Resolution:** Changed to check `zone_brake[i + 1]` against `gradient[i]`: "Is brake high at the NEXT point AND is the gradient leading INTO it high enough?"

**Results:** HIGH confidence detection went from 0/28 (0%) → 28/28 (100%).

### 15.4 Issue #4: Floating-Point Precision in Test Assertions

**Severity:** Low  
**Impact:** 4 unit tests failing despite correct implementation

Tests used direct equality (`==`) for floating-point values. Resolved by using `pytest.approx()` with appropriate tolerances: `abs=1e-6` for time values, `abs=1e-4` for percentages, `abs=1e-9` for values expected to be zero.

### 15.5 Issue #5: Telemetry-Timing Mismatch on Certain Circuits

**Severity:** High (Circuit-Specific)  
**Impact:** Catastrophic corner analysis results for affected circuits (Singapore)

Some driver/session combinations have telemetry that contradicts official timing (e.g., telemetry says RUS was 0.002s slower than VER while official timing says 0.182s faster). The -5.0x scale factor from force-correcting wrong data propagated catastrophically through corner analysis.

**Resolution:** Implemented sanity checks that hide corner analysis when data quality is poor (`abs(scale_factor) > 2.0` or any corner delta > 0.5s). Users see either accurate results or a clear message that analysis is unavailable — never misleading data.

**Key Principle Established:** The system should display either **accurate results** or **no results** — never misleading data. Graceful degradation with clear user messaging is preferable to showing impossible values.

### 15.6 Summary of Lessons Learned

| Issue | Root Cause Category | Prevention |
|-------|---------------------|------------|
| `.env` Override | Configuration management | Single source of truth, delete service-specific `.env` files |
| ML Integration Gap | Layer integration | Integration tests that verify data flow end-to-end |
| Off-by-One Bug | Algorithm implementation | Edge case unit tests, visual algorithm validation |
| Floating-Point Tests | Test methodology | Always use `pytest.approx()` for float comparisons |
| Telemetry Mismatch | External data quality | Sanity checks, graceful degradation, confidence thresholds |

---

## Appendix: Verification Commands

```bash
# Run all ML service tests
docker exec f1-ml pytest tests/ -v

# Verify delta accuracy
curl -X POST http://localhost:8501/ml/performance-insights \
  -H "Content-Type: application/json" \
  -d '{"year":2025,"event":"Monaco","session":"Q3","reference_driver":"VER","compare_drivers":["LEC"]}' \
  | jq '.insights[0].delta_analysis | {official_gap, scaling_factor, confidence}'

# Verify reconciliation
curl -X POST http://localhost:8501/ml/performance-insights \
  -H "Content-Type: application/json" \
  -d '{"year":2025,"event":"Monaco","session":"Q3","reference_driver":"VER","compare_drivers":["LEC"]}' \
  | jq '.insights[0].lap_breakdown | {corner_total, straight_total, official_gap, reconciliation_valid}'

# Race page endpoint (Phase 1+)
curl "http://localhost:8000/race/pace?session=2025_17_Race" | python -m json.tool | head -50

# Run race-specific tests
cd apps/api && python -m pytest tests/test_race_transforms.py tests/test_race_data_service.py -v
```

---

*Documentation Version 3.0 — February 2026*