"""Tests for practice lap classification, fuel correction, and traffic derivation."""

import pytest
import numpy as np
from app.services.practice.transforms import (
    classify_practice_laps,
    apply_practice_fuel_correction,
    derive_practice_traffic,
)


# =============================================================================
# Fixtures
# =============================================================================


def _make_lap(
    driver="VER",
    lap_number=10,
    lap_time=90.0,
    track_status="1",
    pit_in_time=None,
    pit_out_time=None,
    tyre_life=5,
    stint=1,
    compound="MEDIUM",
    position=None,
    cumulative_time=None,
    **overrides,
):
    """Helper to create a single practice lap dict with sensible defaults."""
    lap = {
        "driver": driver,
        "team": "Red Bull Racing",
        "lap_number": lap_number,
        "lap_time": lap_time,
        "sector1_time": lap_time * 0.30 if lap_time else None,
        "sector2_time": lap_time * 0.38 if lap_time else None,
        "sector3_time": lap_time * 0.32 if lap_time else None,
        "compound": compound,
        "tyre_life": tyre_life,
        "stint": stint,
        "position": position,
        "pit_in_time": pit_in_time,
        "pit_out_time": pit_out_time,
        "track_status": track_status,
        "is_personal_best": False,
        "cumulative_time": cumulative_time,
    }
    lap.update(overrides)
    return lap


@pytest.fixture
def sample_racing_laps():
    """Generate a realistic set of 20 racing laps for a single driver."""
    laps = []
    for i in range(1, 21):
        laps.append(_make_lap(lap_number=i, lap_time=90.0 + 0.1 * i, tyre_life=i))
    return laps


@pytest.fixture
def mixed_practice_laps():
    """Generate practice laps with various classification types (no SC/VSC)."""
    return [
        # Normal racing laps
        _make_lap(lap_number=3, lap_time=90.3, tyre_life=3),
        _make_lap(lap_number=4, lap_time=90.2, tyre_life=4),
        _make_lap(lap_number=5, lap_time=90.4, tyre_life=5),
        _make_lap(lap_number=6, lap_time=90.1, tyre_life=6),
        _make_lap(lap_number=7, lap_time=90.3, tyre_life=7),
        _make_lap(lap_number=8, lap_time=90.2, tyre_life=8),
        _make_lap(lap_number=9, lap_time=90.5, tyre_life=9),
        # In-lap (pit stop entry)
        _make_lap(lap_number=10, lap_time=110.0, pit_in_time=950.0, tyre_life=10),
        # Out-lap (pit stop exit)
        _make_lap(lap_number=11, lap_time=95.0, pit_out_time=1060.0, tyre_life=1, stint=2),
        # Red flag
        _make_lap(lap_number=15, lap_time=None, track_status="5", tyre_life=5, stint=2),
        # Warm-up laps (tyre_life 1, 2) in stint 2
        _make_lap(lap_number=12, lap_time=91.5, tyre_life=2, stint=2),
        # Normal racing after pit
        _make_lap(lap_number=13, lap_time=90.4, tyre_life=3, stint=2),
        _make_lap(lap_number=14, lap_time=90.3, tyre_life=4, stint=2),
        _make_lap(lap_number=16, lap_time=90.2, tyre_life=6, stint=2),
        _make_lap(lap_number=17, lap_time=90.5, tyre_life=7, stint=2),
        _make_lap(lap_number=18, lap_time=90.3, tyre_life=8, stint=2),
    ]


# =============================================================================
# Test Lap Classification
# =============================================================================


