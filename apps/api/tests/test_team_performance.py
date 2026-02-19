"""Tests for Phase 5: Team Performance Quadrant aggregation service."""

import pytest
from app.services.race.team_performance import compute_team_performance


def _make_racing_lap(
    driver="VER",
    team="Red Bull Racing",
    lap_number=5,
    lap_time=95.0,
    fuel_corrected_time=93.0,
    speed_trap=310.0,
    classification="RACING",
) -> dict:
    """Helper to create a minimal racing lap dict."""
    return {
        'driver': driver,
        'team': team,
        'lap_number': lap_number,
        'lap_time': lap_time,
        'fuel_corrected_time': fuel_corrected_time,
        'speed_trap': speed_trap,
        'classification': classification,
    }


class TestComputeTeamPerformance:
    """Tests for the team performance aggregation service."""

    # --- Empty / invalid input ---

    def test_empty_laps_returns_empty_response(self):
        result = compute_team_performance([], 5000.0, "2025_17_Race")
        assert result['session_id'] == "2025_17_Race"
        assert result['teams'] == []
        assert result['field_averages']['top_speed'] == 0.0
        assert result['field_averages']['mean_speed'] == 0.0
        assert result['insights']['fastest_on_straights'] is None
        assert result['insights']['highest_mean_speed'] is None

    def test_zero_circuit_length_returns_empty(self):
        laps = [_make_racing_lap()]
        result = compute_team_performance(laps, 0.0, "2025_17_Race")
        assert result['teams'] == []

    def test_negative_circuit_length_returns_empty(self):
        laps = [_make_racing_lap()]
        result = compute_team_performance(laps, -100.0, "2025_17_Race")
        assert result['teams'] == []

    def test_no_racing_laps_returns_empty(self):
        laps = [
            _make_racing_lap(classification="IN_LAP"),
            _make_racing_lap(classification="OUT_LAP"),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")
        assert result['teams'] == []

    def test_racing_laps_with_none_lap_time_excluded(self):
        laps = [
            _make_racing_lap(lap_time=None, fuel_corrected_time=None, speed_trap=None),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")
        assert result['teams'] == []

    # --- Single team (deltas should be zero) ---

    def test_single_team_deltas_are_zero(self):
        laps = [
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             lap_time=95.0, fuel_corrected_time=93.0, speed_trap=310.0),
            _make_racing_lap(driver="PER", team="Red Bull Racing",
                             lap_time=96.0, fuel_corrected_time=94.0, speed_trap=308.0),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")

        assert len(result['teams']) == 1
        team = result['teams'][0]
        assert team['team'] == "Red Bull Racing"
        assert team['top_speed_delta'] == 0.0
        assert team['mean_speed_delta'] == 0.0

    # --- Two-team aggregation ---

    def test_two_team_aggregation(self):
        """Two teams: verify deltas are correct relative to field average."""
        laps = [
            # Red Bull: VER 310 km/h trap, PER 308 km/h trap
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             fuel_corrected_time=90.0, speed_trap=310.0),
            _make_racing_lap(driver="PER", team="Red Bull Racing",
                             fuel_corrected_time=92.0, speed_trap=308.0),
            # Mercedes: HAM 305 km/h trap, RUS 303 km/h trap
            _make_racing_lap(driver="HAM", team="Mercedes",
                             fuel_corrected_time=91.0, speed_trap=305.0),
            _make_racing_lap(driver="RUS", team="Mercedes",
                             fuel_corrected_time=93.0, speed_trap=303.0),
        ]
        circuit_length = 5000.0
        result = compute_team_performance(laps, circuit_length, "2025_17_Race")

        assert len(result['teams']) == 2

        # Field averages: top_speed = mean(309, 304) = 306.5
        # RB top_speed = mean(310, 308) = 309.0
        # Merc top_speed = mean(305, 303) = 304.0
        assert result['field_averages']['top_speed'] == pytest.approx(306.5, abs=0.1)

        rb = next(t for t in result['teams'] if t['team'] == 'Red Bull Racing')
        merc = next(t for t in result['teams'] if t['team'] == 'Mercedes')

        assert rb['top_speed'] == pytest.approx(309.0, abs=0.1)
        assert merc['top_speed'] == pytest.approx(304.0, abs=0.1)

        assert rb['top_speed_delta'] == pytest.approx(2.5, abs=0.1)
        assert merc['top_speed_delta'] == pytest.approx(-2.5, abs=0.1)

    # --- Mean speed calculation ---

    def test_mean_speed_formula(self):
        """Mean speed = circuit_length / fuel_corrected_time * 3.6."""
        circuit_length = 6000.0  # metres
        fct = 100.0  # seconds
        # Expected: 6000 / 100 * 3.6 = 216.0 km/h

        laps = [
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             fuel_corrected_time=fct, speed_trap=300.0),
        ]
        result = compute_team_performance(laps, circuit_length, "2025_17_Race")

        assert len(result['teams']) == 1
        assert result['teams'][0]['mean_speed'] == pytest.approx(216.0, abs=0.01)

    def test_mean_speed_falls_back_to_lap_time(self):
        """If fuel_corrected_time is None, use lap_time for mean speed."""
        circuit_length = 5000.0
        lap_time = 100.0
        # Expected: 5000 / 100 * 3.6 = 180.0 km/h

        laps = [
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             lap_time=lap_time, fuel_corrected_time=None, speed_trap=300.0),
        ]
        result = compute_team_performance(laps, circuit_length, "2025_17_Race")

        assert len(result['teams']) == 1
        assert result['teams'][0]['mean_speed'] == pytest.approx(180.0, abs=0.01)

    # --- Non-RACING laps excluded ---

    def test_non_racing_laps_excluded(self):
        """Only RACING classification laps are used."""
        laps = [
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             speed_trap=310.0, classification="RACING"),
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             speed_trap=200.0, classification="IN_LAP"),
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             speed_trap=150.0, classification="SAFETY_CAR"),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")

        assert len(result['teams']) == 1
        # Only the RACING lap's speed_trap (310.0) should be used
        assert result['teams'][0]['top_speed'] == pytest.approx(310.0, abs=0.1)

    # --- Warm-up laps ARE included ---

    def test_warm_up_laps_included(self):
        """Unlike Phase 3 tyre degradation, warm-up laps are included."""
        laps = [
            {**_make_racing_lap(speed_trap=310.0, fuel_corrected_time=90.0),
             'is_warm_up': True},
            _make_racing_lap(speed_trap=312.0, fuel_corrected_time=89.0),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")

        assert len(result['teams']) == 1
        # Both laps should contribute: mean(310, 312) = 311.0
        assert result['teams'][0]['top_speed'] == pytest.approx(311.0, abs=0.1)

    # --- Missing speed_trap handling ---

    def test_missing_speed_trap_excluded_from_top_speed(self):
        """Drivers without speed_trap data are excluded from top speed."""
        laps = [
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             speed_trap=310.0, fuel_corrected_time=90.0),
            _make_racing_lap(driver="PER", team="Red Bull Racing",
                             speed_trap=None, fuel_corrected_time=92.0),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")

        # Team top speed should only come from VER (310.0), not average with None
        assert result['teams'][0]['top_speed'] == pytest.approx(310.0, abs=0.1)
        # Mean speed should still use both drivers
        ver_mean = (5000.0 / 90.0) * 3.6
        per_mean = (5000.0 / 92.0) * 3.6
        expected_team_mean = (ver_mean + per_mean) / 2
        assert result['teams'][0]['mean_speed'] == pytest.approx(expected_team_mean, abs=0.01)

    def test_all_speed_traps_missing_returns_empty(self):
        """If no driver has speed_trap data, return empty response."""
        laps = [
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             speed_trap=None, fuel_corrected_time=90.0),
            _make_racing_lap(driver="HAM", team="Mercedes",
                             speed_trap=None, fuel_corrected_time=91.0),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")

        assert result['teams'] == []
        assert result['field_averages']['top_speed'] == 0.0

    # --- Single driver per team ---

    def test_single_driver_per_team(self):
        """When a teammate DNFs, single driver still contributes."""
        laps = [
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             speed_trap=315.0, fuel_corrected_time=88.0),
            _make_racing_lap(driver="HAM", team="Mercedes",
                             speed_trap=310.0, fuel_corrected_time=90.0),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")

        assert len(result['teams']) == 2
        rb = next(t for t in result['teams'] if t['team'] == 'Red Bull Racing')
        assert rb['top_speed'] == pytest.approx(315.0, abs=0.1)

    # --- Field averages are team-level means ---

    def test_field_averages_weight_teams_equally(self):
        """Field averages are mean-of-team-means, not mean-of-all-drivers."""
        laps = [
            # Red Bull: 2 laps
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             speed_trap=310.0, fuel_corrected_time=90.0),
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             speed_trap=312.0, fuel_corrected_time=89.0, lap_number=6),
            # Mercedes: 1 lap
            _make_racing_lap(driver="HAM", team="Mercedes",
                             speed_trap=300.0, fuel_corrected_time=95.0),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")

        # RB top speed = mean(310, 312) = 311.0
        # Merc top speed = 300.0
        # Field average = mean(311.0, 300.0) = 305.5
        assert result['field_averages']['top_speed'] == pytest.approx(305.5, abs=0.1)

    # --- Sorting ---

    def test_teams_sorted_by_mean_speed_descending(self):
        laps = [
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             fuel_corrected_time=88.0, speed_trap=315.0),
            _make_racing_lap(driver="HAM", team="Mercedes",
                             fuel_corrected_time=90.0, speed_trap=310.0),
            _make_racing_lap(driver="NOR", team="McLaren",
                             fuel_corrected_time=89.0, speed_trap=312.0),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")

        teams = [t['team'] for t in result['teams']]
        # Fastest mean speed first: RB (88s) → McLaren (89s) → Mercedes (90s)
        assert teams == ['Red Bull Racing', 'McLaren', 'Mercedes']

    # --- Insights ---

    def test_insight_fastest_on_straights(self):
        """Insight identifies the team with highest top speed."""
        laps = [
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             speed_trap=320.0, fuel_corrected_time=90.0),
            _make_racing_lap(driver="HAM", team="Mercedes",
                             speed_trap=310.0, fuel_corrected_time=91.0),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")

        insight = result['insights']['fastest_on_straights']
        assert insight is not None
        assert insight['team'] == 'Red Bull Racing'
        assert insight['value'] == pytest.approx(320.0, abs=0.1)
        assert insight['delta'] > 0  # Above field average

    def test_insight_highest_mean_speed(self):
        """Insight identifies the team with highest mean speed."""
        laps = [
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             speed_trap=310.0, fuel_corrected_time=88.0),
            _make_racing_lap(driver="HAM", team="Mercedes",
                             speed_trap=315.0, fuel_corrected_time=92.0),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")

        insight = result['insights']['highest_mean_speed']
        assert insight is not None
        # RB has faster fuel_corrected_time → higher mean speed
        assert insight['team'] == 'Red Bull Racing'
        assert insight['delta'] > 0

    # --- Multiple laps per driver ---

    def test_multiple_laps_per_driver_averaged(self):
        """Driver with multiple laps gets mean of all lap values."""
        laps = [
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             speed_trap=310.0, fuel_corrected_time=90.0, lap_number=5),
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             speed_trap=314.0, fuel_corrected_time=88.0, lap_number=6),
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             speed_trap=312.0, fuel_corrected_time=89.0, lap_number=7),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")

        assert len(result['teams']) == 1
        # VER top speed mean: (310 + 314 + 312) / 3 = 312.0
        assert result['teams'][0]['top_speed'] == pytest.approx(312.0, abs=0.1)

    # --- Rounding ---

    def test_rounding_precision(self):
        """Top speed rounded to 1dp, mean speed to 2dp, deltas match."""
        laps = [
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             speed_trap=310.456, fuel_corrected_time=90.123),
            _make_racing_lap(driver="HAM", team="Mercedes",
                             speed_trap=305.789, fuel_corrected_time=91.456),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")

        for team in result['teams']:
            # Top speed: 1 decimal place
            assert team['top_speed'] == round(team['top_speed'], 1)
            # Mean speed: 2 decimal places
            assert team['mean_speed'] == round(team['mean_speed'], 2)

    # --- Edge case: zero fuel_corrected_time ---

    def test_zero_fuel_corrected_time_excluded(self):
        """Zero fuel_corrected_time should not cause division by zero."""
        laps = [
            _make_racing_lap(driver="VER", team="Red Bull Racing",
                             fuel_corrected_time=0.0, speed_trap=310.0),
            _make_racing_lap(driver="HAM", team="Mercedes",
                             fuel_corrected_time=90.0, speed_trap=305.0),
        ]
        result = compute_team_performance(laps, 5000.0, "2025_17_Race")

        # VER has no mean speed data (0 fct excluded), but should still
        # have top speed data if lap_time check passes
        # Actually VER's lap has lap_time=95.0 (default) so it passes the
        # RACING filter, but fct=0 is excluded from mean speed calculation
        merc = next((t for t in result['teams'] if t['team'] == 'Mercedes'), None)
        assert merc is not None
