"""
Practice Data Service — shared processing layer for all Practice page endpoints.

Loads practice session data via the data service factory, classifies laps,
applies optional fuel correction, derives traffic context, groups laps into
stints, classifies run types (long vs short), computes per-stint statistics,
and caches the enriched result in memory.
"""

import logging
import numpy as np
from typing import Dict, List, Optional
from collections import defaultdict

from app.services.practice.transforms import (
    classify_practice_laps,
    apply_practice_fuel_correction,
    derive_practice_traffic,
)
from app.models.dto import (
    PracticeStintStats,
    PracticeLapPoint,
    PracticeLongRunStint,
    PracticeLongRunResponse,
    PracticeSessionsResponse,
    PracticeShortRunDriver,
    PracticeShortRunResponse,
    PracticeProgressionEntry,
    PracticeProgressionDriver,
    PracticeProgressionResponse,
)

logger = logging.getLogger(__name__)

# In-memory cache for processed practice data
_practice_data_cache: Dict[str, Dict] = {}

# Minimum valid laps for a stint to be classified as a long run
LONG_RUN_MIN_LAPS = 4


async def get_processed_practice_data(
    session_id: str,
    fuel_effect_per_kg: float = 0.0,
) -> Dict:
    """
    Get fully processed practice data for a session.
    Returns cached result if available.

    Pipeline:
    1. Load raw laps from FastF1/Mock via get_practice_laps()
    2. Classify laps (RACING, IN_LAP, OUT_LAP, RED_FLAG, ANOMALY)
    3. Apply fuel correction (if fuel_effect_per_kg > 0)
    4. Derive traffic context (gap-to-car-ahead)
    5. Group laps into stints
    6. Classify run types (long_run >= 4 valid laps, short_run < 4)
    7. Compute per-stint statistics
    """
    cache_key = f"{session_id}_{fuel_effect_per_kg}"
    if cache_key in _practice_data_cache:
        return _practice_data_cache[cache_key]

    # 1. Load raw laps (lazy import to avoid pulling in FastF1/pyarrow at module level)
    from app.services.data_service import get_data_service
    data_service = get_data_service()
    raw_result = await data_service.get_practice_laps(session_id)

    raw_laps = raw_result.get('laps', []) if isinstance(raw_result, dict) else []

    if not raw_laps:
        logger.warning(f"No practice laps returned for {session_id}")
        empty_result = {
            'laps': [],
            'stints': [],
            'long_run_stints': [],
            'short_run_stints': [],
            'session_id': session_id,
            'fuel_effect_per_kg': fuel_effect_per_kg,
            'session_best_laps': {},
        }
        return empty_result

    # 2. Classify laps
    classified_laps = classify_practice_laps(raw_laps)

    # 3. Apply fuel correction (only if enabled)
    if fuel_effect_per_kg > 0:
        classified_laps = apply_practice_fuel_correction(classified_laps, fuel_effect_per_kg)
    else:
        # Set fuel_corrected_time to None when correction is off
        for lap in classified_laps:
            lap['fuel_corrected_time'] = None

    # 4. Derive traffic
    enriched_laps = derive_practice_traffic(classified_laps)

    # Extract official session-best lap per driver (for verification)
    session_best_laps = _extract_session_best_laps(enriched_laps)

    # 5-7. Group into stints, classify run types, compute stats
    stints = _group_into_stints(enriched_laps, fuel_effect_per_kg > 0)

    long_run_stints = [s for s in stints if s['run_type'] == 'long_run']
    short_run_stints = [s for s in stints if s['run_type'] == 'short_run']

    result = {
        'laps': enriched_laps,
        'stints': stints,
        'long_run_stints': long_run_stints,
        'short_run_stints': short_run_stints,
        'session_id': session_id,
        'fuel_effect_per_kg': fuel_effect_per_kg,
        'session_best_laps': session_best_laps,
    }

    _practice_data_cache[cache_key] = result
    logger.info(
        f"Processed practice data for {session_id}: "
        f"{len(enriched_laps)} laps, {len(stints)} stints "
        f"({len(long_run_stints)} long runs, {len(short_run_stints)} short runs)"
    )
    return result


