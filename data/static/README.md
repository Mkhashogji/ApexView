# Static Data

This directory contains static circuit data that supplements FastF1 information.

## Structure

- `circuits/` - Circuit-specific JSON files with DRS zones, corners, elevation data
- `corners/` - Detailed corner characteristics (optional)
- `elevation/` - Elevation profile data (optional)

## Circuit JSON Schema

Each circuit JSON file should contain:

```json
{
  "circuitName": "string",
  "round": number,
  "season": number,
  "length": number,  // meters
  "sectors": [...],
  "drsZones": [...],
  "corners": [...],
  "elevationData": [...]
}
```

## Data Sources

- Official F1 website
- FastF1 library
- FIA technical documents
- Track maps and elevation profiles

## Usage

The API will merge this static data with live FastF1 session data to provide
comprehensive track information to the frontend.

