# Project Tree Structure

This file documents the complete directory structure of the F1 Engineering App.

```
f1-engineering-app/

├─ apps/
│  ├─ web/                        # Next.js App Router (TypeScript, Tailwind)
│  │  ├─ app/
│  │  │  ├─ layout.tsx            # Root layout with navigation
│  │  │  ├─ page.tsx              # Home (weekend overview)
│  │  │  ├─ globals.css           # Global styles
│  │  │  ├─ qualifying/
│  │  │  │  └─ page.tsx           # Multi-driver lap compare + delta charts
│  │  │  ├─ race/
│  │  │  │  └─ page.tsx           # Stints, tyre degradation, pace evolution
│  │  │  ├─ practice/
│  │  │  │  └─ page.tsx           # FP telemetry consistency & setup hints
│  │  │  ├─ track/
│  │  │  │  └─ [round]/
│  │  │  │     └─ page.tsx        # Circuit layout, sectors, DRS, elevation
│  │  │  └─ api/
│  │  │     └─ sessions/
│  │  │        └─ route.ts        # Next.js server routes (thin proxy)
│  │  ├─ components/
│  │  │  ├─ filters/
│  │  │  │  ├─ DriverMultiSelect.tsx
│  │  │  │  ├─ SessionSwitch.tsx  # Traditional vs Sprint tabs
│  │  │  │  └─ CompoundPicker.tsx
│  │  │  ├─ charts/
│  │  │  │  ├─ TelemetryLine.tsx  # Plotly speed/throttle/brake vs distance
│  │  │  │  ├─ DeltaPlot.tsx      # Reference lap vs others
│  │  │  │  ├─ StintPace.tsx
│  │  │  │  └─ TyreDegradation.tsx
│  │  │  ├─ panels/
│  │  │  │  ├─ SectorCards.tsx
│  │  │  │  ├─ AnalysisInsights.tsx
│  │  │  │  └─ SessionSummary.tsx
│  │  │  └─ track/
│  │  │     ├─ TrackMap.tsx       # SVG/Three.js with sectors & DRS
│  │  │     └─ ElevationMiniMap.tsx
│  │  ├─ lib/
│  │  │  ├─ api.ts                # fetch helpers (talk to FastAPI)
│  │  │  ├─ formatters.ts         # Time/speed/distance formatting
│  │  │  └─ constants.ts          # Color tokens, driver palettes
│  │  ├─ tests/
│  │  │  └─ example.test.ts       # Vitest tests
│  │  ├─ package.json
│  │  ├─ tsconfig.json
│  │  ├─ next.config.js
│  │  ├─ tailwind.config.js
│  │  └─ postcss.config.js
│  │
│  └─ api/                        # FastAPI (Python)
│     ├─ app/
│     │  ├─ main.py               # FastAPI app entry point
│     │  ├─ routes/
│     │  │  ├─ sessions.py        # /sessions?season&round (trad/sprint model)
│     │  │  ├─ laps.py            # /laps?session&drivers
│     │  │  ├─ telemetry.py       # /telemetry?session&drivers
│     │  │  └─ track.py           # /track/{round}
│     │  ├─ core/
│     │  │  ├─ config.py          # Cache dirs, season defaults
│     │  │  └─ cache.py           # FastF1 cache management
│     │  ├─ services/
│     │  │  ├─ fastf1_client.py   # FastF1 access + mapping to DTOs
│     │  │  └─ transforms.py      # Delta, sector aggregation
│     │  ├─ models/
│     │  │  ├─ dto.py             # Pydantic response models (mirror TS types)
│     │  │  └─ session_model.py   # Sprint/traditional JSON schema
│     │  └─ tests/
│     │     └─ test_api.py        # Pytest tests
│     ├─ pyproject.toml           # Python dependencies
│     ├─ .env.example             # Environment variables template
│     └─ README.md                # API documentation
│
├─ packages/
│  ├─ ui/                         # Shared React components (pure UI)
│  │  ├─ charts/
│  │  │  ├─ PlotlyLineChart.tsx   # Thin Plotly wrapper
│  │  │  └─ RechartsWrapper.tsx   # Thin Recharts wrapper
│  │  ├─ primitives/
│  │  │  ├─ Card.tsx
│  │  │  ├─ Badge.tsx
│  │  │  └─ Button.tsx
│  │  ├─ index.ts                 # Barrel exports
│  │  ├─ package.json
│  │  └─ tsconfig.json
│  │
│  └─ models/                     # Shared types & small ML utils
│     ├─ src/
│     │  ├─ types.ts              # TS types: Session, Lap, TelemetryPoint, etc.
│     │  ├─ lapSimilarity.ts      # Lightweight ML heuristic
│     │  └─ index.ts              # Barrel exports
│     ├─ python/                  # Mirrored pydantic models
│     │  ├─ __init__.py
│     │  └─ types.py
│     ├─ package.json
│     └─ tsconfig.json
│
├─ data/
│  ├─ cache/
│  │  └─ .gitkeep                 # FastF1 on-disk cache
│  └─ static/
│     ├─ circuits/
│     │  └─ example-circuit.json  # Circuit JSON (DRS, corners, elevation)
│     └─ README.md                # Data structure documentation
│
├─ docs/
│  ├─ VISION.md                   # Project vision and goals
│  ├─ THEME.md                    # Design system and colors
│  ├─ FEATURES.md                 # Feature specifications
│  ├─ SESSIONS_MODEL.md           # Sprint vs traditional (JSON schema)
│  ├─ TELEMETRY_SPECS.md          # Telemetry data structure and API
│  ├─ QUALI_PAGE_SPEC.md          # Qualifying page detailed spec
│  ├─ RACE_PAGE_SPEC.md           # Race page detailed spec
│  ├─ TRACK_PAGE_SPEC.md          # Track page detailed spec
│  ├─ ML_MIN_FEATURES.md          # Minimal ML features implementation
│  └─ TREE.md                     # THIS FILE (project structure)
│
├─ .cursor/
│  └─ rules/
│     ├─ frontend.md              # Frontend development guidelines
│     ├─ backend.md               # Backend development guidelines
│     └─ data.md                  # Data handling and FastF1 integration
│
├─ package.json                   # Root package.json (pnpm workspaces)
├─ .gitignore                     # Git ignore patterns
└─ README.md                      # Project README

```

