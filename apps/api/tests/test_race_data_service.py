"""Tests for the race data service (stint extraction, pit stops, pace stats)."""

import pytest
import numpy as np
from app.services.race.race_data_service import (
    extract_stints,
    extract_pit_stops,
    compute_race_pace_stats,
)
from app.models.dto import StintResponse, PitStopResponse


# =============================================================================
# Fixtures
# =============================================================================


def _make_lap(
    driver="VER",
    team="Red Bull Racing",
    lap_number=10,
    lap_time=90.0,
    classification="RACING",
    compound="MEDIUM",
    tyre_life=5,
    stint=1,
    position=1,
    in_traffic=False,
    pit_in_time=None,
    pit_out_time=None,
    **overrides,
):
    """Helper to create a single lap dict."""
    lap = {
        "driver": driver,
        "team": team,
        "lap_number": lap_number,
        "lap_time": lap_time,
        "classification": classification,
        "compound": compound,
        "tyre_life": tyre_life,
        "stint": stint,
        "position": position,
        "in_traffic": in_traffic,
        "pit_in_time": pit_in_time,
        "pit_out_time": pit_out_time,
        "fuel_corrected_time": lap_time - 1.0 if lap_time else None,
        "is_warm_up": False,
        "track_status": "1",
        "is_personal_best": False,
    }
    lap.update(overrides)
    return lap


def _make_race_data(laps, stints=None, finishing_positions=None):
    """Helper to create a race data dict for compute_race_pace_stats."""
    from app.services.race.race_data_service import extract_stints as _es
    return {
        "laps": laps,
        "stints": stints if stints is not None else _es(laps),
        "pit_stops": [],
        "total_laps": max((l["lap_number"] for l in laps), default=0),
        "fuel_effect_per_kg": 0.032,
        "session_id": "2025_17_Race",
        "finishing_positions": finishing_positions or {},
    }


@pytest.fixture
def two_driver_laps():
    """Two drivers, 20 laps each, single stint."""
    laps = []
    for i in range(1, 21):
        # VER: faster (89-91s)
        laps.append(_make_lap(
            driver="VER", lap_number=i, lap_time=90.0 + 0.05 * i,
            tyre_life=i, position=1,
        ))
        # NOR: slower (91-93s)
        laps.append(_make_lap(
            driver="NOR", team="McLaren", lap_number=i, lap_time=92.0 + 0.05 * i,
            tyre_life=i, position=2,
        ))
    return laps


@pytest.fixture
def two_stint_laps():
    """Single driver, two stints with different compounds."""
    laps = []
    for i in range(1, 26):
        laps.append(_make_lap(
            lap_number=i, lap_time=90.0 + 0.02 * i,
            compound="MEDIUM", stint=1, tyre_life=i,
        ))
    # Pit stop
    laps.append(_make_lap(
        lap_number=25, lap_time=110.0, classification="IN_LAP",
        compound="MEDIUM", stint=1, tyre_life=25, pit_in_time=2250.0,
    ))
    laps.append(_make_lap(
        lap_number=26, lap_time=95.0, classification="OUT_LAP",
        compound="HARD", stint=2, tyre_life=1, pit_out_time=2360.0,
    ))
    for i in range(27, 51):
        laps.append(_make_lap(
            lap_number=i, lap_time=91.0 + 0.02 * (i - 26),
            compound="HARD", stint=2, tyre_life=i - 25,
        ))
    return laps


# =============================================================================
# Test Stint Extraction
# =============================================================================