def _group_into_stints(laps: List[Dict], use_fuel_corrected: bool) -> List[Dict]:
    """
    Group classified laps into stints by (driver, stint_number).

    For each stint:
    - Determine compound (most common among valid laps)
    - Count valid laps (is_valid == True)
    - Classify run type: long_run (>= LONG_RUN_MIN_LAPS valid) / short_run
    - Compute box plot statistics from valid lap times
    - Compute degradation hint (long runs with >= 4 valid laps)
    - Compute clean-air percentage
    """
    # Group by (driver, stint)
    driver_stints: Dict[str, Dict[int, List[Dict]]] = defaultdict(lambda: defaultdict(list))
    for lap in laps:
        driver = lap.get('driver')
        stint_num = lap.get('stint')
        if driver and stint_num is not None:
            driver_stints[driver][stint_num].append(lap)

    stints = []

    for driver, stint_map in driver_stints.items():
        for stint_num in sorted(stint_map.keys()):
            all_laps = stint_map[stint_num]
            if not all_laps:
                continue

            # Separate valid laps for statistics
            valid_laps = [l for l in all_laps if l.get('is_valid', False)]
            if not valid_laps:
                continue

            # Determine compound (most common among valid laps)
            compounds = [l.get('compound') for l in valid_laps if l.get('compound')]
            compound = max(set(compounds), key=compounds.count) if compounds else 'UNKNOWN'

            # Run type classification
            run_type = 'long_run' if len(valid_laps) >= LONG_RUN_MIN_LAPS else 'short_run'

            # Get analysis times (fuel-corrected if available, else raw)
            analysis_times = _get_analysis_times(valid_laps, use_fuel_corrected)
            if not analysis_times:
                continue

            # Box plot statistics
            stats = _compute_box_stats(analysis_times)

            # Degradation hint (long runs only, minimum 4 valid laps)
            deg_hint = _compute_degradation_hint(analysis_times, run_type)

            # Clean-air percentage
            clean_air_pct = _compute_clean_air_pct(valid_laps)

            # Individual lap points (for violin overlay and scatter dots)
            lap_points = _build_lap_points(valid_laps, use_fuel_corrected)

            team = all_laps[0].get('team', '')

            stints.append({
                'driver': driver,
                'team': team,
                'stint_number': stint_num,
                'compound': compound,
                'run_type': run_type,
                'valid_lap_count': len(valid_laps),
                'total_lap_count': len(all_laps),
                'stats': stats,
                'average_time': stats['mean'],
                'gap_to_fastest': 0.0,  # Set by compute_long_run_stats
                'degradation_hint': deg_hint,
                'clean_air_pct': clean_air_pct,
                'lap_points': lap_points,
            })

    return stints


def _get_analysis_times(laps: List[Dict], use_fuel_corrected: bool) -> List[float]:
    """Get the appropriate time series for analysis (fuel-corrected or raw)."""
    times = []
    for lap in laps:
        if use_fuel_corrected:
            fct = lap.get('fuel_corrected_time')
            if fct is not None:
                times.append(fct)
            elif lap.get('lap_time') is not None:
                times.append(lap['lap_time'])
        else:
            if lap.get('lap_time') is not None:
                times.append(lap['lap_time'])
    return times


def _build_lap_points(valid_laps: List[Dict], use_fuel_corrected: bool) -> List[Dict]:
    """
    Build individual lap data points for violin overlay and scatter dots.

    Each point carries the analysis-time (fuel-corrected or raw), compound
    colour key, tyre life, and traffic flag. Used by the frontend to render
    compound-coloured scatter dots inside the violin shape.
    """
    points = []
    for lap in valid_laps:
        # Determine the time value to use
        if use_fuel_corrected:
            time_val = lap.get('fuel_corrected_time')
            if time_val is None:
                time_val = lap.get('lap_time')
        else:
            time_val = lap.get('lap_time')

        if time_val is None:
            continue

        points.append({
            'lap_number': lap.get('lap_number', 0),
            'lap_time': round(time_val, 3),
            'compound': lap.get('compound'),
            'tyre_life': lap.get('tyre_life'),
            'in_traffic': lap.get('in_traffic', False),
        })
    return points


def _compute_box_stats(times: List[float]) -> Dict:
    """
    Compute box plot and distribution statistics.

    Returns lowerfence, q1, median, q3, upperfence, mean, std_dev — using
    standard 1.5×IQR whisker bounds (Tukey convention) and sample standard
    deviation (Bessel's correction, ddof=1).
    """
    arr = np.array(sorted(times))
    q1 = float(np.percentile(arr, 25))
    median = float(np.percentile(arr, 50))
    q3 = float(np.percentile(arr, 75))
    iqr = q3 - q1
    lowerfence = float(max(arr.min(), q1 - 1.5 * iqr))
    upperfence = float(min(arr.max(), q3 + 1.5 * iqr))
    mean = float(arr.mean())
    std_dev = float(arr.std(ddof=1)) if len(arr) > 1 else 0.0

    return {
        'lowerfence': round(lowerfence, 3),
        'q1': round(q1, 3),
        'median': round(median, 3),
        'q3': round(q3, 3),
        'upperfence': round(upperfence, 3),
        'mean': round(mean, 3),
        'std_dev': round(std_dev, 3),
    }