class TestPracticeClassification:
    """Test the classify_practice_laps function."""

    def test_empty_list(self):
        """Empty input returns empty output."""
        assert classify_practice_laps([]) == []

    def test_normal_racing_lap(self, sample_racing_laps):
        """Normal green-flag laps should be classified as RACING."""
        result = classify_practice_laps(sample_racing_laps)
        racing_count = sum(1 for l in result if l["classification"] == "RACING")
        assert racing_count >= 15  # Most of 20 laps should be RACING

    def test_in_lap_classified(self, mixed_practice_laps):
        """Laps with pit_in_time should be classified as IN_LAP."""
        result = classify_practice_laps(mixed_practice_laps)
        in_laps = [l for l in result if l["classification"] == "IN_LAP"]
        assert len(in_laps) == 1
        assert in_laps[0]["lap_number"] == 10

    def test_out_lap_classified(self, mixed_practice_laps):
        """Laps with pit_out_time should be classified as OUT_LAP."""
        result = classify_practice_laps(mixed_practice_laps)
        out_laps = [l for l in result if l["classification"] == "OUT_LAP"]
        assert len(out_laps) >= 1
        assert any(l["lap_number"] == 11 for l in out_laps)

    def test_red_flag_classified(self, mixed_practice_laps):
        """Laps with track_status containing '5' should be RED_FLAG."""
        result = classify_practice_laps(mixed_practice_laps)
        rf_laps = [l for l in result if l["classification"] == "RED_FLAG"]
        assert len(rf_laps) == 1
        assert rf_laps[0]["lap_number"] == 15

    def test_no_safety_car_classification(self):
        """Practice does NOT classify SAFETY_CAR — track_status '4' stays RACING."""
        laps = [
            _make_lap(lap_number=i, lap_time=90.0 + 0.1 * i, tyre_life=i)
            for i in range(3, 23)
        ]
        # Add a lap with track_status '4' — should remain RACING in practice
        laps.append(_make_lap(lap_number=25, lap_time=120.0, track_status="4", tyre_life=25))
        result = classify_practice_laps(laps)
        sc_laps = [l for l in result if l["classification"] == "SAFETY_CAR"]
        assert len(sc_laps) == 0, "Practice should not have SAFETY_CAR classification"

    def test_no_vsc_classification(self):
        """Practice does NOT classify VSC — track_status '6' stays RACING."""
        laps = [
            _make_lap(lap_number=i, lap_time=90.0 + 0.1 * i, tyre_life=i)
            for i in range(3, 23)
        ]
        laps.append(_make_lap(lap_number=25, lap_time=105.0, track_status="6", tyre_life=25))
        result = classify_practice_laps(laps)
        vsc_laps = [l for l in result if l["classification"] == "VSC"]
        assert len(vsc_laps) == 0, "Practice should not have VSC classification"

    def test_no_formation_classification(self):
        """Practice does NOT classify FORMATION — no formation laps in practice."""
        laps = [
            _make_lap(lap_number=1, lap_time=None, tyre_life=1),
            _make_lap(lap_number=2, lap_time=90.0, tyre_life=2),
            _make_lap(lap_number=3, lap_time=90.1, tyre_life=3),
        ]
        result = classify_practice_laps(laps)
        formation_laps = [l for l in result if l["classification"] == "FORMATION"]
        assert len(formation_laps) == 0, "Practice should not have FORMATION classification"

    def test_null_lap_time_classified_as_out_lap(self):
        """Laps with no valid lap_time and no other flag → treated as OUT_LAP."""
        laps = [
            _make_lap(lap_number=1, lap_time=None, tyre_life=1),
            _make_lap(lap_number=2, lap_time=90.0, tyre_life=2),
            _make_lap(lap_number=3, lap_time=90.1, tyre_life=3),
            _make_lap(lap_number=4, lap_time=90.2, tyre_life=4),
            _make_lap(lap_number=5, lap_time=90.3, tyre_life=5),
        ]
        result = classify_practice_laps(laps)
        lap1 = [l for l in result if l["lap_number"] == 1][0]
        assert lap1["classification"] == "OUT_LAP"

    def test_pit_priority_over_track_status(self):
        """Pit in/out should take priority over track status classification."""
        laps = [
            _make_lap(lap_number=10, lap_time=110.0, pit_in_time=1000.0, track_status="5"),
            _make_lap(lap_number=11, lap_time=90.0, tyre_life=3),
            _make_lap(lap_number=12, lap_time=90.1, tyre_life=4),
            _make_lap(lap_number=13, lap_time=90.2, tyre_life=5),
            _make_lap(lap_number=14, lap_time=90.3, tyre_life=6),
        ]
        result = classify_practice_laps(laps)
        assert result[0]["classification"] == "IN_LAP"

    def test_concatenated_track_status_red_flag(self):
        """TrackStatus '15' or '56' should detect red flag (contains '5')."""
        laps = [
            _make_lap(lap_number=5, lap_time=100.0, track_status="15", tyre_life=5),
            _make_lap(lap_number=6, lap_time=90.0, tyre_life=6),
            _make_lap(lap_number=7, lap_time=90.1, tyre_life=7),
            _make_lap(lap_number=8, lap_time=90.2, tyre_life=8),
            _make_lap(lap_number=9, lap_time=90.3, tyre_life=9),
        ]
        result = classify_practice_laps(laps)
        assert result[0]["classification"] == "RED_FLAG"


