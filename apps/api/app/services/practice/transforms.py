"""
Practice lap classification, fuel correction, and traffic derivation.

Pure transform functions operating on lists of dicts — no FastF1 dependency.
Simplified from race transforms: fewer classification states, optional fuel
correction with within-stint heuristic, and graceful traffic fallback.
"""

import logging
import numpy as np
from typing import List, Dict
from collections import defaultdict

logger = logging.getLogger(__name__)


def classify_practice_laps(laps: List[Dict]) -> List[Dict]:
    """
    Classify each practice lap by type and detect outliers.

    Modifies laps in place, adding 'classification', 'is_warm_up', and
    'is_valid' fields.

    Classification priority (first match wins):
    1. IN_LAP — pit_in_time is set
    2. OUT_LAP — pit_out_time is set
    3. RED_FLAG — track_status contains '5'
    4. ANOMALY — outlier by IQR or 110% median (applied in Phase 2)
    5. RACING — all remaining laps with valid lap_time

    Practice does NOT classify FORMATION, SAFETY_CAR, or VSC because:
    - No formation lap in practice sessions
    - SC/VSC periods in practice are extremely rare and not distinctly
      flagged by FastF1 for practice sessions

    Warm-up: tyre_life <= 2 on RACING laps gets is_warm_up=True.
    is_valid: RACING and not is_warm_up (used for downstream stats).
    """
    if not laps:
        return laps

    # Phase 1: Primary classification
    for lap in laps:
        lap['classification'] = 'RACING'
        lap['is_warm_up'] = False
        lap['is_valid'] = False

        lap_time = lap.get('lap_time')
        track_status = str(lap.get('track_status') or '1')

        # 1. In-lap (entering pit lane)
        if lap.get('pit_in_time') is not None:
            lap['classification'] = 'IN_LAP'
            continue

        # 2. Out-lap (leaving pit lane)
        if lap.get('pit_out_time') is not None:
            lap['classification'] = 'OUT_LAP'
            continue

        # 3. Red flag
        if '5' in track_status:
            lap['classification'] = 'RED_FLAG'
            continue

        # 4. No valid lap time — skip (installation laps, aborted laps)
        if lap_time is None:
            lap['classification'] = 'OUT_LAP'  # Treat as non-representative
            continue

    # Phase 2: Outlier detection on RACING laps (per driver per compound)
    driver_compound_times: Dict[tuple, List[float]] = defaultdict(list)
    for lap in laps:
        if lap['classification'] == 'RACING' and lap.get('lap_time') is not None:
            key = (lap['driver'], lap.get('compound'))
            driver_compound_times[key].append(lap['lap_time'])

    group_stats: Dict[tuple, Dict] = {}
    for key, times in driver_compound_times.items():
        if len(times) < 4:
            # Not enough data for meaningful outlier detection
            group_stats[key] = {
                'q3': float('inf'),
                'iqr_upper': float('inf'),
                'median': float('inf'),
            }
            continue
        arr = np.array(times)
        q3 = float(np.percentile(arr, 75))
        iqr = q3 - float(np.percentile(arr, 25))
        median = float(np.median(arr))
        group_stats[key] = {
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

    # Phase 4: Compute is_valid (RACING, not warm-up)
    for lap in laps:
        lap['is_valid'] = (
            lap['classification'] == 'RACING'
            and not lap['is_warm_up']
        )

    return laps


def apply_practice_fuel_correction(
    laps: List[Dict],
    fuel_effect_per_kg: float,
) -> List[Dict]:
    """
    Apply approximate fuel correction to practice laps.

    Unlike race fuel correction (which knows total fuel and total laps),
    practice fuel correction uses a within-stint heuristic:
    - Estimated burn rate: ~1.6 kg/lap
    - Within each stint, normalize to the END of the stint (lightest point)
    - Earlier laps in the stint get a larger subtraction

    Formula per lap:
        laps_remaining_in_stint = max_tyre_life_in_stint - current_tyre_life
        fuel_remaining = laps_remaining_in_stint * 1.6
        corrected = raw - (fuel_remaining * fuel_effect_per_kg)

    When fuel_effect_per_kg is 0.0, correction is skipped entirely.
    Only RACING and ANOMALY laps with valid lap_time get corrected.
    """
    if not laps:
        return laps

    # If fuel correction is disabled, set all to None and return
    if fuel_effect_per_kg <= 0.0:
        for lap in laps:
            lap['fuel_corrected_time'] = None
        return laps

    BURN_RATE_KG_PER_LAP = 1.6

    # Compute max tyre_life per (driver, stint) for within-stint normalisation
    stint_max_life: Dict[tuple, int] = defaultdict(int)
    for lap in laps:
        driver = lap.get('driver')
        stint = lap.get('stint')
        tyre_life = lap.get('tyre_life')
        if driver is not None and stint is not None and tyre_life is not None:
            key = (driver, stint)
            if tyre_life > stint_max_life[key]:
                stint_max_life[key] = tyre_life

    for lap in laps:
        lap_time = lap.get('lap_time')
        classification = lap.get('classification', '')

        if lap_time is None or classification not in ('RACING', 'ANOMALY'):
            lap['fuel_corrected_time'] = None
            continue

        driver = lap.get('driver')
        stint = lap.get('stint')
        tyre_life = lap.get('tyre_life')

        if driver is None or stint is None or tyre_life is None:
            lap['fuel_corrected_time'] = lap_time  # No correction data available
            continue

        key = (driver, stint)
        max_life = stint_max_life.get(key, tyre_life)
        laps_remaining = max_life - tyre_life
        fuel_remaining = laps_remaining * BURN_RATE_KG_PER_LAP
        correction = fuel_remaining * fuel_effect_per_kg

        lap['fuel_corrected_time'] = lap_time - correction

    return laps


def derive_practice_traffic(
    laps: List[Dict],
    threshold: float = 1.5,
) -> List[Dict]:
    """
    Flag practice laps where gap to car ahead suggests dirty air.

    Same concept as race traffic derivation but with graceful fallback:
    practice sessions often lack cumulative_time and position data from
    FastF1. If fewer than 50% of laps on a given lap_number have both
    position and cumulative_time, traffic derivation is skipped for that
    lap group and all laps default to in_traffic=False.

    Args:
        laps: List of classified lap dicts
        threshold: Gap threshold in seconds (default 1.5)

    Returns:
        Same list with 'gap_to_car_ahead' and 'in_traffic' fields added.
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

        # Practice fallback: skip if fewer than 50% of drivers have data
        if len(valid) < 2 or len(valid) < len(lap_group) * 0.5:
            continue

        # Sort by position (P1 first)
        valid.sort(key=lambda l: l['position'])

        for i in range(1, len(valid)):
            current = valid[i]
            ahead = valid[i - 1]

            gap = abs(current['cumulative_time'] - ahead['cumulative_time'])
            current['gap_to_car_ahead'] = round(gap, 3)
            current['in_traffic'] = gap < threshold

    return laps
