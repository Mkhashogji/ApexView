# Session Model Specification

## Overview

F1 weekends follow two distinct formats: **Traditional** and **Sprint**. This document defines how sessions are modeled and accessed throughout the application.

## Weekend Formats

### Traditional Weekend
Standard race weekend format with three practice sessions.

**Sessions:**
1. **FP1** (Free Practice 1) - Friday
2. **FP2** (Free Practice 2) - Friday
3. **FP3** (Free Practice 3) - Saturday
4. **Q** (Qualifying) - Saturday
   - Q1, Q2, Q3 sub-sessions
5. **R** (Race) - Sunday

**Typical Schedule:**
- Friday: FP1 (1hr), FP2 (1hr)
- Saturday: FP3 (1hr), Q (1hr)
- Sunday: Race (~2hr)

### Sprint Weekend
Condensed format with one practice session and a sprint race.

**Sessions:**
1. **FP1** (Free Practice 1) - Friday
2. **SQ** (Sprint Qualifying) - Friday (replaces FP2)
3. **S** (Sprint Race) - Saturday (~100km race)
4. **Q** (Qualifying) - Saturday (for Sunday's race)
5. **R** (Race) - Sunday

**Typical Schedule:**
- Friday: FP1 (1hr), SQ (1hr)
- Saturday: Sprint (30min), Qualifying (1hr)
- Sunday: Race (~2hr)

## Data Model

### TypeScript Types

```typescript
type SessionFormat = 'traditional' | 'sprint'

type SessionType = 
  | 'Practice'
  | 'Qualifying'
  | 'Sprint Qualifying'
  | 'Sprint'
  | 'Race'

interface Session {
  sessionId: string           // Unique identifier: "{season}_{round}_{type}"
  sessionType: SessionType
  sessionName: string         // "FP1", "Q", "R", etc.
  season: number
  round: number
  isSprintWeekend: boolean
  date?: string
  circuitName?: string
  duration?: number           // minutes
  completed: boolean
  weatherCondition?: 'dry' | 'wet' | 'mixed'
}

interface Weekend {
  season: number
  round: number
  circuitName: string
  country: string
  format: SessionFormat
  sessions: Session[]
  startDate: string
  endDate: string
}
```

### Python Models

```python
from pydantic import BaseModel
from typing import Literal, Optional, List
from datetime import datetime

SessionFormat = Literal["traditional", "sprint"]
SessionType = Literal["Practice", "Qualifying", "Sprint Qualifying", "Sprint", "Race"]

class Session(BaseModel):
    session_id: str
    session_type: SessionType
    session_name: str
    season: int
    round: int
    is_sprint_weekend: bool
    date: Optional[datetime] = None
    circuit_name: Optional[str] = None
    duration: Optional[int] = None
    completed: bool = False
    weather_condition: Optional[Literal["dry", "wet", "mixed"]] = None

class Weekend(BaseModel):
    season: int
    round: int
    circuit_name: str
    country: str
    format: SessionFormat
    sessions: List[Session]
    start_date: datetime
    end_date: datetime
```

## Session Identification

### Session ID Format
```
{season}_{round}_{session_name}

Examples:
- 2024_1_FP1
- 2024_1_Q
- 2024_5_SQ  (sprint qualifying)
- 2024_5_S   (sprint race)
- 2024_1_R
```

### Session Name Conventions
- **FP1, FP2, FP3**: Free Practice sessions
- **Q**: Main qualifying (determines race grid)
- **SQ**: Sprint Qualifying (determines sprint grid)
- **S**: Sprint Race
- **R**: Main Race

## API Endpoints

### Get Weekend Sessions
```
GET /sessions?season={year}&round={num}

Response:
{
  "season": 2024,
  "round": 1,
  "circuitName": "Bahrain International Circuit",
  "format": "traditional",
  "sessions": [
    {
      "sessionId": "2024_1_FP1",
      "sessionType": "Practice",
      "sessionName": "FP1",
      ...
    },
    ...
  ]
}
```

### Get Specific Session
```
GET /sessions/{session_id}

Example: GET /sessions/2024_1_Q

Response:
{
  "sessionId": "2024_1_Q",
  "sessionType": "Qualifying",
  "sessionName": "Q",
  "season": 2024,
  "round": 1,
  "isSprintWeekend": false,
  "date": "2024-03-02T15:00:00Z",
  "circuitName": "Bahrain International Circuit",
  "completed": true
}
```

## Weekend Format Detection

### FastF1 Integration
```python
import fastf1

def detect_weekend_format(season: int, round: int) -> SessionFormat:
    """
    Detect if weekend is traditional or sprint format.
    """
    event = fastf1.get_event(season, round)
    
    # Check if event has sprint qualifying session
    if hasattr(event, 'get_session') and event.get_session(3).name == 'Sprint Qualifying':
        return 'sprint'
    return 'traditional'
```

### Frontend Format Handling
```typescript
function getSessionsForWeekend(format: SessionFormat): string[] {
  return format === 'sprint' 
    ? ['FP1', 'SQ', 'S', 'Q', 'R']
    : ['FP1', 'FP2', 'FP3', 'Q', 'R']
}
```

## Session Context

### UI Display Rules

**Navigation:**
- Show format badge: "Traditional" or "Sprint" 
- Highlight current session
- Gray out incomplete future sessions

**Session Switcher:**
```tsx
<select>
  <optgroup label="Practice">
    <option>FP1</option>
    {!isSprintWeekend && <option>FP2</option>}
    {!isSprintWeekend && <option>FP3</option>}
  </optgroup>
  
  <optgroup label="Qualifying">
    {isSprintWeekend && <option>Sprint Qualifying</option>}
    <option>Qualifying</option>
  </optgroup>
  
  <optgroup label="Race">
    {isSprintWeekend && <option>Sprint</option>}
    <option>Race</option>
  </optgroup>
</select>
```

**Page Availability:**
- **Qualifying Page**: Shows Q or SQ depending on selection
- **Race Page**: Shows R or S
- **Practice Page**: Shows FP1, FP2, FP3 (FP2/3 disabled for sprint)

## Special Cases

### Qualifying Sub-Sessions
Qualifying has three knockout sessions: Q1, Q2, Q3

**Data Model:**
```typescript
interface QualifyingSession extends Session {
  subSessions: {
    q1: SessionResults
    q2: SessionResults
    q3: SessionResults
  }
}
```

**API Response:**
```json
{
  "sessionId": "2024_1_Q",
  "sessionName": "Q",
  "subSessions": {
    "Q1": {
      "duration": 18,
      "eliminatedDrivers": ["LAT", "SAR", "ZHO", "MAG", "HUL"]
    },
    "Q2": {
      "duration": 15,
      "eliminatedDrivers": ["ALB", "TSU", "GAS", "OCO", "BOT"]
    },
    "Q3": {
      "duration": 12,
      "finalOrder": ["VER", "PER", "LEC", "SAI", "HAM", ...]
    }
  }
}
```

### Weather Changes
Track session weather impact on data interpretation.

```typescript
interface WeatherCondition {
  session: string
  trackTemp: number
  airTemp: number
  rainfall: boolean
  trackStatus: 'dry' | 'damp' | 'wet'
}
```

## Caching Strategy

### Backend Cache
- Cache session metadata for 24 hours
- Cache completed session data indefinitely
- Invalidate cache on session completion

### Frontend Cache
- Store current weekend data in state
- Persist recent sessions in localStorage
- Refresh on page load if data >1 hour old

## Error Handling

### Session Not Available
```json
{
  "error": "SessionNotFound",
  "message": "Session 2024_1_FP2 not available for sprint weekend",
  "availableSessions": ["FP1", "SQ", "S", "Q", "R"]
}
```

### Incomplete Session
```json
{
  "error": "SessionIncomplete",
  "message": "Session 2024_1_R has not finished",
  "estimatedCompletion": "2024-03-03T17:00:00Z"
}
```

## Testing

### Test Cases
1. Traditional weekend session list correct
2. Sprint weekend session list correct
3. Session ID generation unique
4. Format detection accurate
5. Sub-session handling for qualifying
6. Error handling for missing sessions
7. Cache invalidation on completion

### Mock Data
See `apps/api/app/tests/fixtures/sessions.json` for test fixtures.

