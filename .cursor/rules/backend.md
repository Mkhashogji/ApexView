# Backend Development Rules

## Technology Stack

- **Framework**: FastAPI
- **Language**: Python 3.10+
- **Data Source**: FastF1 library
- **Validation**: Pydantic v2
- **Testing**: Pytest
- **Dependencies**: Managed via pyproject.toml

## Code Style

### Follow PEP 8

```python
# ✅ Good: Snake case, type hints, docstrings
def calculate_delta(
    reference_telemetry: pd.DataFrame,
    compare_telemetry: pd.DataFrame,
) -> np.ndarray:
    """
    Calculate time delta between two telemetry traces.
    
    Args:
        reference_telemetry: Reference driver telemetry
        compare_telemetry: Comparison driver telemetry
    
    Returns:
        Array of delta times over distance
    """
    # Implementation
    pass

# ❌ Bad: Camel case, no types, no docs
def calculateDelta(ref, cmp):
    pass
```

### Type Hints Always

```python
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

# ✅ Good: Explicit types
def get_laps(
    session_id: str,
    drivers: List[str],
    lap_type: Optional[str] = None
) -> List[LapResponse]:
    pass

# ❌ Bad: No type hints
def get_laps(session_id, drivers, lap_type=None):
    pass
```

## FastAPI Patterns

### Router Structure

```python
# app/routes/sessions.py
from fastapi import APIRouter, Query, HTTPException
from app.models.dto import SessionResponse
from app.services.fastf1_client import FastF1Client

router = APIRouter()
client = FastF1Client()

@router.get("", response_model=List[SessionResponse])
async def get_sessions(
    season: int = Query(..., ge=2018, le=2024, description="F1 season year"),
    round: int = Query(..., ge=1, le=24, description="Race round number"),
):
    """
    Get all sessions for a specific race weekend.
    Handles both traditional and sprint weekend formats.
    """
    try:
        sessions = await client.get_sessions(season, round)
        return sessions
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
```

### Response Models (DTOs)

```python
# app/models/dto.py
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime

SessionType = Literal["Practice", "Qualifying", "Sprint Qualifying", "Sprint", "Race"]

class SessionResponse(BaseModel):
    """Session information response."""
    session_id: str = Field(..., description="Unique session identifier")
    session_type: SessionType
    session_name: str = Field(..., examples=["FP1", "Q", "R"])
    season: int = Field(..., ge=2018)
    round: int = Field(..., ge=1, le=24)
    is_sprint_weekend: bool
    date: Optional[datetime] = None
    circuit_name: Optional[str] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "session_id": "2024_1_Q",
                "session_type": "Qualifying",
                "session_name": "Q",
                "season": 2024,
                "round": 1,
                "is_sprint_weekend": False,
                "circuit_name": "Bahrain International Circuit"
            }
        }
```

### Dependency Injection

```python
# app/core/dependencies.py
from fastapi import Depends
from app.services.fastf1_client import FastF1Client

def get_f1_client() -> FastF1Client:
    """Dependency for F1 client."""
    return FastF1Client()

# Usage in routes
@router.get("/sessions")
async def get_sessions(
    season: int,
    client: FastF1Client = Depends(get_f1_client)
):
    return await client.get_sessions(season)
```

## FastF1 Integration

### Cache Management

```python
# app/core/cache.py
import fastf1
from pathlib import Path
from app.core.config import settings

def enable_cache():
    """Enable FastF1 cache."""
    cache_dir = Path(settings.CACHE_DIR)
    cache_dir.mkdir(parents=True, exist_ok=True)
    fastf1.Cache.enable_cache(str(cache_dir))

# Enable at module level
enable_cache()
```

### Loading Sessions

```python
# app/services/fastf1_client.py
import fastf1
from typing import List
from app.models.dto import SessionResponse

class FastF1Client:
    async def get_sessions(self, season: int, round: int) -> List[SessionResponse]:
        """Load sessions for a race weekend."""
        # Load event
        event = fastf1.get_event(season, round)
        
        # Detect sprint weekend
        is_sprint = self._is_sprint_weekend(event)
        
        # Build session list
        sessions = []
        session_names = self._get_session_names(is_sprint)
        
        for name in session_names:
            try:
                session = event.get_session(name)
                sessions.append(SessionResponse(
                    session_id=f"{season}_{round}_{name}",
                    session_type=self._map_session_type(name),
                    session_name=name,
                    season=season,
                    round=round,
                    is_sprint_weekend=is_sprint,
                    date=session.date,
                    circuit_name=event.Location
                ))
            except Exception as e:
                # Log and skip if session not available
                print(f"Session {name} not available: {e}")
        
        return sessions
    
    def _is_sprint_weekend(self, event) -> bool:
        """Check if weekend has sprint format."""
        try:
            event.get_session('Sprint Qualifying')
            return True
        except:
            return False
```

