"""Tests for race lap classification, fuel correction, and traffic derivation."""

import pytest
import numpy as np
from app.services.race.transforms import (
    classify_race_laps,
    apply_fuel_correction,
    derive_traffic,
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
    position=1,
    **overrides,
):
    """Helper to create a single lap dict with sensible defaults."""
    lap = {
        "driver": driver,
        "team": "Red Bull Racing",
        "lap_number": lap_number,
        "lap_time": lap_time,
        "sector1_time": lap_time * 0.30 if lap_time else None,
        "sector2_time": lap_time * 0.38 if lap_time else None,
        "sector3_time": lap_time * 0.32 if lap_time else None,
        "compound": "MEDIUM",
        "tyre_life": tyre_life,
        "stint": stint,
        "position": position,
        "pit_in_time": pit_in_time,
        "pit_out_time": pit_out_time,
        "track_status": track_status,
        "is_personal_best": False,
    }
    lap.update(overrides)
    return lap


@pytest.fixture
def sample_racing_laps():
    """Generate a realistic set of 20 racing laps for a single driver."""
    laps = []
    for i in range(1, 21):
        # Normal racing times around 90s with small variation
        laps.append(_make_lap(lap_number=i, lap_time=90.0 + 0.1 * i, tyre_life=i))
    return laps


@pytest.fixture
def mixed_laps():
    """Generate laps with various classification types."""
    return [
        # Normal racing laps
        _make_lap(lap_number=2, lap_time=90.5, tyre_life=2),
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
        # Safety car
        _make_lap(lap_number=15, lap_time=120.0, track_status="4", tyre_life=5, stint=2),
        # VSC
        _make_lap(lap_number=16, lap_time=105.0, track_status="6", tyre_life=6, stint=2),
        # Red flag
        _make_lap(lap_number=20, lap_time=None, track_status="5", tyre_life=10, stint=2),
        # Formation lap (no time)
        _make_lap(lap_number=1, lap_time=None, tyre_life=1),
        # Normal racing after pit
        _make_lap(lap_number=12, lap_time=90.6, tyre_life=2, stint=2),
        _make_lap(lap_number=13, lap_time=90.4, tyre_life=3, stint=2),
        _make_lap(lap_number=14, lap_time=90.3, tyre_life=4, stint=2),
        _make_lap(lap_number=17, lap_time=90.2, tyre_life=7, stint=2),
        _make_lap(lap_number=18, lap_time=90.5, tyre_life=8, stint=2),
        _make_lap(lap_number=19, lap_time=90.3, tyre_life=9, stint=2),
    ]


# =============================================================================
# Test Lap Classification
# =============================================================================


