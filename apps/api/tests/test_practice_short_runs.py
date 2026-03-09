"""
Unit tests for compute_short_run_stats() in practice_data_service.

All tests are self-contained. Helpers defined at module level.
Float assertions use pytest.approx(). No shared conftest.
"""

import pytest
from app.services.practice.practice_data_service import (
    compute_short_run_stats,
    _is_lap_in_short_stints,
)


# =============================================================================
# Helpers
# =============================================================================


def _make_lap_point(
    lap_time: float,
    compound: str = 'SOFT',
    tyre_life: int = 2,
    lap_number: int = 10,
) -> dict:
    return {
        'lap_number': lap_number,
        'lap_time': lap_time,
        'compound': compound,
        'tyre_life': tyre_life,
        'in_traffic': False,
    }


def _make_short_stint(
    driver: str,
    team: str,
    lap_times: list,
    compound: str = 'SOFT',
    stint_number: int = 1,
    lap_number_start: int = 10,
) -> dict:
    """Create a short run stint dict matching the shape from get_processed_practice_data."""
    lap_points = [
        _make_lap_point(lt, compound, i + 1, lap_number_start + i)
        for i, lt in enumerate(lap_times)
    ]
    return {
        'driver': driver,
        'team': team,
        'stint_number': stint_number,
        'compound': compound,
        'run_type': 'short_run',
        'valid_lap_count': len(lap_times),
        'total_lap_count': len(lap_times),
        'average_time': sum(lap_times) / len(lap_times) if lap_times else 0,
        'lap_points': lap_points,
        'stats': {},
        'degradation_hint': None,
        'clean_air_pct': 1.0,
        'gap_to_fastest': 0,
    }


# =============================================================================
# Test Empty Input
# =============================================================================


class TestEmptyInput:
    def test_empty_list_returns_empty(self):
        result = compute_short_run_stats([])
        assert result == []

    def test_single_stint_no_lap_points_returns_empty(self):
        stint = _make_short_stint('VER', 'Red Bull', [])
        stint['lap_points'] = []
        result = compute_short_run_stats([stint])
        assert result == []

    def test_stint_with_none_lap_times_returns_empty(self):
        stint = _make_short_stint('VER', 'Red Bull', [88.0])
        stint['lap_points'] = [{'lap_time': None, 'compound': 'SOFT', 'tyre_life': 1}]
        result = compute_short_run_stats([stint])
        assert result == []


# =============================================================================
# Test Single Driver
# =============================================================================


class TestSingleDriver:
    def test_single_driver_single_lap(self):
        stints = [_make_short_stint('VER', 'Red Bull', [88.500])]
        result = compute_short_run_stats(stints)
        assert len(result) == 1
        assert result[0]['driver'] == 'VER'
        assert result[0]['team'] == 'Red Bull'
        assert result[0]['best_lap_time'] == pytest.approx(88.500)
        assert result[0]['gap_to_p1'] == pytest.approx(0.0)
        assert result[0]['position'] == 1

    def test_single_driver_multiple_laps_picks_minimum(self):
        stints = [_make_short_stint('VER', 'Red Bull', [89.1, 88.3, 88.7])]
        result = compute_short_run_stats(stints)
        assert result[0]['best_lap_time'] == pytest.approx(88.3)

    def test_compound_from_best_lap_not_stint_compound(self):
        """If best lap is on lap 2 with MEDIUM, compound should be MEDIUM."""
        stint = _make_short_stint('HAM', 'Mercedes', [89.5, 88.2, 89.1])
        stint['lap_points'][0]['compound'] = 'SOFT'
        stint['lap_points'][1]['compound'] = 'MEDIUM'
        stint['lap_points'][2]['compound'] = 'SOFT'
        result = compute_short_run_stats([stint])
        assert result[0]['best_lap_time'] == pytest.approx(88.2)
        assert result[0]['compound'] == 'MEDIUM'

    def test_tyre_life_from_best_lap(self):
        stint = _make_short_stint('NOR', 'McLaren', [88.9, 88.1])
        result = compute_short_run_stats([stint])
        assert result[0]['tyre_life'] == 2  # Best lap is lap 2, tyre_life=2


# =============================================================================
# Test Multiple Drivers
# =============================================================================


