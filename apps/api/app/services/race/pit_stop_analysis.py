"""
Pit Stop Analysis — Phase 4 aggregation service.

Consumes pit stop records from extract_pit_stops() (PitStopResponse objects)
and produces team/driver aggregates, gap-to-fastest, grid average, and
deterministic insight data for template-based frontend cards.

Tiered consistency metric:
  ≥3 stops → IQR (robust to outlier skew)
  2 stops  → absolute difference (valid pair comparison)
  1 stop   → null (consistency undefined for single observation)
"""

import logging
import numpy as np
from typing import List, Dict, Optional, Any
from collections import defaultdict

from app.models.dto import PitStopResponse

logger = logging.getLogger(__name__)


def analyse_pit_stops(pit_stops: List[PitStopResponse]) -> Dict[str, Any]:
    """
    Aggregate pit stop data into team/driver analysis with insights.

    Args:
        pit_stops: List of PitStopResponse objects from extract_pit_stops().

    Returns:
        Dict matching PitStopAnalysisResponse structure.
    """
    if not pit_stops:
        return _empty_response()

    # Separate normal stops from anomalies for aggregation
    normal_stops = [s for s in pit_stops if not s.is_anomaly]

    # --- Team Aggregates ---
    team_times: Dict[str, List[float]] = defaultdict(list)
    team_names: Dict[str, str] = {}  # Preserve team name casing
    for stop in normal_stops:
        team = stop.team or 'Unknown'
        if stop.pit_lane_time is not None:
            team_times[team].append(stop.pit_lane_time)
            team_names[team] = team

    team_aggregates = []
    for team, times in team_times.items():
        times_arr = np.array(times)
        avg = float(np.mean(times_arr))
        count = len(times)

        # Tiered consistency metric
        consistency = None
        consistency_type = None
        if count >= 3:
            q1 = float(np.percentile(times_arr, 25))
            q3 = float(np.percentile(times_arr, 75))
            consistency = round(q3 - q1, 3)
            consistency_type = 'iqr'
        elif count == 2:
            consistency = round(abs(float(times_arr[0]) - float(times_arr[1])), 3)
            consistency_type = 'range'

        team_aggregates.append({
            'team': team,
            'average_pit_lane_time': round(avg, 3),
            'stop_count': count,
            'consistency': consistency,
            'consistency_type': consistency_type,
        })

    # Sort by average time (fastest first)
    team_aggregates.sort(key=lambda x: x['average_pit_lane_time'])

    # --- Driver Aggregates ---
    driver_data: Dict[str, Dict[str, Any]] = {}
    for stop in normal_stops:
        driver = stop.driver
        if stop.pit_lane_time is not None:
            if driver not in driver_data:
                driver_data[driver] = {
                    'driver': driver,
                    'team': stop.team or 'Unknown',
                    'times': [],
                }
            driver_data[driver]['times'].append(stop.pit_lane_time)

    driver_aggregates = []
    for driver, data in driver_data.items():
        times_arr = np.array(data['times'])
        driver_aggregates.append({
            'driver': data['driver'],
            'team': data['team'],
            'average_pit_lane_time': round(float(np.mean(times_arr)), 3),
            'stop_count': len(data['times']),
        })

    driver_aggregates.sort(key=lambda x: x['average_pit_lane_time'])

    # --- Gap to Fastest ---
    fastest_team_avg = team_aggregates[0]['average_pit_lane_time'] if team_aggregates else 0
    gap_to_fastest = []
    for ta in team_aggregates:
        gap_to_fastest.append({
            'team': ta['team'],
            'gap_to_fastest': round(ta['average_pit_lane_time'] - fastest_team_avg, 3),
        })

    # --- Grid Average ---
    all_normal_times = [s.pit_lane_time for s in normal_stops if s.pit_lane_time is not None]
    grid_average = round(float(np.mean(all_normal_times)), 3) if all_normal_times else 0.0

    # --- Insight Data ---
    insights = _compute_insights(team_aggregates, grid_average)

    # --- Anomaly Summary ---
    anomalies = [s for s in pit_stops if s.is_anomaly]
    anomaly_notes = []
    for a in anomalies:
        anomaly_notes.append({
            'driver': a.driver,
            'team': a.team or 'Unknown',
            'stop_number': a.stop_number,
            'lap_number': a.lap_number,
            'pit_lane_time': a.pit_lane_time,
        })

    # Convert PitStopResponse objects to dicts for serialisation
    stops_dicts = []
    for s in pit_stops:
        stops_dicts.append({
            'driver': s.driver,
            'team': s.team,
            'stop_number': s.stop_number,
            'lap_number': s.lap_number,
            'pit_lane_time': s.pit_lane_time,
            'is_anomaly': s.is_anomaly,
        })

    return {
        'stops': pit_stops,  # Pass through original PitStopResponse objects
        'team_aggregates': team_aggregates,
        'driver_aggregates': driver_aggregates,
        'gap_to_fastest': gap_to_fastest,
        'grid_average': grid_average,
        'fastest_team': team_aggregates[0]['team'] if team_aggregates else None,
        'insights': insights,
        'anomaly_notes': anomaly_notes,
    }


def _compute_insights(
    team_aggregates: List[Dict],
    grid_average: float,
) -> Dict[str, Any]:
    """Compute deterministic insight data for template-based cards."""
    if not team_aggregates or grid_average == 0:
        return {'quickest': None, 'most_consistent': None}

    # Quickest on Average
    quickest = team_aggregates[0]  # Already sorted ascending
    quickest_pct = round(
        ((grid_average - quickest['average_pit_lane_time']) / grid_average) * 100, 1
    )

    # Most Consistent — lowest consistency value across all teams with a value,
    # regardless of whether computed via IQR or absolute difference.
    # Both metrics are in seconds and both measure "spread", so they are
    # directly comparable for selecting the most consistent team.
    teams_with_consistency = [
        t for t in team_aggregates if t['consistency'] is not None
    ]
    most_consistent = None
    if teams_with_consistency:
        most_consistent_team = min(
            teams_with_consistency, key=lambda t: t['consistency']
        )
        most_consistent = {
            'team': most_consistent_team['team'],
            'consistency': most_consistent_team['consistency'],
            'consistency_type': most_consistent_team['consistency_type'],
        }

    return {
        'quickest': {
            'team': quickest['team'],
            'average_time': quickest['average_pit_lane_time'],
            'percentage_faster': quickest_pct,
            'grid_average': grid_average,
        },
        'most_consistent': most_consistent,
    }


def _empty_response() -> Dict[str, Any]:
    """Return empty structure when no pit stop data is available."""
    return {
        'stops': [],
        'team_aggregates': [],
        'driver_aggregates': [],
        'gap_to_fastest': [],
        'grid_average': 0.0,
        'fastest_team': None,
        'insights': {'quickest': None, 'most_consistent': None},
        'anomaly_notes': [],
    }