class TestPracticeOutlierDetection:
    """Test anomaly/outlier detection in practice classification."""

    def test_outlier_iqr_detection(self):
        """Laps beyond Q3 + 1.5*IQR should be classified as ANOMALY."""
        laps = [_make_lap(lap_number=i, lap_time=90.0 + 0.1 * i, tyre_life=i)
                for i in range(3, 23)]
        # Add one very slow lap (well outside IQR)
        laps.append(_make_lap(lap_number=23, lap_time=130.0, tyre_life=23))
        result = classify_practice_laps(laps)
        anomalies = [l for l in result if l["classification"] == "ANOMALY"]
        assert len(anomalies) >= 1
        assert any(l["lap_number"] == 23 for l in anomalies)

    def test_outlier_percentage_cap(self):
        """Laps beyond 110% of driver median should be ANOMALY."""
        # All laps around 90s, one at 100s (> 110% of ~90s median = 99s)
        laps = [_make_lap(lap_number=i, lap_time=90.0, tyre_life=i) for i in range(3, 23)]
        laps.append(_make_lap(lap_number=23, lap_time=100.0, tyre_life=23))
        result = classify_practice_laps(laps)
        anomalies = [l for l in result if l["classification"] == "ANOMALY"]
        assert len(anomalies) >= 1
        assert any(l["lap_number"] == 23 for l in anomalies)

    def test_outlier_or_logic(self):
        """Either IQR or 110% cap should trigger ANOMALY (OR, not AND)."""
        # Tight distribution where 110% threshold triggers before IQR
        laps = [_make_lap(lap_number=i, lap_time=90.0, tyre_life=i) for i in range(3, 23)]
        # 99.5s > 110% of 90s = 99s
        laps.append(_make_lap(lap_number=23, lap_time=99.5, tyre_life=23))
        result = classify_practice_laps(laps)
        anomalies = [l for l in result if l["classification"] == "ANOMALY"]
        assert any(l["lap_number"] == 23 for l in anomalies)

    def test_per_driver_per_compound_outliers(self):
        """Outlier detection should be scoped per (driver, compound)."""
        # VER on MEDIUM ~90s, NOR on SOFT ~85s
        ver_laps = [_make_lap(driver="VER", lap_number=i, lap_time=90.0 + 0.1 * i,
                              tyre_life=i, compound="MEDIUM") for i in range(3, 13)]
        nor_laps = [_make_lap(driver="NOR", lap_number=i, lap_time=85.0 + 0.1 * i,
                              tyre_life=i, compound="SOFT") for i in range(3, 13)]
        # VER at 91s on MEDIUM → normal. NOR at 91s on SOFT → likely ANOMALY
        ver_laps.append(_make_lap(driver="VER", lap_number=20, lap_time=91.0,
                                  tyre_life=20, compound="MEDIUM"))
        nor_laps.append(_make_lap(driver="NOR", lap_number=20, lap_time=94.0,
                                  tyre_life=20, compound="SOFT"))
        result = classify_practice_laps(ver_laps + nor_laps)

        ver_result = [l for l in result if l["driver"] == "VER" and l["lap_number"] == 20][0]
        nor_result = [l for l in result if l["driver"] == "NOR" and l["lap_number"] == 20][0]
        # VER's 91s is within range; NOR's 94s is anomalous relative to 85s group
        assert ver_result["classification"] == "RACING"
        assert nor_result["classification"] == "ANOMALY"

    def test_insufficient_sample_no_outliers(self):
        """With fewer than 4 RACING laps, no outlier detection should happen."""
        laps = [
            _make_lap(lap_number=3, lap_time=90.0, tyre_life=3),
            _make_lap(lap_number=4, lap_time=90.5, tyre_life=4),
            _make_lap(lap_number=5, lap_time=120.0, tyre_life=5),  # Would be outlier with enough data
        ]
        result = classify_practice_laps(laps)
        anomalies = [l for l in result if l["classification"] == "ANOMALY"]
        assert len(anomalies) == 0, "No outliers should be detected with < 4 laps"


