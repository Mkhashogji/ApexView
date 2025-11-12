# Integration Test Checklist - F1 Engineering App MVP

## Test Environment Setup

- [ ] Node.js 18+ installed
- [ ] Python 3.10+ installed
- [ ] pnpm 8+ installed
- [ ] All dependencies installed (`pnpm install` and `pip install`)
- [ ] Environment files configured (`.env` for backend, `.env.local` for frontend)

## Backend Tests

### API Server Startup

- [ ] Backend starts without errors (`uvicorn app.main:app --reload`)
- [ ] API is accessible at `http://localhost:8000`
- [ ] API docs load at `http://localhost:8000/docs`
- [ ] Health check endpoint returns `{"status": "healthy"}` at `/health`

### Mock Data Mode (LIVE_DATA=false)

#### Sessions Endpoint
- [ ] `GET /sessions?season=2024&round=1` returns session data
- [ ] Response includes `session_id`, `session_type`, `season`, `round`
- [ ] Response is valid JSON matching `SessionResponse` schema

#### Laps Endpoint
- [ ] `GET /laps?session=2024_1_Qualifying&drivers=VER&drivers=NOR&drivers=LEC` returns lap data
- [ ] Response includes lap times, sector times, driver abbreviations
- [ ] Multiple drivers can be requested
- [ ] Response matches `LapResponse[]` schema

#### Telemetry Endpoint
- [ ] `GET /telemetry?session=2024_1_Qualifying&drivers=VER&drivers=NOR` returns telemetry
- [ ] Response includes flat arrays: `distance`, `speed`, `throttle`, `brake`, `gear`
- [ ] Arrays have consistent length (1000 points by default)
- [ ] Data looks realistic (speed 80-330 km/h, throttle 0-100%)
- [ ] Response matches `TelemetryResponse[]` schema

#### Delta Endpoint
- [ ] `GET /telemetry/delta?session=2024_1_Qualifying&reference_driver=VER&compare_drivers=NOR` returns delta data
- [ ] Response includes `distance` and `delta` arrays
- [ ] Delta values are reasonable (< 2 seconds typically)
- [ ] Response matches `DeltaResponse[]` schema

#### Sectors Endpoint
- [ ] `GET /laps/sectors?session=2024_1_Qualifying&drivers=VER&drivers=NOR&drivers=LEC` returns sector times
- [ ] Response includes sector_1, sector_2, sector_3, total_time
- [ ] Times are in seconds (floating point)
- [ ] Response matches `SectorTime[]` schema

### Live Data Mode (LIVE_DATA=true)

- [ ] Update `.env` to set `LIVE_DATA=true`
- [ ] Restart backend server
- [ ] First request triggers FastF1 download (may take 30-60 seconds)
- [ ] Cache directory (`data/cache/`) is created and populated
- [ ] Subsequent requests load from cache (< 5 seconds)
- [ ] Real lap data is returned (check for actual lap times)
- [ ] Telemetry data contains real-world values

### Error Handling

- [ ] Invalid session returns appropriate error
- [ ] Missing drivers parameter returns error message
- [ ] Malformed requests return 422 Unprocessable Entity
- [ ] CORS headers are present in responses

## Frontend Tests

### Application Startup

- [ ] Frontend starts without errors (`pnpm dev:web`)
- [ ] Application loads at `http://localhost:3000`
- [ ] No console errors on initial load

### Qualifying Page Load

- [ ] Navigate to `/qualifying`
- [ ] Page loads without errors
- [ ] Title "Qualifying Analysis" is visible
- [ ] Season/Round info displayed (Season 2024 - Round 1 - Qualifying)
- [ ] Loading state appears briefly
- [ ] Data loads successfully

### Driver Multi-Select Component

- [ ] "Add Drivers" button is visible
- [ ] Clicking button opens dropdown
- [ ] All 20 drivers from 2024 are listed
- [ ] Each driver shows:
  - [ ] Team color dot
  - [ ] Driver abbreviation (e.g., VER)
  - [ ] Full name (e.g., Max Verstappen)
