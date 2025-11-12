# ML Service Documentation

## Overview

The ML Service is a FastAPI microservice that provides machine learning features for F1 telemetry analysis. It uses scikit-learn for unsupervised learning tasks including lap similarity detection and driver style clustering.

## Architecture

```
┌──────────────┐
│  API Gateway │
│  (FastAPI)   │
└──────┬───────┘
       │ HTTP POST
       ▼
┌──────────────────────┐
│   ML Service         │
│   Port: 8501         │
├──────────────────────┤
│  Endpoints:          │
│  - /lap-similarity   │
│  - /clustering       │
│  - /health           │
└──────┬───────────────┘
       │
       ▼
┌──────────────────────┐
│  Services:           │
│  - similarity.py     │
│  - clustering.py     │
└──────────────────────┘
```

## Endpoints

### 1. POST /lap-similarity

Calculate cosine similarity between two laps based on telemetry features.

**Request:**

```json
{
  "lap1": {
    "distance": [0, 100, 200, ...],
    "speed": [120, 180, 250, ...],
    "throttle": [50, 80, 100, ...],
    "brake": [0, 20, 80, ...]
  },
  "lap2": {
    "distance": [0, 100, 200, ...],
    "speed": [115, 175, 245, ...],
    "throttle": [45, 75, 95, ...],
    "brake": [0, 25, 85, ...]
  },
  "features": ["speed", "throttle", "brake"]
}
```

**Response:**

```json
{
  "similarity": 0.95,
  "feature_scores": {
    "speed": 0.97,
    "throttle": 0.94,
    "brake": 0.93
  },
  "metadata": {
    "features_used": ["speed", "throttle", "brake"],
    "lap1_points": 1000,
    "lap2_points": 1000
  }
}
```

**Similarity Score Interpretation:**

- **1.0**: Identical driving (same inputs at every distance point)
- **0.8-0.99**: Very similar driving style
- **0.5-0.8**: Moderately similar
- **< 0.5**: Different driving approaches

### 2. POST /driver-style-clustering

Cluster drivers by driving style using PCA + KMeans.

**Request:**

```json
{
  "telemetry_data": [
    {
      "driver": "VER",
      "telemetry": {
        "distance": [...],
        "speed": [...],
        "throttle": [...],
        "brake": [...]
      }
    },
    {
      "driver": "HAM",
      "telemetry": {...}
    }
  ],
  "n_clusters": 3,
  "features": ["speed", "throttle", "brake"]
}
```

**Response:**

```json
{
  "clusters": [
    {
      "driver": "VER",
      "cluster": 0,
      "pca_x": 2.5,
      "pca_y": -1.2
    },
    {
      "driver": "HAM",
      "cluster": 1,
      "pca_x": -0.8,
      "pca_y": 1.5
    }
  ],
  "cluster_descriptions": {
    "0": "High-speed + Aggressive throttle",
    "1": "Medium-speed + Hard braking",
    "2": "Low-speed + Frequent braking"
  },
  "explained_variance": [0.65, 0.25],
  "metadata": {
    "n_drivers": 20,
    "n_clusters": 3,
    "features_used": ["speed", "throttle", "brake"]
  }
}
```

### 3. GET /health

Health check endpoint.

**Response:**

```json
{
  "status": "healthy",
  "version": "0.1.0",
  "service": "f1-ml-service"
}
```

## Algorithms

### Lap Similarity

**Algorithm:** Cosine Similarity

**Steps:**
1. **Distance Alignment:** Interpolate both laps to common distance points (1000 points)
2. **Feature Extraction:** Extract speed, throttle, brake arrays
3. **Normalization:** Normalize each feature to [0, 1]
4. **Concatenation:** Combine all feature vectors
5. **Cosine Similarity:** Calculate similarity between combined vectors

**Formula:**

```
similarity = (A · B) / (||A|| × ||B||)
```

Where:
- A = concatenated feature vector for lap 1
- B = concatenated feature vector for lap 2

**Complexity:** O(n) where n = number of interpolation points

### Driver Style Clustering

**Algorithm:** PCA + KMeans

**Steps:**
1. **Feature Extraction:** Calculate statistical features for each driver
   - Mean, Std Dev, 95th percentile, 5th percentile, Median
   - For each telemetry channel (speed, throttle, brake)
2. **Standardization:** StandardScaler normalization
3. **Dimensionality Reduction:** PCA to 2 components for visualization
4. **Clustering:** KMeans with configurable k (2-10 clusters)
5. **Description Generation:** Analyze cluster centers to create labels