def _compute_degradation_hint(times: List[float], run_type: str) -> Optional[float]:
    """
    Compute degradation hint: average of last 2 laps minus average of first 2 laps.

    Positive value means getting slower (degradation).
    Negative value means getting faster (tyre warm-up or track improvement).

    Only computed for long runs with at least 4 valid laps.
    Returns None for short runs or insufficient data.
    """
    if run_type != 'long_run' or len(times) < 4:
        return None

    first_2_avg = sum(times[:2]) / 2.0
    last_2_avg = sum(times[-2:]) / 2.0
    return round(last_2_avg - first_2_avg, 3)


def _compute_clean_air_pct(laps: List[Dict]) -> float:
    """
    Compute fraction of valid laps in clean air (not in traffic).

    Returns 1.0 if no traffic data is available (conservative default).
    """
    if not laps:
        return 1.0

    total = len(laps)
    clean = sum(1 for l in laps if not l.get('in_traffic', False))
    return round(clean / total, 2)


def _extract_session_best_laps(enriched_laps: List[Dict]) -> Dict[str, Dict]:
    """
    Extract official session-best lap per driver from enriched lap data.

    Primary method: Use FastF1's ``is_personal_best`` flag.
    Fallback: Compute minimum lap_time across all RACING laps per driver.

    The fallback check is session-level (all-or-nothing).  If no driver
    in the session has ``is_personal_best == True`` the flag data is
    presumed absent (mock data or old FastF1 version) and the computed
    minimum is used for every driver instead.

    Returns dict keyed by driver abbreviation::

        {
            'VER': {
                'session_best_time': 88.123,
                'compound': 'SOFT',
                'tyre_life': 3,
                'source': 'fastf1_flag' | 'computed_minimum',
                'lap_number': 15,
            },
            ...
        }

    Returns empty dict when no usable data exists.
    """
    if not enriched_laps:
        return {}

    # Group laps by driver
    driver_laps: Dict[str, List[Dict]] = {}
    for lap in enriched_laps:
        driver = lap.get('driver')
        if driver:
            if driver not in driver_laps:
                driver_laps[driver] = []
            driver_laps[driver].append(lap)

    if not driver_laps:
        return {}

    # Decide extraction strategy: session-level check for is_personal_best
    any_personal_best = any(
        lap.get('is_personal_best', False)
        for laps in driver_laps.values()
        for lap in laps
    )

    result: Dict[str, Dict] = {}

    if any_personal_best:
        # Flag-based extraction
        for driver, laps in driver_laps.items():
            pb_laps = [
                l for l in laps
                if l.get('is_personal_best', False) and l.get('lap_time') is not None
            ]
            if not pb_laps:
                continue
            # Defensive: pick the fastest if multiple flagged
            best = min(pb_laps, key=lambda l: l['lap_time'])
            result[driver] = {
                'session_best_time': round(best['lap_time'], 3),
                'compound': best.get('compound', 'UNKNOWN'),
                'tyre_life': best.get('tyre_life', 0),
                'source': 'fastf1_flag',
                'lap_number': best.get('lap_number', 0),
                'team': best.get('team', ''),
            }
    else:
        # Fallback: computed minimum from RACING laps
        for driver, laps in driver_laps.items():
            racing_laps = [
                l for l in laps
                if l.get('classification') == 'RACING' and l.get('lap_time') is not None
            ]
            if not racing_laps:
                continue
            best = min(racing_laps, key=lambda l: l['lap_time'])
            result[driver] = {
                'session_best_time': round(best['lap_time'], 3),
                'compound': best.get('compound', 'UNKNOWN'),
                'tyre_life': best.get('tyre_life', 0),
                'source': 'computed_minimum',
                'lap_number': best.get('lap_number', 0),
                'team': best.get('team', ''),
            }

    return result


def _is_lap_in_short_stints(
    lap_number: int, driver: str, short_run_stints: List[Dict],
) -> bool:
    """Check if a specific lap belongs to any of the given short run stints.

    Iterates the ``lap_points`` of every short-run stint for *driver* and
    returns ``True`` if *lap_number* is found.
    """
    for stint in short_run_stints:
        if stint.get('driver') != driver:
            continue
        for lp in stint.get('lap_points', []):
            if lp.get('lap_number') == lap_number:
                return True
    return False


