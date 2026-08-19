# ApexView

A comprehensive Formula 1 telemetry and engineering analysis platform built with Next.js and FastAPI, featuring data-driven performance insights and detailed track intelligence.

**Season:** 2025

## Architecture

- **Frontend**: Next.js 14+ with App Router, TypeScript, Tailwind CSS, and React Query
- **Backend API**: FastAPI with FastF1 integration for telemetry and session data
- **Analysis Service**: FastAPI microservice for performance analysis, corner breakdown, technique profiling, and natural language insights
- **Packages**: Shared UI components and type definitions
- **Monorepo**: Managed with pnpm workspaces

## Project Structure

```
f1-engineering-app/
├── apps/
│   ├── web/                    # Next.js frontend
│   │   ├── app/                # App Router pages
│   │   ├── components/         # React components
│   │   │   ├── panels/         # Analysis panels (PerformanceInsights, CornerBreakdown, etc.)
│   │   │   ├── race/           # Race panels (RacePaceBoxPlot, TyreDegradation, PitStop, etc.)
│   │   │   ├── practice/       # Practice panels (LongRun, ShortRun, Sector, Progression)
│   │   │   └── track/          # Track Intelligence components
│   │   ├── lib/                # API clients, hooks, utilities
│   │   └── data/               # Track intelligence data (24 circuit analyses)
│   ├── api/                    # FastAPI backend (main API)
│   │   └── app/
│   │       └── services/       # Telemetry services, FastF1 client
│   └── analysis_service/        # Analysis microservice
│       ├── core/               # Logging, circuit configs (24 circuits)
│       ├── models/             # Pydantic schemas
│       ├── services/           # Analysis modules (Phases 2-6)
│       └── tests/              # 271 tests (8 active files)
├── packages/
│   ├── ui/                     # Shared React components
│   └── models/                 # Shared TypeScript types
├── data/                       # Cache and static data
├── docs/                       # Documentation
└── scripts/                    # Validation and utility scripts
```

## Features Overview

### Track Intelligence (24/24 Circuits Complete)

Comprehensive circuit analysis system covering all 24 circuits on the 2025 F1 calendar. Each circuit features an 11-section analytical framework providing engineering-grade insights verified against official Formula 1 sources. All 24 circuits include validated corner names in their track data files.

#### 11-Section Analysis Framework

| Section | Description |
|---------|-------------|
| **Circuit Overview** | Track length, corners, lap records, DRS zones, and key characteristics |
| **Pirelli Characteristics** | Tyre compound nominations, degradation profiles, and grip evolution |
| **Sector Breakdown** | Detailed analysis of each sector's demands and key corners |
| **Benchmark Lap Analysis** | Sector time targets and optimal lap structure |
| **Strategic Insights** | Pit stop windows, undercut/overcut potential, and race strategy |
| **Aerodynamic Philosophy** | Downforce levels, wing configurations, and efficiency requirements |
| **Weather Profile** | Historical conditions, temperature impacts, and rain probability |
| **Historical Context** | Notable races, records, and circuit evolution |
| **Engineering Analysis** | Technical demands on brakes, power unit, and mechanical components |
| **Defining Characteristics** | Key features that make each circuit unique |

#### Complete 2025 Calendar Coverage

| Region | Circuits |
|--------|----------|
| **Europe** | Monaco, Spain (Barcelona), Great Britain (Silverstone), Belgium (Spa), Netherlands (Zandvoort), Italy (Monza), Hungary (Hungaroring), Austria (Red Bull Ring), Emilia Romagna (Imola) |
| **Middle East** | Bahrain, Saudi Arabia (Jeddah), Qatar (Lusail), Abu Dhabi (Yas Marina) |
| **Americas** | United States (COTA), Las Vegas, Mexico (Rodriguez), Brazil (Interlagos), Canada (Gilles Villeneuve), Miami |
| **Asia-Pacific** | Japan (Suzuka), Singapore (Marina Bay), Australia (Albert Park), China (Shanghai) |

