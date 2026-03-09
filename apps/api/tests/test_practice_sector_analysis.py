"""Tests for compute_sector_analysis() in practice_data_service.py."""

import pytest
from app.services.practice.practice_data_service import compute_sector_analysis


# ── Test helper ──────────────────────────────────────────────────────────────

def _make_lap(
    driver='VER',
    team='Red Bull',
    lap_number=5,
    lap_time=90.0,
    sector1_time=27.0,
    sector2_time=34.2,
    sector3_time=28.8,
    compound='SOFT',
    tyre_life=3,
    classification='RACING',
    is_personal_best=False,
    speed_trap=310.0,
    speed_i1=280.0,
    speed_i2=265.0,
    speed_fl=290.0,
) -> dict:
    """Build a single enriched lap dict for test fixtures."""
    return {
        'driver': driver,
        'team': team,
        'lap_number': lap_number,
        'lap_time': lap_time,
        'sector1_time': sector1_time,
        'sector2_time': sector2_time,
        'sector3_time': sector3_time,
        'compound': compound,
        'tyre_life': tyre_life,
        'classification': classification,
        'is_personal_best': is_personal_best,
        'speed_trap': speed_trap,
        'speed_i1': speed_i1,
        'speed_i2': speed_i2,
        'speed_fl': speed_fl,
    }


def _make_session_best(driver, time, lap_number, team='Red Bull',
                       compound='SOFT', tyre_life=3, source='fastf1_flag'):
    """Build a session_best_laps entry."""
    return {
        'session_best_time': time,
        'compound': compound,
        'tyre_life': tyre_life,
        'source': source,
        'lap_number': lap_number,
        'team': team,
    }


# ── Tests ────────────────────────────────────────────────────────────────────