def _filter_representative_long_runs(
    long_stints: list,
    max_gap_to_median: float = 8.0,
) -> list:
    """Filter out non-representative long run stints.

    Practice sessions include installation runs, aero rake laps, and
    other non-representative running that may have 4+ laps on the same
    compound. These stints have average lap times far slower than genuine
    race simulation pace.

    Computes the median average pace across all long run stints and
    excludes any stint whose average is more than max_gap_to_median
    seconds slower.

    A threshold of 8 seconds keeps all legitimate pace differences
    (frontrunner to backmarker is typically 2-4 seconds in practice)
    while excluding installation-pace stints (30-50+ seconds slower).

    Args:
        long_stints: List of long run stint dicts with 'average_time'
        max_gap_to_median: Maximum seconds slower than median to retain

    Returns:
        Filtered list of representative long run stints
    """
    if len(long_stints) <= 1:
        return long_stints

    averages = sorted(s['average_time'] for s in long_stints)
    mid = len(averages) // 2
    if len(averages) % 2 == 0:
        median_pace = (averages[mid - 1] + averages[mid]) / 2
    else:
        median_pace = averages[mid]

    threshold = median_pace + max_gap_to_median
    return [s for s in long_stints if s['average_time'] <= threshold]


def compute_long_run_stats(practice_data: Dict) -> PracticeLongRunResponse:
    """
    Build the response DTO for long run analysis.

    Filters to long_run stints, removes non-representative stints
    (installation laps, sensor runs), sorts by average_time (fastest
    first), computes gap_to_fastest, and returns PracticeLongRunResponse.
    """
    session_id = practice_data.get('session_id', '')
    fuel_effect = practice_data.get('fuel_effect_per_kg', 0.0)
    long_stints = practice_data.get('long_run_stints', [])
    total_detected = len(long_stints)

    if not long_stints:
        return PracticeLongRunResponse(
            session_id=session_id,
            fuel_corrected=(fuel_effect > 0),
            stints=[],
            session_best_average=None,
            total_long_runs_detected=0,
            stints_filtered_count=0,
        )

    # Filter out non-representative stints (installation laps, sensor runs)
    long_stints = _filter_representative_long_runs(long_stints)
    filtered_count = total_detected - len(long_stints)

    if not long_stints:
        return PracticeLongRunResponse(
            session_id=session_id,
            fuel_corrected=(fuel_effect > 0),
            stints=[],
            session_best_average=None,
            total_long_runs_detected=total_detected,
            stints_filtered_count=filtered_count,
        )

    # Assign display_stint_number: sequential 1-based per driver, chronological order
    driver_stint_counter: Dict[str, int] = {}
    for s in sorted(long_stints, key=lambda x: (x['driver'], x['stint_number'])):
        driver = s['driver']
        driver_stint_counter[driver] = driver_stint_counter.get(driver, 0) + 1
        s['display_stint_number'] = driver_stint_counter[driver]

    # Sort by average_time ascending (fastest first)
    long_stints_sorted = sorted(long_stints, key=lambda s: s['average_time'])

    # Compute gap_to_fastest
    fastest_avg = long_stints_sorted[0]['average_time']
    for s in long_stints_sorted:
        s['gap_to_fastest'] = round(s['average_time'] - fastest_avg, 3)

    # Build response DTOs
    stint_dtos = []
    for s in long_stints_sorted:
        lap_time_dtos = [
            PracticeLapPoint(**lp) for lp in s.get('lap_points', [])
        ]
        stint_dtos.append(PracticeLongRunStint(
            driver=s['driver'],
            team=s.get('team'),
            stint_number=s['stint_number'],
            display_stint_number=s.get('display_stint_number', 1),
            compound=s.get('compound'),
            valid_lap_count=s['valid_lap_count'],
            total_lap_count=s['total_lap_count'],
            stats=PracticeStintStats(**s['stats']),
            average_time=s['average_time'],
            gap_to_fastest=s['gap_to_fastest'],
            degradation_hint=s.get('degradation_hint'),
            clean_air_pct=s['clean_air_pct'],
            lap_times=lap_time_dtos,
        ))

    return PracticeLongRunResponse(
        session_id=session_id,
        fuel_corrected=(fuel_effect > 0),
        stints=stint_dtos,
        session_best_average=round(fastest_avg, 3),
        total_long_runs_detected=total_detected,
        stints_filtered_count=filtered_count,
    )