class TestPracticeWarmUp:
    """Test warm-up flag and is_valid composite."""

    def test_warm_up_flag_tyre_life_1(self):
        """tyre_life == 1 on RACING lap → is_warm_up=True."""
        laps = [
            _make_lap(lap_number=1, lap_time=92.0, tyre_life=1),
            _make_lap(lap_number=2, lap_time=91.0, tyre_life=2),
            _make_lap(lap_number=3, lap_time=90.0, tyre_life=3),
            _make_lap(lap_number=4, lap_time=90.1, tyre_life=4),
            _make_lap(lap_number=5, lap_time=90.2, tyre_life=5),
        ]
        result = classify_practice_laps(laps)
        lap1 = [l for l in result if l["lap_number"] == 1][0]
        lap2 = [l for l in result if l["lap_number"] == 2][0]
        lap3 = [l for l in result if l["lap_number"] == 3][0]
        assert lap1["is_warm_up"] is True
        assert lap2["is_warm_up"] is True
        assert lap3["is_warm_up"] is False

    def test_warm_up_not_set_for_non_racing(self):
        """Warm-up flag should not be set for non-racing laps."""
        laps = [
            _make_lap(lap_number=1, lap_time=110.0, pit_out_time=100.0, tyre_life=1),
            _make_lap(lap_number=2, lap_time=90.0, tyre_life=2),
            _make_lap(lap_number=3, lap_time=90.1, tyre_life=3),
            _make_lap(lap_number=4, lap_time=90.2, tyre_life=4),
            _make_lap(lap_number=5, lap_time=90.3, tyre_life=5),
        ]
        result = classify_practice_laps(laps)
        out_lap = [l for l in result if l["classification"] == "OUT_LAP"][0]
        assert out_lap["is_warm_up"] is False

    def test_is_valid_composite(self):
        """is_valid = RACING AND NOT is_warm_up."""
        laps = [
            _make_lap(lap_number=1, lap_time=92.0, tyre_life=1),   # RACING, warm_up → not valid
            _make_lap(lap_number=2, lap_time=91.0, tyre_life=2),   # RACING, warm_up → not valid
            _make_lap(lap_number=3, lap_time=90.0, tyre_life=3),   # RACING, not warm_up → valid
            _make_lap(lap_number=10, lap_time=110.0, pit_in_time=900.0, tyre_life=10),  # IN_LAP → not valid
        ]
        result = classify_practice_laps(laps)
        assert result[0]["is_valid"] is False   # warm-up
        assert result[1]["is_valid"] is False   # warm-up
        assert result[2]["is_valid"] is True    # valid racing
        assert result[3]["is_valid"] is False   # IN_LAP

    def test_all_fields_present(self):
        """Every classified lap should have classification, is_warm_up, is_valid."""
        laps = [_make_lap(lap_number=i, lap_time=90.0, tyre_life=i) for i in range(3, 8)]
        result = classify_practice_laps(laps)
        for lap in result:
            assert "classification" in lap
            assert "is_warm_up" in lap
            assert "is_valid" in lap


# =============================================================================
# Test Fuel Correction
# =============================================================================