class TestLapClassification:
    """Test the classify_race_laps function."""

    def test_empty_list(self):
        """Empty input returns empty output."""
        assert classify_race_laps([]) == []

    def test_normal_racing_lap(self, sample_racing_laps):
        """Normal green-flag laps should be classified as RACING."""
        result = classify_race_laps(sample_racing_laps)
        # Most laps should be RACING (some may be ANOMALY if outlier detection triggers)
        racing_count = sum(1 for l in result if l["classification"] == "RACING")
        assert racing_count >= 15  # Most of 20 laps should be RACING

    def test_in_lap_classified(self, mixed_laps):
        """Laps with pit_in_time should be classified as IN_LAP."""
        result = classify_race_laps(mixed_laps)
        in_laps = [l for l in result if l["classification"] == "IN_LAP"]
        assert len(in_laps) == 1
        assert in_laps[0]["lap_number"] == 10

    def test_out_lap_classified(self, mixed_laps):
        """Laps with pit_out_time should be classified as OUT_LAP."""
        result = classify_race_laps(mixed_laps)
        out_laps = [l for l in result if l["classification"] == "OUT_LAP"]
        assert len(out_laps) == 1
        assert out_laps[0]["lap_number"] == 11

    def test_safety_car_classified(self, mixed_laps):
        """Laps with track_status containing '4' should be SAFETY_CAR."""
        result = classify_race_laps(mixed_laps)
        sc_laps = [l for l in result if l["classification"] == "SAFETY_CAR"]
        assert len(sc_laps) == 1
        assert sc_laps[0]["lap_number"] == 15

    def test_vsc_classified(self, mixed_laps):
        """Laps with track_status containing '6' should be VSC."""
        result = classify_race_laps(mixed_laps)
        vsc_laps = [l for l in result if l["classification"] == "VSC"]
        assert len(vsc_laps) == 1
        assert vsc_laps[0]["lap_number"] == 16

    def test_red_flag_classified(self, mixed_laps):
        """Laps with track_status containing '5' should be RED_FLAG."""
        result = classify_race_laps(mixed_laps)
        rf_laps = [l for l in result if l["classification"] == "RED_FLAG"]
        assert len(rf_laps) == 1
        assert rf_laps[0]["lap_number"] == 20

    def test_formation_lap_no_time(self, mixed_laps):
        """Lap 1 with no time should be classified as FORMATION."""
        result = classify_race_laps(mixed_laps)
        formation = [l for l in result if l["classification"] == "FORMATION"]
        assert len(formation) >= 1
        assert any(l["lap_number"] == 1 for l in formation)

    def test_concatenated_track_status(self):
        """TrackStatus '14' should detect safety car (contains '4')."""
        laps = [
            _make_lap(lap_number=5, lap_time=100.0, track_status="14"),
            _make_lap(lap_number=6, lap_time=90.0),
            _make_lap(lap_number=7, lap_time=90.1),
            _make_lap(lap_number=8, lap_time=90.2),
            _make_lap(lap_number=9, lap_time=90.3),
        ]
        result = classify_race_laps(laps)
        assert result[0]["classification"] == "SAFETY_CAR"

    def test_outlier_iqr_detection(self):
        """Laps beyond Q3 + 1.5*IQR should be classified as ANOMALY."""
        laps = [_make_lap(lap_number=i, lap_time=90.0 + 0.1 * i, tyre_life=i) for i in range(2, 22)]
        # Add one very slow lap
        laps.append(_make_lap(lap_number=22, lap_time=130.0, tyre_life=22))
        result = classify_race_laps(laps)
        anomalies = [l for l in result if l["classification"] == "ANOMALY"]
        assert len(anomalies) >= 1
        assert any(l["lap_number"] == 22 for l in anomalies)

    def test_outlier_percentage_cap(self):
        """Laps beyond 110% of driver median should be ANOMALY."""
        # All laps around 90s, one at 100s (>110% of ~90s median = 99s)
        laps = [_make_lap(lap_number=i, lap_time=90.0, tyre_life=i) for i in range(2, 22)]
        laps.append(_make_lap(lap_number=22, lap_time=100.0, tyre_life=22))
        result = classify_race_laps(laps)
        anomalies = [l for l in result if l["classification"] == "ANOMALY"]
        assert len(anomalies) >= 1
        assert any(l["lap_number"] == 22 for l in anomalies)

    def test_warm_up_flag(self, mixed_laps):
        """First 2 laps of each stint (tyre_life <= 2) should have is_warm_up=True."""
        result = classify_race_laps(mixed_laps)
        warm_ups = [l for l in result if l.get("is_warm_up", False)]
        # Should include laps with tyre_life 1 and 2 that are RACING
        for wu in warm_ups:
            assert wu["tyre_life"] <= 2
            assert wu["classification"] == "RACING"

    def test_warm_up_not_set_for_non_racing(self):
        """Warm-up flag should not be set for non-racing laps."""
        laps = [
            _make_lap(lap_number=15, lap_time=120.0, track_status="4", tyre_life=1, stint=2),
        ]
        result = classify_race_laps(laps)
        assert result[0]["is_warm_up"] is False

    def test_pit_classification_priority_over_track_status(self):
        """Pit in/out should take priority over track status classification."""
        laps = [
            _make_lap(lap_number=10, lap_time=110.0, pit_in_time=1000.0, track_status="4"),
            _make_lap(lap_number=11, lap_time=90.0),
            _make_lap(lap_number=12, lap_time=90.1),
            _make_lap(lap_number=13, lap_time=90.2),
            _make_lap(lap_number=14, lap_time=90.3),
        ]
        result = classify_race_laps(laps)
        # Pit in takes priority even though track_status has '4'
        assert result[0]["classification"] == "IN_LAP"


# =============================================================================
# Test Fuel Correction
# =============================================================================


