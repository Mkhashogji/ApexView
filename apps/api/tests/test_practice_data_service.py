"""Tests for practice data service — stint grouping, box stats, degradation, and clean air."""

import pytest
import numpy as np
from unittest.mock import AsyncMock, patch, MagicMock
from app.services.practice.practice_data_service import (
    _group_into_stints,
    _compute_box_stats,
    _compute_degradation_hint,
    _compute_clean_air_pct,
    _get_analysis_times,
    _build_lap_points,
    _filter_representative_long_runs,
    _extract_session_best_laps,
    compute_long_run_stats,
    LONG_RUN_MIN_LAPS,
)


# =============================================================================
# Helpers
# =============================================================================


def _make_valid_lap(
    driver="VER",
    stint=1,
    lap_time=90.0,
    tyre_life=5,
    compound="MEDIUM",
    in_traffic=False,
    fuel_corrected_time=None,
    **overrides,
):
    """Helper to create a classified, valid practice lap dict."""
    lap = {
        "driver": driver,
        "team": "Red Bull Racing",
        "lap_number": 10,
        "lap_time": lap_time,
        "compound": compound,
        "tyre_life": tyre_life,
        "stint": stint,
        "classification": "RACING",
        "is_warm_up": False,
        "is_valid": True,
        "in_traffic": in_traffic,
        "gap_to_car_ahead": None,
        "fuel_corrected_time": fuel_corrected_time,
    }
    lap.update(overrides)
    return lap


def _make_stint_laps(
    driver="VER",
    stint=1,
    count=8,
    base_time=90.0,
    deg_per_lap=0.02,
    compound="MEDIUM",
    include_warm_up=True,
    traffic_pattern=None,
):
    """Generate a realistic set of stint laps with optional warm-up and traffic."""
    laps = []
    for i in range(count):
        tyre_life = i + 1
        lap_time = base_time + deg_per_lap * i + np.random.normal(0, 0.05)

        is_warm_up = include_warm_up and tyre_life <= 2
        in_traffic = False
        if traffic_pattern and i < len(traffic_pattern):
            in_traffic = traffic_pattern[i]

        lap = {
            "driver": driver,
            "team": "Red Bull Racing",
            "lap_number": 10 + i,
            "lap_time": round(lap_time, 3),
            "compound": compound,
            "tyre_life": tyre_life,
            "stint": stint,
            "classification": "RACING",
            "is_warm_up": is_warm_up,
            "is_valid": not is_warm_up,
            "in_traffic": in_traffic,
            "gap_to_car_ahead": None,
            "fuel_corrected_time": None,
        }
        laps.append(lap)
    return laps


# =============================================================================
# Test Stint Grouping
# =============================================================================


class TestStintGrouping:
    """Test the _group_into_stints function."""

    def test_single_long_run(self):
        """Stint with >= 5 valid laps classified as long_run."""
        laps = _make_stint_laps(count=10, include_warm_up=True)
        # 10 total, 2 warm-up, 8 valid → long_run
        stints = _group_into_stints(laps, use_fuel_corrected=False)
        assert len(stints) == 1
        assert stints[0]["run_type"] == "long_run"
        assert stints[0]["valid_lap_count"] == 8
        assert stints[0]["total_lap_count"] == 10

    def test_short_run(self):
        """Stint with < 4 valid laps classified as short_run."""
        laps = _make_stint_laps(count=5, include_warm_up=True)
        # 5 total, 2 warm-up, 3 valid → short_run (< 4)
        stints = _group_into_stints(laps, use_fuel_corrected=False)
        assert len(stints) == 1
        assert stints[0]["run_type"] == "short_run"
        assert stints[0]["valid_lap_count"] == 3

    def test_boundary_exactly_5_valid(self):
        """Exactly 5 valid laps → long_run (>= LONG_RUN_MIN_LAPS)."""
        laps = _make_stint_laps(count=7, include_warm_up=True)
        # 7 total, 2 warm-up, 5 valid → long_run
        stints = _group_into_stints(laps, use_fuel_corrected=False)
        assert len(stints) == 1
        assert stints[0]["run_type"] == "long_run"
        assert stints[0]["valid_lap_count"] == 5

    def test_boundary_4_valid_is_long_run(self):
        """Exactly 4 valid laps → long_run (>= LONG_RUN_MIN_LAPS=4)."""
        laps = _make_stint_laps(count=6, include_warm_up=True)
        # 6 total, 2 warm-up, 4 valid → long_run (threshold is 4)
        stints = _group_into_stints(laps, use_fuel_corrected=False)
        assert stints[0]["run_type"] == "long_run"
        assert stints[0]["valid_lap_count"] == 4

    def test_boundary_3_valid_is_short_run(self):
        """Exactly 3 valid laps → short_run (< LONG_RUN_MIN_LAPS=4)."""
        laps = _make_stint_laps(count=5, include_warm_up=True)
        # 5 total, 2 warm-up, 3 valid → short_run
        stints = _group_into_stints(laps, use_fuel_corrected=False)
        assert stints[0]["run_type"] == "short_run"
        assert stints[0]["valid_lap_count"] == 3

    def test_multi_stint_multi_driver(self):
        """Multiple drivers, multiple stints group independently."""
        ver_s1 = _make_stint_laps(driver="VER", stint=1, count=10, compound="MEDIUM")
        ver_s2 = _make_stint_laps(driver="VER", stint=2, count=6, compound="SOFT")
        nor_s1 = _make_stint_laps(driver="NOR", stint=1, count=12, compound="HARD")

        stints = _group_into_stints(ver_s1 + ver_s2 + nor_s1, use_fuel_corrected=False)
        assert len(stints) == 3

        ver_stints = [s for s in stints if s["driver"] == "VER"]
        nor_stints = [s for s in stints if s["driver"] == "NOR"]
        assert len(ver_stints) == 2
        assert len(nor_stints) == 1

    def test_compound_most_common(self):
        """Compound should be the most common among valid laps."""
        laps = _make_stint_laps(count=10, compound="HARD", include_warm_up=False)
        # Override 2 laps to MEDIUM (minority)
        laps[0]["compound"] = "MEDIUM"
        laps[1]["compound"] = "MEDIUM"
        stints = _group_into_stints(laps, use_fuel_corrected=False)
        assert stints[0]["compound"] == "HARD"

    def test_no_valid_laps_skipped(self):
        """A stint with zero valid laps should be excluded."""
        laps = _make_stint_laps(count=2, include_warm_up=True)
        # Only 2 laps, both warm-up → 0 valid → skipped
        stints = _group_into_stints(laps, use_fuel_corrected=False)
        assert len(stints) == 0

    def test_stats_present_in_output(self):
        """Each stint should have box stats fields including std_dev."""
        laps = _make_stint_laps(count=10, include_warm_up=False)
        stints = _group_into_stints(laps, use_fuel_corrected=False)
        stats = stints[0]["stats"]
        for key in ["lowerfence", "q1", "median", "q3", "upperfence", "mean", "std_dev"]:
            assert key in stats
            assert isinstance(stats[key], float)


