# Run Book - F1 Engineering App

## Overview

This guide will help you set up and run the F1 Engineering App, featuring qualifying analysis, ML-powered insights, and microservices architecture.

## Architecture

The application consists of three microservices:
- **Web** (Next.js) - Frontend on port 3000
- **API** (FastAPI) - Backend gateway on port 8000
- **ML** (FastAPI) - ML service on port 8501

## Prerequisites

### Option 1: Docker (Recommended)
- **Docker** 20+
- **Docker Compose** 2.0+

### Option 2: Local Development
- **Node.js** 18+ (for frontend)
- **Python** 3.11+ (for backend & ML)
- **pnpm** 9+ (package manager)
- Git

## Quick Start with Docker

The fastest way to run the entire stack:

```bash
# Build and start all services
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop services
docker-compose down
```

**Services will be available at:**
- Frontend: http://localhost:3000
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- ML Service: http://localhost:8501
- ML Docs: http://localhost:8501/docs

### Docker Services

```bash
# Start only specific services
docker-compose up web api

# Rebuild a single service
docker-compose build api
docker-compose up api

# View service logs
docker-compose logs api
docker-compose logs -f ml

# Execute commands in running containers
docker-compose exec api python -c "print('Hello')"
docker-compose exec web pnpm --version
```

## Local Development Setup

### Installation

### 1. Clone and Install Dependencies

```bash
# Navigate to project root
cd f1-engineering-app

# Install frontend dependencies
pnpm install

# Install backend dependencies
cd apps/api
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
cd ../..

# Install ML service dependencies
cd apps/ml_service
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -e ".[dev]"
cd ../..
```

### 2. Environment Configuration

#### Backend (.env)

Create `apps/api/.env` (copy from `env.template`):

```bash
# Feature Flags
LIVE_DATA=false              # Set to true to use FastF1 live data

# FastF1 Configuration
CACHE_DIR=../../data/cache
DEFAULT_SEASON=2024
DOWNSAMPLE_THRESHOLD=5000

# API Configuration
API_TITLE=F1 Engineering API
API_VERSION=0.1.0
CORS_ORIGINS=http://localhost:3000
```

#### Frontend (.env.local)

Create `apps/web/.env.local`:

```bash
NEXT_PUBLIC_API_URL=http://localhost:8000
```

## Running the Application

### Option 1: Run All Services (Recommended)

From project root:

```bash
# Start both frontend and backend in parallel
pnpm dev
```

This will start:
- Frontend: `http://localhost:3000`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/docs`

**Note:** ML service must be started separately in local dev (see below)

### Option 2: Run Services Individually

#### Backend Only

```bash
cd apps/api
# Activate venv if not already active
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start FastAPI server
uvicorn app.main:app --reload

# Or
python -m app.main
```

Backend will be available at `http://localhost:8000`

#### Frontend Only

```bash
pnpm dev:web
```

Frontend will be available at `http://localhost:3000`

#### ML Service

```bash
cd apps/ml_service
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Start ML service
uvicorn main:app --reload --port 8501
```

ML Service will be available at `http://localhost:8501`

## Testing the Application

### 1. Access the Qualifying Page

Navigate to: `http://localhost:3000/qualifying`

### 2. Using Mock Data (Default)

With `LIVE_DATA=false` (default), the app uses synthetic data:
- Pre-defined qualifying session (2024 Round 1)
- Mock lap data for VER, NOR, LEC, PER, SAI, HAM
- Synthetic telemetry with realistic speed/throttle/brake curves

### 3. Using Live FastF1 Data

To switch to real F1 data:

1. Update `apps/api/.env`:
   ```bash
   LIVE_DATA=true
   ```

2. Restart the backend server

3. On first run, FastF1 will download and cache data (may take 30-60 seconds)

4. Subsequent loads will be faster due to caching

### 4. Feature Testing

**Driver Selection:**
- Click "Add Drivers" to open dropdown
- Select up to 6 drivers (team colors displayed)
- Click driver badges to remove them

**Reference Driver:**
- Change the reference driver for delta comparison
- Must be one of the selected drivers

