# F1 Engineering App - Architecture Overview

## System Architecture

The F1 Engineering App is built as a microservices architecture with three main services and a shared data layer.

```
┌─────────────────────────────────────────────────────────┐
│                    Client (Browser)                     │
│              Next.js 14 + React Query                   │
└──────────────────┬──────────────────────────────────────┘
                   │ HTTP/REST
                   ▼
┌─────────────────────────────────────────────────────────┐
│              API Gateway (FastAPI)                      │
│          Port 8000 - apps/api/                          │
│  Routes: /sessions, /laps, /telemetry, /ml, /track     │
└──┬─────────────────────────┬─────────────────┬──────────┘
   │                         │                 │
   │ HTTP                    │ HTTP            │ Read
   ▼                         ▼                 ▼
┌──────────────┐    ┌────────────────┐    ┌──────────────┐
│ ML Service   │    │  FastF1 API    │    │ Parquet Cache│
│  (FastAPI)   │    │  (External)    │    │   + SQLite   │
│ Port 8501    │    │                │    │ data/cache/  │
│ apps/ml_service/  │                │    │              │
│- Similarity  │    │                │    │              │
│- Clustering  │    │                │    │              │
└──────────────┘    └────────────────┘    └──────────────┘
```

## Service Responsibilities

### 1. Frontend (Next.js + React Query)

**Location:** `apps/web/`

**Technology:** Next.js 14 (App Router), TypeScript, TailwindCSS, React Query, Plotly.js

**Responsibilities:**
- User interface and visualization
- Session/driver selection
- Interactive telemetry charts with Plotly
- Real-time data caching with React Query
- Track maps and circuit information display

**Key Features:**
- Server-side rendering for fast initial load
- Client-side caching prevents unnecessary API calls
- Optimized chart rendering with WebGL support

### 2. API Gateway (FastAPI)

**Location:** `apps/api/`

**Technology:** Python 3.11, FastAPI, FastF1, Pandas, NumPy, PyArrow

**Responsibilities:**
- Single entry point for all frontend requests
- Session and lap data retrieval
- Telemetry processing and downsampling
- Delta calculation between drivers
- ML service proxy
- Parquet caching layer

**Endpoints:**
- `GET /sessions` - List sessions for a race weekend
- `GET /laps` - Get lap data for drivers
- `GET /telemetry` - Get telemetry with optional downsampling
- `GET /telemetry/delta` - Calculate delta between drivers
- `POST /ml/lap-similarity` - Proxy to ML service
- `POST /ml/driver-style-clustering` - Proxy to ML service

### 3. ML Service (FastAPI)

**Location:** `apps/ml_service/`

**Technology:** Python 3.11, FastAPI, scikit-learn, NumPy

**Responsibilities:**
- Lap similarity calculation (cosine similarity)
- Driver style clustering (PCA + KMeans)
- Telemetry feature extraction
- Statistical analysis

**Endpoints:**
- `POST /lap-similarity` - Compare two laps
- `POST /driver-style-clustering` - Group drivers by style
- `GET /health` - Service health check

## Data Flow

### 1. Initial Session Load

```
User → Web → API Gateway → FastF1 → Parquet Cache
                              ↓
                         Process & Transform
                              ↓
                         Store in Parquet
                              ↓
                         Return to Web
```

### 2. Subsequent Requests (Cache Hit)

```
User → Web → API Gateway → Parquet Cache (Read)
                              ↓
                         Return cached data
```

### 3. ML Analysis Request

```
User → Web → API Gateway → Fetch Telemetry → ML Service
                                                  ↓
                                            Analyze & Return
```

## Caching Strategy

### Parquet Cache Layer

**Purpose:** Fast read/write of processed telemetry data

**Location:** `data/cache/parquet/`

**Format:** Parquet with Snappy compression

**Cache Keys:**
- Laps: `{session_id}_laps_{drivers}`
- Telemetry: `{session_id}_telemetry_{drivers}_fastest`