def compute_short_run_stats(
    short_run_stints: List[Dict],
    session_best_laps: Optional[Dict[str, Dict]] = None,
) -> List[Dict]:
    """
    Build the session best-lap ranking for the Short Run / Best Lap panel.

    **Primary path** (when *session_best_laps* is provided and non-empty):
    Uses official session-best lap data per driver — raw ``LapTime`` values
    from FastF1 (FIA timing), unaffected by fuel correction or warm-up
    exclusion.  This guarantees the ranking, times, and gaps match the
    official F1 session classification.  Short-run stint data is used only
    for contextual annotation (stint_count, session_best_from_short_run).

    **Fallback path** (when *session_best_laps* is ``None`` or empty):
    Extracts the best lap per driver from *short_run_stints* lap_points —
    the legacy behaviour prior to official-timing anchoring.

    Returns a list of driver result dicts sorted by best_lap_time
    ascending (fastest first), with gap_to_p1 and position attached.
    Returns an empty list if no data is available.
    """
    # ── Primary path: official session-best ranking ─────────────────────
    if session_best_laps:
        # Count short-run stints per driver for annotation
        driver_stint_counts: Dict[str, int] = {}
        for stint in (short_run_stints or []):
            d = stint.get('driver', '')
            driver_stint_counts[d] = driver_stint_counts.get(d, 0) + 1

        driver_results: List[Dict] = []
        for driver, official in session_best_laps.items():
            driver_results.append({
                'driver': driver,
                'team': official.get('team', ''),
                'best_lap_time': official['session_best_time'],
                'compound': official.get('compound', 'UNKNOWN'),
                'tyre_life': official.get('tyre_life', 0),
                'stint_count': driver_stint_counts.get(driver, 0),
                # Verification fields
                'session_best_time': official['session_best_time'],
                'session_best_source': official.get('source'),
                'session_best_from_short_run': _is_lap_in_short_stints(
                    official.get('lap_number', 0), driver,
                    short_run_stints or [],
                ),
                'session_best_compound': official.get('compound', 'UNKNOWN'),
            })

        if not driver_results:
            return []

        # Sort by best lap time ascending (fastest first)
        driver_results.sort(key=lambda x: x['best_lap_time'])

        # Attach position and gap_to_p1
        p1_time = driver_results[0]['best_lap_time']
        for i, result in enumerate(driver_results):
            result['position'] = i + 1
            result['gap_to_p1'] = round(result['best_lap_time'] - p1_time, 3)

        return driver_results

    # ── Fallback path: extract from short-run stints ────────────────────
    if not short_run_stints:
        return []

    # Group stints by driver
    driver_stints: Dict[str, List[Dict]] = {}
    for stint in short_run_stints:
        driver = stint['driver']
        if driver not in driver_stints:
            driver_stints[driver] = []
        driver_stints[driver].append(stint)

    # Find best lap per driver across all their short run stints
    driver_results = []
    for driver, stints in driver_stints.items():
        best_lap_time: Optional[float] = None
        best_compound: str = 'UNKNOWN'
        best_tyre_life: int = 0
        total_stints = len(stints)
        team = stints[0].get('team', '')

        for stint in stints:
            lap_points = stint.get('lap_points', [])
            for lp in lap_points:
                lt = lp.get('lap_time')
                if lt is None:
                    continue
                if best_lap_time is None or lt < best_lap_time:
                    best_lap_time = lt
                    best_compound = lp.get('compound', 'UNKNOWN')
                    best_tyre_life = lp.get('tyre_life', 0)

        if best_lap_time is None:
            continue

        driver_results.append({
            'driver': driver,
            'team': team,
            'best_lap_time': round(best_lap_time, 3),
            'compound': best_compound,
            'tyre_life': best_tyre_life,
            'stint_count': total_stints,
            # No verification data in fallback path
            'session_best_time': None,
            'session_best_source': None,
            'session_best_from_short_run': None,
            'session_best_compound': None,
        })

    if not driver_results:
        return []

    # Sort by best lap time ascending (fastest first)
    driver_results.sort(key=lambda x: x['best_lap_time'])

    # Attach position and gap_to_p1
    p1_time = driver_results[0]['best_lap_time']
    for i, result in enumerate(driver_results):
        result['position'] = i + 1
        result['gap_to_p1'] = round(result['best_lap_time'] - p1_time, 3)

    return driver_results


