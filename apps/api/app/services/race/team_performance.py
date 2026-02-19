"""
Phase 5: Team Performance Quadrant — aggregation service.

Consumes processed race lap data and computes per-team top speed (SpeedST)
and mean speed (track_length / fuel_corrected_time * 3.6) metrics,
field averages, deltas, and deterministic insight data.

Top speed uses raw SpeedST values (not fuel-corrected — drag-limited).
Mean speed uses fuel-corrected lap times to isolate car performance from
fuel weight effects.

Unlike Phase 3 (tyre degradation), warm-up laps ARE included — the
aero setup is constant throughout a stint and warm-up noise (~0.5 km/h)
is small relative to inter-team differences (~3-8 km/h).
"""

import logging
import numpy as np
from typing import List, Dict, Any
from collections import defaultdict

logger = logging.getLogger(__name__)


def compute_team_performance(
    laps: List[Dict],
    circuit_length_m: float,
    session_id: str,
) -> Dict[str, Any]:
    """
    Compute per-team top speed and mean speed from race lap data.

    Args:
        laps: Enriched race laps from get_processed_race_data()['laps'].
        circuit_length_m: Circuit length in metres (from get_track_info).
        session_id: Session identifier, e.g. '2025_17_Race'.

    Returns:
        Dict matching TeamPerformanceResponse schema.
    """
    if not laps or circuit_length_m <= 0:
        return _empty_response(session_id)

    # --- Filter: RACING laps only (include warm-up) ---
    racing_laps = [
        lap for lap in laps
        if lap.get('classification') == 'RACING'
        and lap.get('lap_time') is not None
    ]

    if not racing_laps:
        return _empty_response(session_id)

    # --- Step 1: Per-driver aggregation ---
    driver_data: Dict[str, Dict[str, Any]] = defaultdict(lambda: {
        'team': None,
        'speed_traps': [],
        'lap_speeds': [],
    })

    for lap in racing_laps:
        driver = lap.get('driver')
        if not driver:
            continue
        d = driver_data[driver]
        if d['team'] is None:
            d['team'] = lap.get('team')

        # Top speed: use raw SpeedST
        st = lap.get('speed_trap')
        if st is not None:
            d['speed_traps'].append(st)

        # Mean speed: track_length / fuel_corrected_time * 3.6
        fct = lap.get('fuel_corrected_time') or lap.get('lap_time')
        if fct is not None and fct > 0:
            mean_speed_kmh = (circuit_length_m / fct) * 3.6
            d['lap_speeds'].append(mean_speed_kmh)

    # --- Step 2: Per-driver means ---
    driver_means: Dict[str, Dict[str, Any]] = {}
    for driver, data in driver_data.items():
        if not data['lap_speeds']:
            continue
        # Top speed: if no speed_trap data, exclude from top speed but keep mean speed
        top_speed = float(np.mean(data['speed_traps'])) if data['speed_traps'] else None
        mean_speed = float(np.mean(data['lap_speeds']))
        driver_means[driver] = {
            'team': data['team'],
            'top_speed': top_speed,
            'mean_speed': mean_speed,
        }

    if not driver_means:
        return _empty_response(session_id)

    # --- Step 3: Per-team means (average both drivers) ---
    team_drivers: Dict[str, List[Dict]] = defaultdict(list)
    for driver, means in driver_means.items():
        team = means['team'] or 'Unknown'
        team_drivers[team].append(means)

    team_stats = []
    for team, drivers in team_drivers.items():
        # Mean speed: always available
        team_mean_speed = float(np.mean([d['mean_speed'] for d in drivers]))

        # Top speed: only from drivers who have speed_trap data
        drivers_with_top_speed = [d for d in drivers if d['top_speed'] is not None]
        team_top_speed = (
            float(np.mean([d['top_speed'] for d in drivers_with_top_speed]))
            if drivers_with_top_speed
            else None
        )

        team_stats.append({
            'team': team,
            'top_speed': round(team_top_speed, 1) if team_top_speed is not None else None,
            'mean_speed': round(team_mean_speed, 2),
        })

    # Separate teams with and without top speed data
    teams_with_top_speed = [t for t in team_stats if t['top_speed'] is not None]
    teams_without_top_speed = [t for t in team_stats if t['top_speed'] is None]

    if not teams_with_top_speed:
        # No speed trap data at all — return empty
        return _empty_response(session_id)

    # --- Step 4: Field averages (mean of all teams that have data) ---
    field_top_speed = float(np.mean([t['top_speed'] for t in teams_with_top_speed]))
    all_mean_speeds = [t['mean_speed'] for t in team_stats]
    field_mean_speed = float(np.mean(all_mean_speeds))

    # --- Step 5: Compute deltas ---
    teams_result = []
    for ts in teams_with_top_speed:
        teams_result.append({
            'team': ts['team'],
            'top_speed': ts['top_speed'],
            'mean_speed': ts['mean_speed'],
            'top_speed_delta': round(ts['top_speed'] - field_top_speed, 1),
            'mean_speed_delta': round(ts['mean_speed'] - field_mean_speed, 2),
        })

    # Sort by mean speed descending (fastest overall team first)
    teams_result.sort(key=lambda t: t['mean_speed'], reverse=True)

    # --- Step 6: Insights ---
    insights = _compute_insights(teams_result, field_top_speed, field_mean_speed)

    return {
        'session_id': session_id,
        'teams': teams_result,
        'field_averages': {
            'top_speed': round(field_top_speed, 1),
            'mean_speed': round(field_mean_speed, 2),
        },
        'insights': insights,
    }


def _compute_insights(
    teams: List[Dict],
    field_top_speed: float,
    field_mean_speed: float,
) -> Dict[str, Any]:
    """Compute deterministic insight data for template-based cards."""
    if not teams:
        return {'fastest_on_straights': None, 'highest_mean_speed': None}

    # Fastest on straights: highest top speed
    fastest_straight = max(teams, key=lambda t: t['top_speed'])

    # Highest mean speed: highest mean speed
    highest_mean = max(teams, key=lambda t: t['mean_speed'])

    return {
        'fastest_on_straights': {
            'team': fastest_straight['team'],
            'value': fastest_straight['top_speed'],
            'delta': round(fastest_straight['top_speed'] - field_top_speed, 1),
        },
        'highest_mean_speed': {
            'team': highest_mean['team'],
            'value': highest_mean['mean_speed'],
            'delta': round(highest_mean['mean_speed'] - field_mean_speed, 2),
        },
    }


def _empty_response(session_id: str) -> Dict[str, Any]:
    """Return empty structure when no valid data is available."""
    return {
        'session_id': session_id,
        'teams': [],
        'field_averages': {'top_speed': 0.0, 'mean_speed': 0.0},
        'insights': {'fastest_on_straights': None, 'highest_mean_speed': None},
    }
