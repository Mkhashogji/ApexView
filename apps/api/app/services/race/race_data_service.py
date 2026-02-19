"""
Race Data Service — shared processing layer for all Race page endpoints.

Loads race session data via the data service factory, classifies laps,
applies fuel correction, derives traffic context, extracts stints and
pit stops, and caches the enriched result in memory.
"""

import logging
import numpy as np
from typing import Dict, List, Optional
from collections import defaultdict

from app.services.race.transforms import (
    classify_race_laps,
    apply_fuel_correction,
    derive_traffic,
)
from app.models.dto import (
    StintResponse,
    PitStopResponse,
    DriverPaceResponse,
    RacePaceResponse,
)

logger = logging.getLogger(__name__)

# In-memory cache for processed race data (keyed by session_id)
_race_data_cache: Dict[str, Dict] = {}


async def get_processed_race_data(
    session_id: str,
    fuel_effect_per_kg: float = 0.032,
) -> Dict:
    """
    Get fully processed race data for a session.
    Returns cached result if available.

    Pipeline:
    1. Load raw laps from FastF1/Mock
    2. Classify laps (RACING, IN_LAP, OUT_LAP, SC, VSC, RF, FORMATION, ANOMALY)
    3. Apply fuel correction (normalize to empty tank)
    4. Derive traffic context (gap-to-car-ahead)
    5. Extract stints
    6. Extract pit stops
    """
    cache_key = f"{session_id}_{fuel_effect_per_kg}"
    if cache_key in _race_data_cache:
        return _race_data_cache[cache_key]

    # 1. Get raw laps (lazy import to avoid pulling in FastF1/pyarrow at module level)
    from app.services.data_service import get_data_service
    data_service = get_data_service()
    raw_result = await data_service.get_race_laps(session_id)

    # Unpack: get_race_laps returns dict with 'laps' and 'finishing_positions'
    if isinstance(raw_result, dict):
        raw_laps = raw_result.get('laps', [])
        finishing_positions = raw_result.get('finishing_positions', {})
    else:
        # Backward compatibility: if still returns a list
        raw_laps = raw_result if raw_result else []
        finishing_positions = {}

    if not raw_laps:
        logger.warning(f"No race laps returned for {session_id}")
        return {
            'laps': [],
            'stints': [],
            'pit_stops': [],
            'total_laps': 0,
            'fuel_effect_per_kg': fuel_effect_per_kg,
            'session_id': session_id,
            'finishing_positions': finishing_positions,
        }

    # 2. Determine total race laps
    total_laps = max(lap.get('lap_number', 0) for lap in raw_laps)

    # 3. Classify laps
    classified_laps = classify_race_laps(raw_laps)

    # 4. Apply fuel correction
    fuel_corrected_laps = apply_fuel_correction(
        classified_laps, total_laps, fuel_effect_per_kg
    )

    # 5. Derive traffic
    enriched_laps = derive_traffic(fuel_corrected_laps)

    # 6. Extract stints
    stints = extract_stints(enriched_laps)

    # 7. Extract pit stops
    pit_stops = extract_pit_stops(enriched_laps)

    result = {
        'laps': enriched_laps,
        'stints': stints,
        'pit_stops': pit_stops,
        'total_laps': total_laps,
        'fuel_effect_per_kg': fuel_effect_per_kg,
        'session_id': session_id,
        'finishing_positions': finishing_positions,
    }

    _race_data_cache[cache_key] = result
    logger.info(
        f"Processed race data for {session_id}: "
        f"{len(enriched_laps)} laps, {len(stints)} stints, {len(pit_stops)} pit stops"
    )
    return result


