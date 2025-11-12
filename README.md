# F1 Engineering App

A comprehensive Formula 1 telemetry and analysis platform built with Next.js and FastAPI.

**Season:** 2025 (Updated November 7, 2025 - Current through Round 21)

## Architecture

- **Frontend**: Next.js 14+ with App Router, TypeScript, and Tailwind CSS
- **Backend API**: FastAPI with FastF1 integration for telemetry and session data
- **ML Service**: FastAPI microservice for lap similarity analysis and driver clustering
- **Packages**: Shared UI components and type definitions
- **Monorepo**: Managed with pnpm workspaces

## Project Structure

```
f1-engineering-app/
├── apps/
│   ├── web/          # Next.js frontend
│   ├── api/          # FastAPI backend (main API)
│   └── ml_service/   # ML microservice
├── packages/
│   ├── ui/           # Shared React components
│   └── models/       # Shared types and utilities
├── data/             # Cache and static data
└── docs/             # Documentation
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+ (3.11+ for ML service)
- pnpm 8+

### Installation

```bash
# Install dependencies
pnpm install

# Start development servers
pnpm dev
```

### Individual Services

```bash
# Frontend only
pnpm dev:web

# Backend API only
pnpm dev:api

# ML service (requires Python 3.11+)
cd apps/ml_service && uvicorn main:app --reload --port 8501
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

## Features

- **Qualifying Analysis**: Multi-driver lap comparison with delta charts
- **Race Analysis**: Stint management, tyre degradation, pace evolution
- **Practice Sessions**: Telemetry consistency and setup insights
- **Track Information**: Circuit layouts, sectors, DRS zones, elevation profiles
- **Sprint Weekend Support**: Traditional vs Sprint session handling
- **ML-Powered Insights**: Lap similarity analysis and driver clustering algorithms

## Documentation

See the `docs/` directory for detailed documentation on:
- Vision and features
- Architecture overview
- Session models (traditional vs sprint)
- Telemetry specifications
- Page-specific requirements
- ML service and features
- CI/CD pipeline
- **2025 Season Updates** - See `docs/SEASON_2025_UPDATES.md` for current driver lineup and calendar

## License

© 2025 F1 Engineering App Project.
All rights reserved for educational and research use.