class TestMultipleDrivers:
    def test_ranking_is_ascending_by_best_lap(self):
        stints = [
            _make_short_stint('HAM', 'Mercedes', [89.2]),
            _make_short_stint('VER', 'Red Bull', [88.5]),
            _make_short_stint('NOR', 'McLaren', [88.9]),
        ]
        result = compute_short_run_stats(stints)
        assert [r['driver'] for r in result] == ['VER', 'NOR', 'HAM']
        assert [r['position'] for r in result] == [1, 2, 3]

    def test_gap_to_p1_correctness(self):
        stints = [
            _make_short_stint('VER', 'Red Bull', [88.0]),
            _make_short_stint('HAM', 'Mercedes', [88.5]),
            _make_short_stint('NOR', 'McLaren', [89.2]),
        ]
        result = compute_short_run_stats(stints)
        assert result[0]['gap_to_p1'] == pytest.approx(0.0)
        assert result[1]['gap_to_p1'] == pytest.approx(0.5)
        assert result[2]['gap_to_p1'] == pytest.approx(1.2)

    def test_p1_driver_has_position_1(self):
        stints = [
            _make_short_stint('HAM', 'Mercedes', [89.0]),
            _make_short_stint('VER', 'Red Bull', [88.0]),
        ]
        result = compute_short_run_stats(stints)
        p1 = next(r for r in result if r['driver'] == 'VER')
        assert p1['position'] == 1
        assert p1['gap_to_p1'] == pytest.approx(0.0)


# =============================================================================
# Test Multi-Stint Per Driver
# =============================================================================


class TestMultiStintPerDriver:
    def test_best_lap_taken_across_all_stints(self):
        """Driver with two short run stints — best lap comes from stint 2."""
        stints = [
            _make_short_stint('VER', 'Red Bull', [89.5], stint_number=1),
            _make_short_stint('VER', 'Red Bull', [88.1], stint_number=3),
        ]
        result = compute_short_run_stats(stints)
        assert len(result) == 1
        assert result[0]['best_lap_time'] == pytest.approx(88.1)

    def test_stint_count_reflects_multiple_stints(self):
        stints = [
            _make_short_stint('HAM', 'Mercedes', [89.8], stint_number=1),
            _make_short_stint('HAM', 'Mercedes', [88.6], stint_number=4),
        ]
        result = compute_short_run_stats(stints)
        assert result[0]['stint_count'] == 2

    def test_compound_from_correct_stint_when_multi_stint(self):
        """Best lap is in stint 2 on MEDIUM — result compound must be MEDIUM."""
        stint1 = _make_short_stint('NOR', 'McLaren', [89.3], compound='SOFT')
        stint2 = _make_short_stint('NOR', 'McLaren', [88.0], compound='MEDIUM', stint_number=3)
        result = compute_short_run_stats([stint1, stint2])
        assert result[0]['compound'] == 'MEDIUM'


# =============================================================================
# Test Single Lap Stints (Edge Case)
# =============================================================================


class TestSingleLapStints:
    def test_single_lap_per_stint_handled(self):
        """1-lap stints are valid short runs — should not be skipped."""
        stints = [
            _make_short_stint('VER', 'Red Bull', [88.0]),
            _make_short_stint('HAM', 'Mercedes', [88.5]),
        ]
        result = compute_short_run_stats(stints)
        assert len(result) == 2

    def test_gap_correct_for_single_lap_stints(self):
        stints = [
            _make_short_stint('VER', 'Red Bull', [88.0]),
            _make_short_stint('HAM', 'Mercedes', [88.5]),
        ]
        result = compute_short_run_stats(stints)
        assert result[1]['gap_to_p1'] == pytest.approx(0.5)


# =============================================================================
# Test Output Format
# =============================================================================


class TestOutputFormat:
    def test_best_lap_time_rounded_to_3dp(self):
        stints = [_make_short_stint('VER', 'Red Bull', [88.12345678])]
        result = compute_short_run_stats(stints)
        assert result[0]['best_lap_time'] == pytest.approx(88.123, abs=1e-3)

    def test_gap_rounded_to_3dp(self):
        stints = [
            _make_short_stint('VER', 'Red Bull', [88.0]),
            _make_short_stint('HAM', 'Mercedes', [88.12345]),
        ]
        result = compute_short_run_stats(stints)
        assert result[1]['gap_to_p1'] == pytest.approx(0.123, abs=1e-3)

    def test_result_dict_contains_all_required_keys(self):
        stints = [_make_short_stint('VER', 'Red Bull', [88.0])]
        result = compute_short_run_stats(stints)
        required_keys = {
            'driver', 'team', 'best_lap_time', 'compound',
            'tyre_life', 'gap_to_p1', 'stint_count', 'position',
        }
        assert required_keys.issubset(result[0].keys())

    def test_team_preserved_from_stint_data(self):
        stints = [_make_short_stint('LEC', 'Ferrari', [87.5])]
        result = compute_short_run_stats(stints)
        assert result[0]['team'] == 'Ferrari'