class TestStintExtraction:
    """Test stint boundary detection."""

    def test_single_stint(self):
        """Driver with no pit stops should have one stint."""
        laps = [_make_lap(lap_number=i, stint=1) for i in range(1, 21)]
        stints = extract_stints(laps)
        assert len(stints) == 1
        assert stints[0].stint_number == 1
        assert stints[0].start_lap == 1
        assert stints[0].end_lap == 20
        assert stints[0].lap_count == 20

    def test_two_stints(self, two_stint_laps):
        """Two stints should be correctly detected."""
        stints = extract_stints(two_stint_laps)
        assert len(stints) == 2
        assert stints[0].compound == "MEDIUM"
        assert stints[1].compound == "HARD"

    def test_stint_compound(self):
        """Compound should be the most common compound in the stint."""
        laps = [
            _make_lap(lap_number=1, stint=1, compound="MEDIUM"),
            _make_lap(lap_number=2, stint=1, compound="MEDIUM"),
            _make_lap(lap_number=3, stint=1, compound="MEDIUM"),
        ]
        stints = extract_stints(laps)
        assert stints[0].compound == "MEDIUM"

    def test_multiple_drivers(self, two_driver_laps):
        """Stints should be extracted per driver."""
        stints = extract_stints(two_driver_laps)
        ver_stints = [s for s in stints if s.driver == "VER"]
        nor_stints = [s for s in stints if s.driver == "NOR"]
        assert len(ver_stints) == 1
        assert len(nor_stints) == 1

    def test_empty_laps(self):
        """Empty input returns empty stints."""
        assert extract_stints([]) == []


# =============================================================================
# Test Pit Stop Extraction
# =============================================================================


class TestPitStopExtraction:
    """Test pit stop event detection."""

    def test_pit_stop_from_in_lap(self):
        """Each IN_LAP classification should produce a pit stop event."""
        laps = [
            _make_lap(lap_number=10, classification="IN_LAP", pit_in_time=900.0),
            _make_lap(lap_number=11, classification="OUT_LAP", pit_out_time=925.0),
        ]
        stops = extract_pit_stops(laps)
        assert len(stops) == 1
        assert stops[0].lap_number == 10
        assert stops[0].stop_number == 1

    def test_pit_duration_computed(self):
        """Pit lane time should be computed from PitInTime and PitOutTime."""
        laps = [
            _make_lap(lap_number=10, classification="IN_LAP", pit_in_time=900.0),
            _make_lap(lap_number=11, classification="OUT_LAP", pit_out_time=925.0),
        ]
        stops = extract_pit_stops(laps)
        assert stops[0].pit_lane_time == pytest.approx(25.0, abs=0.1)

    def test_anomalous_stop_flagged(self):
        """Stops > 35s should be flagged as anomaly."""
        laps = [
            _make_lap(lap_number=10, classification="IN_LAP", pit_in_time=900.0),
            _make_lap(lap_number=11, classification="OUT_LAP", pit_out_time=940.0),
        ]
        stops = extract_pit_stops(laps)
        assert stops[0].pit_lane_time == pytest.approx(40.0, abs=0.1)
        assert stops[0].is_anomaly is True

    def test_stop_numbering_sequential(self):
        """Stop numbers should be sequential per driver."""
        laps = [
            _make_lap(lap_number=10, classification="IN_LAP", pit_in_time=900.0),
            _make_lap(lap_number=11, classification="OUT_LAP", pit_out_time=923.0),
            _make_lap(lap_number=30, classification="IN_LAP", pit_in_time=2700.0),
            _make_lap(lap_number=31, classification="OUT_LAP", pit_out_time=2723.0),
        ]
        stops = extract_pit_stops(laps)
        assert len(stops) == 2
        assert stops[0].stop_number == 1
        assert stops[1].stop_number == 2

    def test_no_pit_stops(self):
        """Race with no pit stops returns empty list."""
        laps = [_make_lap(lap_number=i) for i in range(1, 21)]
        assert extract_pit_stops(laps) == []


# =============================================================================
# Test Race Pace Statistics
# =============================================================================