- [ ] Can select multiple drivers (up to 6)
- [ ] Selected drivers appear as colored badges
- [ ] Clicking badge removes driver
- [ ] Max limit enforced (can't select 7th driver)
- [ ] Team colors match expected colors (Red Bull = blue, Ferrari = red, etc.)

### Reference Driver Selector

- [ ] Reference driver dropdown is visible
- [ ] Shows all currently selected drivers
- [ ] Can change reference driver
- [ ] Changes trigger data re-fetch

### Data Loading

- [ ] Initial data fetch occurs on page load
- [ ] Loading indicator displays during fetch
- [ ] No errors in console
- [ ] Data appears after loading completes
- [ ] Changing drivers triggers re-fetch
- [ ] Multiple rapid changes handled gracefully

### Sector Cards

- [ ] Three sector cards displayed (Sector 1, 2, 3)
- [ ] Each card shows:
  - [ ] Sector name
  - [ ] Fastest time for that sector
  - [ ] Driver who set fastest time
  - [ ] Team color indicator
- [ ] Detailed comparison table visible
- [ ] Table shows all selected drivers
- [ ] Delta values calculated correctly
  - [ ] Reference driver shows "-"
  - [ ] Other drivers show +/- time
  - [ ] Green = faster, Red = slower
- [ ] All columns present: Driver, S1, Δ, S2, Δ, S3, Δ, Total, Δ

### Telemetry Line Chart

- [ ] Plotly chart renders
- [ ] Default view is "Speed"
- [ ] Channel selector buttons visible (Speed, Throttle, Brake)
- [ ] Clicking buttons switches between channels
- [ ] Multiple driver traces displayed
- [ ] Each trace colored by team color
- [ ] Legend shows driver abbreviations
- [ ] Hover tooltip shows exact values
- [ ] X-axis labeled "Distance (m)"
- [ ] Y-axis labeled correctly for each channel
- [ ] Chart is interactive (can zoom, pan)
- [ ] Chart is responsive to window resize

### Delta Plot

- [ ] Plotly chart renders
- [ ] Shows delta vs reference driver
- [ ] Red areas (slower) and green areas (faster) visible
- [ ] Zero line prominently displayed
- [ ] Legend shows comparison drivers
- [ ] Hover tooltip shows exact delta values
- [ ] "How to read" instructions displayed
- [ ] Color-coded legend (red = slower, green = faster)
- [ ] Multiple drivers can be compared simultaneously

### AI Insights Panel

- [ ] Insights panel renders
- [ ] "AI Insights" heading with ✨ icon
- [ ] Multiple insight cards displayed
- [ ] Insights are relevant to selected drivers
- [ ] Insights mention specific sectors and time deltas
- [ ] Language is clear and understandable
- [ ] Footer explanation present

### Responsive Design

- [ ] Page looks good on desktop (1920x1080)
- [ ] Page looks good on laptop (1366x768)
- [ ] Charts resize appropriately
- [ ] Driver selector works on different screen sizes
- [ ] No horizontal scrolling issues

### Error States

- [ ] If API is down, error message displays
- [ ] Error message is user-friendly
- [ ] Can recover when API comes back online
- [ ] No console errors spam

## Cross-Component Integration

### Data Flow

- [ ] Changing drivers in selector updates all components
- [ ] Changing reference driver updates delta plot and sector deltas
- [ ] All components show consistent data
- [ ] No race conditions or stale data

### Performance

- [ ] Initial page load < 3 seconds (mock data)
- [ ] Driver selection change updates < 2 seconds
- [ ] Charts render smoothly (no lag/jank)
- [ ] Scrolling is smooth
- [ ] No memory leaks (check DevTools Memory tab)

## API Integration

### Mock to Live Data Transition

- [ ] Stop backend
- [ ] Change `LIVE_DATA=false` to `LIVE_DATA=true`
- [ ] Start backend
- [ ] Frontend still works
- [ ] Real data displays correctly
- [ ] Performance is acceptable (< 5s after cache)

### Data Consistency

- [ ] Lap times in sector cards match sum of sector times
- [ ] Telemetry distance arrays match across drivers
- [ ] Delta calculations are mathematically correct
- [ ] No NaN or undefined values in UI

## Browser Compatibility

- [ ] Chrome (latest)
- [ ] Firefox (latest)
- [ ] Edge (latest)
- [ ] Safari (latest) - if on Mac

## Edge Cases

### Empty States

- [ ] No drivers selected: shows appropriate message
- [ ] Only one driver selected: delta plot shows no comparison message
- [ ] API returns no data: error message displays

### Extreme Cases

- [ ] Select all 6 drivers: all charts still readable
- [ ] Very fast driver changes: no crashes
- [ ] Network interruption during fetch: graceful handling

## Visual Verification

### Colors

- [ ] Team colors accurate to 2024 F1 teams
- [ ] Red Bull: Blue (#3671C6)
- [ ] Ferrari: Red (#E8002D)
- [ ] Mercedes: Turquoise (#27F4D2)
- [ ] McLaren: Orange (#FF8000)
- [ ] Green for faster, Red for slower deltas

### Typography

- [ ] Text is readable
- [ ] Font sizes appropriate
- [ ] Proper contrast between text and background

### Spacing

- [ ] Components have adequate spacing
- [ ] No overlapping elements
- [ ] Padding and margins consistent

## Final Validation

- [ ] All backend tests pass
- [ ] All frontend tests pass
- [ ] Application can run for extended period without issues
- [ ] Can toggle between mock and live data successfully
- [ ] All documented features work as described in RUN_BOOK.md

## Sign-Off

- **Tester Name:** _______________
- **Date:** _______________
- **Environment:** Mock Data / Live Data (circle one)
- **Overall Status:** Pass / Fail / Partial (circle one)
- **Notes:** 

---

## Known Issues / Future Improvements

(Document any issues found during testing)

1. 
2. 
3. 