**Telemetry Chart:**
- Toggle between Speed, Throttle, and Brake views
- Interactive Plotly chart with zoom/pan
- Hover over traces for exact values

**Delta Plot:**
- Shows time gain/loss vs reference driver
- Red areas = slower, Green areas = faster
- Interactive with hover details

**Sector Cards:**
- View fastest sector times
- Compare all drivers in detailed table
- Color-coded deltas (green = faster, red = slower)

**AI Insights:**
- Auto-generated based on sector analysis
- Identifies performance gaps
- Highlights strengths and weaknesses

## API Endpoints

### Sessions
```
GET /sessions?season=2024&round=1
```

### Laps
```
GET /laps?session=2024_1_Qualifying&drivers=VER&drivers=NOR
```

### Telemetry
```
GET /telemetry?session=2024_1_Qualifying&drivers=VER&drivers=NOR
```

### Delta Analysis
```
GET /telemetry/delta?session=2024_1_Qualifying&reference_driver=VER&compare_drivers=NOR&compare_drivers=LEC
```

### Sectors
```
GET /laps/sectors?session=2024_1_Qualifying&drivers=VER&drivers=NOR
```

## Troubleshooting

### Frontend Issues

**Port 3000 already in use:**
```bash
# Use a different port
PORT=3001 pnpm dev:web
```

**Module not found errors:**
```bash
# Clear cache and reinstall
rm -rf node_modules .next
pnpm install
```

### Backend Issues

**FastF1 cache errors:**
```bash
# Clear the cache
rm -rf data/cache/*
```

**Port 8000 already in use:**
```bash
# Use a different port
uvicorn app.main:app --reload --port 8001
# Update NEXT_PUBLIC_API_URL in frontend .env.local
```

**Import errors:**
```bash
# Reinstall dependencies
cd apps/api
pip install -e ".[dev]"
```

**FastF1 download slow/failing:**
- Ensure stable internet connection
- FastF1 connects to Ergast API and F1 timing servers
- First download takes longer; subsequent loads use cache
- Try a different session/round if one fails

### CORS Issues

If you see CORS errors in browser console:
1. Check that `CORS_ORIGINS` in backend `.env` matches your frontend URL
2. Restart the backend after changing `.env`

### Data Loading Issues

**No data appears:**
1. Check browser console for API errors
2. Check backend terminal for errors
3. Verify `.env` configuration
4. Try switching `LIVE_DATA` flag

**Slow loading:**
- First FastF1 load downloads data (expected)
- Mock data should load instantly
- Check network tab for slow requests

## Clearing Cache

### FastF1 Cache
```bash
rm -rf data/cache/*
```

### Browser Cache
- Hard reload: `Ctrl+Shift+R` (Windows) or `Cmd+Shift+R` (Mac)
- Or clear browser cache in DevTools

## Development Tips

### Hot Reload

- Frontend: Changes auto-reload via Next.js
- Backend: Changes auto-reload via `--reload` flag

### Viewing Logs

- Frontend: Browser console (`F12`)
- Backend: Terminal where `uvicorn` is running

### Testing Different Drivers/Sessions

**Mock Data:**
Edit `apps/api/app/fixtures/lap_data.json` to add more drivers

**Live Data:**
Change `sessionId` in `apps/web/app/qualifying/page.tsx`:
```typescript
const [sessionId] = useState<string>('2024_2_Qualifying') // Different round
```

## Performance Notes

- **Telemetry downsampling**: Enabled above 5000 points (configurable via `DOWNSAMPLE_THRESHOLD`)
- **Plotly rendering**: Dynamic import prevents SSR issues
- **FastF1 caching**: Significantly speeds up repeated queries

## Next Steps

After validating the MVP:
1. Add more sessions (Practice, Race)
2. Implement race pace analysis
3. Add tyre degradation visualization
4. Enhance AI insights with ML models
5. Add user authentication and saved analyses

## Support

For issues or questions:
- Check `docs/INTEGRATION_TEST.md` for testing checklist
- Review API docs: `http://localhost:8000/docs`
- Check existing documentation in `docs/` folder