# =============================================================================
# Test Box Stats
# =============================================================================


class TestBoxStats:
    """Test the _compute_box_stats function."""

    def test_basic_quartiles(self):
        """Verify Q1, median, Q3 for known data."""
        # 1, 2, 3, 4, 5, 6, 7, 8
        times = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
        stats = _compute_box_stats(times)
        assert stats["median"] == pytest.approx(4.5, abs=0.1)
        assert stats["q1"] <= stats["median"]
        assert stats["q3"] >= stats["median"]
        assert stats["lowerfence"] <= stats["q1"]
        assert stats["upperfence"] >= stats["q3"]

    def test_mean_calculated(self):
        """Mean should be arithmetic average."""
        times = [90.0, 91.0, 92.0, 93.0]
        stats = _compute_box_stats(times)
        assert stats["mean"] == pytest.approx(91.5, abs=0.001)

    def test_single_value(self):
        """Single value: all stats should equal that value."""
        stats = _compute_box_stats([90.0])
        assert stats["lowerfence"] == 90.0
        assert stats["q1"] == 90.0
        assert stats["median"] == 90.0
        assert stats["q3"] == 90.0
        assert stats["upperfence"] == 90.0
        assert stats["mean"] == 90.0

    def test_identical_values(self):
        """All identical values: IQR=0, all stats same."""
        stats = _compute_box_stats([90.0, 90.0, 90.0, 90.0])
        assert stats["lowerfence"] == 90.0
        assert stats["median"] == 90.0
        assert stats["upperfence"] == 90.0
        assert stats["q1"] == 90.0
        assert stats["q3"] == 90.0

    def test_whiskers_clamped_to_data(self):
        """Whiskers should not extend beyond actual data range."""
        times = [88.0, 89.0, 90.0, 91.0, 92.0]
        stats = _compute_box_stats(times)
        assert stats["lowerfence"] >= 88.0
        assert stats["upperfence"] <= 92.0

    def test_values_rounded_to_3_decimals(self):
        """All stats should be rounded to 3 decimal places."""
        times = [90.1234, 90.5678, 91.1111, 91.9999]
        stats = _compute_box_stats(times)
        for key in ["lowerfence", "q1", "median", "q3", "upperfence", "mean"]:
            val_str = f"{stats[key]:.10f}"
            # Check that the 4th decimal place and beyond are zero
            decimal_part = val_str.split(".")[1]
            assert decimal_part[3:] == "0000000", f"{key}={stats[key]} not rounded to 3 decimals"


# =============================================================================
# Test Degradation Hint
# =============================================================================


class TestDegradationHint:
    """Test the _compute_degradation_hint function."""

    def test_positive_degradation(self):
        """Getting slower → positive hint."""
        # Clearly degrading: first 2 laps ~90, last 2 laps ~91
        times = [90.0, 90.1, 90.4, 90.6, 90.8, 91.0, 91.1, 91.2]
        hint = _compute_degradation_hint(times, "long_run")
        assert hint is not None
        assert hint > 0, "Degradation should be positive when getting slower"

    def test_stable_tyres(self):
        """Consistent pace → near-zero hint."""
        times = [90.0, 90.0, 90.0, 90.0, 90.0, 90.0]
        hint = _compute_degradation_hint(times, "long_run")
        assert hint is not None
        assert hint == pytest.approx(0.0, abs=0.01)

    def test_improving_pace(self):
        """Getting faster → negative hint (track evolution)."""
        times = [91.0, 90.8, 90.6, 90.4, 90.2, 90.0]
        hint = _compute_degradation_hint(times, "long_run")
        assert hint is not None
        assert hint < 0, "Should be negative when getting faster"

    def test_short_run_returns_none(self):
        """Short runs should return None regardless of data."""
        times = [90.0, 91.0, 92.0, 93.0, 94.0, 95.0]
        hint = _compute_degradation_hint(times, "short_run")
        assert hint is None

    def test_insufficient_data_returns_none(self):
        """Fewer than 4 valid laps → None."""
        times = [90.0, 91.0, 92.0]
        hint = _compute_degradation_hint(times, "long_run")
        assert hint is None

    def test_exactly_4_laps(self):
        """Exactly 4 laps is the minimum for degradation hint."""
        times = [90.0, 90.5, 91.0, 91.5]
        hint = _compute_degradation_hint(times, "long_run")
        assert hint is not None
        # avg(last 2) - avg(first 2) = avg(91.0, 91.5) - avg(90.0, 90.5) = 91.25 - 90.25 = 1.0
        assert hint == pytest.approx(1.0, abs=0.01)

    def test_hint_rounded_to_3_decimals(self):
        """Degradation hint should be rounded to 3 decimal places."""
        times = [90.0, 90.1, 90.3, 90.4, 90.5]
        hint = _compute_degradation_hint(times, "long_run")
        assert hint is not None
        # Check rounding
        assert hint == round(hint, 3)