def compute_sector_analysis(
    enriched_laps: List[Dict],
    session_best_laps: Dict[str, Dict],
) -> Dict:
    """
    Compute per-driver sector breakdown, theoretical best laps, and speed
    trap data for the Sector Analysis panel.

    Uses ``session_best_laps`` for ranking and primary sector times
    (from each driver's official session-best lap), plus scans all
    ``enriched_laps`` for best-individual-sector times (which may come
    from different laps) and maximum speed trap readings.

    Returns a dict with keys ``drivers``, ``summary``, ``speed_traps``,
    ``total_drivers`` — ready for DTO construction in the route handler.
    Returns empty structures when no data is available.
    """
    if not enriched_laps or not session_best_laps:
        return {
            'drivers': [],
            'summary': {
                'fastest_sector1': None,
                'fastest_sector1_driver': None,
                'fastest_sector2': None,
                'fastest_sector2_driver': None,
                'fastest_sector3': None,
                'fastest_sector3_driver': None,
                'theoretical_best_time': None,
                'actual_best_time': None,
                'theoretical_gain': None,
            },
            'speed_traps': [],
            'total_drivers': 0,
        }

    # ── 1. Index enriched laps by (driver, lap_number) for fast lookup ──
    lap_index: Dict[str, Dict[int, Dict]] = {}
    for lap in enriched_laps:
        driver = lap.get('driver')
        ln = lap.get('lap_number')
        if driver and ln is not None:
            if driver not in lap_index:
                lap_index[driver] = {}
            lap_index[driver][ln] = lap

    # ── 2. Build per-driver best-individual-sector + max speed traps ────
    driver_best_sectors: Dict[str, Dict] = {}   # driver -> {best_s1, ...}
    driver_max_speeds: Dict[str, Dict] = {}     # driver -> {speed_trap, ...}

    for lap in enriched_laps:
        driver = lap.get('driver')
        if not driver:
            continue

        # Best individual sectors
        if driver not in driver_best_sectors:
            driver_best_sectors[driver] = {
                'best_s1': None, 'best_s2': None, 'best_s3': None,
            }
        bs = driver_best_sectors[driver]
        s1 = lap.get('sector1_time')
        s2 = lap.get('sector2_time')
        s3 = lap.get('sector3_time')
        if s1 is not None and (bs['best_s1'] is None or s1 < bs['best_s1']):
            bs['best_s1'] = s1
        if s2 is not None and (bs['best_s2'] is None or s2 < bs['best_s2']):
            bs['best_s2'] = s2
        if s3 is not None and (bs['best_s3'] is None or s3 < bs['best_s3']):
            bs['best_s3'] = s3

        # Max speed traps
        if driver not in driver_max_speeds:
            driver_max_speeds[driver] = {
                'speed_trap': None, 'speed_i1': None,
                'speed_i2': None, 'speed_fl': None,
            }
        ms = driver_max_speeds[driver]
        for key in ('speed_trap', 'speed_i1', 'speed_i2', 'speed_fl'):
            val = lap.get(key)
            if val is not None and (ms[key] is None or val > ms[key]):
                ms[key] = val

    # ── 3. Build driver result list from session_best_laps ──────────────
    driver_results: List[Dict] = []

    for driver, official in session_best_laps.items():
        best_lap_num = official.get('lap_number', 0)
        session_time = official['session_best_time']
        team = official.get('team', '')
        compound = official.get('compound', 'UNKNOWN')

        # Look up the actual lap to get sector times
        actual_lap = lap_index.get(driver, {}).get(best_lap_num)
        s1 = actual_lap.get('sector1_time') if actual_lap else None
        s2 = actual_lap.get('sector2_time') if actual_lap else None
        s3 = actual_lap.get('sector3_time') if actual_lap else None

        # Best individual sectors for this driver
        bs = driver_best_sectors.get(driver, {})
        best_s1 = bs.get('best_s1')
        best_s2 = bs.get('best_s2')
        best_s3 = bs.get('best_s3')

        # Theoretical best (sum of best individual sectors)
        theoretical = None
        if best_s1 is not None and best_s2 is not None and best_s3 is not None:
            theoretical = round(best_s1 + best_s2 + best_s3, 3)

        # Potential gain
        potential_gain = None
        if theoretical is not None:
            potential_gain = round(session_time - theoretical, 3)

        driver_results.append({
            'driver': driver,
            'team': team,
            'lap_time': session_time,
            'sector1': round(s1, 3) if s1 is not None else None,
            'sector2': round(s2, 3) if s2 is not None else None,
            'sector3': round(s3, 3) if s3 is not None else None,
            'best_sector1': round(best_s1, 3) if best_s1 is not None else None,
            'best_sector2': round(best_s2, 3) if best_s2 is not None else None,
            'best_sector3': round(best_s3, 3) if best_s3 is not None else None,
            'theoretical_best': theoretical,
            'potential_gain': potential_gain,
            'compound': compound,
        })

    # Sort by session-best lap time ascending (P1 first)
    driver_results.sort(key=lambda x: x['lap_time'])

    # Assign positions
    for i, result in enumerate(driver_results):
        result['position'] = i + 1

    # ── 4. Session-level summary ────────────────────────────────────────
    fastest_s1 = None
    fastest_s1_driver = None
    fastest_s2 = None
    fastest_s2_driver = None
    fastest_s3 = None
    fastest_s3_driver = None

    for dr in driver_results:
        s1 = dr['sector1']
        if s1 is not None and (fastest_s1 is None or s1 < fastest_s1):
            fastest_s1 = s1
            fastest_s1_driver = dr['driver']
        s2 = dr['sector2']
        if s2 is not None and (fastest_s2 is None or s2 < fastest_s2):
            fastest_s2 = s2
            fastest_s2_driver = dr['driver']
        s3 = dr['sector3']
        if s3 is not None and (fastest_s3 is None or s3 < fastest_s3):
            fastest_s3 = s3
            fastest_s3_driver = dr['driver']

    # Absolute theoretical best: best individual S1+S2+S3 across ALL
    # drivers and ALL laps (may come from three different drivers)
    all_best_s1 = [
        bs.get('best_s1') for bs in driver_best_sectors.values()
        if bs.get('best_s1') is not None
    ]
    all_best_s2 = [
        bs.get('best_s2') for bs in driver_best_sectors.values()
        if bs.get('best_s2') is not None
    ]
    all_best_s3 = [
        bs.get('best_s3') for bs in driver_best_sectors.values()
        if bs.get('best_s3') is not None
    ]

    theoretical_best_time = None
    if all_best_s1 and all_best_s2 and all_best_s3:
        theoretical_best_time = round(
            min(all_best_s1) + min(all_best_s2) + min(all_best_s3), 3
        )

    actual_best_time = driver_results[0]['lap_time'] if driver_results else None

    theoretical_gain = None
    if theoretical_best_time is not None and actual_best_time is not None:
        theoretical_gain = round(actual_best_time - theoretical_best_time, 3)

    summary = {
        'fastest_sector1': fastest_s1,
        'fastest_sector1_driver': fastest_s1_driver,
        'fastest_sector2': fastest_s2,
        'fastest_sector2_driver': fastest_s2_driver,
        'fastest_sector3': fastest_s3,
        'fastest_sector3_driver': fastest_s3_driver,
        'theoretical_best_time': theoretical_best_time,
        'actual_best_time': actual_best_time,
        'theoretical_gain': theoretical_gain,
    }

    # ── 5. Speed trap results ───────────────────────────────────────────
    speed_traps: List[Dict] = []
    for driver, official in session_best_laps.items():
        ms = driver_max_speeds.get(driver, {})
        speed_traps.append({
            'driver': driver,
            'team': official.get('team', ''),
            'speed_trap': round(ms.get('speed_trap'), 1) if ms.get('speed_trap') is not None else None,
            'speed_i1': round(ms.get('speed_i1'), 1) if ms.get('speed_i1') is not None else None,
            'speed_i2': round(ms.get('speed_i2'), 1) if ms.get('speed_i2') is not None else None,
            'speed_fl': round(ms.get('speed_fl'), 1) if ms.get('speed_fl') is not None else None,
        })

    # Sort speed traps by speed_trap descending (fastest first)
    speed_traps.sort(
        key=lambda x: x['speed_trap'] if x['speed_trap'] is not None else 0,
        reverse=True,
    )

    return {
        'drivers': driver_results,
        'summary': summary,
        'speed_traps': speed_traps,
        'total_drivers': len(driver_results),
    }


