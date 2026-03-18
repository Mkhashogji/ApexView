# Phase 7: Frontend Implementation — Complete Technical Documentation

## Document Information

| Attribute | Value |
|-----------|-------|
| **Phase** | 7 of 8 |
| **Module** | Performance Insights Panel |
| **Location** | `apps/web/components/panels/PerformanceInsightsPanel/` |
| **Dependencies** | Phase 6 endpoint (`/analysis/performance-insights`), React Query, Tailwind CSS |
| **Status** | Complete |
| **Test Status** | TypeScript compilation passes, Next.js build successful |

---

## Table of Contents

1. [Overview of Phase 7](#1-overview-of-phase-7)
2. [Sequential Implementation Steps](#2-sequential-implementation-steps)
3. [Phase 7 Workflow](#3-phase-7-workflow)
4. [Component Architecture](#4-component-architecture)
5. [Type System Design](#5-type-system-design)
6. [Data Flow](#6-data-flow)
7. [Verification Results](#7-verification-results)

---

## 1. Overview of Phase 7

### 1.1 Objectives

Phase 7 transforms the technical analysis from Phases 2-6 into a user-facing visual interface. The primary objectives were:

1. **Replace AnalysisInsights**: Remove the legacy component displaying meaningless cosine similarity scores ("99.9% similar")
2. **Consume Phase 6 Payload**: Create a frontend that consumes the unified `/analysis/performance-insights` endpoint
3. **Dual-Mode Display**: Support both Engineer (technical metrics) and Driver (actionable coaching) perspectives
4. **Rich Visualization**: Display technique profiles, dimension bars, and focus areas
5. **Maintain Patterns**: Follow existing codebase conventions for consistency

### 1.2 Key Achievements

| Achievement | Description |
|-------------|-------------|
| **Type Safety** | Added ~120 lines of TypeScript interfaces mirroring Phase 6 Pydantic schemas |
| **API Integration** | Created `fetchPerformanceInsights()` function calling the unified endpoint |
| **React Query Hook** | Implemented `usePerformanceInsightsQuery` with proper caching and error handling |
| **Component Library** | Built 8 modular components for the Performance Insights Panel |
| **Seamless Integration** | Replaced AnalysisInsights with zero breaking changes to QualifyingContent |

### 1.3 The Transformation

**Before (AnalysisInsights)**:
```
┌─────────────────────────────────────────────────────────────┐
│  AI Insights                                                │
│  ─────────────────────────────────────────────────────────  │
│  VER vs NOR: 99.9% similar                                  │
│  Cluster: Group A                                           │
│                                                             │
│  VER vs PIA: 99.8% similar                                  │
│  Cluster: Group A                                           │
└─────────────────────────────────────────────────────────────┘
```

**After (PerformanceInsightsPanel)**:
```
┌─────────────────────────────────────────────────────────────┐
│  Performance Insights                    [Engineer] [Driver] │
│  ─────────────────────────────────────────────────────────  │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ NOR vs VER                                    +0.065s   ││
│  │ "Strong exit traction, weak under braking"              ││
│  │                                                         ││
│  │ Braking      ████░░░░░░  P35  -89ms                     ││
│  │ Apex         █████░░░░░  P52  +12ms                     ││
│  │ Exit         ████████░░  P85  +45ms                     ││
│  │ Consistency  ██████░░░░  P68                            ││
│  │                                                         ││
│  │ Focus: 🟢 T3  🟢 T7  🔴 T1  🔴 T4                       ││
│  └─────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────┘
```

### 1.4 Features Implemented

1. **Mode Toggle**: Switch between Engineer and Driver perspectives
2. **Driver Insight Cards**: Per-driver analysis with:
   - Team-colored border and driver badge
   - Official gap delta badge (color-coded)
   - Natural language summary
   - Four-dimension technique profile
   - Focus areas (gaining/losing corners)
   - Expandable details section
3. **Loading States**: Skeleton cards during API calls
4. **Error Handling**: Error state with retry functionality
5. **Idle State**: Informative message when no drivers selected

---

## 2. Sequential Implementation Steps

### Step 1: TypeScript Type Definitions

**File**: `packages/models/src/types.ts`

**Rationale**: TypeScript types must mirror the backend Pydantic schemas exactly to ensure type safety across the API boundary. This prevents runtime errors from shape mismatches.

**Implementation**:

```typescript
// Core Response Types
export interface PerformanceInsightsResponse {
  session_id: string
  reference_driver: string
  circuit_name?: string
  mode: string
  results: DriverPerformanceResult[]
  session_percentiles?: SessionPercentiles
  total_drivers_requested: number
  total_drivers_processed: number
  total_corners: number
  phase_timing: PhaseTimingInfo[]
  total_duration_ms: number
  errors: string[]
  warnings: string[]
}

// Driver Result (combines Phases 2-5)
export interface DriverPerformanceResult {
  driver: string
  // Phase 2: Scaled Delta
  official_gap: number
  scaling_confidence: number
  delta?: number[]
  distance?: number[]
  // Phase 3: Corner Analysis
  corners_gaining: number
  corners_losing: number
  total_corner_delta: number
  corner_results: PerformanceCornerResult[]
  // Phase 4 & 5
  technique_profile?: TechniqueProfile
  insight?: NaturalLanguageInsight
}
```

**Key Design Decisions**:

1. **Snake_case preservation**: Field names match Python's snake_case to avoid transformation overhead
2. **Optional fields**: Used `?` for fields that may not be present (e.g., `technique_profile`, `insight`)
3. **Reusable types**: Created helper types (`DimensionType`, `DimensionLevel`, `InsightMode`) for UI components
4. **Comprehensive coverage**: Added all nested types (TechniqueProfile, NaturalLanguageInsight, DimensionInsight, etc.)

---

### Step 2: API Client Function

**File**: `apps/web/lib/api.ts`

**Rationale**: The API client function encapsulates the HTTP request logic, providing a clean interface for the React Query hook.

**Implementation**:

```typescript
export async function fetchPerformanceInsights(
  sessionId: string,
  referenceDriver: string,
  compareDrivers: string[],
  corners: Corner[],
  mode: 'engineer' | 'driver' = 'engineer',
  sessionPart?: string
): Promise<PerformanceInsightsResponse> {
  const response = await fetch(`${ML_SERVICE_URL}/analysis/performance-insights`, {
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
      mode,
      session_part: sessionPart ?? null,
      include_telemetry: false, // Optimize payload size
    }),
  })

  if (!response.ok) {
    const errorText = await response.text()
    throw new ApiError(response.status, `Performance insights request failed: ${errorText}`)
  }

  return response.json()
}
```

**Key Design Decisions**:

1. **Case transformation**: Converts frontend camelCase (`cornerNumber`) to backend snake_case (`corner_number`)
2. **Telemetry exclusion**: Sets `include_telemetry: false` to reduce payload size (frontend doesn't need raw delta arrays)
3. **Error propagation**: Throws `ApiError` with status and message for proper error handling upstream
4. **Null handling**: Uses `sessionPart ?? null` to handle optional parameters correctly

---

### Step 3: Query Key Factory Update

**File**: `apps/web/lib/hooks/queryKeys.ts`

**Rationale**: React Query uses query keys for caching and deduplication. A well-designed key factory ensures cache coherence.

**Implementation**:

```typescript
performanceInsights: (
  sessionId: string,
  refDriver: string,
  compareDrivers: string[],
  mode: 'engineer' | 'driver',
  sessionPart?: string
) =>
  ['ml', 'performanceInsights', sessionId, refDriver, {
    compareDrivers: [...compareDrivers].sort(),
    mode,
    sessionPart
  }] as const,
```

**Key Design Decisions**:

1. **Sorted drivers**: `[...compareDrivers].sort()` ensures cache hits regardless of driver order
2. **Mode inclusion**: Mode is part of the key because responses differ between engineer/driver modes
3. **Hierarchical structure**: `['ml', 'performanceInsights', ...]` allows invalidating all ML queries if needed
4. **Const assertion**: `as const` provides precise TypeScript inference

---

### Step 4: React Query Hook

**File**: `apps/web/lib/hooks/usePerformanceInsightsQuery.ts`

**Rationale**: The hook encapsulates React Query configuration, providing a reusable interface for components.

**Implementation**:

```typescript
export function usePerformanceInsightsQuery({
  sessionId,
  referenceDriver,
  compareDrivers,
  corners,
  mode = 'engineer',
  sessionPart,
}: UsePerformanceInsightsOptions) {
  return useQuery<PerformanceInsightsResponse, Error>({
    queryKey: queryKeys.ml.performanceInsights(
      sessionId, referenceDriver, compareDrivers, mode, sessionPart
    ),
    queryFn: () => fetchPerformanceInsights(
      sessionId, referenceDriver, compareDrivers, corners!, mode, sessionPart
    ),
    enabled: !!sessionId && !!referenceDriver &&
             compareDrivers.length > 0 && !!corners && corners.length > 0,
    staleTime: 5 * 60 * 1000,  // 5 minutes
    gcTime: 30 * 60 * 1000,    // 30 minutes
    retry: 2,
    refetchOnWindowFocus: false,
  })
}
```

**Key Design Decisions**:

1. **Enabled condition**: Prevents queries when required data is missing
2. **Stale time**: 5 minutes is appropriate for F1 session data (doesn't change frequently)
3. **GC time**: 30 minutes cache retention reduces re-fetches during analysis sessions
4. **Retry limit**: 2 retries handles transient failures without excessive waiting
5. **No refetch on focus**: F1 data is static per session, no need to re-fetch

---

### Step 5: Component Library Creation

**Directory**: `apps/web/components/panels/PerformanceInsightsPanel/`

Eight components were created following a bottom-up approach (atomic → composite):

#### 5.1 CornerChip (Atomic)

```typescript
export function CornerChip({ corner, type }: CornerChipProps) {
  const isGain = type === 'gain'
  return (
    <span className={`... ${isGain
      ? 'bg-green-900/30 text-green-400 border-green-700/50'
      : 'bg-red-900/30 text-red-400 border-red-700/50'
    }`}>
      <span className={`h-1.5 w-1.5 rounded-full ${isGain ? 'bg-green-400' : 'bg-red-400'}`} />
      {corner}
    </span>
  )
}
```

**Purpose**: Small badge showing a corner with gain/loss coloring.

#### 5.2 DimensionBar (Atomic)

```typescript
export function DimensionBar({ dimension, percentile, level, delta }: DimensionBarProps) {
  const barWidth = 100 - percentile  // Lower percentile = better = longer bar
  return (
    <div className="flex items-center gap-3">
      <span className="w-24 text-sm text-gray-400">{DIMENSION_LABELS[dimension]}</span>
      <div className="flex-1 h-2 bg-gray-700 rounded-full overflow-hidden">
        <div
          className={`h-full rounded-full transition-all duration-500 ${LEVEL_COLORS[level]}`}
          style={{ width: `${barWidth}%` }}
        />
      </div>
      <span className="w-12 text-right font-mono text-xs">P{Math.round(percentile)}</span>
      {delta !== undefined && (
        <span className={`w-16 text-right font-mono text-xs ${delta <= 0 ? 'text-green-400' : 'text-red-400'}`}>
          {formatDelta(delta)}
        </span>
      )}
    </div>
  )
}
```

**Purpose**: Progress bar visualization for technique dimensions.

**Logic**:
- `barWidth = 100 - percentile` inverts the percentile so that lower (better) percentiles show longer bars
- Level colors: green (strong), yellow (neutral), red (weak)
- Delta colors: green (negative/faster), red (positive/slower)

#### 5.3 ModeToggle (Atomic)

```typescript
export function ModeToggle({ mode, onChange }: ModeToggleProps) {
  return (
    <div className="flex gap-1 rounded-lg bg-gray-800/50 p-1">
      <button
        onClick={() => onChange('engineer')}
        className={mode === 'engineer' ? 'bg-f1red text-white' : 'bg-transparent text-gray-400'}
        aria-pressed={mode === 'engineer'}
      >
        Engineer
      </button>
      <button
        onClick={() => onChange('driver')}
        className={mode === 'driver' ? 'bg-f1red text-white' : 'bg-transparent text-gray-400'}
        aria-pressed={mode === 'driver'}
      >
        Driver
      </button>
    </div>
  )
}
```

**Purpose**: Toggle between Engineer and Driver insight modes.

#### 5.4 FocusAreas (Composite)

```typescript
export function FocusAreas({ gainingCorners, losingCorners, mode }: FocusAreasProps) {
  const gainLabel = mode === 'engineer' ? 'Gaining:' : 'Strengths:'
  const lossLabel = mode === 'engineer' ? 'Losing:' : 'Work On:'
  // Renders CornerChip components for each corner
}
```

**Purpose**: Groups gaining and losing corners with mode-sensitive labels.

#### 5.5 TechniqueProfileDisplay (Composite)

```typescript
export function TechniqueProfileDisplay({ profile, showDeltas = true }: TechniqueProfileDisplayProps) {
  return (
    <div className="space-y-3">
      <h4>Technique Profile</h4>
      <DimensionBar dimension="braking" percentile={profile.braking.percentile} ... />
      <DimensionBar dimension="apex" percentile={profile.apex.percentile} ... />
      <DimensionBar dimension="exit" percentile={profile.exit.percentile} ... />
      <DimensionBar dimension="consistency" percentile={profile.consistency.percentile} />
    </div>
  )
}
```

**Purpose**: Renders all four dimension bars together.

#### 5.6 DriverInsightCard (Composite)

```typescript
export function DriverInsightCard({ result, referenceDriver, mode }: DriverInsightCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)
  return (
    <article style={{ borderLeftColor: getTeamColor(result.driver) }}>
      {/* Header with driver badge and delta */}
      {/* Summary text */}
      {/* TechniqueProfileDisplay */}
      {/* FocusAreas */}
      {/* Expandable details */}
    </article>
  )
}
```

**Purpose**: Complete card for one driver's performance insights.

#### 5.7 PerformanceInsightsPanel (Container)

```typescript
export function PerformanceInsightsPanel({ sessionId, referenceDriver, selectedDrivers, corners, sessionPart }) {
  const [mode, setMode] = useState<InsightMode>('engineer')
  const { data, isLoading, isError, error, refetch } = usePerformanceInsightsQuery({ ... })

  // Render states: idle → loading → error → success
}
```

**Purpose**: Main container orchestrating all sub-components.

---

### Step 6: Integration into QualifyingContent

**File**: `apps/web/app/qualifying/QualifyingContent.tsx`

**Changes**:

```diff
- import { AnalysisInsights } from '@/components/panels/AnalysisInsights'
+ import { PerformanceInsightsPanel } from '@/components/panels/PerformanceInsightsPanel'

- <AnalysisInsights
-   sessionId={sessionId}
-   sectorData={sectorsData ?? []}
-   referenceDriver={referenceDriver}
-   selectedDrivers={selectedDrivers}
- />
+ <PerformanceInsightsPanel
+   sessionId={sessionId}
+   referenceDriver={referenceDriver}
+   selectedDrivers={selectedDrivers}
+   corners={trackData?.corners ?? []}
+   sessionPart={qualifyingPart}
+ />
```

**Rationale**: The new component requires corners (from trackData) and sessionPart for the Phase 6 endpoint. The old AnalysisInsights used sectorData which is no longer needed.

---

## 3. Phase 7 Workflow

### 3.1 User Interaction Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         USER INTERACTION FLOW                               │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  1. USER: Selects drivers in sidebar                                        │
│     ↓                                                                       │
│  2. QualifyingContent: Updates selectedDrivers state                        │
│     ↓                                                                       │
│  3. PerformanceInsightsPanel: Receives new props                            │
│     ↓                                                                       │
│  4. usePerformanceInsightsQuery: Enabled condition becomes true             │
│     ↓                                                                       │
│  5. fetchPerformanceInsights: POST to /analysis/performance-insights              │
│     ↓                                                                       │
│  6. Phase 6 Backend: Orchestrates Phases 2→3→4→5                            │
│     ↓                                                                       │
│  7. Response: PerformanceInsightsResponse returned                          │
│     ↓                                                                       │
│  8. React Query: Caches response, updates hook state                        │
│     ↓                                                                       │
│  9. PerformanceInsightsPanel: Renders DriverInsightCards                    │
│     ↓                                                                       │
│  10. USER: Views insights, toggles mode, expands details                    │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.2 State Machine

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         PANEL STATE MACHINE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│                    ┌──────────────┐                                         │
│                    │    IDLE      │ compareDrivers.length === 0             │
│                    └──────┬───────┘                                         │
│                           │ drivers selected                                │
│                           ▼                                                 │
│                    ┌──────────────┐                                         │
│                    │   LOADING    │ isLoading === true                      │
│                    └──────┬───────┘                                         │
│                           │                                                 │
│              ┌────────────┼────────────┐                                    │
│              │ success    │            │ error                              │
│              ▼            │            ▼                                    │
│       ┌──────────────┐    │     ┌──────────────┐                            │
│       │   SUCCESS    │    │     │    ERROR     │                            │
│       └──────────────┘    │     └──────┬───────┘                            │
│                           │            │ retry                              │
│                           │            ▼                                    │
│                           └───────► LOADING                                 │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

### 3.3 Component Composition

```
PerformanceInsightsPanel
├── ModeToggle
│   ├── Engineer button
│   └── Driver button
│
├── DriverInsightCard (for each result)
│   ├── Header (driver badge + delta)
│   ├── Summary text
│   ├── TechniqueProfileDisplay
│   │   ├── DimensionBar (braking)
│   │   ├── DimensionBar (apex)
│   │   ├── DimensionBar (exit)
│   │   └── DimensionBar (consistency)
│   ├── FocusAreas
│   │   ├── CornerChip (gain) × N
│   │   └── CornerChip (loss) × N
│   └── Expandable details
│
└── Footer (stats)
```

### 3.4 Data Transformation Pipeline

```
Backend Response (snake_case)     →    Frontend Display
═══════════════════════════════        ═══════════════════════════

official_gap: 0.065               →    "+0.065s" (red badge)
technique_profile.braking.percentile: 35  →  ████░░░░░░ P35
technique_profile.braking.raw_value: -0.089  →  -89ms (green)
top_gaining_corners: ["Turn 3"]   →    🟢 Turn 3 (green chip)
top_losing_corners: ["Turn 1"]    →    🔴 Turn 1 (red chip)
insight.summary: "..."            →    Paragraph text
```

---

## 4. Component Architecture

### 4.1 Directory Structure

```
apps/web/components/panels/PerformanceInsightsPanel/
├── index.tsx                     # Barrel export
├── PerformanceInsightsPanel.tsx  # Main container (253 lines)
├── ModeToggle.tsx               # Mode toggle (44 lines)
├── DriverInsightCard.tsx        # Per-driver card (144 lines)
├── TechniqueProfileDisplay.tsx  # Profile bars (44 lines)
├── DimensionBar.tsx             # Single bar (76 lines)
├── FocusAreas.tsx               # Corner groups (56 lines)
└── CornerChip.tsx               # Corner badge (27 lines)
```

### 4.2 Component Responsibilities

| Component | Responsibility | Props |
|-----------|---------------|-------|
| PerformanceInsightsPanel | Data fetching, state management, layout | sessionId, referenceDriver, selectedDrivers, corners, sessionPart |
| ModeToggle | Mode switching UI | mode, onChange |
| DriverInsightCard | Single driver display | result, referenceDriver, mode |
| TechniqueProfileDisplay | Four dimensions | profile, showDeltas |
| DimensionBar | Single dimension | dimension, percentile, level, delta |
| FocusAreas | Corner grouping | gainingCorners, losingCorners, mode |
| CornerChip | Corner badge | corner, type |

### 4.3 Styling Approach

All components use Tailwind CSS following existing patterns:

- **Container**: `card-panel` class with F1-themed gradient
- **Cards**: `rounded-lg border border-f1gray/50 bg-f1dark/60`
- **Team colors**: `getTeamColor(driver)` for driver-specific accents
- **Delta colors**: Green (negative/faster), Red (positive/slower)
- **Level colors**: Green (strong), Yellow (neutral), Red (weak)
- **Loading**: `animate-pulse` with gray skeleton elements

---

## 5. Type System Design

### 5.1 Type Hierarchy

```
PerformanceInsightsResponse
├── session_id: string
├── reference_driver: string
├── mode: string
├── results: DriverPerformanceResult[]
│   ├── driver: string
│   ├── official_gap: number
│   ├── technique_profile?: TechniqueProfile
│   │   ├── braking: TechniqueDimension
│   │   │   ├── level: DimensionLevel
│   │   │   ├── percentile: number
│   │   │   └── raw_value: number
│   │   ├── apex: TechniqueDimension
│   │   ├── exit: TechniqueDimension
│   │   ├── consistency: TechniqueDimension
│   │   ├── top_gaining_corners: string[]
│   │   └── top_losing_corners: string[]
│   └── insight?: NaturalLanguageInsight
│       ├── summary: string
│       ├── confidence_level: string
│       └── dimension_insights: DimensionInsightDetail[]
├── phase_timing: PhaseTimingInfo[]
├── errors: string[]
└── warnings: string[]
```

### 5.2 Union Types

```typescript
export type InsightMode = 'engineer' | 'driver'
export type DimensionType = 'braking' | 'apex' | 'exit' | 'consistency'
export type DimensionLevel = 'strong' | 'neutral' | 'weak'
export type CornerCause = 'braking' | 'apex' | 'exit' | 'multiple' | 'unknown'
export type CornerConfidence = 'high' | 'medium' | 'low'
```

---

## 6. Data Flow

### 6.1 Props Flow

```
QualifyingContent
    │
    ├── sessionId ─────────────────┐
    ├── referenceDriver ───────────┤
    ├── selectedDrivers ───────────┤
    ├── trackData?.corners ────────┤
    └── qualifyingPart ────────────┤
                                   ▼
                    PerformanceInsightsPanel
                           │
                           ├── mode (local state)
                           ├── usePerformanceInsightsQuery
                           │         │
                           │         ▼
                           │   fetchPerformanceInsights
                           │         │
                           │         ▼
                           │   /analysis/performance-insights
                           │         │
                           │         ▼
                           │   PerformanceInsightsResponse
                           │
                           ▼
                    DriverInsightCard (per result)
                           │
                           ├── result.technique_profile
                           │         │
                           │         ▼
                           │   TechniqueProfileDisplay
                           │         │
                           │         ▼
                           │   DimensionBar × 4
                           │
                           └── result.technique_profile.top_*_corners
                                     │
                                     ▼
                               FocusAreas
                                     │
                                     ▼
                               CornerChip × N
```

### 6.2 Cache Strategy

```
Query Key: ['ml', 'performanceInsights', sessionId, refDriver, { compareDrivers, mode, sessionPart }]

Cache Behavior:
┌─────────────────────────────────────────────────────────────────────────────┐
│  Same session + same drivers + same mode → Cache HIT (instant)              │
│  Same session + same drivers + diff mode → Cache MISS (re-fetch)            │
│  Same session + diff drivers            → Cache MISS (re-fetch)             │
│  Different session                       → Cache MISS (re-fetch)            │
└─────────────────────────────────────────────────────────────────────────────┘

Timing:
- staleTime: 5 minutes (data considered fresh)
- gcTime: 30 minutes (cache retained)
- refetchOnWindowFocus: false (no auto-refresh)
```

---

## 7. Verification Results

### 7.1 TypeScript Compilation

```bash
$ npx tsc --noEmit
# No errors - compilation successful
```

### 7.2 Next.js Build

```bash
$ npm run build
✓ Compiled successfully
✓ Generating static pages (8/8)
# Build successful (Windows symlink warning is unrelated to code)
```

### 7.3 Files Created/Modified

| File | Action | Lines |
|------|--------|-------|
| `packages/models/src/types.ts` | Modified | +120 lines |
| `apps/web/lib/api.ts` | Modified | +42 lines |
| `apps/web/lib/hooks/queryKeys.ts` | Modified | +8 lines |
| `apps/web/lib/hooks/usePerformanceInsightsQuery.ts` | Created | 68 lines |
| `apps/web/lib/hooks/index.ts` | Modified | +1 line |
| `apps/web/components/panels/PerformanceInsightsPanel/index.tsx` | Created | 8 lines |
| `apps/web/components/panels/PerformanceInsightsPanel/PerformanceInsightsPanel.tsx` | Created | 253 lines |
| `apps/web/components/panels/PerformanceInsightsPanel/ModeToggle.tsx` | Created | 44 lines |
| `apps/web/components/panels/PerformanceInsightsPanel/DriverInsightCard.tsx` | Created | 144 lines |
| `apps/web/components/panels/PerformanceInsightsPanel/TechniqueProfileDisplay.tsx` | Created | 44 lines |
| `apps/web/components/panels/PerformanceInsightsPanel/DimensionBar.tsx` | Created | 76 lines |
| `apps/web/components/panels/PerformanceInsightsPanel/FocusAreas.tsx` | Created | 56 lines |
| `apps/web/components/panels/PerformanceInsightsPanel/CornerChip.tsx` | Created | 27 lines |
| `apps/web/app/qualifying/QualifyingContent.tsx` | Modified | 2 lines changed |

### 7.4 Success Criteria Checklist

- [x] TypeScript types added and exported
- [x] API function implemented
- [x] React Query hook created
- [x] Query keys updated
- [x] All sub-components implemented
- [x] Main panel component assembled
- [x] Integration into QualifyingContent complete
- [x] TypeScript compilation passes
- [x] Next.js build successful
- [x] Follows existing codebase patterns
- [x] Proper error handling
- [x] Loading states implemented
- [x] Mode toggle functional

---

## Conclusion

Phase 7 successfully transforms the raw analytical data from Phases 2-6 into a rich, interactive user interface. The implementation:

1. **Maintains type safety** across the frontend-backend boundary
2. **Follows existing patterns** for consistency with the codebase
3. **Provides meaningful insights** replacing the legacy "similarity score" display
4. **Supports dual perspectives** for engineers and drivers
5. **Handles all states** (idle, loading, error, success) gracefully

The PerformanceInsightsPanel is now ready for end-to-end testing in Phase 8.