# =============================================================================
# Test Clean Air Percentage
# =============================================================================


class TestCleanAirPct:
    """Test the _compute_clean_air_pct function."""

    def test_all_clean(self):
        """All laps in clean air → 1.0."""
        laps = [
            _make_valid_lap(in_traffic=False),
            _make_valid_lap(in_traffic=False),
            _make_valid_lap(in_traffic=False),
        ]
        assert _compute_clean_air_pct(laps) == pytest.approx(1.0, abs=0.01)

    def test_all_traffic(self):
        """All laps in traffic → 0.0."""
        laps = [
            _make_valid_lap(in_traffic=True),
            _make_valid_lap(in_traffic=True),
            _make_valid_lap(in_traffic=True),
        ]
        assert _compute_clean_air_pct(laps) == pytest.approx(0.0, abs=0.01)

    def test_mixed(self):
        """2 clean + 1 dirty → 0.67."""
        laps = [
            _make_valid_lap(in_traffic=False),
            _make_valid_lap(in_traffic=False),
            _make_valid_lap(in_traffic=True),
        ]
        assert _compute_clean_air_pct(laps) == pytest.approx(0.67, abs=0.01)

    def test_no_traffic_data_default(self):
        """Laps without in_traffic field → default to clean (1.0)."""
        laps = [{"lap_time": 90.0}, {"lap_time": 91.0}]
        assert _compute_clean_air_pct(laps) == pytest.approx(1.0, abs=0.01)

    def test_empty_returns_1(self):
        """Empty list → 1.0 (conservative default)."""
        assert _compute_clean_air_pct([]) == 1.0


# =============================================================================
# Test Analysis Times
# =============================================================================


class TestAnalysisTimes:
    """Test _get_analysis_times helper."""

    def test_raw_times_when_not_fuel_corrected(self):
        """When use_fuel_corrected=False, should return raw lap_times."""
        laps = [
            _make_valid_lap(lap_time=90.0),
            _make_valid_lap(lap_time=91.0),
        ]
        times = _get_analysis_times(laps, use_fuel_corrected=False)
        assert times == [90.0, 91.0]

    def test_fuel_corrected_times_when_available(self):
        """When use_fuel_corrected=True and values exist, use fuel_corrected_time."""
        laps = [
            _make_valid_lap(lap_time=90.0, fuel_corrected_time=89.5),
            _make_valid_lap(lap_time=91.0, fuel_corrected_time=90.2),
        ]
        times = _get_analysis_times(laps, use_fuel_corrected=True)
        assert times == [89.5, 90.2]

    def test_fallback_to_raw_when_fuel_corrected_none(self):
        """When use_fuel_corrected=True but value is None, fallback to raw."""
        laps = [
            _make_valid_lap(lap_time=90.0, fuel_corrected_time=None),
        ]
        times = _get_analysis_times(laps, use_fuel_corrected=True)
        assert times == [90.0]

    def test_skip_none_lap_times(self):
        """Laps with lap_time=None should be skipped."""
        laps = [
            _make_valid_lap(lap_time=None),
            _make_valid_lap(lap_time=90.0),
        ]
        times = _get_analysis_times(laps, use_fuel_corrected=False)
        assert times == [90.0]


# =============================================================================
# Test compute_long_run_stats (DTO builder)
# =============================================================================


