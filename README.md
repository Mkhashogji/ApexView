# F1 Engineering App

A comprehensive Formula 1 telemetry and analysis platform built with Next.js and FastAPI.

**Season:** 2025 (Updated November 7, 2025 - Current through Round 21)

## Architecture

- **Frontend**: Next.js 14+ with App Router, TypeScript, and Tailwind CSS
- **Backend**: FastAPI with FastF1 integration
- **Packages**: Shared UI components and type definitions
- **Monorepo**: Managed with pnpm workspaces

## Project Structure

```
f1-engineering-app/
├── apps/
│   ├── web/          # Next.js frontend
│   └── api/          # FastAPI backend
├── packages/
│   ├── ui/           # Shared React components
│   └── models/       # Shared types and utilities
├── data/             # Cache and static data
└── docs/             # Documentation
```

## Getting Started

### Prerequisites

- Node.js 18+
- Python 3.10+
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

# Backend only
pnpm dev:api
```

## Features

- **Qualifying Analysis**: Multi-driver lap comparison with delta charts
- **Race Analysis**: Stint management, tyre degradation, pace evolution
- **Practice Sessions**: Telemetry consistency and setup insights
- **Track Information**: Circuit layouts, sectors, DRS zones, elevation profiles
- **Sprint Weekend Support**: Traditional vs Sprint session handling

## Documentation

See the `docs/` directory for detailed documentation on:
- Vision and features
- Session models (traditional vs sprint)
- Telemetry specifications
- Page-specific requirements
- ML features
- **2025 Season Updates** - See `docs/SEASON_2025_UPDATES.md` for current driver lineup and calendar

## License

© 2025 F1 Engineering App Project.
All rights reserved for educational and research use.