### Lap Data Processing

```python
async def get_laps(self, session_id: str, drivers: List[str]) -> List[LapResponse]:
    """Get lap data for specified drivers."""
    # Parse session ID
    season, round_num, session_name = session_id.split('_')
    
    # Load session
    event = fastf1.get_event(int(season), int(round_num))
    session = event.get_session(session_name)
    session.load()  # This may take time
    
    # Filter laps
    laps = session.laps
    if drivers:
        laps = laps[laps['Driver'].isin(drivers)]
    
    # Convert to response models
    result = []
    for idx, lap in laps.iterrows():
        result.append(LapResponse(
            lap_number=int(lap['LapNumber']),
            driver=lap['Driver'],
            lap_time=lap['LapTime'].total_seconds() if pd.notna(lap['LapTime']) else None,
            sector1_time=lap['Sector1Time'].total_seconds() if pd.notna(lap['Sector1Time']) else None,
            sector2_time=lap['Sector2Time'].total_seconds() if pd.notna(lap['Sector2Time']) else None,
            sector3_time=lap['Sector3Time'].total_seconds() if pd.notna(lap['Sector3Time']) else None,
            compound=lap['Compound'] if pd.notna(lap['Compound']) else None,
            tyre_age=int(lap['TyreLife']) if pd.notna(lap['TyreLife']) else None,
            is_personal_best=bool(lap['IsPersonalBest']) if 'IsPersonalBest' in lap else False
        ))
    
    return result
```

### Telemetry Processing

```python
async def get_telemetry(
    self, 
    session_id: str, 
    drivers: List[str], 
    lap_type: str = "fastest"
) -> List[TelemetryResponse]:
    """Get telemetry data for specified drivers."""
    # Load session
    session = self._load_session(session_id)
    
    results = []
    for driver in drivers:
        # Get appropriate lap
        if lap_type == "fastest":
            lap = session.laps.pick_driver(driver).pick_fastest()
        elif lap_type == "average":
            # Calculate average lap (implementation needed)
            lap = self._get_average_lap(session, driver)
        else:
            raise ValueError(f"Unknown lap_type: {lap_type}")
        
        # Get telemetry
        telemetry = lap.get_telemetry()
        
        # Convert to response
        results.append(TelemetryResponse(
            driver=driver,
            lap_number=int(lap['LapNumber']),
            data=[
                TelemetryPoint(
                    distance=float(row['Distance']),
                    speed=float(row['Speed']),
                    throttle=float(row['Throttle']),
                    brake=float(row['Brake']) if 'Brake' in telemetry else 0,
                    gear=int(row['nGear']),
                    rpm=int(row['RPM']) if 'RPM' in telemetry and pd.notna(row['RPM']) else None,
                    drs=int(row['DRS']) if 'DRS' in telemetry and pd.notna(row['DRS']) else None,
                )
                for _, row in telemetry.iterrows()
            ]
        ))
    
    return results
```

## Data Transformations

### Delta Calculation

```python
# app/services/transforms.py
import numpy as np
import pandas as pd
from scipy.interpolate import interp1d

def calculate_delta(
    reference_telemetry: pd.DataFrame,
    compare_telemetry: pd.DataFrame,
) -> tuple[np.ndarray, np.ndarray]:
    """
    Calculate time delta between two telemetry traces.
    
    Returns:
        Tuple of (distances, deltas)
    """
    # Get common distance range
    min_dist = max(reference_telemetry['Distance'].min(), 
                   compare_telemetry['Distance'].min())
    max_dist = min(reference_telemetry['Distance'].max(),
                   compare_telemetry['Distance'].max())
    
    # Create common distance grid
    distances = np.linspace(min_dist, max_dist, 1000)
    
    # Interpolate time data
    ref_time_interp = interp1d(
        reference_telemetry['Distance'],
        reference_telemetry['Time'],
        kind='linear'
    )
    cmp_time_interp = interp1d(
        compare_telemetry['Distance'],
        compare_telemetry['Time'],
        kind='linear'
    )
    
    # Calculate delta
    ref_times = ref_time_interp(distances)
    cmp_times = cmp_time_interp(distances)
    deltas = cmp_times - ref_times
    
    return distances, deltas
```

### Outlier Detection