class TestComputeLongRunStats:
    """Test the compute_long_run_stats function that builds the response DTO."""

    def test_empty_long_runs(self):
        """No long run stints → empty response."""
        data = {
            "session_id": "2025_1_FP2",
            "fuel_effect_per_kg": 0.0,
            "long_run_stints": [],
        }
        result = compute_long_run_stats(data)
        assert result.session_id == "2025_1_FP2"
        assert result.fuel_corrected is False
        assert result.stints == []
        assert result.session_best_average is None

    def test_sorted_by_average_time(self):
        """Stints should be sorted fastest first."""
        data = {
            "session_id": "2025_1_FP2",
            "fuel_effect_per_kg": 0.0,
            "long_run_stints": [
                {
                    "driver": "NOR", "team": "McLaren", "stint_number": 1,
                    "compound": "MEDIUM", "run_type": "long_run",
                    "valid_lap_count": 8, "total_lap_count": 10,
                    "stats": {"lowerfence": 90.0, "q1": 90.2, "median": 90.5,
                              "q3": 90.8, "upperfence": 91.0, "mean": 90.5,
                              "std_dev": 0.3},
                    "average_time": 90.5, "gap_to_fastest": 0,
                    "degradation_hint": 0.1, "clean_air_pct": 0.9,
                    "lap_points": [],
                },
                {
                    "driver": "VER", "team": "Red Bull Racing", "stint_number": 1,
                    "compound": "MEDIUM", "run_type": "long_run",
                    "valid_lap_count": 8, "total_lap_count": 10,
                    "stats": {"lowerfence": 89.5, "q1": 89.8, "median": 90.0,
                              "q3": 90.3, "upperfence": 90.5, "mean": 90.0,
                              "std_dev": 0.25},
                    "average_time": 90.0, "gap_to_fastest": 0,
                    "degradation_hint": 0.05, "clean_air_pct": 1.0,
                    "lap_points": [],
                },
            ],
        }
        result = compute_long_run_stats(data)
        assert result.stints[0].driver == "VER"  # Fastest first
        assert result.stints[1].driver == "NOR"

    def test_gap_to_fastest_computed(self):
        """gap_to_fastest should be relative to the fastest stint."""
        data = {
            "session_id": "2025_1_FP2",
            "fuel_effect_per_kg": 0.032,
            "long_run_stints": [
                {
                    "driver": "VER", "team": "Red Bull Racing", "stint_number": 1,
                    "compound": "MEDIUM", "run_type": "long_run",
                    "valid_lap_count": 8, "total_lap_count": 10,
                    "stats": {"lowerfence": 89.5, "q1": 89.8, "median": 90.0,
                              "q3": 90.3, "upperfence": 90.5, "mean": 90.0,
                              "std_dev": 0.25},
                    "average_time": 90.0, "gap_to_fastest": 0,
                    "degradation_hint": 0.05, "clean_air_pct": 1.0,
                    "lap_points": [],
                },
                {
                    "driver": "NOR", "team": "McLaren", "stint_number": 1,
                    "compound": "MEDIUM", "run_type": "long_run",
                    "valid_lap_count": 8, "total_lap_count": 10,
                    "stats": {"lowerfence": 90.0, "q1": 90.2, "median": 90.5,
                              "q3": 90.8, "upperfence": 91.0, "mean": 90.5,
                              "std_dev": 0.3},
                    "average_time": 90.5, "gap_to_fastest": 0,
                    "degradation_hint": 0.1, "clean_air_pct": 0.9,
                    "lap_points": [],
                },
            ],
        }
        result = compute_long_run_stats(data)
        assert result.stints[0].gap_to_fastest == pytest.approx(0.0, abs=0.001)
        assert result.stints[1].gap_to_fastest == pytest.approx(0.5, abs=0.001)

    def test_fuel_corrected_flag(self):
        """fuel_corrected should reflect whether fuel_effect_per_kg > 0."""
        data_with = {
            "session_id": "test", "fuel_effect_per_kg": 0.032, "long_run_stints": [],
        }
        data_without = {
            "session_id": "test", "fuel_effect_per_kg": 0.0, "long_run_stints": [],
        }
        assert compute_long_run_stats(data_with).fuel_corrected is True
        assert compute_long_run_stats(data_without).fuel_corrected is False

    def test_session_best_average(self):
        """session_best_average should be the fastest stint average."""
        data = {
            "session_id": "test",
            "fuel_effect_per_kg": 0.0,
            "long_run_stints": [
                {
                    "driver": "VER", "team": "RBR", "stint_number": 1,
                    "compound": "MEDIUM", "run_type": "long_run",
                    "valid_lap_count": 8, "total_lap_count": 10,
                    "stats": {"lowerfence": 89.5, "q1": 89.8, "median": 90.0,
                              "q3": 90.3, "upperfence": 90.5, "mean": 89.95,
                              "std_dev": 0.2},
                    "average_time": 89.95, "gap_to_fastest": 0,
                    "degradation_hint": None, "clean_air_pct": 1.0,
                    "lap_points": [],
                },
            ],
        }
        result = compute_long_run_stats(data)
        assert result.session_best_average == pytest.approx(89.95, abs=0.001)

    def test_dto_fields_populated(self):
        """Verify all expected fields are present in the DTO."""
        data = {
            "session_id": "2025_5_FP1",
            "fuel_effect_per_kg": 0.0,
            "long_run_stints": [
                {
                    "driver": "HAM", "team": "Mercedes", "stint_number": 2,
                    "compound": "HARD", "run_type": "long_run",
                    "valid_lap_count": 10, "total_lap_count": 12,
                    "stats": {"lowerfence": 89.0, "q1": 89.5, "median": 90.0,
                              "q3": 90.5, "upperfence": 91.0, "mean": 90.0,
                              "std_dev": 0.35},
                    "average_time": 90.0, "gap_to_fastest": 0,
                    "degradation_hint": 0.2, "clean_air_pct": 0.85,
                    "lap_points": [
                        {"lap_number": 5, "lap_time": 89.5, "compound": "HARD",
                         "tyre_life": 3, "in_traffic": False},
                        {"lap_number": 6, "lap_time": 90.0, "compound": "HARD",
                         "tyre_life": 4, "in_traffic": True},
                    ],
                },
            ],
        }
        result = compute_long_run_stats(data)
        stint = result.stints[0]
        assert stint.driver == "HAM"
        assert stint.team == "Mercedes"
        assert stint.stint_number == 2
        assert stint.compound == "HARD"
        assert stint.valid_lap_count == 10
        assert stint.total_lap_count == 12
        assert stint.average_time == 90.0
        assert stint.degradation_hint == 0.2
        assert stint.clean_air_pct == 0.85
        assert stint.stats.lowerfence == 89.0
        assert stint.stats.q1 == 89.5
        assert stint.stats.median == 90.0
        assert stint.stats.q3 == 90.5
        assert stint.stats.upperfence == 91.0
        assert stint.stats.mean == 90.0
        assert stint.stats.std_dev == 0.35
        # Verify display_stint_number
        assert stint.display_stint_number == 1
        # Verify lap_times populated as PracticeLapPoint DTOs
        assert len(stint.lap_times) == 2
        assert stint.lap_times[0].lap_number == 5
        assert stint.lap_times[0].lap_time == 89.5
        assert stint.lap_times[0].compound == "HARD"
        assert stint.lap_times[0].in_traffic is False
        assert stint.lap_times[1].in_traffic is True

    def test_filter_metadata_in_response(self):
        """total_long_runs_detected and stints_filtered_count present and correct."""
        data = {
            "session_id": "2025_24_FP2",
            "fuel_effect_per_kg": 0.0,
            "long_run_stints": [
                {
                    "driver": "VER", "team": "RBR", "stint_number": 1,
                    "compound": "MEDIUM", "run_type": "long_run",
                    "valid_lap_count": 8, "total_lap_count": 10,
                    "stats": {"lowerfence": 89.5, "q1": 89.8, "median": 90.0,
                              "q3": 90.3, "upperfence": 90.5, "mean": 90.0,
                              "std_dev": 0.25},
                    "average_time": 90.0, "gap_to_fastest": 0,
                    "degradation_hint": 0.05, "clean_air_pct": 1.0,
                    "lap_points": [],
                },
                {
                    "driver": "NOR", "team": "McLaren", "stint_number": 1,
                    "compound": "MEDIUM", "run_type": "long_run",
                    "valid_lap_count": 6, "total_lap_count": 8,
                    "stats": {"lowerfence": 90.0, "q1": 90.2, "median": 90.5,
                              "q3": 90.8, "upperfence": 91.0, "mean": 90.5,
                              "std_dev": 0.3},
                    "average_time": 90.5, "gap_to_fastest": 0,
                    "degradation_hint": 0.1, "clean_air_pct": 0.9,
                    "lap_points": [],
                },
                {
                    # Installation lap — should be filtered out
                    "driver": "TSU", "team": "RB", "stint_number": 1,
                    "compound": "HARD", "run_type": "long_run",
                    "valid_lap_count": 5, "total_lap_count": 7,
                    "stats": {"lowerfence": 125.0, "q1": 126.0, "median": 127.0,
                              "q3": 128.0, "upperfence": 130.0, "mean": 127.0,
                              "std_dev": 1.5},
                    "average_time": 127.0, "gap_to_fastest": 0,
                    "degradation_hint": None, "clean_air_pct": 1.0,
                    "lap_points": [],
                },
            ],
        }
        result = compute_long_run_stats(data)
        assert result.total_long_runs_detected == 3
        assert result.stints_filtered_count == 1
        assert len(result.stints) == 2
        # TSU's installation stint should be excluded
        drivers = [s.driver for s in result.stints]
        assert "TSU" not in drivers
        assert "VER" in drivers
        assert "NOR" in drivers