class TestFuelCorrection:
    """Test the apply_fuel_correction function."""

    def test_early_lap_corrected_more(self):
        """Early-race laps should have larger correction than late-race laps."""
        laps = [
            _make_lap(lap_number=1, lap_time=95.0),
            _make_lap(lap_number=50, lap_time=92.0),
        ]
        for l in laps:
            l["classification"] = "RACING"
        result = apply_fuel_correction(laps, total_race_laps=50, fuel_effect_per_kg=0.032)
        correction_lap1 = result[0]["lap_time"] - result[0]["fuel_corrected_time"]
        correction_lap50 = result[1]["lap_time"] - result[1]["fuel_corrected_time"]
        assert correction_lap1 > correction_lap50

    def test_corrected_time_less_than_raw(self):
        """Fuel corrected time should always be less than raw time."""
        laps = [_make_lap(lap_number=i, lap_time=90.0) for i in range(1, 51)]
        for l in laps:
            l["classification"] = "RACING"
        result = apply_fuel_correction(laps, total_race_laps=50)
        for l in result:
            assert l["fuel_corrected_time"] <= l["lap_time"]

    def test_non_racing_laps_not_corrected(self):
        """IN_LAP, OUT_LAP, SAFETY_CAR laps should not get fuel correction."""
        laps = [
            _make_lap(lap_number=10, lap_time=110.0),
            _make_lap(lap_number=11, lap_time=100.0),
        ]
        laps[0]["classification"] = "IN_LAP"
        laps[1]["classification"] = "OUT_LAP"
        result = apply_fuel_correction(laps, total_race_laps=50)
        assert result[0]["fuel_corrected_time"] is None
        assert result[1]["fuel_corrected_time"] is None

    def test_none_lap_time_handled(self):
        """Laps with None lap_time should get None fuel_corrected_time."""
        laps = [_make_lap(lap_number=5, lap_time=None)]
        laps[0]["classification"] = "RACING"
        result = apply_fuel_correction(laps, total_race_laps=50)
        assert result[0]["fuel_corrected_time"] is None

    def test_fuel_remaining_clamped_to_zero(self):
        """Fuel remaining should never go negative (lap beyond race length)."""
        laps = [_make_lap(lap_number=55, lap_time=90.0)]
        laps[0]["classification"] = "RACING"
        result = apply_fuel_correction(laps, total_race_laps=50)
        # With fuel_remaining = 0, no correction applied
        assert result[0]["fuel_corrected_time"] == pytest.approx(result[0]["lap_time"])

    def test_custom_fuel_factor(self):
        """Different fuel_effect_per_kg should produce different corrections."""
        lap_low = _make_lap(lap_number=1, lap_time=95.0)
        lap_high = _make_lap(lap_number=1, lap_time=95.0)
        lap_low["classification"] = "RACING"
        lap_high["classification"] = "RACING"

        result_low = apply_fuel_correction([lap_low], 50, fuel_effect_per_kg=0.028)
        result_high = apply_fuel_correction([lap_high], 50, fuel_effect_per_kg=0.036)
        # Higher factor → larger correction → lower corrected time
        assert result_high[0]["fuel_corrected_time"] < result_low[0]["fuel_corrected_time"]

    def test_zero_fuel_effect(self):
        """With fuel_effect_per_kg=0, corrected equals raw."""
        laps = [_make_lap(lap_number=1, lap_time=90.0)]
        laps[0]["classification"] = "RACING"
        result = apply_fuel_correction(laps, total_race_laps=50, fuel_effect_per_kg=0.0)
        assert result[0]["fuel_corrected_time"] == pytest.approx(result[0]["lap_time"])

    def test_anomaly_laps_get_corrected(self):
        """ANOMALY laps should also receive fuel correction."""
        laps = [_make_lap(lap_number=10, lap_time=120.0)]
        laps[0]["classification"] = "ANOMALY"
        result = apply_fuel_correction(laps, total_race_laps=50)
        assert result[0]["fuel_corrected_time"] is not None
        assert result[0]["fuel_corrected_time"] < result[0]["lap_time"]

    def test_empty_laps(self):
        """Empty input returns empty output."""
        assert apply_fuel_correction([], total_race_laps=50) == []

    def test_zero_total_laps(self):
        """Zero total_race_laps should set all corrections to None."""
        laps = [_make_lap(lap_number=1, lap_time=90.0)]
        laps[0]["classification"] = "RACING"
        result = apply_fuel_correction(laps, total_race_laps=0)
        assert result[0]["fuel_corrected_time"] is None


# =============================================================================
# Test Traffic Derivation
# =============================================================================


