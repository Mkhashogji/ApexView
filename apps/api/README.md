# F1 Engineering API

FastAPI backend for F1 telemetry and race analysis.

## Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e ".[dev]"
```

## Running

```bash
# Development server with auto-reload
uvicorn app.main:app --reload

# Or
python -m app.main
```

API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
pytest
```

## Endpoints

- `GET /sessions?season={year}&round={num}` - Get race weekend sessions
- `GET /laps?session={id}&drivers={list}` - Get lap data
- `GET /telemetry?session={id}&drivers={list}` - Get telemetry data
- `GET /track/{round}` - Get track information