## Directory Purposes

### `/apps/web` - Next.js Frontend
- **Purpose**: User-facing web application
- **Tech**: Next.js 14, React 18, TypeScript, Tailwind CSS
- **Pages**: Home, Qualifying, Race, Practice, Track
- **Components**: Reusable UI components for filters, charts, panels
- **Lib**: Utility functions, API clients, formatters

### `/apps/api` - FastAPI Backend
- **Purpose**: Data processing and API endpoints
- **Tech**: FastAPI, Python 3.10+, FastF1, Pydantic
- **Routes**: REST API endpoints for sessions, laps, telemetry, tracks
- **Services**: Business logic and FastF1 integration
- **Models**: Data transfer objects (DTOs) and schemas

### `/packages/ui` - Shared UI Components
- **Purpose**: Reusable pure UI components
- **Tech**: React, TypeScript
- **Contents**: Charts, buttons, cards, badges
- **Usage**: Imported by web app

### `/packages/models` - Shared Type Definitions
- **Purpose**: Type safety across frontend and backend
- **Tech**: TypeScript (TS), Python (Pydantic)
- **Contents**: Session, Lap, Telemetry types
- **ML**: Lightweight similarity and analysis utilities

### `/data` - Static and Cache Data
- **Purpose**: Store FastF1 cache and static circuit data
- **Cache**: Downloaded session data from FastF1
- **Static**: Circuit layouts, DRS zones, elevation data

### `/docs` - Documentation
- **Purpose**: Comprehensive project documentation
- **Contents**: Vision, features, specs, API docs
- **Audience**: Developers, contributors, stakeholders

### `/.cursor/rules` - Development Guidelines
- **Purpose**: AI assistant rules and coding standards
- **Frontend**: React/Next.js best practices
- **Backend**: FastAPI and Python patterns
- **Data**: FastF1 usage and data handling

## Key Files

### Configuration Files
- **`package.json`**: Root workspace configuration
- **`pyproject.toml`**: Python project dependencies
- **`tsconfig.json`**: TypeScript compiler options
- **`next.config.js`**: Next.js configuration
- **`tailwind.config.js`**: Tailwind CSS theme

### Entry Points
- **`apps/web/app/layout.tsx`**: Root React layout
- **`apps/api/app/main.py`**: FastAPI application
- **`packages/ui/index.ts`**: UI component exports
- **`packages/models/src/index.ts`**: Type exports

## Workspace Structure

This is a monorepo managed by **pnpm workspaces**.

### Workspace Configuration
```json
{
  "workspaces": [
    "apps/*",
    "packages/*"
  ]
}
```

### Package References
```json
{
  "dependencies": {
    "@ui/charts": "workspace:*",
    "@models/types": "workspace:*"
  }
}
```

## Build Outputs (Not in Git)

These directories are generated during build and ignored by git:

```
├─ apps/web/.next/               # Next.js build output
├─ apps/web/out/                 # Static export
├─ apps/api/__pycache__/         # Python bytecode
├─ packages/*/dist/              # Package builds
├─ node_modules/                 # Node dependencies
├─ data/cache/*                  # FastF1 cache files
└─ *.log                         # Log files
```

## Scripts

### Root Level
- `pnpm dev` - Start all services in parallel
- `pnpm build` - Build all packages
- `pnpm test` - Run all tests
- `pnpm lint` - Lint all packages

### Web App
- `pnpm --filter web dev` - Start Next.js dev server
- `pnpm --filter web build` - Build for production
- `pnpm --filter web test` - Run Vitest tests

### API
- `uvicorn app.main:app --reload` - Start FastAPI dev server
- `pytest` - Run pytest tests

## Environment Variables

### Web App (`.env.local`)
```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

### API (`.env`)
```bash
CACHE_DIR=../../data/cache
DEFAULT_SEASON=2024
```

## Development Workflow

1. **Start Backend**: `cd apps/api && uvicorn app.main:app --reload`
2. **Start Frontend**: `cd apps/web && pnpm dev`
3. **Access App**: http://localhost:3000
4. **Access API Docs**: http://localhost:8000/docs

## Adding New Files

### New Page
Create in `apps/web/app/{page-name}/page.tsx`

### New API Route
Create in `apps/api/app/routes/{route-name}.py`

### New Component
Create in `apps/web/components/{category}/{ComponentName}.tsx`

### New Shared Type
Add to `packages/models/src/types.ts`

### New Circuit Data
Add JSON to `data/static/circuits/{circuit-name}.json`

## Notes

- All TypeScript files use `.tsx` or `.ts` extensions
- All Python files follow snake_case naming
- React components use PascalCase
- Utilities and hooks use camelCase
- Keep components focused and single-purpose
- Document complex logic and algorithms
- Write tests for critical functionality