#### Data Architecture

Track Intelligence uses a hybrid architecture combining editorial content with real-time geometry data:

- **Frontend Editorial Content**: Circuit descriptions, strategic insights, historical notes, Pirelli characteristics, aerodynamic philosophy
- **Backend Geometry Data**: Corner positions, sector boundaries, track coordinates via FastF1 API

```typescript
interface TrackIntelligence {
  circuitOverview: CircuitOverview;
  pirelliCharacteristics: PirelliCharacteristics;
  sectorBreakdown: SectorBreakdown[];
  benchmarkLap: BenchmarkLap;
  strategicInsights: StrategicInsights;
  aerodynamicPhilosophy: AerodynamicPhilosophy;
  weatherProfile: WeatherProfile;
  historicalContext: HistoricalContext;
  engineeringAnalysis: EngineeringAnalysis;
  definingCharacteristics: DefiningCharacteristic[];
}
```

#### Implementation Principles

- All data verified against official Formula 1 sources
- Defining characteristics condensed to 60-80 characters for layout compatibility
- Consistent TypeScript interfaces across all circuits
- Template-based structure ensuring uniform quality

---

### Data-Driven Performance Analysis (Telemetry Analysis Pipeline)

The Analysis service implements an 8-phase analysis pipeline for qualifying telemetry analysis, replacing the original cosine similarity system that produced meaningless 99.9% similarity scores.

#### Phase Architecture

| Phase | Module | Purpose |
|-------|--------|---------|
| 1 | `core/logging_config.py` | Structured logging, lap filtering, session part awareness |
| 2 | `services/delta_analysis.py` | Scaled delta calculation matching official F1 timing |
| 3 | `services/corner_analysis.py` | Corner-by-corner time gain/loss attribution |
| 4 | `services/technique_profiling.py` | Session-relative driver technique classification |
| 5 | `services/insight_generation.py` | Template-based natural language insights (anti-hallucination) |
| 6 | `services/performance_orchestrator.py` | Unified BFF endpoint chaining Phases 2-5 |
| 7 | Frontend components | PerformanceInsightsPanel, CornerBreakdownPanel |
| 8 | Testing & validation | 271 tests, multi-circuit validation |

#### Analysis Service Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/health` | GET | Health check |
| `/lap-similarity` | POST | Cosine similarity between laps |
| `/driver-style-clustering` | POST | PCA + KMeans driver clustering |
| `/analysis/scaled-delta` | POST | Phase 2: Scaled delta analysis |
| `/analysis/corner-analysis` | POST | Phase 3: Corner breakdown |
| `/analysis/technique-profile` | POST | Phase 4: Technique profiling |
| `/analysis/generate-insight` | POST | Phase 5: Natural language insights |
| `/analysis/performance-insights` | POST | Phase 6: Unified orchestrator (BFF) |

#### Confidence Scoring System

Corner analysis assigns confidence per corner based on how closely the two brake detection methods (boolean brake signal and deceleration refinement) agreed:
- **HIGH**: Boolean brake and deceleration refinement aligned within 20 metres
- **MEDIUM**: Aligned within 40 metres
- **LOW**: Diverged beyond 40 metres, zone boundaries approximate

Confidence propagates through the pipeline:
- Phase 4: Weights corner contributions (HIGH=1.0, MEDIUM=0.7, LOW=0.3)
- Phase 5: Determines hedging language ("Analysis shows" vs "Limited data indicates")
- Phase 6: Aggregates into overall result reliability indicator

#### Circuit-Specific Corner Analysis Tuning

The Analysis service includes per-circuit configurations for all 24 circuits:

```python
CIRCUIT_CONFIGS = {
    "monaco": CornerAnalysisConfig(
        braking_decel_threshold=-4.0,  # Lighter braking, lower speeds
        decel_smoothing_window=7,       # Bumpy surface
    ),
    "monza": CornerAnalysisConfig(
        braking_decel_threshold=-6.0,  # Heavy braking from high speeds
        apex_search_margin=60.0,        # Larger margins for chicanes
    ),
    # ... configurations for all 24 circuits
}
```