class TestComputeSectorAnalysis:
    """Tests for the compute_sector_analysis function."""

    def test_basic_two_drivers(self):
        """Two drivers with valid sector data produce correct results."""
        laps = [
            _make_lap('VER', team='Red Bull', lap_number=5, lap_time=84.5,
                       sector1_time=26.5, sector2_time=31.0, sector3_time=27.0,
                       speed_trap=315.0),
            _make_lap('NOR', team='McLaren', lap_number=8, lap_time=84.8,
                       sector1_time=26.7, sector2_time=31.1, sector3_time=27.0,
                       speed_trap=312.0),
        ]
        session_best = {
            'VER': _make_session_best('VER', 84.5, 5, team='Red Bull'),
            'NOR': _make_session_best('NOR', 84.8, 8, team='McLaren'),
        }

        result = compute_sector_analysis(laps, session_best)

        assert result['total_drivers'] == 2
        assert result['drivers'][0]['driver'] == 'VER'
        assert result['drivers'][0]['position'] == 1
        assert result['drivers'][1]['driver'] == 'NOR'
        assert result['drivers'][1]['position'] == 2

    def test_session_best_lap_sectors_extracted(self):
        """Sectors come from the session-best lap (matched by lap_number)."""
        laps = [
            _make_lap('VER', lap_number=3, sector1_time=27.0, sector2_time=32.0,
                       sector3_time=28.0, lap_time=87.0),
            _make_lap('VER', lap_number=5, sector1_time=26.5, sector2_time=31.0,
                       sector3_time=27.0, lap_time=84.5),
        ]
        session_best = {
            'VER': _make_session_best('VER', 84.5, 5),
        }

        result = compute_sector_analysis(laps, session_best)
        driver = result['drivers'][0]

        # Should use lap 5 sectors, not lap 3
        assert driver['sector1'] == 26.5
        assert driver['sector2'] == 31.0
        assert driver['sector3'] == 27.0

    def test_best_individual_sectors_differ_from_session_best(self):
        """Best individual sectors may come from different laps."""
        laps = [
            # Session best lap (lap 5): decent all-round
            _make_lap('VER', lap_number=5, sector1_time=26.5, sector2_time=31.0,
                       sector3_time=27.0, lap_time=84.5),
            # Lap 3: faster S1 but slower overall
            _make_lap('VER', lap_number=3, sector1_time=26.2, sector2_time=31.5,
                       sector3_time=27.5, lap_time=85.2),
            # Lap 8: faster S3 but slower overall
            _make_lap('VER', lap_number=8, sector1_time=26.8, sector2_time=31.2,
                       sector3_time=26.7, lap_time=84.7),
        ]
        session_best = {
            'VER': _make_session_best('VER', 84.5, 5),
        }

        result = compute_sector_analysis(laps, session_best)
        driver = result['drivers'][0]

        # Session best lap sectors
        assert driver['sector1'] == 26.5
        assert driver['sector3'] == 27.0

        # Best individual sectors from different laps
        assert driver['best_sector1'] == 26.2  # From lap 3
        assert driver['best_sector2'] == 31.0  # From lap 5
        assert driver['best_sector3'] == 26.7  # From lap 8

        # Theoretical best = 26.2 + 31.0 + 26.7 = 83.9
        assert driver['theoretical_best'] == pytest.approx(83.9, abs=0.001)

    def test_missing_sector_times_handled(self):
        """Laps with null sector times don't crash; driver still included."""
        laps = [
            _make_lap('VER', lap_number=5, sector1_time=None, sector2_time=None,
                       sector3_time=None, lap_time=84.5),
        ]
        session_best = {
            'VER': _make_session_best('VER', 84.5, 5),
        }

        result = compute_sector_analysis(laps, session_best)

        assert result['total_drivers'] == 1
        driver = result['drivers'][0]
        assert driver['sector1'] is None
        assert driver['sector2'] is None
        assert driver['sector3'] is None
        assert driver['best_sector1'] is None
        assert driver['theoretical_best'] is None
        assert driver['potential_gain'] is None

    def test_summary_fastest_sectors(self):
        """Summary correctly identifies fastest sector per sector."""
        laps = [
            _make_lap('VER', lap_number=5, sector1_time=26.5, sector2_time=31.5,
                       sector3_time=27.0, lap_time=85.0),
            _make_lap('NOR', lap_number=8, sector1_time=26.8, sector2_time=31.0,
                       sector3_time=27.2, lap_time=85.0),
            _make_lap('LEC', lap_number=10, sector1_time=26.6, sector2_time=31.3,
                       sector3_time=26.8, lap_time=84.7),
        ]
        session_best = {
            'VER': _make_session_best('VER', 85.0, 5, team='Red Bull'),
            'NOR': _make_session_best('NOR', 85.0, 8, team='McLaren'),
            'LEC': _make_session_best('LEC', 84.7, 10, team='Ferrari'),
        }

        result = compute_sector_analysis(laps, session_best)
        summary = result['summary']

        assert summary['fastest_sector1'] == 26.5
        assert summary['fastest_sector1_driver'] == 'VER'
        assert summary['fastest_sector2'] == 31.0
        assert summary['fastest_sector2_driver'] == 'NOR'
        assert summary['fastest_sector3'] == 26.8
        assert summary['fastest_sector3_driver'] == 'LEC'

    def test_theoretical_best_computation(self):
        """Theoretical best combines best individual sectors from different drivers."""
        laps = [
            # VER: best S1 = 26.2 (from lap 3)
            _make_lap('VER', lap_number=3, sector1_time=26.2, sector2_time=31.5,
                       sector3_time=27.5, lap_time=85.2),
            _make_lap('VER', lap_number=5, sector1_time=26.5, sector2_time=31.0,
                       sector3_time=27.0, lap_time=84.5),
            # NOR: best S2 = 30.8 (from lap 7)
            _make_lap('NOR', lap_number=7, sector1_time=27.0, sector2_time=30.8,
                       sector3_time=27.5, lap_time=85.3),
            _make_lap('NOR', lap_number=8, sector1_time=26.8, sector2_time=31.1,
                       sector3_time=27.0, lap_time=84.9),
            # LEC: best S3 = 26.5 (from lap 12)
            _make_lap('LEC', lap_number=10, sector1_time=26.9, sector2_time=31.2,
                       sector3_time=26.8, lap_time=84.9),
            _make_lap('LEC', lap_number=12, sector1_time=27.1, sector2_time=31.4,
                       sector3_time=26.5, lap_time=85.0),
        ]
        session_best = {
            'VER': _make_session_best('VER', 84.5, 5, team='Red Bull'),
            'NOR': _make_session_best('NOR', 84.9, 8, team='McLaren'),
            'LEC': _make_session_best('LEC', 84.9, 10, team='Ferrari'),
        }

        result = compute_sector_analysis(laps, session_best)
        summary = result['summary']

        # Best individual: S1=26.2 (VER lap3) + S2=30.8 (NOR lap7) + S3=26.5 (LEC lap12) = 83.5
        assert summary['theoretical_best_time'] == pytest.approx(83.5, abs=0.001)
        assert summary['actual_best_time'] == 84.5
        assert summary['theoretical_gain'] == pytest.approx(1.0, abs=0.001)

    def test_theoretical_gain_positive(self):
        """Theoretical best should be faster than actual best (positive gain)."""
        laps = [
            _make_lap('VER', lap_number=5, sector1_time=26.5, sector2_time=31.0,
                       sector3_time=27.0, lap_time=84.5),
        ]
        session_best = {
            'VER': _make_session_best('VER', 84.5, 5),
        }

        result = compute_sector_analysis(laps, session_best)
        summary = result['summary']

        # When only one driver with one lap, theoretical = actual
        assert summary['theoretical_gain'] == pytest.approx(0.0, abs=0.001)

    def test_potential_gain_per_driver(self):
        """Each driver's potential gain = lap_time - their theoretical best."""
        laps = [
            _make_lap('VER', lap_number=3, sector1_time=26.2, sector2_time=31.5,
                       sector3_time=27.5, lap_time=85.2),
            _make_lap('VER', lap_number=5, sector1_time=26.5, sector2_time=31.0,
                       sector3_time=27.0, lap_time=84.5),
        ]
        session_best = {
            'VER': _make_session_best('VER', 84.5, 5),
        }

        result = compute_sector_analysis(laps, session_best)
        driver = result['drivers'][0]

        # Best individual: S1=26.2, S2=31.0, S3=27.0 = 84.2
        assert driver['theoretical_best'] == pytest.approx(84.2, abs=0.001)
        assert driver['potential_gain'] == pytest.approx(0.3, abs=0.001)

    def test_speed_trap_maximums(self):
        """Max speed per driver across all laps."""
        laps = [
            _make_lap('VER', lap_number=3, speed_trap=310.0, speed_i1=280.0,
                       speed_i2=265.0, speed_fl=290.0),
            _make_lap('VER', lap_number=5, speed_trap=315.5, speed_i1=278.0,
                       speed_i2=268.0, speed_fl=292.0),
        ]
        session_best = {
            'VER': _make_session_best('VER', 84.5, 5),
        }

        result = compute_sector_analysis(laps, session_best)
        st = result['speed_traps'][0]

        assert st['driver'] == 'VER'
        assert st['speed_trap'] == 315.5
        assert st['speed_i1'] == 280.0
        assert st['speed_i2'] == 268.0
        assert st['speed_fl'] == 292.0

    def test_speed_trap_handles_nulls(self):
        """Null speed values don't crash."""
        laps = [
            _make_lap('VER', lap_number=5, speed_trap=None, speed_i1=None,
                       speed_i2=None, speed_fl=None),
        ]
        session_best = {
            'VER': _make_session_best('VER', 84.5, 5),
        }

        result = compute_sector_analysis(laps, session_best)
        st = result['speed_traps'][0]

        assert st['speed_trap'] is None
        assert st['speed_i1'] is None

    def test_empty_laps_returns_empty(self):
        """Empty enriched_laps returns empty structures."""
        result = compute_sector_analysis([], {'VER': _make_session_best('VER', 84.5, 5)})

        assert result['total_drivers'] == 0
        assert result['drivers'] == []
        assert result['speed_traps'] == []
        assert result['summary']['fastest_sector1'] is None

    def test_empty_session_best_returns_empty(self):
        """Empty session_best_laps returns empty structures."""
        laps = [_make_lap('VER', lap_number=5)]
        result = compute_sector_analysis(laps, {})

        assert result['total_drivers'] == 0
        assert result['drivers'] == []

    def test_drivers_sorted_by_lap_time(self):
        """Drivers are sorted by session-best lap time ascending (P1 first)."""
        laps = [
            _make_lap('HAM', lap_number=3, lap_time=85.5),
            _make_lap('VER', lap_number=5, lap_time=84.5),
            _make_lap('NOR', lap_number=8, lap_time=84.8),
        ]
        session_best = {
            'HAM': _make_session_best('HAM', 85.5, 3, team='Mercedes'),
            'VER': _make_session_best('VER', 84.5, 5, team='Red Bull'),
            'NOR': _make_session_best('NOR', 84.8, 8, team='McLaren'),
        }

        result = compute_sector_analysis(laps, session_best)

        drivers = result['drivers']
        assert drivers[0]['driver'] == 'VER'
        assert drivers[0]['position'] == 1
        assert drivers[1]['driver'] == 'NOR'
        assert drivers[1]['position'] == 2
        assert drivers[2]['driver'] == 'HAM'
        assert drivers[2]['position'] == 3

    def test_gap_to_sector_fastest(self):
        """Non-fastest sectors should show correct delta when computed in frontend.
        Backend provides raw sector times; gap is computed client-side from summary fastest."""
        laps = [
            _make_lap('VER', lap_number=5, sector1_time=26.5, sector2_time=31.0,
                       sector3_time=27.0, lap_time=84.5),
            _make_lap('NOR', lap_number=8, sector1_time=26.8, sector2_time=31.3,
                       sector3_time=27.1, lap_time=85.2),
        ]
        session_best = {
            'VER': _make_session_best('VER', 84.5, 5, team='Red Bull'),
            'NOR': _make_session_best('NOR', 85.2, 8, team='McLaren'),
        }

        result = compute_sector_analysis(laps, session_best)

        # Frontend would compute: NOR S1 - fastest S1 = 26.8 - 26.5 = 0.3
        summary = result['summary']
        nor = result['drivers'][1]
        delta_s1 = nor['sector1'] - summary['fastest_sector1']
        assert delta_s1 == pytest.approx(0.3, abs=0.001)

    def test_speed_traps_sorted_by_speed_descending(self):
        """Speed traps are sorted by speed_trap descending (fastest first)."""
        laps = [
            _make_lap('VER', lap_number=5, speed_trap=310.0),
            _make_lap('NOR', lap_number=8, speed_trap=318.0),
            _make_lap('LEC', lap_number=10, speed_trap=314.0),
        ]
        session_best = {
            'VER': _make_session_best('VER', 84.5, 5, team='Red Bull'),
            'NOR': _make_session_best('NOR', 84.8, 8, team='McLaren'),
            'LEC': _make_session_best('LEC', 85.0, 10, team='Ferrari'),
        }

        result = compute_sector_analysis(laps, session_best)

        speeds = result['speed_traps']
        assert speeds[0]['driver'] == 'NOR'
        assert speeds[0]['speed_trap'] == 318.0
        assert speeds[1]['driver'] == 'LEC'
        assert speeds[2]['driver'] == 'VER'

    def test_compound_from_session_best(self):
        """Compound field comes from session_best_laps."""
        laps = [
            _make_lap('VER', lap_number=5, compound='MEDIUM'),
        ]
        session_best = {
            'VER': _make_session_best('VER', 84.5, 5, compound='SOFT'),
        }

        result = compute_sector_analysis(laps, session_best)
        assert result['drivers'][0]['compound'] == 'SOFT'

    def test_team_from_session_best(self):
        """Team field comes from session_best_laps."""
        laps = [
            _make_lap('VER', lap_number=5, team='Wrong Team'),
        ]
        session_best = {
            'VER': _make_session_best('VER', 84.5, 5, team='Red Bull'),
        }

        result = compute_sector_analysis(laps, session_best)
        assert result['drivers'][0]['team'] == 'Red Bull'