class TestPracticeFuelCorrection:
    """Test the apply_practice_fuel_correction function."""

    def test_disabled_with_zero_effect(self):
        """With fuel_effect_per_kg=0, all fuel_corrected_time should be None."""
        laps = [_make_lap(lap_number=i, lap_time=90.0, tyre_life=i) for i in range(3, 8)]
        for l in laps:
            l["classification"] = "RACING"
        result = apply_practice_fuel_correction(laps, fuel_effect_per_kg=0.0)
        for l in result:
            assert l["fuel_corrected_time"] is None

    def test_disabled_with_negative_effect(self):
        """With fuel_effect_per_kg < 0, all fuel_corrected_time should be None."""
        laps = [_make_lap(lap_number=1, lap_time=90.0, tyre_life=3)]
        laps[0]["classification"] = "RACING"
        result = apply_practice_fuel_correction(laps, fuel_effect_per_kg=-0.01)
        assert result[0]["fuel_corrected_time"] is None

    def test_within_stint_earlier_lap_corrected_more(self):
        """Earlier laps in a stint should have larger fuel correction."""
        laps = [
            _make_lap(lap_number=3, lap_time=90.0, tyre_life=1, stint=1),
            _make_lap(lap_number=4, lap_time=90.0, tyre_life=2, stint=1),
            _make_lap(lap_number=5, lap_time=90.0, tyre_life=3, stint=1),
            _make_lap(lap_number=6, lap_time=90.0, tyre_life=4, stint=1),
            _make_lap(lap_number=7, lap_time=90.0, tyre_life=5, stint=1),
        ]
        for l in laps:
            l["classification"] = "RACING"
        result = apply_practice_fuel_correction(laps, fuel_effect_per_kg=0.032)
        correction_first = result[0]["lap_time"] - result[0]["fuel_corrected_time"]
        correction_last = result[-1]["lap_time"] - result[-1]["fuel_corrected_time"]
        # Earlier laps have more fuel remaining → larger correction
        assert correction_first > correction_last

    def test_last_lap_of_stint_has_zero_correction(self):
        """The last lap in a stint (max tyre_life) should have near-zero correction."""
        laps = [
            _make_lap(lap_number=3, lap_time=90.0, tyre_life=1, stint=1),
            _make_lap(lap_number=4, lap_time=90.0, tyre_life=2, stint=1),
            _make_lap(lap_number=5, lap_time=90.0, tyre_life=3, stint=1),
        ]
        for l in laps:
            l["classification"] = "RACING"
        result = apply_practice_fuel_correction(laps, fuel_effect_per_kg=0.032)
        last_correction = result[-1]["lap_time"] - result[-1]["fuel_corrected_time"]
        assert last_correction == pytest.approx(0.0, abs=1e-6)

    def test_corrected_time_less_than_raw(self):
        """Fuel-corrected time should be less than or equal to raw time."""
        laps = [
            _make_lap(lap_number=i, lap_time=90.0, tyre_life=i, stint=1)
            for i in range(1, 11)
        ]
        for l in laps:
            l["classification"] = "RACING"
        result = apply_practice_fuel_correction(laps, fuel_effect_per_kg=0.032)
        for l in result:
            if l["fuel_corrected_time"] is not None:
                assert l["fuel_corrected_time"] <= l["lap_time"]

    def test_non_racing_laps_not_corrected(self):
        """IN_LAP, OUT_LAP, RED_FLAG laps should not get fuel correction."""
        laps = [
            _make_lap(lap_number=10, lap_time=110.0),
            _make_lap(lap_number=11, lap_time=100.0),
            _make_lap(lap_number=15, lap_time=None),
        ]
        laps[0]["classification"] = "IN_LAP"
        laps[1]["classification"] = "OUT_LAP"
        laps[2]["classification"] = "RED_FLAG"
        result = apply_practice_fuel_correction(laps, fuel_effect_per_kg=0.032)
        assert result[0]["fuel_corrected_time"] is None
        assert result[1]["fuel_corrected_time"] is None
        assert result[2]["fuel_corrected_time"] is None

    def test_anomaly_laps_get_corrected(self):
        """ANOMALY laps should also receive fuel correction."""
        laps = [
            _make_lap(lap_number=10, lap_time=120.0, tyre_life=5, stint=1),
        ]
        laps[0]["classification"] = "ANOMALY"
        result = apply_practice_fuel_correction(laps, fuel_effect_per_kg=0.032)
        assert result[0]["fuel_corrected_time"] is not None

    def test_multi_stint_independence(self):
        """Each stint should be corrected independently (different max_tyre_life)."""
        laps = [
            # Stint 1: 3 laps
            _make_lap(lap_number=3, lap_time=90.0, tyre_life=1, stint=1),
            _make_lap(lap_number=4, lap_time=90.0, tyre_life=2, stint=1),
            _make_lap(lap_number=5, lap_time=90.0, tyre_life=3, stint=1),
            # Stint 2: 5 laps (different max_tyre_life)
            _make_lap(lap_number=15, lap_time=90.0, tyre_life=1, stint=2),
            _make_lap(lap_number=16, lap_time=90.0, tyre_life=2, stint=2),
            _make_lap(lap_number=17, lap_time=90.0, tyre_life=3, stint=2),
            _make_lap(lap_number=18, lap_time=90.0, tyre_life=4, stint=2),
            _make_lap(lap_number=19, lap_time=90.0, tyre_life=5, stint=2),
        ]
        for l in laps:
            l["classification"] = "RACING"
        result = apply_practice_fuel_correction(laps, fuel_effect_per_kg=0.032)

        # First lap of stint 1: max_life=3, laps_remaining=2, correction=2*1.6*0.032
        s1_correction = result[0]["lap_time"] - result[0]["fuel_corrected_time"]
        expected_s1 = 2 * 1.6 * 0.032
        assert s1_correction == pytest.approx(expected_s1, abs=1e-6)

        # First lap of stint 2: max_life=5, laps_remaining=4, correction=4*1.6*0.032
        s2_correction = result[3]["lap_time"] - result[3]["fuel_corrected_time"]
        expected_s2 = 4 * 1.6 * 0.032
        assert s2_correction == pytest.approx(expected_s2, abs=1e-6)

    def test_correction_magnitude(self):
        """Verify exact correction calculation: (laps_remaining * 1.6 * fuel_effect)."""
        laps = [
            _make_lap(lap_number=3, lap_time=92.0, tyre_life=1, stint=1),
            _make_lap(lap_number=4, lap_time=91.5, tyre_life=2, stint=1),
            _make_lap(lap_number=5, lap_time=91.0, tyre_life=3, stint=1),
        ]
        for l in laps:
            l["classification"] = "RACING"
        fuel_effect = 0.032
        result = apply_practice_fuel_correction(laps, fuel_effect)

        # Max tyre_life in stint = 3
        # Lap 1: laps_remaining = 3-1 = 2, correction = 2 * 1.6 * 0.032 = 0.1024
        # Lap 2: laps_remaining = 3-2 = 1, correction = 1 * 1.6 * 0.032 = 0.0512
        # Lap 3: laps_remaining = 3-3 = 0, correction = 0
        assert result[0]["fuel_corrected_time"] == pytest.approx(92.0 - 0.1024, abs=1e-6)
        assert result[1]["fuel_corrected_time"] == pytest.approx(91.5 - 0.0512, abs=1e-6)
        assert result[2]["fuel_corrected_time"] == pytest.approx(91.0 - 0.0, abs=1e-6)

    def test_empty_laps(self):
        """Empty input returns empty output."""
        assert apply_practice_fuel_correction([], 0.032) == []

    def test_none_lap_time_handled(self):
        """Laps with None lap_time should get None fuel_corrected_time."""
        laps = [_make_lap(lap_number=5, lap_time=None, tyre_life=3, stint=1)]
        laps[0]["classification"] = "RACING"
        result = apply_practice_fuel_correction(laps, 0.032)
        assert result[0]["fuel_corrected_time"] is None