---

### Qualifying Analysis

- Multi-driver lap comparison with interactive delta charts
- Scaled delta analysis matching official F1 timing
- Corner-by-corner time gain/loss breakdown with cause attribution
- Technique profiling across five dimensions (braking, apex, exit, consistency, straight-line)
- Natural language performance insights in Engineer and Driver modes
- Session part filtering (Q1/Q2/Q3)

### Race Analysis

- Race pace distribution box plots with fuel correction toggle and team-coloured styling
- Tyre degradation analysis with fuel-adjusted scatter plots and server-side linear regression
- Pit stop analysis with three views: by team, by driver, and gap-to-fastest
- Team performance quadrant with aerodynamic setup philosophy (SpeedST vs mean speed)
- DNF status handling with finishing position resolution
- Per-compound outlier detection for accurate lap classification

### Practice Sessions

- Long run pace comparison with violin charts, stint summary cards, and compound-coloured dots
- Short run / best lap ranking with session-best verification indicators
- Sector analysis with sector times table, purple sector highlighting, and speed trap bar chart
- SVG track maps with colour-coded sector overlays for all 24 circuits
- Cross-session progression showing gap-to-session-best across FP1/FP2/FP3
- Fuel correction toggle with circuit-specific correction factors from Track Intelligence

### Transparency & Attribution

- Dedicated `/transparency` page covering project disclaimer, data sources, analysis methodology, privacy, attribution, and intellectual property
- Analysis methodology section with verified thresholds and algorithm descriptions from production code
- Linked from footer across all pages
- Built as a Server Component — static text only, no client-side JavaScript

---

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+ (3.11+ recommended for Analysis service)
- pnpm 8+
- Docker (optional, for containerized deployment)

### Installation

```bash
# Install dependencies
pnpm install

# Start development servers
pnpm dev
```

### Individual Services

```bash
# Frontend only (http://localhost:3000)
pnpm dev:web

# Backend API only (http://localhost:8000)
pnpm dev:api

# Analysis service (http://localhost:8501)
cd apps/analysis_service && uvicorn main:app --reload --port 8501
```

### Docker Deployment

```bash
# Start all services with Docker Compose
docker-compose up -d

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

### Running Tests

```bash
# API tests (313 tests)
cd apps/api
python -m pytest tests/ -v

# Analysis service tests (271 tests)
cd apps/analysis_service
python -m pytest tests/ -v