**Benefits:**
- 70% faster than re-fetching from FastF1
- Columnar format optimized for analytics
- Compressed storage (10-20x smaller than JSON)

### FastF1 SQLite Cache

**Purpose:** Native FastF1 caching layer

**Location:** `data/cache/sqlite/`

**Used As:** Fallback when Parquet cache misses

### React Query Cache

**Purpose:** Frontend in-memory caching

**Stale Times:**
- Sessions: 2 minutes
- Laps: 30 seconds
- Telemetry: 30 seconds
- Delta: 30 seconds

## Directory Structure

```
f1-engineering-app/
├── apps/
│   ├── web/              # Next.js frontend
│   │   ├── app/          # App router pages
│   │   ├── components/   # React components
│   │   └── lib/          # Utils, API client, hooks
│   ├── api/              # FastAPI backend
│   │   └── app/
│   │       ├── core/     # Config, cache
│   │       ├── models/   # Pydantic schemas
│   │       ├── routes/   # API endpoints
│   │       └── services/ # Business logic
│   └── ml_service/       # ML microservice
│       ├── models/       # Pydantic schemas
│       ├── services/     # ML algorithms
│       └── main.py       # FastAPI app
├── packages/
│   ├── models/           # Shared TypeScript types
│   └── ui/               # Shared UI components
├── data/
│   ├── cache/            # Parquet + SQLite caches
│   └── static/           # Circuit data
├── docs/                 # Documentation
└── docker-compose.yml    # Container orchestration
```

## Deployment Architecture

### Development

```bash
# Start all services
docker-compose up --build

# Services will be available at:
# - Frontend: http://localhost:3000
# - API: http://localhost:8000
# - ML Service: http://localhost:8501
```

### Production

Services are containerized and can be deployed to:
- Kubernetes (recommended for scale)
- Docker Swarm
- Cloud platforms (AWS ECS, Google Cloud Run, Azure Container Instances)

**Container Images:**
- `f1-web` - Next.js frontend
- `f1-api` - FastAPI backend
- `f1-ml` - ML microservice

## Scaling Considerations

### Horizontal Scaling

**ML Service:** Can run multiple instances behind a load balancer

**API Gateway:** Stateless, can be replicated

**Frontend:** Can use CDN + edge caching

### Vertical Scaling

**Telemetry Processing:** CPU-intensive, benefits from more cores

**ML Computations:** Can use GPU-accelerated instances if needed

## Security

### Current State (Development)

- CORS enabled for localhost
- No authentication (MVP)
- Internal network communication between services

### Future Enhancements

- JWT-based authentication
- Rate limiting
- API key for external access
- TLS/HTTPS in production
- Service mesh for inter-service communication

## Monitoring & Observability

### Health Checks

All services expose `/health` endpoints for container orchestration.

### Logging

- Structured JSON logging
- Log levels: INFO, WARNING, ERROR
- FastAPI automatic request logging

### Future

- Prometheus metrics
- Grafana dashboards
- Sentry error tracking
- APM (Application Performance Monitoring)

## Technology Choices

### Why Next.js?

- SSR for fast initial load
- Built-in routing
- API routes option
- Excellent TypeScript support
- Large ecosystem

### Why FastAPI?

- Native async support
- Automatic OpenAPI documentation
- Pydantic validation
- High performance
- Python ecosystem for data science

### Why Separate ML Service?

- Independent scaling
- Isolated ML dependencies
- Clear separation of concerns
- Easier to swap ML models

### Why Parquet?

- Columnar format perfect for analytics
- Excellent compression
- Fast read performance
- Industry standard for big data

## Performance Targets

- **API Response Time:** < 500ms (cached)
- **ML Analysis:** < 2 seconds
- **Chart Rendering:** 60 FPS
- **Initial Page Load:** < 3 seconds
- **Cache Hit Rate:** > 80%

