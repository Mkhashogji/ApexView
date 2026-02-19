"""Tests for Phase 4: Pit Stop Analysis aggregation service."""

import pytest
from app.models.dto import PitStopResponse
from app.services.race.pit_stop_analysis import analyse_pit_stops


def _make_stop(
    driver="VER",
    team="Red Bull Racing",
    stop_number=1,
    lap_number=20,
    pit_lane_time=22.5,
    is_anomaly=False,
) -> PitStopResponse:
    """Helper to create a PitStopResponse object."""
    return PitStopResponse(
        driver=driver,
        team=team,
        stop_number=stop_number,
        lap_number=lap_number,
        pit_lane_time=pit_lane_time,
        is_anomaly=is_anomaly,
    )


class TestAnalysePitStops:
    """Tests for the pit stop analysis aggregation service."""

    def test_empty_input_returns_empty_response(self):
        result = analyse_pit_stops([])
        assert result['stops'] == []
        assert result['team_aggregates'] == []
        assert result['driver_aggregates'] == []
        assert result['gap_to_fastest'] == []
        assert result['grid_average'] == 0.0
        assert result['fastest_team'] is None
        assert result['insights']['quickest'] is None
        assert result['insights']['most_consistent'] is None
        assert result['anomaly_notes'] == []

    def test_basic_aggregation_two_teams(self):
        stops = [
            _make_stop(driver='VER', team='Red Bull Racing', pit_lane_time=22.5),
            _make_stop(driver='PER', team='Red Bull Racing', pit_lane_time=23.1, lap_number=21),
            _make_stop(driver='HAM', team='Mercedes', pit_lane_time=24.0, lap_number=22),
            _make_stop(driver='RUS', team='Mercedes', pit_lane_time=23.8, lap_number=23),
        ]
        result = analyse_pit_stops(stops)

        assert len(result['team_aggregates']) == 2
        # Red Bull should be first (faster average)
        assert result['team_aggregates'][0]['team'] == 'Red Bull Racing'
        assert result['team_aggregates'][0]['average_pit_lane_time'] == pytest.approx(22.8, abs=0.01)
        assert result['team_aggregates'][1]['team'] == 'Mercedes'
        assert result['team_aggregates'][1]['average_pit_lane_time'] == pytest.approx(23.9, abs=0.01)

        # Gap to fastest
        assert result['gap_to_fastest'][0]['gap_to_fastest'] == 0.0
        assert result['gap_to_fastest'][1]['gap_to_fastest'] == pytest.approx(1.1, abs=0.01)

        assert result['fastest_team'] == 'Red Bull Racing'

    def test_anomalies_excluded_from_averages(self):
        stops = [
            _make_stop(driver='VER', team='Red Bull Racing', stop_number=1,
                       pit_lane_time=22.5),
            _make_stop(driver='VER', team='Red Bull Racing', stop_number=2,
                       lap_number=40, pit_lane_time=38.0, is_anomaly=True),
            _make_stop(driver='PER', team='Red Bull Racing', stop_number=1,
                       lap_number=21, pit_lane_time=23.0),
        ]
        result = analyse_pit_stops(stops)

        # Average should exclude the 38.0s anomaly
        rb = result['team_aggregates'][0]
        assert rb['team'] == 'Red Bull Racing'
        assert rb['average_pit_lane_time'] == pytest.approx(22.75, abs=0.01)
        assert rb['stop_count'] == 2  # Only 2 normal stops counted

        # Anomaly should be in anomaly_notes
        assert len(result['anomaly_notes']) == 1
        assert result['anomaly_notes'][0]['driver'] == 'VER'
        assert result['anomaly_notes'][0]['pit_lane_time'] == 38.0

        # But all 3 stops should be in the stops pass-through
        assert len(result['stops']) == 3

    def test_tiered_consistency_iqr_for_three_plus_stops(self):
        """Teams with >=3 stops get IQR-based consistency."""
        stops = [
            _make_stop(driver='HAM', team='Mercedes', stop_number=1,
                       lap_number=18, pit_lane_time=23.5),
            _make_stop(driver='HAM', team='Mercedes', stop_number=2,
                       lap_number=38, pit_lane_time=24.0),
            _make_stop(driver='RUS', team='Mercedes', stop_number=1,
                       lap_number=19, pit_lane_time=23.8),
            _make_stop(driver='RUS', team='Mercedes', stop_number=2,
                       lap_number=39, pit_lane_time=24.2),
        ]
        result = analyse_pit_stops(stops)

        merc = result['team_aggregates'][0]
        assert merc['team'] == 'Mercedes'
        assert merc['consistency'] is not None
        assert merc['consistency'] > 0
        assert merc['consistency_type'] == 'iqr'

    def test_tiered_consistency_range_for_two_stops(self):
        """Teams with exactly 2 stops get absolute-difference consistency."""
        stops = [
            _make_stop(driver='VER', team='Red Bull Racing', stop_number=1,
                       lap_number=20, pit_lane_time=22.5),
            _make_stop(driver='PER', team='Red Bull Racing', stop_number=1,
                       lap_number=21, pit_lane_time=23.1),
        ]
        result = analyse_pit_stops(stops)

        rb = result['team_aggregates'][0]
        assert rb['team'] == 'Red Bull Racing'
        assert rb['consistency'] == pytest.approx(0.6, abs=0.001)
        assert rb['consistency_type'] == 'range'

    def test_tiered_consistency_null_for_one_stop(self):
        """Teams with only 1 stop have no consistency metric."""
        stops = [
            _make_stop(driver='VER', team='Red Bull Racing', stop_number=1,
                       lap_number=20, pit_lane_time=22.5),
        ]
        result = analyse_pit_stops(stops)

        rb = result['team_aggregates'][0]
        assert rb['consistency'] is None
        assert rb['consistency_type'] is None

    def test_tiered_consistency_mixed_strategies(self):
        """IQR and range teams are both evaluated for most-consistent insight."""
        stops = [
            # Red Bull: one-stop (2 stops total) -> range
            _make_stop(driver='VER', team='Red Bull Racing', stop_number=1,
                       lap_number=25, pit_lane_time=22.3),
            _make_stop(driver='PER', team='Red Bull Racing', stop_number=1,
                       lap_number=26, pit_lane_time=22.5),
            # Mercedes: two-stop (4 stops total) -> iqr
            _make_stop(driver='HAM', team='Mercedes', stop_number=1,
                       lap_number=15, pit_lane_time=23.0),
            _make_stop(driver='HAM', team='Mercedes', stop_number=2,
                       lap_number=35, pit_lane_time=23.8),
            _make_stop(driver='RUS', team='Mercedes', stop_number=1,
                       lap_number=16, pit_lane_time=23.5),
            _make_stop(driver='RUS', team='Mercedes', stop_number=2,
                       lap_number=36, pit_lane_time=24.0),
        ]
        result = analyse_pit_stops(stops)

        rb = next(t for t in result['team_aggregates'] if t['team'] == 'Red Bull Racing')
        merc = next(t for t in result['team_aggregates'] if t['team'] == 'Mercedes')

        assert rb['consistency_type'] == 'range'
        assert rb['consistency'] == pytest.approx(0.2, abs=0.001)

        assert merc['consistency_type'] == 'iqr'
        assert merc['consistency'] is not None

        # Red Bull (0.2s range) should be more consistent than Mercedes
        insight = result['insights']['most_consistent']
        assert insight is not None
        assert insight['team'] == 'Red Bull Racing'
        assert insight['consistency_type'] == 'range'

    def test_insight_quickest_team(self):
        stops = [
            _make_stop(driver='VER', team='Red Bull Racing', pit_lane_time=22.0),
            _make_stop(driver='HAM', team='Mercedes', pit_lane_time=24.0, lap_number=22),
        ]
        result = analyse_pit_stops(stops)

        quickest = result['insights']['quickest']
        assert quickest is not None
        assert quickest['team'] == 'Red Bull Racing'
        assert quickest['average_time'] == 22.0
        assert quickest['grid_average'] == pytest.approx(23.0, abs=0.01)
        assert quickest['percentage_faster'] > 0

    def test_insight_most_consistent_one_stop_race(self):
        """In a one-stop race, consistency uses 'range' type."""
        stops = [
            _make_stop(driver='VER', team='Red Bull Racing', pit_lane_time=22.0),
            _make_stop(driver='PER', team='Red Bull Racing', pit_lane_time=22.3, lap_number=21),
            _make_stop(driver='HAM', team='Mercedes', pit_lane_time=23.5, lap_number=22),
            _make_stop(driver='RUS', team='Mercedes', pit_lane_time=24.5, lap_number=23),
        ]
        result = analyse_pit_stops(stops)

        insight = result['insights']['most_consistent']
        assert insight is not None
        assert insight['team'] == 'Red Bull Racing'
        assert insight['consistency'] == pytest.approx(0.3, abs=0.001)
        assert insight['consistency_type'] == 'range'

    def test_insight_most_consistent_null_when_all_single_stop(self):
        """If every team has only 1 stop total, no consistency insight."""
        stops = [
            _make_stop(driver='VER', team='Red Bull Racing', pit_lane_time=22.0),
            _make_stop(driver='HAM', team='Mercedes', pit_lane_time=23.0, lap_number=22),
        ]
        result = analyse_pit_stops(stops)

        assert result['insights']['most_consistent'] is None

    def test_driver_aggregates_sorted_by_time(self):
        stops = [
            _make_stop(driver='VER', team='Red Bull Racing', pit_lane_time=22.0),
            _make_stop(driver='HAM', team='Mercedes', pit_lane_time=24.0, lap_number=22),
            _make_stop(driver='NOR', team='McLaren', pit_lane_time=23.0, lap_number=21),
        ]
        result = analyse_pit_stops(stops)

        drivers = [d['driver'] for d in result['driver_aggregates']]
        assert drivers == ['VER', 'NOR', 'HAM']

    def test_none_pit_lane_time_handled(self):
        """Stops with None pit_lane_time should not crash aggregation."""
        stops = [
            _make_stop(driver='VER', team='Red Bull Racing', pit_lane_time=None),
            _make_stop(driver='HAM', team='Mercedes', pit_lane_time=23.5, lap_number=22),
        ]
        result = analyse_pit_stops(stops)

        teams = [t['team'] for t in result['team_aggregates']]
        assert 'Mercedes' in teams
        assert result['grid_average'] == pytest.approx(23.5, abs=0.01)

    def test_all_stops_anomalous(self):
        """If every stop is anomalous, aggregates should be empty."""
        stops = [
            _make_stop(driver='VER', team='Red Bull Racing', pit_lane_time=40.0, is_anomaly=True),
            _make_stop(driver='HAM', team='Mercedes', pit_lane_time=45.0, is_anomaly=True, lap_number=22),
        ]
        result = analyse_pit_stops(stops)

        assert result['team_aggregates'] == []
        assert result['driver_aggregates'] == []
        assert result['fastest_team'] is None
        assert len(result['anomaly_notes']) == 2

    def test_grid_average_excludes_anomalies(self):
        stops = [
            _make_stop(driver='VER', team='Red Bull Racing', pit_lane_time=22.0),
            _make_stop(driver='HAM', team='Mercedes', pit_lane_time=24.0, lap_number=22),
            _make_stop(driver='NOR', team='McLaren', pit_lane_time=50.0, is_anomaly=True, lap_number=21),
        ]
        result = analyse_pit_stops(stops)

        # Grid average should only include VER (22.0) and HAM (24.0)
        assert result['grid_average'] == pytest.approx(23.0, abs=0.01)

    def test_stops_passthrough_includes_all(self):
        """The stops array passes through all stops including anomalies."""
        stops = [
            _make_stop(driver='VER', team='Red Bull Racing', pit_lane_time=22.0),
            _make_stop(driver='HAM', team='Mercedes', pit_lane_time=40.0, is_anomaly=True, lap_number=22),
        ]
        result = analyse_pit_stops(stops)

        assert len(result['stops']) == 2