# Frontend tests
pnpm test
```

---

## Frontend Components

### Analysis Panels

| Component | Purpose |
|-----------|---------|
| `PerformanceInsightsPanel` | Unified qualifying performance analysis with technique profiles and insights |
| `DriverInsightCard` | Individual driver technique breakdown with dimension bars |
| `CornerBreakdownPanel` | Corner-by-corner delta table with cause attribution |
| `ScalingMetadataPanel` | Delta confidence and scaling factor indicators |
| `TelemetryChart` | Speed/throttle/brake trace visualisation |
| `DeltaChart` | Cumulative time delta visualisation |
| `RacePaceBoxPlot` | Race pace distribution with fuel correction toggle |
| `TyreDegradationPanel` | Fuel-adjusted tyre wear scatter plots with linear regression |
| `PitStopPanel` | Pit stop analysis with by-team, by-driver, gap-to-fastest views |
| `TeamPerformancePanel` | Aerodynamic setup quadrant chart (SpeedST vs mean speed) |
| `LongRunPacePanel` | Practice long run violin charts with stint summary cards |
| `ShortRunPanel` | Practice best lap ranking with verification indicators |
| `SectorAnalysisPanel` | Practice sector times table + speed trap bar chart |
| `SectorMapPanel` | SVG track overlay with colour-coded sector highlighting |
| `SessionProgressionPanel` | Cross-session pace progression (connected dot plot) |

### Track Intelligence Components

| Component | Purpose |
|-----------|---------|
| `TrackIntelligencePanel` | Main container for circuit analysis |
| `CircuitOverview` | Track statistics and key information |
| `SectorBreakdown` | Sector-by-sector analysis display |
| `StrategicInsights` | Race strategy information |
| `TechnicalInsights` | Engineering and aerodynamic analysis |

### React Query Hooks

| Hook | Purpose |
|------|---------|
| `usePerformanceInsightsQuery` | Fetches unified qualifying performance data |
| `useAnalysisInsightsQuery` | Fetches combined analysis data (delta, corners, technique, insights) |
| `useTelemetryQuery` | Fetches telemetry traces |
| `useSectorsQuery` | Fetches sector times |
| `useTrackIntelligence` | Fetches track intelligence data |
| `useRacePaceQuery` | Fetches race pace box plot data |
| `useTyreDegradationQuery` | Fetches tyre degradation regression data |
| `usePitStopQuery` | Fetches pit stop durations and consistency |
| `useTeamPerformanceQuery` | Fetches team performance quadrant data |
| `usePracticeSessionsQuery` | Fetches available practice sessions |
| `useLongRunQuery` | Fetches long run stint data |
| `useShortRunQuery` | Fetches short run best laps |
| `useSectorAnalysisQuery` | Fetches sector analysis data |
| `useCircuitSVGQuery` | Fetches track SVG for map rendering |
| `useSessionProgressionQuery` | Fetches cross-session progression data |

---

## Known Limitations

### Corner Analysis Reliability

Corner analysis reliability varies by circuit due to telemetry-timing alignment:
- Works well when scale factor is between 0.5x and 2.0x
- May show unreliable results when scale factor exceeds 2.0x or is negative
- Street circuits with clustered corners show higher variability

The Scaled Delta Analysis panel indicates reliability through confidence scores. Results with confidence below 50% should be interpreted with caution.

---

## Documentation

See the `docs/` directory for detailed documentation:

### Architecture & Features
- `ARCHITECTURE_OVERVIEW.md` - System architecture
- `FEATURES.md` - Feature specifications
- `ANALYSIS_SERVICE_README.md` - Analysis service documentation

### Phase Implementation
- `corner-analysis-implementation.md` - Phase 3 implementation details
- `CORNER-ANALYSIS-V2-IMPLEMENTATION.md` - V2 deceleration-based algorithm
- `CORNER-ANALYSIS-ACCURACY-ENHANCEMENT.md` - Accuracy improvements
- `PHASE3-CORNER-ANALYSIS-REPORT.md` - Phase 3 validation report
- `PHASE3-V2-ENHANCEMENT-VALIDATION.md` - V2 validation results
- `PHASE4-TECHNIQUE-PROFILING.md` - Phase 4 documentation
- `PHASE5-NATURAL-LANGUAGE-INSIGHTS.md` - Phase 5 documentation
- `PHASE6-PERFORMANCE-ORCHESTRATOR.md` - Phase 6 documentation
- `PHASE7-FRONTEND-IMPLEMENTATION.md` - Phase 7 documentation

### Season Updates
- `SEASON_2025_UPDATES.md` - 2025 driver lineup and calendar
- `2025_DATA_VERIFICATION.md` - Data verification for 2025 season

---

## Tech Stack

### Frontend
- Next.js 14+ (App Router)
- TypeScript
- Tailwind CSS
- React Query (TanStack Query)
- Plotly.js (data visualisation via plotly.js-cartesian-dist-min)

### Backend
- FastAPI
- FastF1 (F1 telemetry library)
- Pydantic (schema validation)
- httpx (async HTTP client)

### Analysis Service
- FastAPI
- NumPy / SciPy
- scikit-learn (clustering)
- Custom analysis algorithms

### Infrastructure
- Docker / Docker Compose
- pnpm workspaces (monorepo)