def extract_stints(laps: List[Dict]) -> List[StintResponse]:
    """Extract stint summaries from classified laps."""
    stints = []

    # Group by (driver, stint)
    driver_stints: Dict[str, Dict[int, List[Dict]]] = defaultdict(lambda: defaultdict(list))
    for lap in laps:
        driver = lap.get('driver')
        stint_num = lap.get('stint')
        if driver and stint_num is not None:
            driver_stints[driver][stint_num].append(lap)

    for driver, stint_map in driver_stints.items():
        for stint_num in sorted(stint_map.keys()):
            stint_laps = stint_map[stint_num]
            if not stint_laps:
                continue

            team = stint_laps[0].get('team')
            lap_numbers = [l['lap_number'] for l in stint_laps]
            compounds = [l.get('compound') for l in stint_laps if l.get('compound')]

            # Most common compound in the stint
            compound = None
            if compounds:
                compound = max(set(compounds), key=compounds.count)

            stints.append(StintResponse(
                driver=driver,
                team=team,
                stint_number=stint_num,
                compound=compound,
                start_lap=min(lap_numbers),
                end_lap=max(lap_numbers),
                lap_count=len(lap_numbers),
            ))

    return stints


def extract_pit_stops(laps: List[Dict]) -> List[PitStopResponse]:
    """
    Extract pit stop events from classified lap data.
    Identifies in-laps and computes pit lane duration.
    Flags anomalous stops (>35s or >2× team median).
    """
    pit_stops = []
    driver_stop_count: Dict[str, int] = defaultdict(int)

    # Find all in-laps (laps classified as IN_LAP or with pit_in_time)
    in_laps = [l for l in laps if l.get('classification') == 'IN_LAP' or l.get('pit_in_time') is not None]

    # Group out-laps by (driver, lap_number) for matching
    out_laps_map: Dict[str, Dict[int, Dict]] = defaultdict(dict)
    for l in laps:
        if l.get('pit_out_time') is not None:
            out_laps_map[l['driver']][l['lap_number']] = l

    for in_lap in in_laps:
        driver = in_lap['driver']
        team = in_lap.get('team')
        in_lap_num = in_lap['lap_number']

        # Try to find matching out-lap (typically the next lap)
        out_lap = out_laps_map.get(driver, {}).get(in_lap_num + 1)

        pit_duration = None
        if in_lap.get('pit_in_time') is not None and out_lap and out_lap.get('pit_out_time') is not None:
            pit_duration = out_lap['pit_out_time'] - in_lap['pit_in_time']
            if pit_duration < 0:
                pit_duration = None  # Invalid data

        driver_stop_count[driver] += 1

        pit_stops.append(PitStopResponse(
            driver=driver,
            team=team,
            stop_number=driver_stop_count[driver],
            lap_number=in_lap_num,
            pit_lane_time=round(pit_duration, 3) if pit_duration is not None else None,
            is_anomaly=False,  # Set below
        ))

    # Flag anomalous stops
    # Compute team median pit times
    team_times: Dict[str, List[float]] = defaultdict(list)
    for ps in pit_stops:
        if ps.pit_lane_time is not None and ps.pit_lane_time > 0:
            team = ps.team or 'unknown'
            team_times[team].append(ps.pit_lane_time)

    team_medians: Dict[str, float] = {}
    for team, times in team_times.items():
        team_medians[team] = float(np.median(times))

    for ps in pit_stops:
        if ps.pit_lane_time is None:
            continue
        team = ps.team or 'unknown'
        team_med = team_medians.get(team, 25.0)
        if ps.pit_lane_time > 35.0 or ps.pit_lane_time > 2.0 * team_med:
            ps.is_anomaly = True

    return pit_stops


