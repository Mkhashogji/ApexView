# 2025 Season Data Updates

**Last Updated:** November 7, 2025  
**Data Status:** Official FIA data through Round 21 (São Paulo GP)

## Overview

The F1 Engineering App has been updated with the official 2025 season data, reflecting all mid-season driver changes and the complete 24-race calendar.

## Driver Lineup Changes (2025)

### Major Team Changes

**Ferrari**
- ✅ Lewis Hamilton (#44) - Joined from Mercedes
- ✅ Charles Leclerc (#16) - Continues

**Red Bull Racing**
- ✅ Max Verstappen (#1) - Continues
- ✅ Yuki Tsunoda (#22) - Promoted from RB (Round 3, Japanese GP)

**Mercedes**
- ✅ George Russell (#63) - Continues
- ✅ Andrea Kimi Antonelli (#12) - Rookie, replaces Hamilton

**Williams Racing**
- ✅ Alexander Albon (#23) - Continues
- ✅ Carlos Sainz (#55) - Joined from Ferrari

**Alpine F1 Team**
- ✅ Pierre Gasly (#10) - Continues
- ✅ Franco Colapinto (#43) - Permanent seat from Round 7 (Imola GP)

**Haas F1 Team**
- ✅ Oliver Bearman (#87) - Rookie, full-time seat
- ✅ Esteban Ocon (#31) - Joined from Alpine

**RB (Racing Bulls)**
- ✅ Liam Lawson (#30) - Started season, then demoted after Round 2
- ✅ Isack Hadjar (#6) - Rookie

**Kick Sauber**
- ✅ Nico Hülkenberg (#27) - Joined from Haas
- ✅ Gabriel Bortoleto (#5) - Rookie

### New Driver Abbreviations

The following 3-letter codes have been added for 2025:

- **ANT** - Andrea Kimi Antonelli (Mercedes)
- **LAW** - Liam Lawson (RB)
- **HAD** - Isack Hadjar (RB)
- **COL** - Franco Colapinto (Alpine)
- **BEA** - Oliver Bearman (Haas)
- **BOR** - Gabriel Bortoleto (Kick Sauber)

## 2025 Calendar

### Season Structure
- **Total Rounds:** 24 races
- **Sprint Weekends:** 6 races
- **Pre-Season Testing:** February 26-28, Bahrain

### Sprint Race Rounds
1. Round 2 - Chinese GP (Shanghai)
2. Round 6 - Miami GP
3. Round 13 - Belgian GP (Spa)
4. Round 19 - United States GP (Austin)
5. Round 21 - São Paulo GP (Interlagos)
6. Round 23 - Qatar GP (Lusail)

### Notable Calendar Features
- Season opener: Australian GP (Melbourne) - March 14-16
- Triple-header: Canada → Austria → Britain (June 13 - July 6)
- Season finale: Abu Dhabi GP - December 5-7
- New/Returning: All circuits from 2024 calendar retained

## Implementation Details

### Updated Files

#### Driver Data
- `apps/web/data/drivers.json` - Frontend driver database
- `apps/api/app/data/drivers_2025.json` - Backend driver database (renamed from drivers_2024.json)
- `apps/web/lib/drivers.ts` - Updated to export `DRIVERS_2025` constant

#### Calendar Data
- `apps/web/data/calendar_2025.json` - Frontend calendar
- `apps/api/app/data/calendar_2025.json` - Backend calendar

#### Configuration
- `apps/api/app/core/config.py` - DEFAULT_SEASON changed to 2025
- `apps/api/env.template` - Default season updated to 2025
- `apps/web/app/qualifying/page.tsx` - Default season and session IDs updated

#### Mock Data
- `apps/api/app/fixtures/qualifying_session.json` - Updated to 2025 Round 1 (Australia)
- `apps/api/app/fixtures/lap_data.json` - Updated driver abbreviations (TSU for Tsunoda)

### Backward Compatibility

The codebase maintains backward compatibility:
- `DRIVERS_2024` constant aliased to `DRIVERS_2025` in `drivers.ts`
- Old 2024 data files preserved (drivers_2024.json remains available)
- Season can be switched via configuration

### Data Validation

All 2025 data has been validated against:
- ✅ FIA Official Entry List
- ✅ Formula 1 Official Calendar
- ✅ Team color schemes (preserved from 2024)
- ✅ Driver numbers (official FIA assignments)
- ✅ Sprint race weekend designations

## Team Colors (2025)

Team colors preserved from 2024 season for consistency:

| Team | Color Code | Visual |
|------|-----------|--------|
| Red Bull Racing | `#3671C6` | Blue |
| Ferrari | `#E8002D` | Red |
| Mercedes | `#27F4D2` | Turquoise |
| McLaren | `#FF8000` | Papaya Orange |
| Aston Martin | `#229971` | Green |
| Alpine | `#FF87BC` | Pink |
| Williams | `#64C4FF` | Light Blue |
| RB | `#6692FF` | Navy Blue |
| Haas | `#B6BABD` | Silver/Grey |
| Kick Sauber | `#52E252` | Lime Green |

## Usage Notes

### With Mock Data
Default mock data now uses 2025 drivers and sessions:
- Default session: 2025 Round 1 (Australian GP Qualifying)
- Default drivers: VER, NOR, HAM (showcasing Hamilton at Ferrari)

### With Live FastF1 Data
When `LIVE_DATA=true` in backend `.env`:
- FastF1 will fetch 2025 season data automatically
- Calendar data available for all 24 rounds
- Driver data reflects current 2025 lineup

### Testing the Updates

1. Start the application: `pnpm dev`
2. Navigate to `/qualifying`
3. Verify new driver lineup appears in driver selector
4. Check that Hamilton appears with Ferrari team color (red)
5. Verify Tsunoda appears with Red Bull team color (blue)
6. Check rookies are available: ANT, BEA, HAD, BOR

## Future Season Updates

To update for 2026 season:

1. Create new driver files:
   - `apps/web/data/drivers.json` (update with 2026 lineup)
   - `apps/api/app/data/drivers_2026.json`

2. Create new calendar files:
   - `apps/web/data/calendar_2026.json`
   - `apps/api/app/data/calendar_2026.json`

3. Update `apps/web/lib/drivers.ts`:
   ```typescript
   export const DRIVERS_2026: DriverInfo[] = driversData.drivers
   ```

4. Update configuration:
   - `apps/api/app/core/config.py`: Change `DEFAULT_SEASON` to 2026
   - `apps/api/env.template`: Update default season

5. Update mock fixtures if needed

## Sources

- **Driver Lineup:** FIA Official Entry List 2025
- **Calendar:** FIA Formula 1 World Championship 2025 Calendar
- **Mid-Season Changes:** Official team press releases and FIA bulletins
- **Sprint Weekends:** FIA Sprint Format Designation

## Contact

For questions or issues with 2025 data, refer to:
- `docs/RUN_BOOK.md` - Setup and running instructions
- `docs/INTEGRATION_TEST.md` - Testing procedures
- FastF1 Documentation - https://docs.fastf1.dev/

---

**Data Accuracy Note:** This data reflects the official F1 grid as of November 7, 2025 (after Round 21). Any further changes during the remainder of the season will require additional updates.