```python
def detect_outliers(lap_times: List[float], threshold: float = 3.0) -> List[bool]:
    """
    Detect outlier laps using standard deviation.
    
    Args:
        lap_times: List of lap times in seconds
        threshold: Number of standard deviations for outlier
    
    Returns:
        Boolean list indicating outliers
    """
    times = np.array(lap_times)
    mean = np.mean(times)
    std = np.std(times)
    
    z_scores = np.abs((times - mean) / std)
    return (z_scores > threshold).tolist()
```

## Error Handling

### Custom Exceptions

```python
# app/core/exceptions.py
class F1DataError(Exception):
    """Base exception for F1 data errors."""
    pass

class SessionNotFoundError(F1DataError):
    """Session not found or not available."""
    pass

class TelemetryUnavailableError(F1DataError):
    """Telemetry data not available for requested lap."""
    pass
```

### Exception Handlers

```python
# app/main.py
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from app.core.exceptions import F1DataError, SessionNotFoundError

app = FastAPI()

@app.exception_handler(SessionNotFoundError)
async def session_not_found_handler(request: Request, exc: SessionNotFoundError):
    return JSONResponse(
        status_code=status.HTTP_404_NOT_FOUND,
        content={
            "error": "SessionNotFound",
            "message": str(exc),
            "path": str(request.url)
        }
    )

@app.exception_handler(F1DataError)
async def f1_data_error_handler(request: Request, exc: F1DataError):
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "F1DataError",
            "message": str(exc)
        }
    )
```

## Caching Strategy

### In-Memory Caching

```python
from functools import lru_cache
from typing import Optional

@lru_cache(maxsize=128)
def get_session_cached(season: int, round: int, session_name: str):
    """Cache loaded sessions in memory."""
    event = fastf1.get_event(season, round)
    session = event.get_session(session_name)
    session.load()
    return session
```

### Response Caching

```python
from fastapi_cache import FastAPICache
from fastapi_cache.backends.inmemory import InMemoryBackend
from fastapi_cache.decorator import cache

# Initialize cache
FastAPICache.init(InMemoryBackend())

# Use cache decorator
@router.get("/sessions")
@cache(expire=3600)  # Cache for 1 hour
async def get_sessions(season: int, round: int):
    # Implementation
    pass
```

## Configuration

### Settings Management

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from pathlib import Path

class Settings(BaseSettings):
    """Application settings."""
    
    # API Settings
    API_TITLE: str = "F1 Engineering API"
    API_VERSION: str = "0.1.0"
    
    # FastF1 Settings
    CACHE_DIR: Path = Path(__file__).parent.parent.parent.parent / "data" / "cache"
    DEFAULT_SEASON: int = 2024
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

settings = Settings()

# Ensure cache directory exists
settings.CACHE_DIR.mkdir(parents=True, exist_ok=True)
```

## Testing

### Test Structure

```python
# app/tests/test_sessions.py
import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_get_sessions_success():
    """Test successful session retrieval."""
    response = client.get("/sessions?season=2024&round=1")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) > 0

def test_get_sessions_invalid_season():
    """Test error handling for invalid season."""
    response = client.get("/sessions?season=2000&round=1")
    assert response.status_code == 422  # Validation error

@pytest.mark.skip("Requires FastF1 data")
def test_get_sessions_integration():
    """Integration test with real data."""
    # This would require actual data download
    pass
```

### Fixtures

```python
# app/tests/conftest.py
import pytest
from app.models.dto import SessionResponse

@pytest.fixture
def sample_session():
    return SessionResponse(
        session_id="2024_1_Q",
        session_type="Qualifying",
        session_name="Q",
        season=2024,
        round=1,
        is_sprint_weekend=False,
        circuit_name="Bahrain International Circuit"
    )

@pytest.fixture
def mock_fastf1_client(mocker):
    client = mocker.Mock()
    client.get_sessions.return_value = [sample_session()]
    return client
```

## Best Practices

### Do's

✅ Use type hints everywhere
✅ Validate inputs with Pydantic
✅ Handle FastF1 exceptions gracefully
✅ Cache expensive operations
✅ Use async/await for I/O operations
✅ Document all public functions
✅ Log errors with context
✅ Return consistent error responses
✅ Test edge cases
✅ Keep routes thin, logic in services

### Don'ts

❌ Don't block the event loop (use async)
❌ Don't return raw pandas/numpy objects (convert to Pydantic)
❌ Don't ignore FastF1 cache (always enable it)
❌ Don't expose internal errors to clients
❌ Don't hardcode configuration
❌ Don't skip input validation
❌ Don't load entire sessions if not needed
❌ Don't forget to handle missing data