# =============================================================================
# Test Standard Deviation
# =============================================================================


class TestStdDev:
    """Test standard deviation computation in _compute_box_stats."""

    def test_std_dev_known_value(self):
        """Verify exact std_dev against known data (sample std dev, ddof=1)."""
        times = [90.0, 91.0, 92.0, 93.0]
        stats = _compute_box_stats(times)
        # numpy.std([90, 91, 92, 93], ddof=1) = 1.2909944...
        assert stats["std_dev"] == pytest.approx(1.291, abs=0.001)

    def test_std_dev_single_value(self):
        """Single value → std_dev should be 0.0 (can't compute sample std dev)."""
        stats = _compute_box_stats([90.0])
        assert stats["std_dev"] == 0.0

    def test_std_dev_identical_values(self):
        """All identical values → std_dev should be 0.0."""
        stats = _compute_box_stats([90.0, 90.0, 90.0, 90.0])
        assert stats["std_dev"] == 0.0

    def test_std_dev_two_values(self):
        """Two values → verify ddof=1 Bessel correction."""
        times = [90.0, 92.0]
        stats = _compute_box_stats(times)
        # numpy.std([90, 92], ddof=1) = sqrt((2+2)/1) = sqrt(2) ≈ 1.414
        assert stats["std_dev"] == pytest.approx(1.414, abs=0.001)

    def test_std_dev_in_box_stats_keys(self):
        """std_dev should be present alongside all other box stats keys."""
        times = [90.0, 91.0, 92.0, 93.0, 94.0]
        stats = _compute_box_stats(times)
        expected_keys = {"lowerfence", "q1", "median", "q3", "upperfence", "mean", "std_dev"}
        assert set(stats.keys()) == expected_keys

    def test_std_dev_rounded_to_3_decimals(self):
        """std_dev should be rounded to 3 decimal places."""
        times = [90.1234, 90.5678, 91.1111, 91.9999, 92.3456]
        stats = _compute_box_stats(times)
        val_str = f"{stats['std_dev']:.10f}"
        decimal_part = val_str.split(".")[1]
        assert decimal_part[3:] == "0000000", f"std_dev={stats['std_dev']} not rounded to 3 decimals"


# =============================================================================
# Test Lap Points (individual lap data for violin overlay)
# =============================================================================