# =============================================================================
# Test Traffic Derivation
# =============================================================================


class TestPracticeTraffic:
    """Test the derive_practice_traffic function."""

    def test_close_following_flagged(self):
        """Driver within 1.5s of car ahead should be flagged in_traffic=True."""
        laps = [
            _make_lap(driver="VER", lap_number=5, position=1, cumulative_time=5400.0),
            _make_lap(driver="NOR", lap_number=5, position=2, cumulative_time=5400.8),
        ]
        result = derive_practice_traffic(laps)
        follower = [l for l in result if l["driver"] == "NOR"][0]
        assert follower["in_traffic"] is True
        assert follower["gap_to_car_ahead"] == pytest.approx(0.8, abs=0.01)

    def test_gap_above_threshold_not_flagged(self):
        """Driver more than 1.5s behind should not be flagged."""
        laps = [
            _make_lap(driver="VER", lap_number=5, position=1, cumulative_time=5400.0),
            _make_lap(driver="NOR", lap_number=5, position=2, cumulative_time=5403.5),
        ]
        result = derive_practice_traffic(laps)
        follower = [l for l in result if l["driver"] == "NOR"][0]
        assert follower["in_traffic"] is False
        assert follower["gap_to_car_ahead"] == pytest.approx(3.5, abs=0.01)

    def test_custom_threshold(self):
        """Custom threshold value should work correctly."""
        laps = [
            _make_lap(driver="VER", lap_number=5, position=1, cumulative_time=5400.0),
            _make_lap(driver="NOR", lap_number=5, position=2, cumulative_time=5401.0),
        ]
        result = derive_practice_traffic(laps, threshold=0.5)
        follower = [l for l in result if l["driver"] == "NOR"][0]
        # 1.0s gap > 0.5s threshold → not in traffic
        assert follower["in_traffic"] is False

    def test_empty_laps(self):
        """Empty input returns empty output."""
        assert derive_practice_traffic([]) == []

    def test_missing_position_fallback(self):
        """Laps without position should default to in_traffic=False."""
        laps = [
            _make_lap(driver="VER", lap_number=5, position=None, cumulative_time=5400.0),
            _make_lap(driver="NOR", lap_number=5, position=None, cumulative_time=5400.8),
        ]
        result = derive_practice_traffic(laps)
        for l in result:
            assert l["in_traffic"] is False

    def test_missing_cumulative_time_fallback(self):
        """Laps without cumulative_time should default to in_traffic=False."""
        laps = [
            _make_lap(driver="VER", lap_number=5, position=1),
            _make_lap(driver="NOR", lap_number=5, position=2),
        ]
        result = derive_practice_traffic(laps)
        for l in result:
            assert l["in_traffic"] is False

    def test_practice_50_percent_threshold(self):
        """If fewer than 50% of drivers have valid data, skip traffic detection."""
        # 3 drivers on same lap: only 1 has valid data → < 50% → skip
        laps = [
            _make_lap(driver="VER", lap_number=5, position=1, cumulative_time=5400.0),
            _make_lap(driver="NOR", lap_number=5, position=None, cumulative_time=None),
            _make_lap(driver="LEC", lap_number=5, position=None, cumulative_time=None),
        ]
        result = derive_practice_traffic(laps)
        for l in result:
            assert l["in_traffic"] is False

    def test_multi_car_train(self):
        """3-car train with close gaps → followers flagged."""
        laps = [
            _make_lap(driver="VER", lap_number=10, position=1, cumulative_time=5400.0),
            _make_lap(driver="NOR", lap_number=10, position=2, cumulative_time=5400.5),
            _make_lap(driver="LEC", lap_number=10, position=3, cumulative_time=5401.2),
        ]
        result = derive_practice_traffic(laps)
        ver = [l for l in result if l["driver"] == "VER"][0]
        nor = [l for l in result if l["driver"] == "NOR"][0]
        lec = [l for l in result if l["driver"] == "LEC"][0]

        assert ver["in_traffic"] is False
        assert nor["in_traffic"] is True
        assert nor["gap_to_car_ahead"] == pytest.approx(0.5, abs=0.01)
        assert lec["in_traffic"] is True
        assert lec["gap_to_car_ahead"] == pytest.approx(0.7, abs=0.01)

    def test_defaults_set(self):
        """All laps should have gap_to_car_ahead and in_traffic after processing."""
        laps = [
            _make_lap(driver="VER", lap_number=5, position=1, cumulative_time=5400.0),
        ]
        result = derive_practice_traffic(laps)
        for l in result:
            assert "gap_to_car_ahead" in l
            assert "in_traffic" in l