**Feature Vector (per driver):**
```
[speed_mean, speed_std, speed_p95, speed_p5, speed_median,
 throttle_mean, throttle_std, throttle_p95, throttle_p5, throttle_median,
 brake_mean, brake_std, brake_p95, brake_p5, brake_median]
```

**Complexity:** O(k × n × i) where k=clusters, n=drivers, i=iterations (typically ~10)

## Usage Examples

### Via API Gateway (Recommended)

```bash
# Lap Similarity
curl -X POST http://localhost:8000/ml/lap-similarity \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "2025_1_Qualifying",
    "driver1": "VER",
    "driver2": "HAM"
  }'

# Driver Clustering
curl -X POST http://localhost:8000/ml/driver-style-clustering \
  -H "Content-Type: application/json" \
  -d '{
    "session_id": "2025_1_Qualifying",
    "drivers": ["VER", "HAM", "LEC", "PER"],
    "n_clusters": 2
  }'
```

### Direct to ML Service

```bash
# Health Check
curl http://localhost:8501/health

# Direct similarity call
curl -X POST http://localhost:8501/lap-similarity \
  -H "Content-Type: application/json" \
  -d @lap_similarity_request.json
```

## Development

### Local Development

```bash
# Navigate to ML service directory
cd apps/ml_service

# Install dependencies
pip install -e ".[dev]"

# Run service
uvicorn main:app --host 0.0.0.0 --port 8501 --reload
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=ml_service --cov-report=html

# Run specific test
pytest tests/test_similarity.py -v
```

### Docker Development

```bash
# Build image
docker build -t f1-ml-service -f apps/ml_service/Dockerfile .

# Run container
docker run -p 8501:8501 f1-ml-service

# Run with docker-compose
docker-compose up ml
```

## Performance

### Benchmarks

**Lap Similarity:**
- Input: 2 laps with 1000 points each
- Features: speed, throttle, brake
- Average Time: 50ms
- Memory: ~20MB

**Driver Clustering:**
- Input: 20 drivers
- Clusters: 3
- Features: 15 statistical features per driver
- Average Time: 150ms
- Memory: ~30MB

### Optimization Tips

1. **Reduce Interpolation Points:** Fewer points = faster similarity
2. **Limit Features:** Use only essential telemetry channels
3. **Batch Processing:** Process multiple comparisons in one request
4. **Caching:** Cache results for identical inputs

## Error Handling

### Common Errors

**Empty Telemetry:**
```json
{
  "error": "Telemetry arrays cannot be empty"
}
```

**Mismatched Lengths:**
```json
{
  "error": "Distance and value arrays must have same length"
}
```

**Too Few Drivers:**
```json
{
  "error": "Need at least 2 drivers for clustering"
}
```

## Future Enhancements

### Short-term
- [ ] Lap segment analysis (sector-by-sector similarity)
- [ ] Time series forecasting for lap time prediction
- [ ] Anomaly detection for outlier laps

### Medium-term
- [ ] Deep learning models for pattern recognition
- [ ] Real-time analysis during live sessions
- [ ] Multi-session comparison

### Long-term
- [ ] Reinforcement learning for strategy optimization
- [ ] Natural language generation for insights
- [ ] Video-telemetry synchronization

## API Reference

Full OpenAPI documentation available at:
- **Interactive Docs:** http://localhost:8501/docs
- **ReDoc:** http://localhost:8501/redoc
- **OpenAPI JSON:** http://localhost:8501/openapi.json

## Dependencies

### Core
- `fastapi>=0.109.0` - Web framework
- `uvicorn>=0.27.0` - ASGI server
- `pydantic>=2.5.0` - Data validation
- `numpy>=1.26.0` - Numerical computing
- `pandas>=2.1.0` - Data manipulation
- `scikit-learn>=1.3.0` - Machine learning

### Development
- `pytest>=7.4.0` - Testing framework
- `pytest-asyncio>=0.23.0` - Async test support
- `httpx>=0.26.0` - HTTP client for testing
- `black>=24.1.0` - Code formatting
- `ruff>=0.1.0` - Linting

## Contributing

When adding new ML features:

1. Create service module in `services/`
2. Define Pydantic schemas in `models/schemas.py`
3. Add endpoint in `main.py`
4. Write unit tests in `tests/`
5. Update this documentation
6. Add proxy route in API gateway

## Support

For issues or questions:
- Check `/docs` for interactive API testing
- Review test files for usage examples
- See ARCHITECTURE_OVERVIEW.md for system context