class TestLapPoints:
    """Test _build_lap_points and lap_points in stint output."""

    def test_lap_points_populated(self):
        """Stint output should include lap_points with correct count."""
        laps = _make_stint_laps(count=8, include_warm_up=True)
        # 8 total, 2 warm-up, 6 valid → 6 lap_points
        stints = _group_into_stints(laps, use_fuel_corrected=False)
        assert len(stints) == 1
        assert len(stints[0]["lap_points"]) == 6

    def test_lap_points_fields(self):
        """Each lap_point should have all expected fields."""
        laps = [
            _make_valid_lap(driver="VER", stint=1, lap_time=90.5,
                            compound="MEDIUM", tyre_life=3, in_traffic=True,
                            lap_number=5),
        ]
        points = _build_lap_points(laps, use_fuel_corrected=False)
        assert len(points) == 1
        p = points[0]
        assert p["lap_number"] == 5
        assert p["lap_time"] == 90.5
        assert p["compound"] == "MEDIUM"
        assert p["tyre_life"] == 3
        assert p["in_traffic"] is True

    def test_lap_points_use_raw_time(self):
        """When use_fuel_corrected=False, lap_points use raw lap_time."""
        laps = [
            _make_valid_lap(lap_time=90.0, fuel_corrected_time=89.0),
            _make_valid_lap(lap_time=91.0, fuel_corrected_time=90.0),
        ]
        points = _build_lap_points(laps, use_fuel_corrected=False)
        assert points[0]["lap_time"] == 90.0
        assert points[1]["lap_time"] == 91.0

    def test_lap_points_use_fuel_corrected(self):
        """When use_fuel_corrected=True, lap_points use fuel_corrected_time."""
        laps = [
            _make_valid_lap(lap_time=90.0, fuel_corrected_time=89.0),
            _make_valid_lap(lap_time=91.0, fuel_corrected_time=90.0),
        ]
        points = _build_lap_points(laps, use_fuel_corrected=True)
        assert points[0]["lap_time"] == 89.0
        assert points[1]["lap_time"] == 90.0

    def test_lap_points_fuel_corrected_fallback(self):
        """When use_fuel_corrected=True but value is None, fallback to raw."""
        laps = [
            _make_valid_lap(lap_time=90.0, fuel_corrected_time=None),
        ]
        points = _build_lap_points(laps, use_fuel_corrected=True)
        assert points[0]["lap_time"] == 90.0

    def test_lap_points_skip_none_time(self):
        """Laps with no usable time should be skipped."""
        laps = [
            _make_valid_lap(lap_time=None, fuel_corrected_time=None),
            _make_valid_lap(lap_time=90.0),
        ]
        points = _build_lap_points(laps, use_fuel_corrected=False)
        assert len(points) == 1
        assert points[0]["lap_time"] == 90.0

    def test_lap_points_time_rounded(self):
        """Lap times in points should be rounded to 3 decimal places."""
        laps = [
            _make_valid_lap(lap_time=90.12345),
        ]
        points = _build_lap_points(laps, use_fuel_corrected=False)
        assert points[0]["lap_time"] == 90.123

    def test_lap_points_in_stint_output(self):
        """lap_points key should exist in stint dict from _group_into_stints."""
        laps = _make_stint_laps(count=10, include_warm_up=True)
        stints = _group_into_stints(laps, use_fuel_corrected=False)
        assert "lap_points" in stints[0]
        # 10 total - 2 warm-up = 8 valid
        assert len(stints[0]["lap_points"]) == 8
        # Verify each point has required fields
        for p in stints[0]["lap_points"]:
            assert "lap_number" in p
            assert "lap_time" in p
            assert "compound" in p
            assert "tyre_life" in p
            assert "in_traffic" in p


# =============================================================================
# Test LONG_RUN_MIN_LAPS constant
# =============================================================================


class TestLongRunMinLaps:
    """Verify the LONG_RUN_MIN_LAPS constant value."""

    def test_threshold_is_4(self):
        """LONG_RUN_MIN_LAPS should be 4 (aligned with external sources)."""
        assert LONG_RUN_MIN_LAPS == 4


# =============================================================================
# Test Display Stint Number
# =============================================================================


