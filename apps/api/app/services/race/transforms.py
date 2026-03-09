"""
Race lap classification, fuel correction, and traffic derivation.

Pure transform functions operating on lists of dicts — no FastF1 dependency.
"""

import logging
import numpy as np
from typing import List, Dict, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


def classify_race_laps(laps: List[Dict]) -> List[Dict]:
    """
    Classify each race lap by type and detect outliers.

    Modifies laps in place, adding 'classification' and 'is_warm_up' fields.

    Classification priority (first match wins):
    1. FORMATION — lap_number <= 1 with no valid lap_time
    2. IN_LAP — pit_in_time is set
    3. OUT_LAP — pit_out_time is set
    4. SAFETY_CAR — track_status contains '4'
    5. VSC — track_status contains '6' or '7'
    6. RED_FLAG — track_status contains '5'
    7. RACING — all remaining laps with valid lap_time

    After primary classification, outlier detection on RACING laps:
    - IQR-based: time > Q3 + 1.5 * IQR
    - Percentage cap: time > 1.10 * driver_median
    Either condition → ANOMALY (OR logic).
    Outlier thresholds are computed per driver per compound so that
    wet-tyre laps are not compared against dry-tyre baselines.

    Warm-up: first 2 laps of each stint (tyre_life <= 2) get is_warm_up=True.
    """
    if not laps:
        return laps

    # Phase 1: Primary classification
    for lap in laps:
        lap['classification'] = 'RACING'
        lap['is_warm_up'] = False

        lap_time = lap.get('lap_time')
        track_status = str(lap.get('track_status') or '1')

        # 1. Formation lap
        if lap.get('lap_number', 0) <= 1 and lap_time is None:
            lap['classification'] = 'FORMATION'
            continue

        # 2. In-lap (entering pit lane)
        if lap.get('pit_in_time') is not None:
            lap['classification'] = 'IN_LAP'
            continue

        # 3. Out-lap (leaving pit lane)
        if lap.get('pit_out_time') is not None:
            lap['classification'] = 'OUT_LAP'
            continue

        # 4-6. Track status flags (check SC/VSC/RF before green)
        if '4' in track_status:
            lap['classification'] = 'SAFETY_CAR'
            continue
        if '6' in track_status or '7' in track_status:
            lap['classification'] = 'VSC'
            continue
        if '5' in track_status:
            lap['classification'] = 'RED_FLAG'
            continue

        # 7. Remaining: RACING (default set above)
        if lap_time is None:
            lap['classification'] = 'FORMATION'

    # Phase 2: Outlier detection on RACING laps (per driver per compound)
    # Using (driver, compound) groups ensures wet-tyre laps are compared
    # against wet-tyre baselines, not dry-tyre baselines.
    driver_compound_times: Dict[tuple, List[float]] = defaultdict(list)
    for lap in laps:
        if lap['classification'] == 'RACING' and lap.get('lap_time') is not None:
            key = (lap['driver'], lap.get('compound'))
            driver_compound_times[key].append(lap['lap_time'])

    group_stats: Dict[tuple, Dict] = {}
    for key, times in driver_compound_times.items():
        if len(times) < 4:
            # Not enough data for meaningful outlier detection
            group_stats[key] = {'q1': 0, 'q3': float('inf'), 'iqr_upper': float('inf'), 'median': float('inf')}
            continue
        arr = np.array(times)
        q1 = float(np.percentile(arr, 25))
        q3 = float(np.percentile(arr, 75))
        iqr = q3 - q1
        median = float(np.median(arr))
        group_stats[key] = {
            'q1': q1,
            'q3': q3,
            'iqr_upper': q3 + 1.5 * iqr,
            'median': median,
        }

    for lap in laps:
        if lap['classification'] != 'RACING' or lap.get('lap_time') is None:
            continue
        key = (lap['driver'], lap.get('compound'))
        stats = group_stats.get(key)
        if stats is None:
            continue
        lt = lap['lap_time']
        # OR logic: either condition triggers ANOMALY
        if lt > stats['iqr_upper'] or lt > 1.10 * stats['median']:
            lap['classification'] = 'ANOMALY'

    # Phase 3: Warm-up flag (first 2 laps of each stint by tyre_life)
    for lap in laps:
        if lap['classification'] == 'RACING':
            tyre_life = lap.get('tyre_life')
            if tyre_life is not None and tyre_life <= 2:
                lap['is_warm_up'] = True

    return laps


def apply_fuel_correction(
    laps: List[Dict],
    total_race_laps: int,
    fuel_effect_per_kg: float = 0.032,
    total_fuel_kg: float = 110.0,
) -> List[Dict]:
    """
    Apply fuel correction to race laps, normalizing to empty tank.

    corrected = raw_time - (fuel_remaining * fuel_effect_per_kg)

    Earlier laps get a larger subtraction (heavier car = more penalty removed).

    Only applies to RACING and ANOMALY laps with valid lap_time.
    """
    if not laps or total_race_laps <= 0:
        for lap in laps:
            lap['fuel_corrected_time'] = None
        return laps

    fuel_per_lap = total_fuel_kg / total_race_laps

    for lap in laps:
        lap_time = lap.get('lap_time')
        classification = lap.get('classification', '')

        if lap_time is None:
            lap['fuel_corrected_time'] = None
            continue

        if classification in ('RACING', 'ANOMALY'):
            lap_number = lap.get('lap_number', 0)
            fuel_remaining = total_fuel_kg - (fuel_per_lap * lap_number)
            fuel_remaining = max(fuel_remaining, 0.0)
            lap['fuel_corrected_time'] = lap_time - (fuel_remaining * fuel_effect_per_kg)
        else:
            lap['fuel_corrected_time'] = None

    return laps


def derive_traffic(
    laps: List[Dict],
    threshold: float = 1.5,
) -> List[Dict]:
    """
    Compute gap-to-car-ahead and flag laps in traffic.

    Uses cumulative session time (cumulative_time) to compute actual physical
    gaps between cars. Groups laps by lap_number, sorts by position, and
    computes the difference in cumulative time between consecutive positions.

    Laps with gap < threshold are flagged in_traffic=True.
    Falls back gracefully if cumulative_time or position data is unavailable.
    """
    if not laps:
        return laps

    # Set defaults
    for lap in laps:
        lap.setdefault('gap_to_car_ahead', None)
        lap.setdefault('in_traffic', False)

    # Group laps by lap_number
    laps_by_lap: Dict[int, List[Dict]] = defaultdict(list)
    for lap in laps:
        ln = lap.get('lap_number')
        if ln is not None:
            laps_by_lap[ln].append(lap)

    for lap_number, lap_group in laps_by_lap.items():
        # Filter to laps with valid position and cumulative_time
        valid = [
            l for l in lap_group
            if l.get('position') is not None and l.get('cumulative_time') is not None
        ]
        if len(valid) < 2:
            continue

        # Sort by position (P1 first)
        valid.sort(key=lambda l: l['position'])

        # For each driver (except leader), compute gap to car ahead
        # using cumulative session time — the actual physical gap
        for i in range(1, len(valid)):
            current = valid[i]
            ahead = valid[i - 1]

            gap = abs(current['cumulative_time'] - ahead['cumulative_time'])
            current['gap_to_car_ahead'] = round(gap, 3)
            current['in_traffic'] = gap < threshold

    return laps