# =============================================================================
# Test _is_lap_in_short_stints helper
# =============================================================================


class TestIsLapInShortStints:
    """Test _is_lap_in_short_stints helper function."""

    def test_lap_found_returns_true(self):
        stints = [_make_short_stint('VER', 'Red Bull', [88.0], lap_number_start=5)]
        assert _is_lap_in_short_stints(5, 'VER', stints) is True

    def test_lap_not_found_returns_false(self):
        stints = [_make_short_stint('VER', 'Red Bull', [88.0], lap_number_start=5)]
        assert _is_lap_in_short_stints(99, 'VER', stints) is False

    def test_wrong_driver_returns_false(self):
        stints = [_make_short_stint('VER', 'Red Bull', [88.0], lap_number_start=5)]
        assert _is_lap_in_short_stints(5, 'HAM', stints) is False

    def test_empty_stints_returns_false(self):
        assert _is_lap_in_short_stints(5, 'VER', []) is False


# =============================================================================
# Test Session Verification
# =============================================================================


class TestSessionVerification:
    """Test session verification enrichment in compute_short_run_stats."""

    def _make_session_best(
        self, driver='VER', time=88.0, compound='SOFT',
        tyre_life=3, source='fastf1_flag', lap_number=5,
        team='Red Bull',
    ):
        return {
            driver: {
                'session_best_time': time, 'compound': compound,
                'tyre_life': tyre_life, 'source': source,
                'lap_number': lap_number, 'team': team,
            }
        }

    def test_verification_fields_present_when_session_best_provided(self):
        """All 4 verification fields should appear when session_best_laps is given."""
        stints = [_make_short_stint('VER', 'Red Bull', [89.0], lap_number_start=5)]
        session_best = self._make_session_best('VER', time=89.0, lap_number=5)
        result = compute_short_run_stats(stints, session_best)
        assert 'session_best_time' in result[0]
        assert 'session_best_source' in result[0]
        assert 'session_best_from_short_run' in result[0]
        assert 'session_best_compound' in result[0]

    def test_verification_fields_null_when_no_session_best(self):
        """When session_best_laps is None, all verification fields are None."""
        stints = [_make_short_stint('VER', 'Red Bull', [89.0])]
        result = compute_short_run_stats(stints, None)
        assert result[0]['session_best_time'] is None
        assert result[0]['session_best_source'] is None
        assert result[0]['session_best_from_short_run'] is None
        assert result[0]['session_best_compound'] is None

    def test_session_best_matches_short_run_best(self):
        """When session best IS in a short-run stint, session_best_from_short_run is True."""
        stints = [_make_short_stint('VER', 'Red Bull', [88.5], lap_number_start=5)]
        session_best = self._make_session_best('VER', time=88.5, lap_number=5)
        result = compute_short_run_stats(stints, session_best)
        assert result[0]['session_best_from_short_run'] is True

    def test_session_best_from_long_run(self):
        """When session best came from a lap NOT in short stints, from_short_run is False."""
        stints = [_make_short_stint('VER', 'Red Bull', [89.5], lap_number_start=15)]
        # Session best on lap 5 — not in the short run stint (starts at lap 15)
        session_best = self._make_session_best('VER', time=88.0, lap_number=5)
        result = compute_short_run_stats(stints, session_best)
        assert result[0]['session_best_from_short_run'] is False
        assert result[0]['session_best_time'] == pytest.approx(88.0, abs=0.001)

    def test_session_best_time_value_correct(self):
        """session_best_time should match the value passed in."""
        stints = [_make_short_stint('VER', 'Red Bull', [90.0])]
        session_best = self._make_session_best('VER', time=87.654)
        result = compute_short_run_stats(stints, session_best)
        assert result[0]['session_best_time'] == pytest.approx(87.654, abs=0.001)

    def test_session_best_compound_correct(self):
        """Compound field matches the session best data."""
        stints = [_make_short_stint('VER', 'Red Bull', [90.0])]
        session_best = self._make_session_best('VER', compound='MEDIUM')
        result = compute_short_run_stats(stints, session_best)
        assert result[0]['session_best_compound'] == 'MEDIUM'

    def test_session_best_source_fastf1_flag(self):
        """Source should be 'fastf1_flag' when passed as such."""
        stints = [_make_short_stint('VER', 'Red Bull', [90.0])]
        session_best = self._make_session_best('VER', source='fastf1_flag')
        result = compute_short_run_stats(stints, session_best)
        assert result[0]['session_best_source'] == 'fastf1_flag'

    def test_session_best_source_computed_minimum(self):
        """Source should be 'computed_minimum' when passed as such."""
        stints = [_make_short_stint('VER', 'Red Bull', [90.0])]
        session_best = self._make_session_best('VER', source='computed_minimum')
        result = compute_short_run_stats(stints, session_best)
        assert result[0]['session_best_source'] == 'computed_minimum'

    def test_driver_only_in_session_best_no_stints(self):
        """A driver with session best but no short-run stints should still appear."""
        session_best = self._make_session_best('NOR', time=89.0, team='McLaren')
        result = compute_short_run_stats([], session_best)
        assert len(result) == 1
        assert result[0]['driver'] == 'NOR'
        assert result[0]['best_lap_time'] == pytest.approx(89.0, abs=0.001)
        assert result[0]['stint_count'] == 0

    def test_multiple_drivers_from_session_best(self):
        """Multiple drivers ranked from session best, stint count from short stints."""
        stints = [_make_short_stint('VER', 'Red Bull', [88.5])]
        session_best = {
            'VER': {'session_best_time': 87.5, 'compound': 'SOFT', 'tyre_life': 3,
                    'source': 'fastf1_flag', 'lap_number': 5, 'team': 'Red Bull'},
            'HAM': {'session_best_time': 88.0, 'compound': 'MEDIUM', 'tyre_life': 4,
                    'source': 'fastf1_flag', 'lap_number': 10, 'team': 'Mercedes'},
        }
        result = compute_short_run_stats(stints, session_best)
        assert len(result) == 2
        assert result[0]['driver'] == 'VER'
        assert result[1]['driver'] == 'HAM'
        assert result[0]['best_lap_time'] == pytest.approx(87.5, abs=0.001)
        assert result[1]['best_lap_time'] == pytest.approx(88.0, abs=0.001)
        assert result[0]['stint_count'] == 1  # VER has a short-run stint
        assert result[1]['stint_count'] == 0  # HAM has no short-run stints