class TestDisplayStintNumber:
    """Test display_stint_number: sequential 1-based per driver, chronological order."""

    def _make_stint_dict(self, driver, stint_number, average_time, team="Red Bull Racing"):
        """Helper to create a minimal long-run stint dict for compute_long_run_stats."""
        return {
            "driver": driver,
            "team": team,
            "stint_number": stint_number,
            "compound": "MEDIUM",
            "run_type": "long_run",
            "valid_lap_count": 8,
            "total_lap_count": 10,
            "stats": {
                "lowerfence": 89.5, "q1": 89.8, "median": 90.0,
                "q3": 90.3, "upperfence": 90.5, "mean": average_time,
                "std_dev": 0.25,
            },
            "average_time": average_time,
            "gap_to_fastest": 0,
            "degradation_hint": 0.05,
            "clean_air_pct": 1.0,
            "lap_points": [],
        }

    def test_sequential_numbering_single_driver(self):
        """VER with raw stints 1, 3 → display 1, 2."""
        data = {
            "session_id": "2025_1_FP2",
            "fuel_effect_per_kg": 0.0,
            "long_run_stints": [
                self._make_stint_dict("VER", stint_number=1, average_time=90.0),
                self._make_stint_dict("VER", stint_number=3, average_time=90.5),
            ],
        }
        result = compute_long_run_stats(data)
        ver_stints = sorted(
            [(s.stint_number, s.display_stint_number) for s in result.stints],
            key=lambda x: x[0],
        )
        assert ver_stints == [(1, 1), (3, 2)]

    def test_sequential_numbering_with_gaps(self):
        """HAM with raw stints 2, 5 → display 1, 2 (chronological, not pace-sorted)."""
        data = {
            "session_id": "2025_1_FP2",
            "fuel_effect_per_kg": 0.0,
            "long_run_stints": [
                # Stint 5 is faster than stint 2 — but display should be chronological
                self._make_stint_dict("HAM", stint_number=5, average_time=89.0),
                self._make_stint_dict("HAM", stint_number=2, average_time=91.0),
            ],
        }
        result = compute_long_run_stats(data)
        # Result is sorted by average_time (fastest first)
        assert result.stints[0].driver == "HAM"
        assert result.stints[0].stint_number == 5
        assert result.stints[0].display_stint_number == 2  # Chronologically second
        assert result.stints[1].stint_number == 2
        assert result.stints[1].display_stint_number == 1  # Chronologically first

    def test_multi_driver_independent_numbering(self):
        """VER and NOR each get independent display_stint_number counters."""
        data = {
            "session_id": "2025_1_FP2",
            "fuel_effect_per_kg": 0.0,
            "long_run_stints": [
                self._make_stint_dict("VER", stint_number=1, average_time=90.0),
                self._make_stint_dict("NOR", stint_number=1, average_time=90.2),
            ],
        }
        result = compute_long_run_stats(data)
        ver = [s for s in result.stints if s.driver == "VER"]
        nor = [s for s in result.stints if s.driver == "NOR"]
        assert len(ver) == 1
        assert len(nor) == 1
        assert ver[0].display_stint_number == 1
        assert nor[0].display_stint_number == 1

    def test_display_stint_number_in_dto(self):
        """display_stint_number should be present and correct in DTO output."""
        data = {
            "session_id": "2025_1_FP2",
            "fuel_effect_per_kg": 0.0,
            "long_run_stints": [
                self._make_stint_dict("VER", stint_number=3, average_time=90.0),
            ],
        }
        result = compute_long_run_stats(data)
        stint = result.stints[0]
        assert hasattr(stint, "display_stint_number")
        assert stint.display_stint_number == 1
        assert stint.stint_number == 3  # Raw number preserved


# =============================================================================
# Test Filter Representative Long Runs
# =============================================================================


class TestFilterRepresentativeLongRuns:
    """Test _filter_representative_long_runs: median-based outlier exclusion."""

    def _make_stub(self, average_time: float) -> dict:
        """Minimal stub with the one field the filter inspects."""
        return {"average_time": average_time, "driver": "VER"}

    def test_normal_stints_all_retained(self):
        """4 stints within 8s of median → all kept."""
        stints = [
            self._make_stub(88.0),
            self._make_stub(89.5),
            self._make_stub(90.0),
            self._make_stub(91.0),
        ]
        result = _filter_representative_long_runs(stints)
        assert len(result) == 4

    def test_extreme_outlier_removed(self):
        """Stint 40+s slower than median → excluded."""
        stints = [
            self._make_stub(88.0),
            self._make_stub(89.0),
            self._make_stub(90.0),
            self._make_stub(130.0),  # Installation lap: ~40s slower
        ]
        result = _filter_representative_long_runs(stints)
        assert len(result) == 3
        assert all(s["average_time"] <= 100 for s in result)

    def test_slow_backmarker_retained(self):
        """Stint 5-6s slower than median → kept (within 8s threshold)."""
        stints = [
            self._make_stub(88.0),
            self._make_stub(89.0),
            self._make_stub(90.0),
            self._make_stub(95.0),  # Slow backmarker: 5-6s off median
        ]
        result = _filter_representative_long_runs(stints)
        assert len(result) == 4

    def test_threshold_boundary(self):
        """Stint exactly at threshold → kept; just over → excluded."""
        # 6 stints: sorted avgs = [88, 89, 90, 91, 92, X]
        # Median = (90 + 91) / 2 = 90.5; threshold = 90.5 + 8.0 = 98.5
        at_threshold = [
            self._make_stub(88.0),
            self._make_stub(89.0),
            self._make_stub(90.0),
            self._make_stub(91.0),
            self._make_stub(92.0),
            self._make_stub(98.5),  # Exactly at threshold → kept (<=)
        ]
        result_at = _filter_representative_long_runs(at_threshold)
        assert len(result_at) == 6

        over_threshold = [
            self._make_stub(88.0),
            self._make_stub(89.0),
            self._make_stub(90.0),
            self._make_stub(91.0),
            self._make_stub(92.0),
            self._make_stub(98.501),  # Just over threshold → excluded
        ]
        result_over = _filter_representative_long_runs(over_threshold)
        assert len(result_over) == 5

    def test_single_stint_not_filtered(self):
        """Single stint always returned (no peers to compare against)."""
        stints = [self._make_stub(130.0)]
        result = _filter_representative_long_runs(stints)
        assert len(result) == 1
        assert result[0]["average_time"] == 130.0

    def test_empty_input(self):
        """Empty list → empty list."""
        result = _filter_representative_long_runs([])
        assert result == []

    def test_multiple_outliers_removed(self):
        """Multiple installation-pace stints excluded."""
        stints = [
            self._make_stub(88.0),
            self._make_stub(89.0),
            self._make_stub(90.0),
            self._make_stub(91.0),
            self._make_stub(125.0),  # Installation lap
            self._make_stub(140.0),  # Sensor check lap
        ]
        result = _filter_representative_long_runs(stints)
        assert len(result) == 4
        times = [s["average_time"] for s in result]
        assert 125.0 not in times
        assert 140.0 not in times