class TestTrafficDerivation:
    """Test the derive_traffic function using cumulative session time."""

    def test_leader_not_in_traffic(self):
        """Race leader should never be flagged as in traffic."""
        laps = [
            _make_lap(driver="VER", lap_number=5, position=1, cumulative_time=5400.0),
            _make_lap(driver="NOR", lap_number=5, position=2, cumulative_time=5400.8),
        ]
        result = derive_traffic(laps)
        leader = [l for l in result if l["driver"] == "VER"][0]
        assert leader["in_traffic"] is False
        assert leader["gap_to_car_ahead"] is None

    def test_close_following_flagged(self):
        """Driver within 1.5s of car ahead should be flagged in_traffic=True."""
        laps = [
            _make_lap(driver="VER", lap_number=5, position=1, cumulative_time=5400.0),
            _make_lap(driver="NOR", lap_number=5, position=2, cumulative_time=5400.8),
        ]
        result = derive_traffic(laps)
        follower = [l for l in result if l["driver"] == "NOR"][0]
        assert follower["in_traffic"] is True
        assert follower["gap_to_car_ahead"] == pytest.approx(0.8, abs=0.01)

    def test_gap_above_threshold_not_flagged(self):
        """Driver more than 1.5s behind should not be flagged."""
        laps = [
            _make_lap(driver="VER", lap_number=5, position=1, cumulative_time=5400.0),
            _make_lap(driver="NOR", lap_number=5, position=2, cumulative_time=5403.5),
        ]
        result = derive_traffic(laps)
        follower = [l for l in result if l["driver"] == "NOR"][0]
        assert follower["in_traffic"] is False
        assert follower["gap_to_car_ahead"] == pytest.approx(3.5, abs=0.01)

    def test_custom_threshold(self):
        """Custom threshold value should work correctly."""
        laps = [
            _make_lap(driver="VER", lap_number=5, position=1, cumulative_time=5400.0),
            _make_lap(driver="NOR", lap_number=5, position=2, cumulative_time=5401.0),
        ]
        result = derive_traffic(laps, threshold=0.5)
        follower = [l for l in result if l["driver"] == "NOR"][0]
        # 1.0s gap > 0.5s threshold → not in traffic
        assert follower["in_traffic"] is False

    def test_empty_laps(self):
        """Empty input returns empty output."""
        assert derive_traffic([]) == []

    def test_single_car(self):
        """Single car on a lap should not be flagged."""
        laps = [_make_lap(driver="VER", lap_number=5, position=1, cumulative_time=5400.0)]
        result = derive_traffic(laps)
        assert result[0]["in_traffic"] is False

    def test_missing_position_fallback(self):
        """Laps without position should get safe defaults."""
        laps = [
            _make_lap(driver="VER", lap_number=5, position=None, cumulative_time=5400.0),
            _make_lap(driver="NOR", lap_number=5, position=None, cumulative_time=5400.8),
        ]
        result = derive_traffic(laps)
        for l in result:
            assert l["in_traffic"] is False

    def test_missing_cumulative_time_fallback(self):
        """Laps without cumulative_time should get safe defaults (no crash)."""
        laps = [
            _make_lap(driver="VER", lap_number=5, position=1),
            _make_lap(driver="NOR", lap_number=5, position=2),
        ]
        result = derive_traffic(laps)
        for l in result:
            assert l["in_traffic"] is False
            assert l["gap_to_car_ahead"] is None

    def test_distinguishes_close_pace_from_close_gap(self):
        """Two drivers with identical pace but 15s physical gap → NOT in traffic.

        This is the exact failure mode of the old lap-time-differential proxy:
        both drivers lap at ~90s, so the time diff is ~0s, but they are 15s apart
        on track. The old method would flag this as traffic; the new method does not.
        """
        laps = [
            _make_lap(driver="VER", lap_number=10, lap_time=90.0, position=1, cumulative_time=5400.0),
            _make_lap(driver="NOR", lap_number=10, lap_time=90.1, position=2, cumulative_time=5415.0),
        ]
        result = derive_traffic(laps)
        follower = [l for l in result if l["driver"] == "NOR"][0]
        assert follower["in_traffic"] is False
        assert follower["gap_to_car_ahead"] == pytest.approx(15.0, abs=0.01)

    def test_multi_car_train(self):
        """3-car DRS train with 0.5-0.7s intervals → all followers in traffic."""
        laps = [
            _make_lap(driver="VER", lap_number=10, position=1, cumulative_time=5400.0),
            _make_lap(driver="NOR", lap_number=10, position=2, cumulative_time=5400.5),
            _make_lap(driver="LEC", lap_number=10, position=3, cumulative_time=5401.2),
        ]
        result = derive_traffic(laps)
        ver = [l for l in result if l["driver"] == "VER"][0]
        nor = [l for l in result if l["driver"] == "NOR"][0]
        lec = [l for l in result if l["driver"] == "LEC"][0]

        # Leader: not in traffic
        assert ver["in_traffic"] is False
        assert ver["gap_to_car_ahead"] is None

        # NOR: 0.5s behind VER → in traffic
        assert nor["in_traffic"] is True
        assert nor["gap_to_car_ahead"] == pytest.approx(0.5, abs=0.01)

        # LEC: 0.7s behind NOR → in traffic (pairwise, not gap to leader)
        assert lec["in_traffic"] is True
        assert lec["gap_to_car_ahead"] == pytest.approx(0.7, abs=0.01)


