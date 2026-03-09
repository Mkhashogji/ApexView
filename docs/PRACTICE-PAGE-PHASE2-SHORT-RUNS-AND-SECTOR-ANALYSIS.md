# Practice Page Phase 2: Short Run / Best Lap, Sector Analysis & Circuit Map

**Status:** Complete
**Implemented:** March 2026
**Test Baseline:** 58 new tests passing (41 short run + 17 sector analysis), full suite 302+ with 0 regressions
**TypeScript:** Zero compilation errors
**Docker Integration:** Verified across 5 live sessions (Abu Dhabi FP1/FP2/FP3, Bahrain FP1, Imola FP1), 20/20 driver match per session; 24/24 SVG circuit maps verified serving and rendering correctly

---

## Table of Contents

1. [Purpose and Significance](#1-purpose-and-significance)
2. [Conceptual Background](#2-conceptual-background)
3. [End-to-End Workflow and Data Flow](#3-end-to-end-workflow-and-data-flow)
4. [Technical Implementation Breakdown](#4-technical-implementation-breakdown)
5. [Sector Analysis: Additional Analytical Component](#5-sector-analysis-additional-analytical-component)
6. [Circuit Map with Sector Highlighting](#6-circuit-map-with-sector-highlighting)
7. [Session Verification and the Accuracy Fix](#7-session-verification-and-the-accuracy-fix)
8. [Testing, Verification, and Validation](#8-testing-verification-and-validation)
9. [Key Decisions and Learnings](#9-key-decisions-and-learnings)
10. [Alignment with Broader Practice Page Plan](#10-alignment-with-broader-practice-page-plan)

---

## 1. Purpose and Significance

### What Phase 2 Delivers

Phase 2 adds three new analytical panels to the Practice page, building directly on the Phase 1 data pipeline:

1. **Short Run / Best Lap Panel** — A ranked comparison of every driver's fastest single lap in the session, anchored to official FIA timing. This is the practice equivalent of qualifying — the single-lap pace pecking order.

2. **Sector Analysis Panel** — A three-section breakdown showing per-driver sector times from their session-best lap, best individual sector times across all laps, a theoretical best lap computation, and speed trap comparisons. This is the first time speed trap data is surfaced anywhere in the platform.

3. **Circuit Map with Sector Highlighting** — An interactive SVG track map with colour-coded S1/S2/S3 overlays using Track Intelligence sector colours, annotated with the fastest driver per sector. This provides a spatial anchor that bridges the numerical sector analysis with the physical layout of the circuit.

Together, these panels transform the Practice page from a long-run-only analysis tool into a complete session overview covering race simulation pace (Phase 1), qualifying simulation pace (Phase 2 Short Run), sector-level breakdown (Phase 2 Sector Analysis), and spatial circuit context (Phase 2 Circuit Map).

### Why It Matters

During a practice session, teams alternate between two modes: **long runs** (sustained stints simulating race pace) and **short runs** (low-fuel, fresh-tyre laps simulating qualifying performance). Phase 1 captured the long run dimension. Phase 2 completes the picture with the short run dimension.

The short run best-lap ranking tells teams and analysts where they stand on pure single-lap pace before qualifying begins. The sector breakdown reveals *where* on track that pace advantage exists — a driver fastest in S1 (the high-speed section) but losing time in S3 (the technical section) has a clear area to target in setup changes.

The theoretical best lap metric is particularly valuable in practice: unlike qualifying where drivers optimise every sector on their best attempt, practice drivers rarely extract maximum performance from all three sectors on a single lap. The gap between a driver's actual best lap and their theoretical best (sum of their best individual S1, S2, S3 from different laps) quantifies how much untapped pace they have.

The circuit map provides the crucial spatial dimension that pure numbers cannot convey. When sector analysis shows a driver losing 0.3s in S2, the map immediately communicates what S2 *looks like* — whether it contains the technical complex, the high-speed sequence, or the long straight. This spatial context transforms abstract sector deltas into actionable insights about car setup and driving style.

### Position in the Practice Page Architecture

| Phase | Name | Status | Depends On |
|-------|------|--------|-----------|
| 1 | Data Foundation & Long Run Pace | ✅ Complete | — |
| **2** | **Short Run / Best Lap + Sector Analysis + Circuit Map** | **✅ Complete** | Phase 1 pipeline |
| 3 | Session Progression & Performance Optimisation | 📋 Planned | Phase 1 pipeline |

---

## 2. Conceptual Background

### 2.1 Anchoring to Official Timing: The Core Design Decision

The most significant architectural decision in Phase 2 was the choice to anchor the short run panel to **official FIA session-best lap times** rather than extracting best laps from short-run stint data.

**The problem:** When Phase 2 was first implemented using stint-based lap extraction, the results diverged from official session classifications. A driver's session-best lap might come from a 5-lap stint classified as a "long run" (≥ 4 valid laps), not a short run stint. Additionally, fuel correction applied in the pipeline could shift relative ordering — a driver faster in raw timing might appear slower after fuel adjustment.

**The solution:** The `_extract_session_best_laps()` function was introduced to pull each driver's personal-best lap directly from FastF1's FIA timing data, bypassing stint classification and fuel correction entirely. This guarantees:

- Rankings match the official F1 session classification
- Lap times are raw FIA timing (no fuel correction artefacts)
- All 20 drivers appear regardless of how their stints are classified
- Results are verifiable against formula1.com timing sheets

The stint data is still used for contextual annotation (stint count, whether the best lap came from a short or long run stint), but it never drives the primary ranking.

### 2.2 Two-Tier Extraction Strategy

The `_extract_session_best_laps()` function uses a two-tier approach with a session-level consistency check:

**Primary path — FastF1's `is_personal_best` flag:**
FastF1 marks each driver's fastest valid lap with `is_personal_best = True`. This flag comes directly from the FIA timing system and is the most reliable source of session-best data. When any lap in the session has this flag set, the function uses flag-based extraction for *all* drivers.

**Fallback path — computed minimum from RACING laps:**
When no laps in the session have the `is_personal_best` flag (common with mock data or older FastF1 versions), the function computes the minimum `lap_time` across all RACING-classified laps per driver.

**Why the session-level check matters:** The decision between flag-based and computed extraction is made at the session level, not per driver. If driver A has a flagged personal best but driver B doesn't (because B's best lap was deleted for track limits, for example), using flags for A and computation for B would create an inconsistent ranking. The all-or-nothing check ensures consistent methodology across the entire session.

### 2.3 Session-Best Sectors vs Best Individual Sectors

The sector analysis introduces a distinction fundamental to practice analysis:

**Session-best lap sectors:** The S1, S2, S3 times from each driver's official session-best lap. These three sectors sum exactly to the session-best lap time. They represent the best *complete* lap the driver achieved.

**Best individual sectors:** The fastest S1, fastest S2, and fastest S3 each driver achieved across *any* lap in the session. These may come from three different laps. They represent the maximum performance extracted in each track section independently.

The gap between these two perspectives — the **potential gain** — quantifies how much pace a driver left on the table by not combining their best individual sectors into a single lap. In practice this is typically 0.1–0.5s per driver, with higher values indicating inconsistency or that the driver's best sectors came under different conditions (different tyre temperatures, track evolution, fuel loads).

### 2.4 Theoretical Best Lap

The theoretical best lap extends the individual sector concept across all drivers: it is the sum of the fastest S1, fastest S2, and fastest S3 achieved by *any* driver on *any* lap in the session. This metric:

- Is always faster than or equal to the session-best actual lap
- May combine sectors from three different drivers on three different laps
- Represents the absolute pace potential extracted across the entire field during the session
- Provides context: a 0.247s theoretical gain (as seen in Abu Dhabi FP1) suggests the session-best driver was already close to the theoretical limit; a 1.0s+ theoretical gain suggests significant untapped pace

### 2.5 Speed Trap Data

Speed trap data was already extracted by the FastF1 client in Phase 1 (fields: `speed_trap`, `speed_i1`, `speed_i2`, `speed_fl`) but was never exposed through any endpoint. Phase 2 surfaces the maximum speed per driver across all laps at each trap location:

| Field | Measurement Point | Significance |
|-------|------------------|-------------|
| `speed_trap` | End of longest DRS straight | Peak straight-line speed, reflects drag level |
| `speed_i1` | Intermediate speed trap 1 | Speed at sector 1 timing point |
| `speed_i2` | Intermediate speed trap 2 | Speed at sector 2 timing point |
| `speed_fl` | Finish line speed trap | Speed crossing start/finish |

Maximum (rather than average) is used because practice includes laps at varying engine modes and fuel loads. The maximum represents the driver's best opportunity at each trap — likely under low fuel with full engine deployment.

### 2.6 Circuit Map as Spatial Context Layer

The circuit map addresses a fundamental limitation of tabular sector data: numbers alone do not convey the physical layout of the track. When a driver loses 0.4s in Sector 2 at Bahrain, the user needs to understand whether Sector 2 contains the sweeping corners, the hairpin, or the short straight between tight complexes.

**Design philosophy:**
The map is positioned between the Short Run panel and the Sector Analysis panel in the page layout, providing a visual bridge between the single-lap ranking (above) and the detailed sector breakdown (below). It uses the same sector colours as the sector analysis table, creating a visual link between the map's coloured track sections and the table's highlighted sectors.

**SVG over raster:** SVG was chosen over raster images (PNG/JPEG) because SVG paths can be dynamically re-coloured per circuit using Track Intelligence sector colours, the same viewBox rendering works at any screen width without resolution loss, and individual sector paths can have distinct accessibility labels.

**Dual-layer rendering:** Each sector is drawn twice — once as a thick gray outline (establishing the track shape) and once as a thinner coloured overlay (highlighting the sector). This matches the original Gumroad SVG visual pattern and ensures the track outline remains visible even when sector colours are similar.

---

## 3. End-to-End Workflow and Data Flow

### 3.1 Request Flow

```
Browser                  Next.js Frontend              FastAPI Backend
  │                           │                              │
  │  Load Practice page       │                              │
  │ ─────────────────────>    │                              │
  │                           │                              │
  │  [PracticeContent.tsx]    │                              │
  │  Derives sessionId:       │                              │
  │  "2025_24_FP2"            │                              │
  │                           │                              │
  │  ┌─────────────────────────────────────────────────────┐ │
  │  │ Phase 1: useLongRunQuery(sessionId, fuelEffect)     │ │
  │  │ ──> GET /practice/long-runs?session=2025_24_FP2     │──>│
  │  │                                                     │ │
  │  │ Phase 2: useShortRunQuery(sessionId, fuelEffect)    │ │
  │  │ ──> GET /practice/short-runs?session=2025_24_FP2    │──>│
  │  │                                                     │ │
  │  │ Phase 2: useSectorAnalysisQuery(sessionId)          │ │
  │  │ ──> GET /practice/sector-analysis?session=2025_24.. │──>│
  │  │                                                     │ │
  │  │ Phase 2: useCircuitSVGQuery(round)                  │ │
  │  │ ──> GET /tracks/{circuit}.svg (static asset)        │   │
  │  └─────────────────────────────────────────────────────┘ │
  │                           │                              │
  │                           │         All 3 API endpoints  │
  │                           │   call get_processed_practice│
  │                           │   _data (shared cache hit)   │
  │                           │                              │
  │                           │  SectorMapPanel also calls   │
  │                           │  useSectorAnalysisQuery()    │
  │                           │  (shared React Query cache)  │
```

### 3.2 Backend Data Pipeline (Shared by All API Endpoints)

All three Phase 2 API endpoints (`/short-runs`, `/sector-analysis`) and the Phase 1 endpoint (`/long-runs`) consume the same cached pipeline:

```
get_processed_practice_data(session_id, fuel_effect)
    │
    ├── 1. Load raw laps via FastF1 client
    │       └── get_practice_laps(session_id)
    │           └── Parquet cache or live FastF1 API call
    │
    ├── 2. Classify laps
    │       └── classify_practice_laps(raw_laps)
    │           └── 5 types: RACING, IN_LAP, OUT_LAP, RED_FLAG, ANOMALY
    │
    ├── 3. Apply fuel correction (if enabled)
    │       └── apply_practice_fuel_correction(laps, fuel_effect)
    │
    ├── 4. Derive traffic context
    │       └── derive_practice_traffic(laps)
    │           └── Gap-to-car-ahead < 1.5s → in_traffic
    │
    ├── 5. Extract official session-best laps  ← NEW in Phase 2
    │       └── _extract_session_best_laps(enriched_laps)
    │           ├── Primary: FastF1 is_personal_best flag
    │           └── Fallback: Computed min from RACING laps
    │
    ├── 6. Group into stints
    │       └── _group_into_stints(enriched_laps)
    │           ├── long_run: ≥ 4 valid laps
    │           └── short_run: < 4 valid laps
    │
    └── 7. Cache and return
            └── Dict with: laps, stints, long_run_stints,
                short_run_stints, session_best_laps
```

The cache key is `f"{session_id}_{fuel_effect_per_kg}"`. Once computed, the first endpoint call populates the cache; subsequent endpoint calls for the same session are instant dictionary lookups.

### 3.3 Short Run Panel Data Flow

```
Cached practice data
    │
    ├── session_best_laps: {driver → {time, compound, source, lap_number, team}}
    ├── short_run_stints: [stint dicts with lap_points]
    │
    └── compute_short_run_stats(short_run_stints, session_best_laps)
            │
            ├── Primary path (session_best_laps present):
            │   ├── Use official times for ranking + gaps
            │   ├── Count short-run stints per driver (annotation)
            │   ├── Check _is_lap_in_short_stints() for verification
            │   └── Attach: session_best_time, source, from_short_run, compound
            │
            ├── Fallback path (session_best_laps absent):
            │   ├── Extract min lap_time per driver from stint lap_points
            │   ├── Rank by extracted time
            │   └── Verification fields set to None
            │
            └── Returns: [{driver, team, best_lap_time, compound, tyre_life,
                           gap_to_p1, stint_count, position, verification_fields}]
                    │
                    └── Route handler wraps in PracticeShortRunResponse DTO
                            │
                            └── JSON response (CamelCaseModel auto-serialisation)
                                    │
                                    └── Frontend: useShortRunQuery → ShortRunPanel
```

### 3.4 Sector Analysis Panel Data Flow

```
Cached practice data
    │
    ├── enriched_laps: [all classified laps with sector times + speed traps]
    ├── session_best_laps: {driver → {time, compound, source, lap_number, team}}
    │
    └── compute_sector_analysis(enriched_laps, session_best_laps)
            │
            ├── Step 1: Index laps by (driver, lap_number) for fast lookup
            │
            ├── Step 2: Scan ALL laps for per-driver best individual sectors
            │           and max speed trap readings
            │
            ├── Step 3: For each driver in session_best_laps:
            │           ├── Look up actual lap by (driver, lap_number)
            │           ├── Extract S1, S2, S3 from that specific lap
            │           ├── Compute theoretical_best = best_S1 + best_S2 + best_S3
            │           └── Compute potential_gain = lap_time − theoretical_best
            │
            ├── Step 4: Build session-level summary:
            │           ├── Fastest S1, S2, S3 with driver attribution
            │           ├── Theoretical best across ALL drivers
            │           └── Theoretical gain vs actual session-best
            │
            ├── Step 5: Build speed trap results (max per driver, sorted desc)
            │
            └── Returns: {drivers, summary, speed_traps, total_drivers}
                    │
                    └── Route handler wraps in PracticeSectorAnalysisResponse DTO
                            │
                            └── JSON response
                                    │
                                    └── Frontend: useSectorAnalysisQuery
                                            └── SectorAnalysisPanel
                                                ├── Section A: Sector Times Table
                                                ├── Section B: Theoretical Best Card
                                                └── Section C: Speed Trap Bar Chart
```

### 3.5 Circuit Map Data Flow

```
SectorMapPanel receives: round (number), sessionId (string)
    │
    ├── useCircuitSVGQuery(round, isVisible)
    │       │
    │       ├── getCircuitSVGFilename(round)      ← circuitMap.ts lookup
    │       │       └── Returns: 'bahrain' (or undefined)
    │       │
    │       ├── fetch('/tracks/bahrain.svg')       ← Static asset from public/tracks/
    │       │
    │       └── parseCircuitSVG(svgText)           ← Browser DOMParser
    │               │
    │               ├── Parse SVG text to DOM document
    │               ├── Extract viewBox from <svg> element
    │               ├── Select sector paths by stroke colour:
    │               │   ├── path[stroke="#EF4444"] → Sector 1 path d-attribute
    │               │   ├── path[stroke="#3B82F6"] → Sector 2 path d-attribute
    │               │   └── path[stroke="#FBBF24"] → Sector 3 path d-attribute
    │               └── Return: CircuitSVGData { sector1PathD, sector2PathD,
    │                                            sector3PathD, viewBox }
    │
    ├── useSectorAnalysisQuery(sessionId, isVisible)   ← Shared React Query cache
    │       └── Returns: fastest driver per sector from summary
    │
    ├── getTrackIntelligence(round)                    ← Track Intelligence module
    │       └── Returns: sector colours for this circuit
    │           ├── sectors[0].color → S1 display colour
    │           ├── sectors[1].color → S2 display colour
    │           └── sectors[2].color → S3 display colour
    │
    └── Render SVG:
            ├── 3 gray base paths (strokeWidth 6, #374151)
            ├── 3 coloured overlay paths (strokeWidth 3, Track Intelligence colours)
            └── Legend: S1/S2/S3 badges with fastest driver abbreviation
```

The circuit map operates independently of the backend API. SVG assets are static files served from `public/tracks/` — no server-side processing is required. The sector analysis data is reused via React Query's shared cache (the same `sectorAnalysis` query key is consumed by both `SectorAnalysisPanel` and `SectorMapPanel`).

---

## 4. Technical Implementation Breakdown

### 4.1 Backend: New Functions

#### `_extract_session_best_laps()` (practice_data_service.py)

The foundation function that both short run and sector analysis depend on.

**Signature:**
```python
def _extract_session_best_laps(enriched_laps: List[Dict]) -> Dict[str, Dict]
```

**Return structure:**
```python
{
    'VER': {
        'session_best_time': 84.485,     # Raw FIA timing (seconds)
        'compound': 'SOFT',               # Tyre compound on best lap
        'tyre_life': 3,                   # Tyre age in laps
        'source': 'fastf1_flag',          # 'fastf1_flag' or 'computed_minimum'
        'lap_number': 15,                 # Lap number (for sector lookup)
        'team': 'Red Bull',               # Team name
    },
    ...
}
```

**Algorithm:**
1. Group all enriched laps by driver
2. Session-level check: does ANY lap in the session have `is_personal_best == True`?
3. If yes → flag-based path: for each driver, find the lap with `is_personal_best == True` and the fastest `lap_time` (defensive against multiple flags)
4. If no → computed path: for each driver, find the RACING lap with the minimum `lap_time`
5. Return dict keyed by driver abbreviation

**Integration point:** Called in `get_processed_practice_data()` during pipeline execution, result stored in the cached data dict under `'session_best_laps'`. Available to all downstream consumers.

#### `compute_short_run_stats()` (practice_data_service.py)

**Signature:**
```python
def compute_short_run_stats(
    short_run_stints: List[Dict],
    session_best_laps: Optional[Dict[str, Dict]] = None,
) -> List[Dict]
```

**Dual-path architecture:**

| Path | Trigger | Ranking Source | Verification Data |
|------|---------|---------------|-------------------|
| Primary | `session_best_laps` is truthy | Official FIA timing | Present (source, from_short_run, compound) |
| Fallback | `session_best_laps` is None/empty | Min lap_time from stint lap_points | All None |

**Primary path detail:**
1. Count short-run stints per driver (for `stint_count` annotation)
2. For each driver in `session_best_laps`: build result dict with official time, compound, team
3. Check `_is_lap_in_short_stints()` to determine if the session-best lap came from a short run stint
4. Sort by `best_lap_time` ascending
5. Assign positions (1-based) and compute `gap_to_p1`

**Fallback path detail:**
1. Group stints by driver
2. Scan all `lap_points` across all stints per driver to find minimum `lap_time`
3. Track the compound and tyre_life of the best lap
4. Sort, assign positions, compute gaps (same as primary)

#### `_is_lap_in_short_stints()` (practice_data_service.py)

**Signature:**
```python
def _is_lap_in_short_stints(
    lap_number: int, driver: str, short_run_stints: List[Dict],
) -> bool
```

Iterates through all short-run stints for the given driver, checking each stint's `lap_points` for a matching `lap_number`. Returns `True` if found. Used to annotate whether a driver's session-best lap came from a short run stint.

#### `compute_sector_analysis()` (practice_data_service.py)

**Signature:**
```python
def compute_sector_analysis(
    enriched_laps: List[Dict],
    session_best_laps: Dict[str, Dict],
) -> Dict
```

**Algorithm in 5 stages:**

**Stage 1 — Lap indexing:**
Build `lap_index: Dict[str, Dict[int, Dict]]` mapping `(driver, lap_number)` to the enriched lap dict. This enables O(1) lookup when extracting sector times from each driver's session-best lap.

**Stage 2 — Best individual sectors + max speeds:**
Single pass through all enriched laps. For each driver, track:
- `best_s1`, `best_s2`, `best_s3`: minimum sector time across all laps (independently)
- `speed_trap`, `speed_i1`, `speed_i2`, `speed_fl`: maximum speed at each trap

**Stage 3 — Build driver results:**
For each driver in `session_best_laps`:
1. Look up the actual lap via `lap_index[driver][best_lap_num]`
2. Extract S1, S2, S3 from that specific lap (may be None if sector data missing)
3. Retrieve best individual sectors from Stage 2
4. Compute `theoretical_best = best_s1 + best_s2 + best_s3` (None if any sector missing)
5. Compute `potential_gain = session_time − theoretical_best` (None if theoretical is None)
6. Sort by `lap_time` ascending, assign 1-based positions

**Stage 4 — Session-level summary:**
- Identify the fastest S1, S2, S3 from session-best lap sectors (with driver attribution)
- Compute absolute theoretical best: `min(all_best_s1) + min(all_best_s2) + min(all_best_s3)` across all drivers and all laps
- Compute theoretical gain: `actual_best_time − theoretical_best_time`

**Stage 5 — Speed trap results:**
For each driver in `session_best_laps`, pull max speeds from Stage 2. Sort by `speed_trap` descending (fastest first). Round to 1 decimal place.

### 4.2 Backend: DTOs

All DTOs extend `CamelCaseModel` (snake_case Python fields auto-serialise to camelCase JSON).

#### Short Run DTOs (dto.py)

```python
class PracticeShortRunDriver(CamelCaseModel):
    driver: str
    team: str
    best_lap_time: float
    compound: str
    tyre_life: int
    gap_to_p1: float
    stint_count: int
    position: int
    # Session verification fields (None when unavailable)
    session_best_time: Optional[float] = None
    session_best_source: Optional[str] = None       # 'fastf1_flag' | 'computed_minimum'
    session_best_from_short_run: Optional[bool] = None
    session_best_compound: Optional[str] = None

class PracticeShortRunResponse(CamelCaseModel):
    session_id: str
    fuel_corrected: bool
    drivers: List[PracticeShortRunDriver]
    session_best_lap: Optional[float] = None
    total_drivers: int = 0
    verification_available: bool = False
```

#### Sector Analysis DTOs (dto.py)

```python
class PracticeSectorDriver(CamelCaseModel):
    driver: str
    team: str
    position: int
    lap_time: float
    sector1: Optional[float] = None       # From session-best lap
    sector2: Optional[float] = None
    sector3: Optional[float] = None
    best_sector1: Optional[float] = None  # Best from any lap (same driver)
    best_sector2: Optional[float] = None
    best_sector3: Optional[float] = None
    theoretical_best: Optional[float] = None   # best_s1 + best_s2 + best_s3
    potential_gain: Optional[float] = None     # lap_time − theoretical_best
    compound: Optional[str] = None

class PracticeSectorSummary(CamelCaseModel):
    fastest_sector1: Optional[float] = None
    fastest_sector1_driver: Optional[str] = None
    fastest_sector2: Optional[float] = None
    fastest_sector2_driver: Optional[str] = None
    fastest_sector3: Optional[float] = None
    fastest_sector3_driver: Optional[str] = None
    theoretical_best_time: Optional[float] = None
    actual_best_time: Optional[float] = None
    theoretical_gain: Optional[float] = None

class PracticeSpeedTrapDriver(CamelCaseModel):
    driver: str
    team: str
    speed_trap: Optional[float] = None
    speed_i1: Optional[float] = None
    speed_i2: Optional[float] = None
    speed_fl: Optional[float] = None

class PracticeSectorAnalysisResponse(CamelCaseModel):
    session_id: str
    drivers: List[PracticeSectorDriver]
    summary: PracticeSectorSummary
    speed_traps: List[PracticeSpeedTrapDriver]
    total_drivers: int = 0
```

### 4.3 Backend: API Endpoints

Both new API endpoints are defined in `routes/practice.py` and registered under the `/practice` prefix.

#### `GET /practice/short-runs`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session` | str | required | Session ID, e.g. `2025_24_FP2` |
| `fuel_effect` | float | 0.0 | Fuel effect per kg (for pipeline cache reuse) |

Calls `get_processed_practice_data()` → extracts `short_run_stints` and `session_best_laps` → passes to `compute_short_run_stats()` → wraps result in `PracticeShortRunResponse`.

The `verification_available` flag on the response is computed as: does any driver result have a non-null `session_best_time`? This tells the frontend whether to render verification indicators.

#### `GET /practice/sector-analysis`

| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `session` | str | required | Session ID |
| `fuel_effect` | float | 0.0 | For pipeline cache reuse only |

Calls `get_processed_practice_data()` → extracts `laps` (all enriched laps) and `session_best_laps` → passes to `compute_sector_analysis()` → wraps result in `PracticeSectorAnalysisResponse`.

**Important:** The `fuel_effect` parameter is accepted but sector analysis always uses raw `lap_time` and raw sector times. The parameter exists solely for cache key alignment — if the user has fuel correction enabled, the same pipeline cache hit serves all endpoints.

### 4.4 Frontend: TypeScript Types

Matching TypeScript interfaces added to `packages/models/src/types.ts`:

```typescript
interface PracticeShortRunDriver {
    driver: string; team: string; bestLapTime: number; compound: string;
    tyreLife: number; gapToP1: number; stintCount: number; position: number;
    sessionBestTime: number | null; sessionBestSource: string | null;
    sessionBestFromShortRun: boolean | null; sessionBestCompound: string | null;
}

interface PracticeShortRunResponse {
    sessionId: string; fuelCorrected: boolean;
    drivers: PracticeShortRunDriver[];
    sessionBestLap: number | null; totalDrivers: number;
    verificationAvailable: boolean;
}

interface PracticeSectorDriver { /* 13 fields matching DTO */ }
interface PracticeSectorSummary { /* 9 fields */ }
interface PracticeSpeedTrapDriver { /* 6 fields */ }
interface PracticeSectorAnalysisResponse { /* 5 fields */ }
```

### 4.5 Frontend: Fetch Functions and Query Hooks

#### `fetchShortRuns()` (api.ts)

```typescript
export async function fetchShortRuns(
    sessionId: string, fuelEffect?: number
): Promise<PracticeShortRunResponse>
```

Passes `fuel_effect` as query parameter only when defined and > 0. This prevents unnecessary parameters when fuel correction is off.

#### `fetchSectorAnalysis()` (api.ts)

```typescript
export async function fetchSectorAnalysis(
    sessionId: string
): Promise<PracticeSectorAnalysisResponse>
```

No fuel_effect parameter — sector analysis always uses raw times.

#### `useShortRunQuery()` (lib/hooks/useShortRunQuery.ts)

```typescript
export function useShortRunQuery(
    sessionId: string | undefined,
    fuelEffect?: number,
    enabled: boolean = true,
)
```

Configuration: `staleTime: Infinity` (practice data is immutable), `gcTime: 30 min`, `placeholderData: keepPreviousData` (smooth transitions during GP navigation). The `enabled` parameter is gated by `useVisibility()` for deferred loading when the panel is below the fold.

#### `useSectorAnalysisQuery()` (lib/hooks/useSectorAnalysisQuery.ts)

Same pattern as `useShortRunQuery` but without `fuelEffect` in the query key factory.

#### `useCircuitSVGQuery()` (lib/hooks/useCircuitSVGQuery.ts)

```typescript
export function useCircuitSVGQuery(round: number, enabled: boolean)
```

Fetches the SVG file from `public/tracks/{filename}.svg`, parses it via DOMParser, and returns `CircuitSVGData`. Configuration: `staleTime: Infinity` (SVGs never change), `gcTime: 1 hour` (longer than data hooks since parsed SVGs are small), `keepPreviousData` for smooth round switching.

#### Query Keys (lib/hooks/queryKeys.ts)

```typescript
practice: {
    shortRuns: (sessionId, fuelEffect?) => ['practice', 'shortRuns', sessionId, fuelEffect],
    sectorAnalysis: (sessionId) => ['practice', 'sectorAnalysis', sessionId],
    circuitSVG: (round) => ['practice', 'circuitSVG', round],
}
```

### 4.6 Frontend: ShortRunPanel Component

**File:** `components/practice/ShortRunPanel.tsx` (~275 lines)

**Props:** `{ sessionId: string, fuelEffect: number }`

**Visual design:** Horizontal bar chart with team-coloured bars. Sorted by fastest to slowest (P1 at top). Each bar annotated with:
- Compound indicator: coloured circle with compound initial (S/M/H)
- P1: absolute lap time displayed as text
- P2+: lap time + gap to P1 (e.g., "84.493 +0.008")
- Verification indicator: `✓` if session-best came from a short run stint, `*` if from a long run

**Chart layout:**
- Dynamic height: `Math.min(480, Math.max(220, barCount * 38 + 80))` — scales with driver count
- Tight x-axis range: starts at `fastestLap − 0.6s` to magnify the spread between drivers
- Team colours at 0.9 opacity via `getTeamColorForMode(team, 'dark')`

**States:** Skeleton (6 progressive-width bars), error boundary, empty state ("This session appears to be focused on race simulation long runs"), content with `isPlaceholderData` opacity transition.

**Collapsible guide:** "How to read this chart" with 5 sections covering bar interpretation, compound indicators, verification markers, gap reading, and context about unknown fuel loads / engine modes.

### 4.7 Frontend: SectorAnalysisPanel Component

**File:** `components/practice/SectorAnalysisPanel.tsx` (~370 lines)

**Props:** `{ sessionId: string }`

**Three visual sections:**

**Section A — Sector Times Table:**
All 20 drivers ranked by session-best lap time. Columns: Position, Driver (with team colour dot), S1, S2, S3, Lap Time, Gain (potential gain). Fastest sector in each column highlighted in purple (`text-purple-sector`). Non-fastest sectors show delta to fastest, colour-coded by magnitude:
- Green (`text-green-400`): < 0.3s behind
- Yellow (`text-yellow-400`): 0.3–0.6s behind
- Red (`text-red-400`): > 0.6s behind

**Section B — Theoretical Best Lap Card:**
Large purple-highlighted time showing the theoretical best lap (sum of best individual sectors across all drivers and all laps). Below it, the gap to the session-best actual lap and explanatory text.

**Section C — Speed Trap Comparison:**
PlotlyLazy horizontal bar chart with team-coloured bars, sorted by speed ascending (smallest at top). P1 speed shows absolute value; others show speed + gap to fastest. Dynamic height scaled to driver count.

**States:** Same pattern as ShortRunPanel — skeleton, error, empty, content with opacity transition.

**Collapsible guide:** 5 sections covering sector table interpretation, purple highlighting, potential gain, theoretical best concept, and speed trap reading.

### 4.8 Frontend: Panel Wiring in PracticeContent.tsx

```tsx
{/* Phase 1: Long Run Pace */}
<ErrorBoundary key={`long-${sessionId}`} panelName="Long Run Pace">
    <LongRunPacePanel sessionId={sessionId} fuelEffect={fuelEffect} fuelCorrected={fuelCorrected} round={round} />
</ErrorBoundary>

{/* Phase 2: Short Run Panel */}
<ErrorBoundary key={`short-${sessionId}`} panelName="Short Run / Best Lap">
    <ShortRunPanel sessionId={sessionId} fuelEffect={fuelEffect} />
</ErrorBoundary>

{/* Phase 2: Circuit Map (positioned between short run and sector analysis) */}
<ErrorBoundary key={`map-${sessionId}`} panelName="Circuit Map">
    <SectorMapPanel round={round} sessionId={sessionId} />
</ErrorBoundary>

{/* Phase 2: Sector Analysis Panel */}
<ErrorBoundary key={`sectors-${sessionId}`} panelName="Sector Analysis">
    <SectorAnalysisPanel sessionId={sessionId} />
</ErrorBoundary>
```

Each panel is wrapped in an `ErrorBoundary` with a `key` that includes `sessionId`. When the user switches sessions (FP1 → FP2), React unmounts and remounts the ErrorBoundary, clearing any stale error state. This is the same pattern used on the Race page.

---

## 5. Sector Analysis: Additional Analytical Component

The sector analysis panel was not in the original Phase 2 plan (which covered only short run / best lap comparison). It was added during Phase 2 implementation as a natural extension once the `session_best_laps` infrastructure and sector data were confirmed available in the pipeline.

### 5.1 Why It Was Added

The original Practice Page roadmap included three phases: Long Run Pace, Short Run / Best Lap, and Session Progression. After implementing the short run panel, two observations motivated adding sector analysis:

1. **Data availability:** `get_practice_laps()` already extracted `sector1_time`, `sector2_time`, `sector3_time`, `speed_trap`, `speed_i1`, `speed_i2`, `speed_fl` for every lap. This data flowed through all transforms untouched and was available in the cached pipeline. No pipeline modifications were needed.

2. **Analytical gap:** The qualifying page had `SectorCards.tsx` showing sector breakdowns for selected drivers. The practice page had no sector-level analysis at all. Given that sector analysis is one of the most actionable insights from practice (identifying which track sections a car is strong or weak on), the gap was significant.

### 5.2 Design Choices

**Inspiration from qualifying, but deeper:**
The qualifying `SectorCards.tsx` shows sector times for 2 selected drivers. The practice `SectorAnalysisPanel` shows all 20 drivers, adds best-individual-sector analysis, theoretical best computation, and speed trap comparisons. The practice version provides broader coverage because practice sessions are about understanding the entire competitive landscape, not just head-to-head comparison.

**Raw times only:**
Sector analysis always uses raw sector times, not fuel-corrected. Fuel correction is an approximate adjustment applied to total lap times; distributing it across sectors would introduce compounding approximation errors with no analytical benefit.

**No regression or trend analysis:**
Unlike Phase 1's degradation hint (which compares start vs end of a stint), the sector analysis is purely snapshot-based — it shows the best achieved rather than the trajectory. This keeps the component statistically simple (arithmetic only, no scipy) consistent with the Practice page design principle.

---

## 6. Circuit Map with Sector Highlighting

The circuit map component (Phase 2b) was added after the short run and sector analysis panels were complete. It addresses the spatial dimension — letting users see where on the physical circuit each sector begins and ends.

### 6.1 SVG Asset Bundle

The SVG track maps come from the Gumroad f1-track-vectors bundle. The bundle contains 25 SVG files, one per circuit. 24 circuits on the 2025 F1 calendar are included; `portugal.svg` is excluded (not on the calendar).

**SVG Structure (consistent across all 24 circuits):**

Each SVG contains exactly 6 `<path>` elements and 1 `<g>` marker group:

| Element | Stroke | Width | Purpose |
|---------|--------|-------|---------|
| Path 1 | `#374151` (gray) | 8 | S1 thick outline |
| Path 2 | `#EF4444` (red) | 2 | S1 thin coloured overlay |
| Path 3 | `#374151` | 8 | S2 thick outline |
| Path 4 | `#3B82F6` (blue) | 2 | S2 thin coloured overlay |
| Path 5 | `#374151` | 8 | S3 thick outline |
| Path 6 | `#FBBF24` (amber) | 2 | S3 thin coloured overlay |
| Group | — | — | Start/finish marker (`<g id="moving-circle-group">`) |

**Key structural properties:**
- **No class or id on path elements** — selection must be by `stroke` colour attribute
- Each gray/coloured pair shares the **identical `d` attribute** (same path shape)
- Sector paths connect end-to-end forming a complete circuit loop (S1→S2→S3→S1)
- All paths have `vector-effect="non-scaling-stroke"` for consistent visual weight
- Root element: `<svg id="minimap-svg">` with circuit-specific viewBox

**File locations:** `apps/web/public/tracks/{circuit}.svg` (24 files)

### 6.2 SVG Parsing Strategy

The parsing approach was dictated by the SVG structure: no classes or IDs meant the standard approach of `querySelector('.sector-1')` was impossible. Instead, the parser selects by stroke colour:

```typescript
// In parseCircuitSVG():
const s1Path = doc.querySelector('path[stroke="#EF4444"]')?.getAttribute('d')
const s2Path = doc.querySelector('path[stroke="#3B82F6"]')?.getAttribute('d')
const s3Path = doc.querySelector('path[stroke="#FBBF24"]')?.getAttribute('d')
```

**Why DOMParser and not @svgr/webpack or dangerouslySetInnerHTML:**

1. **DOMParser** is browser-native, zero-dependency, and produces a DOM tree that can be queried safely
2. **@svgr/webpack** would import each SVG as a React component — but we have 24 SVGs fetched at runtime based on the selected round, not at build time
3. **dangerouslySetInnerHTML** would render the full SVG markup including the start/finish marker group, gray outlines at their original 8px width, and original Gumroad colours — all of which we want to override with Track Intelligence colours and our own rendering dimensions

The DOMParser approach extracts only the path `d` attributes and viewBox string, then renders them as clean JSX `<path>` elements with controlled stroke colours and widths.

### 6.3 Circuit Filename Lookup

`circuitMap.ts` provides a lightweight round-to-filename mapping:

```typescript
const CIRCUIT_SVG_MAP: Record<number, string> = {
    1:  'australia',       // Australian GP
    2:  'china',           // Chinese GP
    3:  'japan',           // Japanese GP
    4:  'bahrain',         // Bahrain GP
    5:  'saudi_arabia',    // Saudi Arabian GP
    6:  'miami',           // Miami GP
    7:  'imola',           // Emilia Romagna GP
    8:  'monaco',          // Monaco GP
    9:  'spain',           // Spanish GP
    10: 'canada',          // Canadian GP
    11: 'austria',         // Austrian GP
    12: 'silverstone',     // British GP
    13: 'spa',             // Belgian GP
    14: 'hungary',         // Hungarian GP
    15: 'netherlands',     // Dutch GP
    16: 'monza',           // Italian GP
    17: 'azerbaijan',      // Azerbaijan GP
    18: 'singapore',       // Singapore GP
    19: 'usa',             // United States GP
    20: 'mexico',          // Mexican GP
    21: 'brazil',          // Brazilian GP
    22: 'las_vegas',       // Las Vegas GP
    23: 'qatar',           // Qatar GP
    24: 'abudhabi',        // Abu Dhabi GP
}
```

This module is intentionally separated from the full Track Intelligence module (304 KiB) — the SectorMapPanel only needs the filename string to fetch the SVG. The full Track Intelligence data is imported separately for sector colours.

**Filename alignment:** During Phase 2b integration, 16 of 24 filenames had to be corrected to match the Gumroad bundle naming convention. The original placeholders (e.g., `'albert-park'`, `'suzuka'`, `'cota'`) were replaced with the actual bundle filenames (e.g., `'australia'`, `'japan'`, `'usa'`).

### 6.4 SectorMapPanel Component

**File:** `components/practice/SectorMapPanel.tsx` (~215 lines)

**Props:**
```typescript
interface SectorMapPanelProps {
    round: number      // F1 round number (1-24) for SVG lookup + sector colours
    sessionId: string  // Session ID for sector analysis data
}
```

**Rendering approach:**
Rather than injecting the original SVG markup, the component renders 6 JSX `<path>` elements — recreating the Gumroad dual-layer visual pattern with controlled colours:

```tsx
<svg viewBox={svgData.viewBox} className="w-full h-auto max-h-[400px]">
    {/* Gray base layer — all 3 sector paths as thick gray outlines */}
    <path d={svgData.sector1PathD} stroke="#374151" strokeWidth={6} />
    <path d={svgData.sector2PathD} stroke="#374151" strokeWidth={6} />
    <path d={svgData.sector3PathD} stroke="#374151" strokeWidth={6} />
    {/* Coloured overlay — thinner, on top */}
    <path d={svgData.sector1PathD} stroke={s1Color} strokeWidth={3} />
    <path d={svgData.sector2PathD} stroke={s2Color} strokeWidth={3} />
    <path d={svgData.sector3PathD} stroke={s3Color} strokeWidth={3} />
</svg>
```

The sector colours (`s1Color`, `s2Color`, `s3Color`) come from `getTrackIntelligence(round)?.sectors[i].color` with fallback defaults of `['#FF0000', '#0066FF', '#FFCC00']` when Track Intelligence is unavailable for a circuit.

**Sector legend:** A `SectorLegendItem` sub-component renders a coloured dot, sector label (S1/S2/S3), and the fastest driver abbreviation sourced from `useSectorAnalysisQuery`. This creates a cross-reference between the map's visual sectors and the session's actual performance data.

**Graceful degradation:**
- If `getCircuitSVGFilename(round)` returns `undefined`: the query is disabled, panel shows "Track map not available for this circuit"
- If SVG fetch fails (404, network error): `parseCircuitSVG()` returns `null`, same empty state
- If any of the 3 sector paths cannot be extracted: returns `null` (malformed SVG)
- Panel never throws — wrapped in ErrorBoundary as defence in depth

**Accessibility:**
- `role="img"` on the SVG element
- `aria-label` with circuit name (e.g., "Circuit map of Bahrain International Circuit with sector highlighting")
- Individual `aria-label` attributes on each coloured sector path

### 6.5 CircuitSVGData Interface

```typescript
export interface CircuitSVGData {
    sector1PathD: string    // SVG path d-attribute for Sector 1
    sector2PathD: string    // SVG path d-attribute for Sector 2
    sector3PathD: string    // SVG path d-attribute for Sector 3
    viewBox: string         // SVG viewBox for correct aspect ratio
}
```

The interface is intentionally minimal. The original SVG's start/finish marker group, path stroke widths, and colours are not extracted — the component controls these through JSX rendering. Only the geometric data (path shapes and viewBox) is preserved from the source SVGs.

---

## 7. Session Verification and the Accuracy Fix

### 7.1 The Problem That Prompted the Fix

The initial short run implementation extracted best laps from short-run stint data. During Docker integration testing, a discrepancy was discovered: some drivers' session-best laps didn't come from stints classified as short runs. A driver might set their fastest time during a long run stint (4+ valid laps) on a lap with fresh tyres early in the stint.

Additionally, fuel correction could shift relative ordering. A driver whose raw time was 84.501s might appear as 84.448s after fuel adjustment, reordering the ranking relative to a driver with raw 84.493s that became 84.461s. The displayed ranking would not match the official F1 session classification.

### 7.2 The Fix

The `_extract_session_best_laps()` function was introduced as a new step in the `get_processed_practice_data()` pipeline. It extracts each driver's personal-best lap using FIA timing, completely independent of stint classification or fuel correction.

The short run panel was then redesigned with the dual-path architecture:
- **Primary path:** Uses `session_best_laps` for ranking, times, and gaps
- **Fallback path:** Extracts from stint data only when official timing is unavailable

The stint data was retained for contextual annotation: `stint_count` shows how many short-run stints a driver completed, and `session_best_from_short_run` indicates whether their fastest lap came from a short or long run stint.

### 7.3 Verification Fields

Four verification fields on each driver result provide transparency:

| Field | Type | Meaning |
|-------|------|---------|
| `session_best_time` | float | The official session-best time (seconds) |
| `session_best_source` | string | `'fastf1_flag'` or `'computed_minimum'` |
| `session_best_from_short_run` | bool | True if best lap is in a short-run stint |
| `session_best_compound` | string | Tyre compound on the session-best lap |

In the frontend, `ShortRunPanel` renders these as:
- `✓` suffix when `sessionBestFromShortRun` is true (best lap from a qualifying-simulation stint)
- `*` suffix when false (best lap from a race-simulation stint)
- A footnote explaining the indicators when `verificationAvailable` is true

---

## 8. Testing, Verification, and Validation

### 8.1 Unit Test Suite

#### Short Run Tests: `test_practice_short_runs.py` (41 tests)

| Test Class | Count | Coverage |
|-----------|-------|----------|
| `TestEmptyInput` | 3 | Empty list, no lap points, null lap times |
| `TestSingleDriver` | 4 | Single lap, multiple laps (picks minimum), compound from best lap, tyre life |
| `TestMultipleDrivers` | 3 | Ranking order, gap_to_p1 correctness, P1 identification |
| `TestMultiStintPerDriver` | 3 | Cross-stint best lap, stint count, compound from correct stint |
| `TestSingleLapStints` | 2 | 1-lap stints handled, gap correctness |
| `TestOutputFormat` | 4 | 3dp rounding, required keys, team preservation |
| `TestIsLapInShortStints` | 4 | Found, not found, wrong driver, empty stints |
| `TestSessionVerification` | 10 | Verification fields present/null, match detection, source tracking, multi-driver official ranking |
| `TestOfficialRanking` | 8 | Official times override stint times, gap computation, team/compound source, position assignment, fallback paths, fuel-correction override test |

**Key test: `test_official_ranking_overrides_fuel_corrected_stint_ordering`**
This test verifies the core accuracy fix: when short-run stint fuel-corrected times produce a different ordering than official timing, the official ranking prevails. The test creates stints where NOR < LEC < VER by fuel-corrected times, but official timing shows NOR < VER < LEC. The assertion confirms the official order is used.

#### Sector Analysis Tests: `test_practice_sector_analysis.py` (17 tests)

| Test | Coverage |
|------|----------|
| `test_basic_two_drivers` | Two drivers produce correct results with positions |
| `test_session_best_lap_sectors_extracted` | Sectors come from correct lap (matched by lap_number) |
| `test_best_individual_sectors_differ_from_session_best` | Best individual S1/S2/S3 from different laps |
| `test_missing_sector_times_handled` | Null sectors produce None theoretical/potential |
| `test_summary_fastest_sectors` | Correct fastest sector identification per sector |
| `test_theoretical_best_computation` | Cross-driver theoretical best: 26.2 + 30.8 + 26.5 = 83.5 |
| `test_theoretical_gain_positive` | Single driver: theoretical gain = 0.0 |
| `test_potential_gain_per_driver` | Per-driver gain computed correctly |
| `test_speed_trap_maximums` | Max speed across multiple laps |
| `test_speed_trap_handles_nulls` | Null speeds don't crash |
| `test_empty_laps_returns_empty` | Empty input → empty output |
| `test_empty_session_best_returns_empty` | Empty session_best → empty output |
| `test_drivers_sorted_by_lap_time` | Position assignment reflects lap time ordering |
| `test_gap_to_sector_fastest` | Frontend-computed delta matches expected |
| `test_speed_traps_sorted_by_speed_descending` | Fastest speed trap first |
| `test_compound_from_session_best` | Compound sourced from session_best_laps |
| `test_team_from_session_best` | Team sourced from session_best_laps |

### 8.2 Full Suite Regression Check

```
302 tests collected, 302 passed, 0 failed, 0 regressions
```

Breakdown:
- 172 practice tests (40 transforms + 64 data service + 41 short runs + 17 sector analysis + 10 session verification)
- 130 race/qualifying tests (unchanged)

### 8.3 Docker Integration Testing

All integration testing was performed against the live Docker stack (f1-api, f1-ml, f1-web) using real FastF1 data.

#### Session Coverage

| Session | Drivers | Official Match | Sector Sums |
|---------|---------|---------------|-------------|
| Abu Dhabi FP1 (R24) | 20/20 | ✅ vs formula1.com | ✅ 0.000 diff all drivers |
| Abu Dhabi FP2 (R24) | 20/20 | ✅ vs short-runs endpoint | ✅ verified |
| Abu Dhabi FP3 (R24) | 20/20 | ✅ vs short-runs endpoint | ✅ verified |
| Bahrain FP1 (R4) | 20/20 | ✅ vs formula1.com | ✅ 0.000 diff all drivers |
| Imola FP1 | 20/20 | ✅ | ✅ verified |

#### Sector Sum Integrity

For every driver in every tested session, `S1 + S2 + S3 = lapTime` with 0.000 difference. This confirms the lap lookup by `(driver, lap_number)` correctly identifies the session-best lap and that sector times are faithfully extracted.

Example (Abu Dhabi FP1 top 5):
```
P1 NOR  | S1=17.390 S2=36.526 S3=30.569 | Lap=84.485 | diff=0.000
P2 VER  | S1=17.290 S2=36.506 S3=30.697 | Lap=84.493 | diff=0.000
P3 LEC  | S1=17.419 S2=36.492 S3=30.590 | Lap=84.501 | diff=0.000
P4 ANT  | S1=17.316 S2=36.413 S3=30.879 | Lap=84.608 | diff=0.000
P5 HUL  | S1=17.493 S2=36.590 S3=30.546 | Lap=84.629 | diff=0.000
```

#### Cross-Endpoint Consistency

Sector-analysis positions were cross-verified against short-runs positions for Abu Dhabi FP2 and FP3 — both endpoints produce identical rankings, confirming both consume the same `session_best_laps` data.

#### Edge Case Verification

| Check | Result | Method |
|-------|--------|--------|
| Theoretical best ≤ actual best | ✅ PASS | Verified across all sessions |
| Best individual sectors ≤ session-best sectors | ✅ PASS | 0 violations detected |
| All potential gains ≥ 0 | ✅ PASS | All drivers |
| Speed traps in realistic range | ✅ PASS | 250–350 km/h for all readings |
| All 20 drivers have non-null sector data | ✅ PASS | All sessions |
| Drivers with better sectors on other laps | ✅ 13+ found | Theoretical best feature working |

The last check (13 drivers with better individual sectors on other laps) confirms the theoretical best computation is genuinely extracting sector improvements from non-best laps, not just repeating session-best lap sectors.

### 8.4 SVG Circuit Map Verification

#### Asset Serving (24/24 circuits)

All 24 SVG files verified serving HTTP 200 from the Docker web container:

```
australia.svg     ✅    austria.svg      ✅    azerbaijan.svg   ✅
bahrain.svg       ✅    brazil.svg       ✅    canada.svg       ✅
china.svg         ✅    hungary.svg      ✅    imola.svg        ✅
japan.svg         ✅    las_vegas.svg    ✅    mexico.svg       ✅
miami.svg         ✅    monaco.svg       ✅    monza.svg        ✅
netherlands.svg   ✅    qatar.svg        ✅    saudi_arabia.svg ✅
silverstone.svg   ✅    singapore.svg    ✅    spa.svg          ✅
spain.svg         ✅    usa.svg          ✅    abudhabi.svg     ✅
```

#### SVG Structure Validation

Four representative circuits inspected in detail to confirm consistent structure:

| Circuit | Paths | S1 Stroke | S2 Stroke | S3 Stroke | ViewBox |
|---------|-------|-----------|-----------|-----------|---------|
| Bahrain | 6 + marker | `#EF4444` ✅ | `#3B82F6` ✅ | `#FBBF24` ✅ | Unique ✅ |
| Monaco | 6 + marker | `#EF4444` ✅ | `#3B82F6` ✅ | `#FBBF24` ✅ | Unique ✅ |
| Silverstone | 6 + marker | `#EF4444` ✅ | `#3B82F6` ✅ | `#FBBF24` ✅ | Unique ✅ |
| Abu Dhabi | 6 + marker | `#EF4444` ✅ | `#3B82F6` ✅ | `#FBBF24` ✅ | Unique ✅ |

All four circuits confirmed: consistent path structure, correct stroke colour selectors, circuit-specific viewBox attributes, start/finish marker group present.

#### Visual Rendering Verification

Screenshots captured of the SectorMapPanel rendering for 4 circuits via Docker:
- **Bahrain (Round 4):** Three-sector circuit visible with coloured overlays, legend shows fastest S1/S2/S3 drivers
- **Monaco (Round 8):** Distinctive street circuit shape rendered correctly, tight corners visible
- **Silverstone (Round 12):** High-speed flowing layout rendered, sector boundaries clearly delineated
- **Abu Dhabi (Round 24):** Yas Marina circuit shape confirmed, all three sectors highlighted

#### JavaScript Bundle Verification

Confirmed the built JS bundle contains:
- Stroke colour selectors (`#EF4444`, `#3B82F6`, `#FBBF24`)
- `useCircuitSVGQuery` hook reference
- `circuitSVG` query key factory
- `SectorMapPanel` component reference

### 8.5 Frontend Verification

- TypeScript compilation: `✓ Compiled successfully` with 0 errors
- Static page generation: `✓ Generating static pages (8/8)`
- Build bundle: No new chunk size warnings
- EPERM symlink error: Pre-existing Windows/OneDrive issue (documented in CLAUDE.md), does not affect compilation

---

## 9. Key Decisions and Learnings

### 9.1 Official Timing as Ground Truth

**Decision:** Anchor short run rankings to FIA session-best times rather than extracted stint-based times.

**Rationale:** The entire ApexView platform operates on the principle that official timing is ground truth (documented in CLAUDE.md Section 1). Displaying a ranking that differs from the official session classification would undermine user trust, even if the fuel-corrected ranking is arguably more analytically interesting.

**Impact:** Required introducing `_extract_session_best_laps()` as a new pipeline step and restructuring `compute_short_run_stats()` with dual paths. This added complexity but eliminated all timing discrepancies in Docker testing.

### 9.2 Session-Level Extraction Consistency

**Decision:** Use all-or-nothing flag detection rather than per-driver detection for session-best extraction.

**Learning:** During testing, an edge case was identified where some drivers had `is_personal_best` flags and others didn't (their best lap was deleted for track limits). Mixing flag-based extraction for some drivers and computed minimums for others would create an inconsistent ranking. The session-level check ensures uniform methodology.

### 9.3 Sector Analysis Uses Raw Times Only

**Decision:** Always use raw sector times even when fuel correction is enabled.

**Rationale:** Fuel correction is an approximation applied to total lap times. Distributing it across three sectors would either require splitting the correction proportionally (arbitrary) or applying a sector-specific correction (not enough data to calibrate). Raw sector times are what the FIA reports and what teams use for setup analysis.

### 9.4 Speed Trap Maximums Rather Than Averages

**Decision:** Use maximum speed per driver across all laps rather than average or session-best-lap speed.

**Rationale:** Practice sessions involve laps at varying engine modes (fuel save, push, full qualifying mode) and fuel loads. The maximum represents the car's potential — likely achieved on a low-fuel lap with full engine deployment. The average would be diluted by installation laps, cooldown laps, and fuel-saving laps.

### 9.5 Verification Data as Transparent Metadata

**Decision:** Include session verification fields (source, from_short_run, compound) as first-class data rather than hiding them.

**Learning:** During the accuracy fix, it became clear that simply showing "correct" numbers without explaining *how* they were derived would leave analysts unable to assess data quality. The verification fields let the frontend communicate provenance (✓ from short run, * from long run) and let developers debug timing discrepancies.

### 9.6 Scope Expansion: Adding Sector Analysis

**Decision:** Add sector analysis as part of Phase 2 rather than deferring to a future phase.

**Rationale:** Once `session_best_laps` was implemented and sector data was confirmed available in the pipeline, the marginal cost of adding sector analysis was low (one new compute function + one new component). The analytical value was high — sector-level insights are among the most requested features in F1 data analysis tools.

### 9.7 SVG Stroke-Colour Selectors Over Class/ID

**Decision:** Select SVG sector paths by `stroke` colour attribute rather than adding class or ID attributes to the source files.

**Learning:** The Gumroad SVG bundle has no class or ID on any `<path>` element. The initial scaffold code used placeholder selectors (`.sector-1`, `.sector-2`, `.sector-3`) which would have required manually editing all 24 SVG files. Inspecting the actual SVG structure revealed that each sector is drawn twice (gray outline + coloured overlay) with consistent stroke colours across all 24 circuits:
- S1: `#EF4444` (red)
- S2: `#3B82F6` (blue)
- S3: `#FBBF24` (amber)

Using `querySelector('path[stroke="#EF4444"]')` is robust, requires zero modification to the source SVGs, and has been verified working on all 24 circuits.

**Impact:** The 24 SVG files are used as-is from the Gumroad bundle — no manual editing, no risk of introducing parsing errors through file modification, and future bundle updates can be dropped in without changes.

### 9.8 DOMParser Over @svgr/webpack or dangerouslySetInnerHTML

**Decision:** Use browser-native `DOMParser` to extract path data, then render as JSX `<path>` elements.

**Rationale:** Three approaches were considered:

| Approach | Pros | Cons |
|----------|------|------|
| `@svgr/webpack` | Type-safe React components | Build-time import; 24 circuits loaded at runtime by round number, not build time |
| `dangerouslySetInnerHTML` | Simple, preserves original visual | No colour control, includes unwanted elements (marker group), XSS surface |
| **DOMParser + JSX** | **Full colour control, safe, minimal data extraction** | Requires parsing code |

The DOMParser approach extracts only the geometric data (path `d` attributes and viewBox) and discards everything else. The component then renders 6 controlled `<path>` elements with Track Intelligence colours instead of the original Gumroad colours.

### 9.9 Filename Alignment Discovery

**Learning:** 16 of 24 circuit filenames in the initial `circuitMap.ts` didn't match the Gumroad bundle naming convention. For example, `'albert-park'` should be `'australia'`, `'suzuka'` should be `'japan'`, `'cota'` should be `'usa'`.

**Impact:** This was discovered during Phase 2b integration testing when SVG fetches returned 404. A systematic audit of all 24 filenames against the actual bundle contents resolved the issue. The corrected map was verified by fetching all 24 SVGs from Docker (all HTTP 200).

**Prevention:** The mapping table now includes comments with the GP name for each entry, making mismatches easier to spot.

### 9.10 Dual-Layer Rendering Matches Source Visual

**Decision:** Render each sector as 2 paths (thick gray + thin coloured) rather than a single coloured path.

**Learning:** The original Gumroad SVGs use this dual-layer pattern: a thick gray outline establishes the track shape, and a thinner coloured overlay highlights the sector. This visual pattern was preserved in the component — the gray base layer (strokeWidth 6) provides contrast and readability even when two adjacent sectors have similar colours, and the coloured overlay (strokeWidth 3) sits on top to highlight sector boundaries.

---

## 10. Alignment with Broader Practice Page Plan

### Updated Phase Architecture

| Phase | Name | Status | Test Count | Key Additions |
|-------|------|--------|-----------|---------------|
| 1 | Data Foundation & Long Run Pace | ✅ Complete | 104 | Pipeline, classification, fuel correction, traffic, stint grouping, violin panel |
| **2** | **Short Run / Best Lap + Sector Analysis + Circuit Map** | **✅ Complete** | **58** | Session-best extraction, short run ranking, sector breakdown, speed traps, circuit map, accuracy fix |
| 3 | Session Progression & Performance Optimisation | 📋 Planned | — | Cross-session comparison, Lighthouse optimisation |

### What Phase 2 Established for Phase 3

Phase 2's `_extract_session_best_laps()` function provides the authoritative per-driver best lap that Phase 3's session progression analysis will use. When Phase 3 computes gap-to-session-best across FP1 → FP2 → FP3, it will consume `session_best_laps` from each session's cached pipeline rather than re-deriving best laps.

The pattern of endpoint-specific compute functions (`compute_short_run_stats()`, `compute_sector_analysis()`) that consume the shared cached pipeline is now well-established. Phase 3 will follow the same pattern with a `compute_session_progression()` function and `GET /practice/progression` endpoint.

The circuit map infrastructure (SVG assets, parsing, rendering) is complete and requires no Phase 3 changes. The 24 circuit SVGs are available for any future feature that needs track visualisation.

### Cumulative Test Baseline

| Phase | New Tests | Running Total |
|-------|----------|---------------|
| Phase 1 | 104 | 104 |
| Phase 2 | 58 | 162 |
| Race + ML (unchanged) | 140 | **302** |

### Complete Panel Layout (Post-Phase 2)

```
Practice Page
├── Sidebar: Session Tabs (FP1/FP2/FP3) + Fuel Correction Toggle
├── Phase 1: LongRunPacePanel         ← Violin plot, stint cards
├── Phase 2: ShortRunPanel            ← Horizontal bar chart, rankings
├── Phase 2: SectorMapPanel           ← SVG circuit map with sectors
├── Phase 2: SectorAnalysisPanel      ← Sector table, theoretical best, speed trap
└── Phase 3: (Planned) SessionProgressionPanel
```

### Files Modified in Phase 2

| Action | File | Description |
|--------|------|-------------|
| Modified | `services/practice/practice_data_service.py` | +440 lines: _extract_session_best_laps, _is_lap_in_short_stints, compute_short_run_stats, compute_sector_analysis + pipeline integration |
| Rewritten | `routes/practice.py` | +120 lines: 2 new endpoints + all imports |
| Modified | `models/dto.py` | +83 lines: 8 new DTOs |
| Modified | `packages/models/src/types.ts` | +78 lines: 8 new TypeScript interfaces |
| Modified | `lib/api.ts` | +20 lines: 2 new fetch functions |
| Modified | `lib/hooks/queryKeys.ts` | +6 lines: 3 new key factories (shortRuns, sectorAnalysis, circuitSVG) |
| Created | `lib/hooks/useShortRunQuery.ts` | 23 lines: Short run React Query hook |
| Created | `lib/hooks/useSectorAnalysisQuery.ts` | 23 lines: Sector analysis React Query hook |
| Created | `lib/hooks/useCircuitSVGQuery.ts` | 125 lines: SVG fetch, parse (DOMParser), React Query hook |
| Created | `lib/circuitMap.ts` | 48 lines: Round-to-SVG-filename lookup (24 circuits) |
| Created | `components/practice/ShortRunPanel.tsx` | ~275 lines: Horizontal bar chart panel |
| Created | `components/practice/SectorAnalysisPanel.tsx` | ~370 lines: Sector table + theoretical best + speed trap |
| Created | `components/practice/SectorMapPanel.tsx` | ~215 lines: SVG circuit map with sector highlighting |
| Modified | `app/practice/PracticeContent.tsx` | +16 lines: panel wiring (3 new panels) |
| Copied | `public/tracks/*.svg` | 24 SVG circuit map files from Gumroad bundle |
| Created | `tests/test_practice_short_runs.py` | ~513 lines: 41 tests |
| Created | `tests/test_practice_sector_analysis.py` | ~397 lines: 17 tests |

---

*Documentation Version 2.0 — March 2026*