async def compute_progression_stats(
    year: int,
    round_num: int,
) -> dict:
    """Compute cross-session progression data for a practice weekend.

    For each available FP session, loads processed data (using the
    cached pipeline — no duplicate FastF1 calls if session was already
    viewed), extracts per-driver session-best laps, and computes
    gap-to-session-best for each driver.

    Always uses fuel_effect=0.0 so gaps are comparable across sessions.

    Args:
        year: Championship year (e.g. 2025)
        round_num: Round number (e.g. 1)

    Returns:
        dict with keys: year, round_num, available_sessions,
        is_sprint_weekend, drivers, total_drivers
    """
    # Step 1: Determine which sessions exist for this weekend
    sessions_response = await get_available_sessions(year, round_num)
    available_sessions = sessions_response.sessions  # List[str]

    if not available_sessions:
        return {
            'year': year,
            'round_num': round_num,
            'available_sessions': [],
            'is_sprint_weekend': False,
            'drivers': [],
            'total_drivers': 0,
        }

    is_sprint_weekend = len(available_sessions) == 1

    # Step 2: Load processed data for each available session
    # Always use fuel_effect=0.0 — gaps must be based on raw times
    session_data: Dict[str, Dict] = {}

    for session_label in available_sessions:
        session_id = f"{year}_{round_num}_{session_label}"
        try:
            data = await get_processed_practice_data(
                session_id,
                fuel_effect_per_kg=0.0,
            )
            # Only include sessions that returned usable data
            if data.get('session_best_laps'):
                session_data[session_label] = data
        except Exception as e:
            logger.error(
                f"compute_progression_stats: failed to load {session_id}: {e}"
            )
            # Continue — partial results are valid

    if not session_data:
        return {
            'year': year,
            'round_num': round_num,
            'available_sessions': available_sessions,
            'is_sprint_weekend': is_sprint_weekend,
            'drivers': [],
            'total_drivers': 0,
        }

    # Step 3: Build per-session entries, then aggregate by driver
    # driver_entries: { 'VER': {'driver': ..., 'team': ..., 'sessions': [...]}, ... }
    driver_entries: Dict[str, dict] = {}

    for session_label, data in session_data.items():
        best_laps: Dict[str, Dict] = data['session_best_laps']
        if not best_laps:
            continue

        # Compute session_best = fastest of all drivers in this session
        session_best_time = min(
            entry['session_best_time']
            for entry in best_laps.values()
        )

        for driver_abbrev, lap_data in best_laps.items():
            gap = round(lap_data['session_best_time'] - session_best_time, 3)

            entry = {
                'session': session_label,
                'best_lap_time': lap_data['session_best_time'],
                'compound': lap_data.get('compound', 'UNKNOWN'),
                'tyre_life': lap_data.get('tyre_life', 0),
                'gap_to_session_best': max(0.0, gap),  # Guard against float imprecision
                'source': lap_data.get('source', 'computed_minimum'),
            }

            if driver_abbrev not in driver_entries:
                driver_entries[driver_abbrev] = {
                    'driver': driver_abbrev,
                    'team': lap_data.get('team', ''),
                    'sessions': [],
                }
            driver_entries[driver_abbrev]['sessions'].append(entry)

    # Step 4: Sort sessions within each driver by session order
    session_order = {label: i for i, label in enumerate(available_sessions)}

    drivers = []
    for driver_data in driver_entries.values():
        driver_data['sessions'].sort(
            key=lambda e: session_order.get(e['session'], 99)
        )
        drivers.append(driver_data)

    # Step 5: Sort drivers by their best gap across all sessions
    # (driver who posted the smallest gap to any session best ranks first)
    drivers.sort(
        key=lambda d: min(e['gap_to_session_best'] for e in d['sessions'])
    )

    return {
        'year': year,
        'round_num': round_num,
        'available_sessions': available_sessions,
        'is_sprint_weekend': is_sprint_weekend,
        'drivers': drivers,
        'total_drivers': len(drivers),
    }