# =============================================================================
# Test Official Ranking (Primary Path)
# =============================================================================


class TestOfficialRanking:
    """Test that session_best_laps drives ranking, times, and gaps."""

    def _make_session_best_multi(self, drivers):
        """Build session_best_laps for multiple drivers.

        drivers: list of (driver, team, time, compound) tuples.
        """
        result = {}
        for i, (drv, team, time, compound) in enumerate(drivers):
            result[drv] = {
                'session_best_time': time, 'compound': compound,
                'tyre_life': 3, 'source': 'fastf1_flag',
                'lap_number': i + 5, 'team': team,
            }
        return result

    def test_ranking_uses_official_times_not_stint_times(self):
        """Even if stints have different times, ranking comes from session_best_laps."""
        stints = [
            _make_short_stint('VER', 'Red Bull', [90.0]),  # stint says 90.0
            _make_short_stint('NOR', 'McLaren', [89.0]),   # stint says 89.0
        ]
        session_best = self._make_session_best_multi([
            ('VER', 'Red Bull', 88.0, 'SOFT'),   # official: VER is faster
            ('NOR', 'McLaren', 88.5, 'SOFT'),
        ])
        result = compute_short_run_stats(stints, session_best)
        assert result[0]['driver'] == 'VER'
        assert result[0]['best_lap_time'] == pytest.approx(88.0, abs=0.001)
        assert result[1]['driver'] == 'NOR'
        assert result[1]['best_lap_time'] == pytest.approx(88.5, abs=0.001)

    def test_gap_to_p1_from_official_times(self):
        """Gaps computed from official times, not stint data."""
        session_best = self._make_session_best_multi([
            ('NOR', 'McLaren', 84.485, 'SOFT'),
            ('VER', 'Red Bull', 84.493, 'SOFT'),
            ('LEC', 'Ferrari', 84.501, 'SOFT'),
        ])
        result = compute_short_run_stats([], session_best)
        assert result[0]['driver'] == 'NOR'
        assert result[0]['gap_to_p1'] == pytest.approx(0.0)
        assert result[1]['driver'] == 'VER'
        assert result[1]['gap_to_p1'] == pytest.approx(0.008, abs=0.001)
        assert result[2]['driver'] == 'LEC'
        assert result[2]['gap_to_p1'] == pytest.approx(0.016, abs=0.001)

    def test_team_from_session_best(self):
        """Team field comes from session_best_laps, not stints."""
        session_best = self._make_session_best_multi([
            ('VER', 'Red Bull Racing', 88.0, 'SOFT'),
        ])
        result = compute_short_run_stats([], session_best)
        assert result[0]['team'] == 'Red Bull Racing'

    def test_compound_from_session_best(self):
        """Compound comes from session_best_laps official data."""
        session_best = self._make_session_best_multi([
            ('HAM', 'Mercedes', 89.0, 'MEDIUM'),
        ])
        result = compute_short_run_stats([], session_best)
        assert result[0]['compound'] == 'MEDIUM'

    def test_position_assigned_correctly(self):
        """Positions 1,2,3 assigned based on official ranking."""
        session_best = self._make_session_best_multi([
            ('HAM', 'Mercedes', 89.5, 'SOFT'),
            ('VER', 'Red Bull', 88.0, 'SOFT'),
            ('NOR', 'McLaren', 88.8, 'SOFT'),
        ])
        result = compute_short_run_stats([], session_best)
        assert [r['driver'] for r in result] == ['VER', 'NOR', 'HAM']
        assert [r['position'] for r in result] == [1, 2, 3]

    def test_empty_session_best_falls_back_to_stints(self):
        """When session_best_laps is empty dict, use fallback stint extraction."""
        stints = [
            _make_short_stint('VER', 'Red Bull', [88.0]),
            _make_short_stint('HAM', 'Mercedes', [89.0]),
        ]
        result = compute_short_run_stats(stints, {})
        # Fallback: extract from stints
        assert result[0]['driver'] == 'VER'
        assert result[0]['best_lap_time'] == pytest.approx(88.0, abs=0.001)

    def test_none_session_best_falls_back_to_stints(self):
        """When session_best_laps is None, use fallback stint extraction."""
        stints = [_make_short_stint('VER', 'Red Bull', [88.0])]
        result = compute_short_run_stats(stints, None)
        assert result[0]['driver'] == 'VER'
        assert result[0]['best_lap_time'] == pytest.approx(88.0, abs=0.001)
        # Fallback: no verification data
        assert result[0]['session_best_time'] is None

    def test_official_ranking_overrides_fuel_corrected_stint_ordering(self):
        """When stints have fuel-corrected times that differ from official,
        the official ranking prevails.

        This is the key fix: fuel correction in stints should NOT affect
        the displayed ranking."""
        stints = [
            # Fuel-corrected times show NOR faster
            _make_short_stint('NOR', 'McLaren', [84.327]),
            _make_short_stint('LEC', 'Ferrari', [84.448]),
            _make_short_stint('VER', 'Red Bull', [84.461]),
        ]
        session_best = self._make_session_best_multi([
            # Official times show different order
            ('NOR', 'McLaren', 84.485, 'SOFT'),
            ('VER', 'Red Bull', 84.493, 'SOFT'),
            ('LEC', 'Ferrari', 84.501, 'SOFT'),
        ])
        result = compute_short_run_stats(stints, session_best)
        # Official ordering: NOR, VER, LEC (not NOR, LEC, VER from stints)
        assert [r['driver'] for r in result] == ['NOR', 'VER', 'LEC']
        assert result[0]['best_lap_time'] == pytest.approx(84.485, abs=0.001)
        assert result[1]['best_lap_time'] == pytest.approx(84.493, abs=0.001)
        assert result[2]['best_lap_time'] == pytest.approx(84.501, abs=0.001)