# =============================================================================
# Test Complex Race Scenarios
# =============================================================================


class TestComplexScenarios:
    """Edge cases from real race patterns."""

    def test_multiple_safety_car_periods(self):
        """Green → SC → Green → SC → Red → Green sequence."""
        laps = []
        for i in range(1, 21):
            status = "1"  # default green
            if i in (5, 6):
                status = "4"       # first SC
            elif i in (12, 13):
                status = "4"       # second SC
            elif i == 14:
                status = "5"       # red flag
            laps.append(_make_lap(
                lap_number=i,
                lap_time=90.0 if status == "1" else 110.0,
                track_status=status,
                tyre_life=i,
            ))
        classified = classify_race_laps(laps)
        sc_count = sum(1 for l in classified if l["classification"] == "SAFETY_CAR")
        rf_count = sum(1 for l in classified if l["classification"] == "RED_FLAG")
        racing_count = sum(1 for l in classified if l["classification"] == "RACING")
        assert sc_count == 4   # laps 5, 6, 12, 13
        assert rf_count == 1   # lap 14
        assert racing_count > 0

    def test_driver_dnf_mid_race(self):
        """Driver with only 15 of 57 laps still produces valid classifications."""
        laps = []
        for i in range(2, 17):  # 15 laps then DNF
            laps.append(_make_lap(
                driver="SAR",
                lap_number=i,
                lap_time=92.0 + (i * 0.05),
                tyre_life=i,
                position=18,
            ))
        classified = classify_race_laps(laps)
        racing = [l for l in classified if l["classification"] == "RACING"]
        assert len(racing) > 0
        # With such consistent data, no anomalies expected
        anomalies = [l for l in classified if l["classification"] == "ANOMALY"]
        assert len(anomalies) == 0

    def test_red_flag_restart_stint_numbering(self):
        """Red flag restart may reset stint numbering — verify stints extract."""
        from app.services.race.race_data_service import extract_stints
        laps = []
        # Stint 1: laps 2-10
        for i in range(2, 11):
            laps.append({
                "driver": "VER", "team": "RBR",
                "lap_number": i, "lap_time": 90.0,
                "compound": "SOFT", "tyre_life": i - 1,
                "stint": 1, "classification": "RACING",
                "position": 1,
            })
        # Stint 2 after red flag: laps 15-25 (gap in lap numbers)
        for i in range(15, 26):
            laps.append({
                "driver": "VER", "team": "RBR",
                "lap_number": i, "lap_time": 89.5,
                "compound": "MEDIUM", "tyre_life": i - 14,
                "stint": 2, "classification": "RACING",
                "position": 1,
            })
        stints = extract_stints(laps)
        assert len(stints) == 2
        assert stints[0].compound == "SOFT"
        assert stints[1].compound == "MEDIUM"


# =============================================================================
# Test Fuel Correction Mathematical Properties
# =============================================================================


class TestFuelCorrectionMathematical:
    """Verify the mathematical properties of fuel correction."""

    def test_correction_magnitude_matches_physics(self):
        """
        For a 57-lap race with 110kg fuel at 0.032 s/kg:
        Lap 1 correction = (110 - 110/57 * 1) * 0.032 ≈ 3.46s
        Lap 57 correction = (110 - 110/57 * 57) * 0.032 ≈ 0.0s
        Total spread removed ≈ 3.46s
        """
        laps = []
        for i in range(1, 58):
            laps.append(_make_lap(
                lap_number=i,
                lap_time=90.0,
                tyre_life=i,
            ))
        # Pre-classify as RACING
        for l in laps:
            l["classification"] = "RACING"

        corrected = apply_fuel_correction(laps, 57, 0.032, 110.0)
        racing = [l for l in corrected if l["fuel_corrected_time"] is not None]

        lap1 = next(l for l in racing if l["lap_number"] == 1)
        lap57 = next(l for l in racing if l["lap_number"] == 57)

        # Lap 1 should have ~3.4-3.5s subtracted
        correction_lap1 = lap1["lap_time"] - lap1["fuel_corrected_time"]
        assert 3.0 < correction_lap1 < 4.0, f"Lap 1 correction: {correction_lap1}"

        # Lap 57 should have ~0.06s subtracted (nearly empty)
        correction_lap57 = lap57["lap_time"] - lap57["fuel_corrected_time"]
        assert correction_lap57 < 0.1, f"Lap 57 correction: {correction_lap57}"

        # Total spread of corrections should be ~3.4s
        spread = correction_lap1 - correction_lap57
        assert 3.0 < spread < 4.0, f"Correction spread: {spread}"