def compute_race_pace_stats(race_data: Dict) -> RacePaceResponse:
    """
    Compute per-driver box plot statistics from processed race data.

    For each driver:
    - Filter to RACING laps (exclude IN_LAP, OUT_LAP, SC, VSC, RF, FORMATION)
    - Compute: min, Q1, median, mean, Q3, max, outliers (beyond 1.5×IQR whiskers)
    - Compute gap_to_fastest (this driver's mean - fastest driver's mean)
    - Extract tyre_strategy (ordered list of compounds from stints)
    - Compute consistency_score (mean of per-stint standard deviations)
    - Count laps_in_traffic
    """
    laps = race_data.get('laps', [])
    stints = race_data.get('stints', [])
    session_id = race_data.get('session_id', '')
    finishing_positions = race_data.get('finishing_positions', {})

    if not laps:
        return RacePaceResponse(session_id=session_id, drivers=[])

    # Group racing laps by driver (include ANOMALY for outlier dots)
    driver_laps: Dict[str, List[Dict]] = defaultdict(list)
    for lap in laps:
        if lap.get('classification') in ('RACING', 'ANOMALY') and lap.get('lap_time') is not None:
            driver_laps[lap['driver']].append(lap)

    # Build tyre strategy per driver from stints
    driver_stints: Dict[str, List[str]] = defaultdict(list)
    for stint in stints:
        if stint.compound:
            driver_stints[stint.driver].append(stint.compound)

    # Get team mapping
    driver_teams: Dict[str, str] = {}
    for lap in laps:
        if lap.get('driver') and lap.get('team'):
            driver_teams[lap['driver']] = lap['team']

    driver_stats = []
    for driver, d_laps in driver_laps.items():
        # Separate RACING from ANOMALY
        # Use fuel_corrected_time when available, fall back to raw lap_time
        racing_times = [l.get('fuel_corrected_time') or l['lap_time'] for l in d_laps if l['classification'] == 'RACING']
        all_times = [l.get('fuel_corrected_time') or l['lap_time'] for l in d_laps]

        if not racing_times:
            continue

        arr = np.array(racing_times)
        q1 = float(np.percentile(arr, 25))
        q3 = float(np.percentile(arr, 75))
        iqr = q3 - q1
        median = float(np.median(arr))
        mean = float(np.mean(arr))
        min_time = float(np.min(arr))

        # Whisker bounds
        whisker_upper = q3 + 1.5 * iqr
        whisker_lower = q1 - 1.5 * iqr
        max_within_whisker = float(np.max(arr[arr <= whisker_upper])) if np.any(arr <= whisker_upper) else float(np.max(arr))

        # Outliers beyond whiskers (from ALL times including ANOMALY)
        all_arr = np.array(all_times)
        outliers = sorted([float(t) for t in all_arr if t > whisker_upper])

        # Consistency: mean of per-stint standard deviations
        consistency_score = None
        stint_stdevs = []
        stint_laps_map: Dict[int, List[float]] = defaultdict(list)
        for l in d_laps:
            if l['classification'] == 'RACING' and l.get('stint') is not None:
                stint_laps_map[l['stint']].append(l.get('fuel_corrected_time') or l['lap_time'])
        for stint_num, stint_times in stint_laps_map.items():
            if len(stint_times) >= 3:
                stint_stdevs.append(float(np.std(stint_times)))
        if stint_stdevs:
            consistency_score = round(float(np.mean(stint_stdevs)), 4)

        # Traffic count
        laps_in_traffic = sum(1 for l in d_laps if l.get('in_traffic', False))

        # Tyre strategy
        strategy = driver_stints.get(driver, [])

        driver_stats.append(DriverPaceResponse(
            driver=driver,
            team=driver_teams.get(driver),
            min_time=round(min_time, 3),
            q1=round(q1, 3),
            median=round(median, 3),
            mean=round(mean, 3),
            q3=round(q3, 3),
            max_time=round(max_within_whisker, 3),
            outliers=[round(o, 3) for o in outliers],
            gap_to_fastest=0.0,  # Set below
            tyre_strategy=strategy,
            consistency_score=consistency_score,
            laps_in_traffic=laps_in_traffic,
            total_racing_laps=len(racing_times),
            finishing_position=finishing_positions.get(driver),
        ))

    # Sort by mean ascending (fastest first) — matches industry convention
    # (FDataAnalysis, F1-Tempo). Mean is computed from RACING laps only
    # (ANOMALY excluded), so outlier robustness is handled upstream.
    driver_stats.sort(key=lambda d: d.mean)

    # Compute gap_to_fastest using mean
    if driver_stats:
        fastest_mean = driver_stats[0].mean
        for ds in driver_stats:
            ds.gap_to_fastest = round(ds.mean - fastest_mean, 3)

    return RacePaceResponse(
        session_id=session_id,
        drivers=driver_stats,
    )