class TestRacePaceStats:
    """Test box plot statistics computation."""

    def test_median_computed_correctly(self, two_driver_laps):
        """Median should be the middle value of RACING laps (fuel-corrected)."""
        race_data = _make_race_data(two_driver_laps)
        result = compute_race_pace_stats(race_data)
        ver_stats = [d for d in result.drivers if d.driver == "VER"][0]
        # VER fuel_corrected_time: (90.05-1)=89.05, ..., (91.00-1)=90.00 — median ≈ 89.525
        assert 89.0 < ver_stats.median < 90.5

    def test_sorted_by_mean(self, two_driver_laps):
        """Drivers should be sorted by mean lap time ascending (fastest first)."""
        race_data = _make_race_data(two_driver_laps)
        result = compute_race_pace_stats(race_data)
        assert len(result.drivers) == 2
        assert result.drivers[0].driver == "VER"  # Faster
        assert result.drivers[1].driver == "NOR"  # Slower
        assert result.drivers[0].mean <= result.drivers[1].mean

    def test_gap_to_fastest(self, two_driver_laps):
        """Gap should be this driver's mean minus the fastest driver's mean."""
        race_data = _make_race_data(two_driver_laps)
        result = compute_race_pace_stats(race_data)
        assert result.drivers[0].gap_to_fastest == 0.0
        assert result.drivers[1].gap_to_fastest > 0.0
        # NOR should be ~2s slower than VER (mean-based)
        expected_gap = round(result.drivers[1].mean - result.drivers[0].mean, 3)
        assert result.drivers[1].gap_to_fastest == expected_gap

    def test_tyre_strategy_ordered(self, two_stint_laps):
        """Strategy should list compounds in stint order."""
        race_data = _make_race_data(two_stint_laps)
        result = compute_race_pace_stats(race_data)
        assert result.drivers[0].tyre_strategy == ["MEDIUM", "HARD"]

    def test_consistency_score(self, two_stint_laps):
        """Consistency should be the mean of per-stint standard deviations."""
        race_data = _make_race_data(two_stint_laps)
        result = compute_race_pace_stats(race_data)
        # Should be a small number (low variation in synthetic data)
        assert result.drivers[0].consistency_score is not None
        assert result.drivers[0].consistency_score < 1.0

    def test_outliers_beyond_whiskers(self):
        """Outlier list should contain times beyond Q3 + 1.5*IQR."""
        laps = [_make_lap(lap_number=i, lap_time=90.0 + 0.05 * i) for i in range(1, 21)]
        # Add anomaly lap (fuel_corrected_time = 130.0 - 1.0 = 129.0)
        laps.append(_make_lap(
            lap_number=21, lap_time=130.0, classification="ANOMALY",
        ))
        race_data = _make_race_data(laps)
        result = compute_race_pace_stats(race_data)
        assert 129.0 in result.drivers[0].outliers

    def test_total_racing_laps_count(self, two_driver_laps):
        """total_racing_laps should count only RACING laps."""
        race_data = _make_race_data(two_driver_laps)
        result = compute_race_pace_stats(race_data)
        assert result.drivers[0].total_racing_laps == 20

    def test_empty_laps(self):
        """Empty race data should return empty drivers list."""
        race_data = _make_race_data([])
        result = compute_race_pace_stats(race_data)
        assert result.drivers == []

    def test_traffic_count(self):
        """Laps flagged in_traffic should be counted."""
        laps = [
            _make_lap(lap_number=i, lap_time=90.0, in_traffic=(i <= 5))
            for i in range(1, 21)
        ]
        race_data = _make_race_data(laps)
        result = compute_race_pace_stats(race_data)
        assert result.drivers[0].laps_in_traffic == 5

    def test_finishing_position_included(self, two_driver_laps):
        """Finishing position should be included when provided."""
        race_data = _make_race_data(
            two_driver_laps,
            finishing_positions={"VER": 1, "NOR": 2},
        )
        result = compute_race_pace_stats(race_data)
        ver_stats = [d for d in result.drivers if d.driver == "VER"][0]
        nor_stats = [d for d in result.drivers if d.driver == "NOR"][0]
        assert ver_stats.finishing_position == 1
        assert nor_stats.finishing_position == 2

    def test_finishing_position_none_when_missing(self, two_driver_laps):
        """Finishing position should be None when not provided."""
        race_data = _make_race_data(two_driver_laps)
        result = compute_race_pace_stats(race_data)
        assert result.drivers[0].finishing_position is None