# =============================================================================
# Test Extract Session Best Laps
# =============================================================================


class TestExtractSessionBestLaps:
    """Test _extract_session_best_laps: official session-best lap extraction."""

    def _make_enriched_lap(
        self, driver="VER", lap_time=90.0, lap_number=5,
        compound="SOFT", tyre_life=3, classification="RACING",
        is_personal_best=False, team="Red Bull",
    ) -> dict:
        return {
            "driver": driver, "lap_time": lap_time, "lap_number": lap_number,
            "compound": compound, "tyre_life": tyre_life,
            "classification": classification,
            "is_personal_best": is_personal_best,
            "team": team,
        }

    def test_extracts_personal_best_flagged_lap(self):
        """When is_personal_best flag exists, use it as primary source."""
        laps = [
            self._make_enriched_lap(lap_time=91.0, lap_number=3, is_personal_best=False),
            self._make_enriched_lap(lap_time=90.5, lap_number=5, is_personal_best=True),
            self._make_enriched_lap(lap_time=92.0, lap_number=7, is_personal_best=False),
        ]
        result = _extract_session_best_laps(laps)
        assert "VER" in result
        assert result["VER"]["session_best_time"] == pytest.approx(90.5, abs=0.001)
        assert result["VER"]["lap_number"] == 5
        assert result["VER"]["source"] == "fastf1_flag"

    def test_fallback_to_computed_minimum_when_all_false(self):
        """When all is_personal_best are False, fall back to min RACING lap time."""
        laps = [
            self._make_enriched_lap(lap_time=91.0, lap_number=3),
            self._make_enriched_lap(lap_time=89.5, lap_number=5),
            self._make_enriched_lap(lap_time=92.0, lap_number=7),
        ]
        result = _extract_session_best_laps(laps)
        assert "VER" in result
        assert result["VER"]["session_best_time"] == pytest.approx(89.5, abs=0.001)
        assert result["VER"]["lap_number"] == 5
        assert result["VER"]["source"] == "computed_minimum"

    def test_source_field_fastf1_flag(self):
        """Source is 'fastf1_flag' when using is_personal_best."""
        laps = [self._make_enriched_lap(is_personal_best=True)]
        result = _extract_session_best_laps(laps)
        assert result["VER"]["source"] == "fastf1_flag"

    def test_source_field_computed_minimum(self):
        """Source is 'computed_minimum' when falling back."""
        laps = [self._make_enriched_lap()]
        result = _extract_session_best_laps(laps)
        assert result["VER"]["source"] == "computed_minimum"

    def test_empty_laps_returns_empty_dict(self):
        """Empty input returns empty dict."""
        assert _extract_session_best_laps([]) == {}

    def test_multiple_drivers_each_has_own_best(self):
        """Multiple drivers return independent best laps."""
        laps = [
            self._make_enriched_lap(driver="VER", lap_time=89.0, lap_number=3, is_personal_best=True),
            self._make_enriched_lap(driver="VER", lap_time=90.0, lap_number=5),
            self._make_enriched_lap(driver="NOR", lap_time=89.5, lap_number=4, is_personal_best=True),
            self._make_enriched_lap(driver="NOR", lap_time=91.0, lap_number=6),
        ]
        result = _extract_session_best_laps(laps)
        assert len(result) == 2
        assert result["VER"]["session_best_time"] == pytest.approx(89.0, abs=0.001)
        assert result["NOR"]["session_best_time"] == pytest.approx(89.5, abs=0.001)

    def test_non_racing_laps_excluded_from_fallback(self):
        """IN_LAP and OUT_LAP laps not used in computed_minimum fallback."""
        laps = [
            self._make_enriched_lap(lap_time=85.0, classification="IN_LAP"),
            self._make_enriched_lap(lap_time=87.0, classification="OUT_LAP"),
            self._make_enriched_lap(lap_time=91.0, classification="RACING", lap_number=5),
        ]
        result = _extract_session_best_laps(laps)
        assert result["VER"]["session_best_time"] == pytest.approx(91.0, abs=0.001)
        assert result["VER"]["lap_number"] == 5

    def test_lap_with_none_time_excluded(self):
        """Laps with lap_time=None are skipped."""
        laps = [
            self._make_enriched_lap(lap_time=None, is_personal_best=True),
            self._make_enriched_lap(lap_time=90.5, lap_number=8, is_personal_best=True),
        ]
        result = _extract_session_best_laps(laps)
        assert result["VER"]["session_best_time"] == pytest.approx(90.5, abs=0.001)

    def test_compound_and_tyre_life_recorded(self):
        """Compound and tyre life from the best lap are recorded."""
        laps = [
            self._make_enriched_lap(
                lap_time=88.5, compound="MEDIUM", tyre_life=7,
                is_personal_best=True,
            ),
        ]
        result = _extract_session_best_laps(laps)
        assert result["VER"]["compound"] == "MEDIUM"
        assert result["VER"]["tyre_life"] == 7

    def test_team_recorded_from_best_lap(self):
        """Team from the best lap is included in the result."""
        laps = [
            self._make_enriched_lap(
                driver="NOR", team="McLaren", lap_time=88.0,
                is_personal_best=True,
            ),
        ]
        result = _extract_session_best_laps(laps)
        assert result["NOR"]["team"] == "McLaren"
