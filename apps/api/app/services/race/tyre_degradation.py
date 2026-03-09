"""
Phase 3: Tyre Degradation Analysis Service

Computes fuel-adjusted tyre degradation with linear regression for each
driver (or team) per compound. Consumes Phase 1's processed race data
with pre-computed fuel_corrected_time.
"""

import logging
from typing import Optional, Dict, List
from collections import defaultdict
from scipy.stats import linregress

from app.services.race.race_data_service import get_processed_race_data

logger = logging.getLogger(__name__)

# Minimum laps required for regression (excluding warm-up)
MIN_REGRESSION_LAPS = 7

# Compound display order (hardest → softest, wets at end)
COMPOUND_ORDER = ['HARD', 'MEDIUM', 'SOFT', 'INTERMEDIATE', 'WET']


async def compute_tyre_degradation(
    session_id: str,
    fuel_effect_per_kg: float = 0.032,
    mode: str = 'driver',
) -> dict:
    """
    Main entry point for Phase 3 computation.

    Args:
        session_id: e.g. '2025_17_Race'
        fuel_effect_per_kg: fuel correction factor (from Track Intelligence)
        mode: 'driver' or 'team'

    Returns:
        Dict matching TyreDegradationResponse schema
    """
    race_data = await get_processed_race_data(session_id, fuel_effect_per_kg)
    laps = race_data['laps']

    # Filter to regression-eligible laps:
    # - RACING classification (excludes in/out laps, SC, VSC, red flag, formation)
    # - Not warm-up (first 2 laps of each stint)
    # - Has valid fuel_corrected_time
    eligible_laps = [
        lap for lap in laps
        if lap['classification'] == 'RACING'
        and not lap.get('is_warm_up', False)
        and lap.get('fuel_corrected_time') is not None
        and lap.get('tyre_life') is not None
    ]

    logger.info(
        "Phase 3: %d eligible laps from %d total for session %s (mode=%s)",
        len(eligible_laps), len(laps), session_id, mode,
    )

    # Group by compound
    compounds_data: Dict[str, List[dict]] = defaultdict(list)
    for lap in eligible_laps:
        compound = lap.get('compound')
        if compound:
            compounds_data[compound].append(lap)

    # For each compound, group by driver or team, then compute regression
    compounds_result = []
    for compound, compound_laps in compounds_data.items():
        drivers_result = _compute_per_group(compound_laps, mode)
        compounds_result.append({
            'compound': compound,
            'drivers': drivers_result,
        })

    # Sort compounds by display order
    def compound_sort_key(x):
        try:
            return COMPOUND_ORDER.index(x['compound'])
        except ValueError:
            return 999

    compounds_result.sort(key=compound_sort_key)

    compound_order = [c for c in COMPOUND_ORDER if c in compounds_data]

    # Enrich with warm-up counts from full lap set
    _enrich_warm_up_counts(compounds_result, laps, mode)

    return {
        'session_id': session_id,
        'mode': mode,
        'compounds': compounds_result,
        'compound_order': compound_order,
    }


def _compute_per_group(laps: List[dict], mode: str) -> List[dict]:
    """
    Group laps by driver or team, compute regression for each group.
    """
    groups: Dict[str, dict] = {}
    for lap in laps:
        key = lap.get('team', 'Unknown') if mode == 'team' else lap['driver']
        if key not in groups:
            groups[key] = {
                'identifier': key,
                'team': lap.get('team', 'Unknown'),
                'laps': [],
            }
        groups[key]['laps'].append(lap)

    results = []
    for key, group_data in groups.items():
        group_laps = group_data['laps']

        # Build data points for response
        data_points = [
            {
                'tyre_age': lap.get('tyre_life') or 0,
                'fuel_adjusted_time': lap['fuel_corrected_time'],
                'raw_time': lap['lap_time'],
                'lap_number': lap['lap_number'],
                'driver': lap['driver'],
                'team': lap.get('team', 'Unknown'),
                'stint_number': lap.get('stint', 1),
            }
            for lap in group_laps
            if lap.get('fuel_corrected_time') is not None
            and lap.get('lap_time') is not None
        ]

        # Compute regression if sufficient data
        regression = None
        wear_rate = None
        usable_count = len(data_points)

        if usable_count >= MIN_REGRESSION_LAPS:
            regression, wear_rate = _compute_regression(data_points)
        else:
            logger.debug(
                "Insufficient data for regression: %s has %d laps (need %d)",
                key, usable_count, MIN_REGRESSION_LAPS,
            )

        results.append({
            'identifier': group_data['identifier'],
            'team': group_data['team'],
            'data_points': data_points,
            'regression': regression,
            'wear_rate': wear_rate,
            'usable_lap_count': usable_count,
            'total_stint_laps': 0,      # Enriched later by _enrich_warm_up_counts
            'warm_up_laps_excluded': 0,  # Enriched later
        })

    return results


def _compute_regression(
    data_points: List[dict],
) -> tuple[Optional[dict], Optional[float]]:
    """
    Compute linear regression on (tyre_age, fuel_adjusted_time).

    Returns:
        (regression_dict, wear_rate) or (None, None) if computation fails
    """
    x = [p['tyre_age'] for p in data_points]
    y = [p['fuel_adjusted_time'] for p in data_points]

    try:
        result = linregress(x, y)

        start_x = min(x)
        end_x = max(x)

        regression = {
            'start_x': float(start_x),
            'start_y': float(result.intercept + result.slope * start_x),
            'end_x': float(end_x),
            'end_y': float(result.intercept + result.slope * end_x),
            'slope': float(result.slope),
            'intercept': float(result.intercept),
            'r_squared': float(result.rvalue ** 2),
        }

        wear_rate = float(result.slope)

        logger.debug(
            "Regression: slope=%.4f s/lap, R²=%.3f, n=%d",
            wear_rate, regression['r_squared'], len(x),
        )

        return regression, wear_rate

    except Exception as e:
        logger.warning("Regression computation failed: %s", e)
        return None, None


def _enrich_warm_up_counts(
    compounds_result: List[dict],
    all_laps: List[dict],
    mode: str,
) -> None:
    """
    Enrich each driver/team entry with total stint laps and warm-up exclusion counts.
    Operates on all laps (not just eligible) to count warm-ups accurately.
    """
    for compound_data in compounds_result:
        compound = compound_data['compound']
        for driver_data in compound_data['drivers']:
            identifier = driver_data['identifier']

            # Find all RACING laps for this driver/team on this compound
            if mode == 'team':
                matching_laps = [
                    lap for lap in all_laps
                    if lap.get('team') == identifier
                    and lap.get('compound') == compound
                    and lap.get('classification') == 'RACING'
                ]
            else:
                matching_laps = [
                    lap for lap in all_laps
                    if lap.get('driver') == identifier
                    and lap.get('compound') == compound
                    and lap.get('classification') == 'RACING'
                ]

            total = len(matching_laps)
            warm_ups = sum(1 for lap in matching_laps if lap.get('is_warm_up', False))

            driver_data['total_stint_laps'] = total
            driver_data['warm_up_laps_excluded'] = warm_ups