async def get_available_sessions(year: int, round_num: int) -> PracticeSessionsResponse:
    """
    Return available practice sessions for a race weekend.

    Uses the existing sessions endpoint to enumerate which FP sessions
    are available (FP1/FP2/FP3 for traditional weekends, FP1 for sprint).
    """
    from app.services.data_service import get_data_service
    data_service = get_data_service()

    try:
        sessions = await data_service.get_sessions(year, round_num)
    except Exception as e:
        logger.error(f"Error getting sessions for {year} round {round_num}: {e}")
        sessions = []

    # Filter to practice sessions (FP1, FP2, FP3)
    practice_sessions = []
    if isinstance(sessions, list):
        for s in sessions:
            # sessions is a list of SessionResponse objects
            name = getattr(s, 'session_name', None) or (s.get('session_name') if isinstance(s, dict) else None)
            if name and name.startswith('FP'):
                practice_sessions.append(name)
    else:
        # Fallback: default to FP1/FP2/FP3
        practice_sessions = ['FP1', 'FP2', 'FP3']

    if not practice_sessions:
        # Default when we can't determine (traditional weekend assumed)
        practice_sessions = ['FP1', 'FP2', 'FP3']

    return PracticeSessionsResponse(
        year=year,
        round_num=round_num,
        sessions=sorted(practice_sessions),
    )
