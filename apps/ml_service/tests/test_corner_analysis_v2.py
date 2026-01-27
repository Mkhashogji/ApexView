"""
Tests for v2 Corner Analysis Functions

Tests the deceleration-based corner analysis system including:
- compute_deceleration()
- detect_apex_from_speed_v2()
- detect_braking_zone_v2()
- detect_exit_zone_v2()
- validate_against_sectors()
- analyze_single_corner_v2()
- analyze_corners_v2()
"""

import pytest
import numpy as np
from typing import List

from services.corner_analysis import (
    compute_deceleration,
    detect_apex_from_speed_v2,
    detect_braking_zone_v2,
    detect_exit_zone_v2,
    validate_against_sectors,
    analyze_single_corner_v2,
    analyze_corners_v2,
    CornerInput,
    CornerResult,
    CornerResultV2,
    SectorValidation,
)
from services.delta_analysis import DeltaResult
from core.corner_config import CornerAnalysisConfig, get_config_for_circuit


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_telemetry():
    """Create sample telemetry data for testing."""
    # Simulate a straight into a corner
    # Distance: 0-500m, Speed starts at 300km/h, drops to 100km/h at apex (400m), accelerates to 250km/h
    distance = np.linspace(0, 500, 100)

    # Speed profile: accelerating, then braking, then accelerating
    speed = np.zeros(100)
    for i, d in enumerate(distance):
        if d < 250:
            speed[i] = 300  # High speed on straight
        elif d < 350:
            # Braking zone
            speed[i] = 300 - (d - 250) * 2  # Decelerate
        elif d < 400:
            # Trail braking to apex
            speed[i] = 100 + (d - 350) * 0.5  # Slow decel
        else:
            # Exit acceleration
            speed[i] = 125 + (d - 400) * 1.25  # Accelerate

    # Brake signal: on in braking zone
    brake = np.zeros(100)
    for i, d in enumerate(distance):
        if 250 <= d <= 380:
            brake[i] = 100.0  # Full brake
        else:
            brake[i] = 0.0

    return distance, speed, brake


@pytest.fixture
def sample_delta_result():
    """Create a sample DeltaResult for testing."""
    distance = list(np.linspace(0, 500, 100))
    # Simulate compare driver being slower (positive delta)
    delta = [0.0] * 40 + list(np.linspace(0, 0.1, 30)) + [0.1] * 30

    return DeltaResult(
        reference_driver="REF",
        compare_driver="CMP",
        distance=distance,
        delta=delta,
        raw_delta=delta,
        official_gap=0.1,
        scaling_factor=1.0,
        telemetry_gap=0.1,
        confidence=1.0
    )


@pytest.fixture
def default_config():
    """Get default corner analysis config."""
    return CornerAnalysisConfig()


# =============================================================================
# Test compute_deceleration()
# =============================================================================

class TestComputeDeceleration:
    """Tests for compute_deceleration function."""

    def test_constant_speed_zero_deceleration(self):
        """Constant speed should result in near-zero deceleration."""
        distance = np.linspace(0, 100, 50)
        speed = np.full(50, 200.0)  # Constant 200 km/h

        decel = compute_deceleration(distance, speed, smoothing_window=1)

        # Should be near zero (within numerical precision)
        assert np.allclose(decel, 0, atol=0.1)

    def test_braking_negative_deceleration(self):
        """Braking should produce negative deceleration."""
        distance = np.linspace(0, 100, 50)
        # Speed drops from 300 to 100 km/h over 100m
        speed = np.linspace(300, 100, 50)

        decel = compute_deceleration(distance, speed, smoothing_window=1)

        # All values should be negative (braking)
        assert np.all(decel < 0)
        # Heavy braking should produce < -5 m/s²
        assert decel.min() < -5

    def test_acceleration_positive_deceleration(self):
        """Acceleration should produce positive values."""
        distance = np.linspace(0, 100, 50)
        # Speed increases from 100 to 200 km/h over 100m
        speed = np.linspace(100, 200, 50)

        decel = compute_deceleration(distance, speed, smoothing_window=1)

        # All values should be positive (accelerating)
        assert np.all(decel > 0)

    def test_smoothing_reduces_noise(self):
        """Smoothing should reduce noise in the signal."""
        distance = np.linspace(0, 100, 50)
        # Add noise to speed
        np.random.seed(42)
        speed = 200 + np.random.normal(0, 5, 50)

        decel_unsmoothed = compute_deceleration(distance, speed, smoothing_window=1)
        decel_smoothed = compute_deceleration(distance, speed, smoothing_window=5)

        # Smoothed should have lower variance
        assert np.std(decel_smoothed) < np.std(decel_unsmoothed)

    def test_handles_empty_arrays(self):
        """Should handle empty arrays gracefully."""
        decel = compute_deceleration(np.array([]), np.array([]))

        # Should return a valid array (even if just default)
        assert isinstance(decel, np.ndarray)


# =============================================================================
# Test detect_apex_from_speed_v2()
# =============================================================================

class TestDetectApexFromSpeedV2:
    """Tests for detect_apex_from_speed_v2 function."""

    def test_finds_speed_minimum(self):
        """Should find the speed minimum within search window."""
        distance = np.linspace(0, 500, 100)
        # Minimum speed at 400m
        speed = np.abs(distance - 400) + 100  # V shape with min at 400

        apex_dist, apex_speed, confidence = detect_apex_from_speed_v2(
            distance, speed, nominal_apex=400, search_margin=50
        )

        # Should find the minimum
        assert 395 <= apex_dist <= 405  # Close to 400m
        assert 100 <= apex_speed <= 105  # Minimum speed (approx due to linspace)

    def test_high_confidence_near_nominal(self):
        """Apex near nominal should have high confidence."""
        distance = np.linspace(0, 500, 100)
        speed = np.abs(distance - 400) + 100

        apex_dist, apex_speed, confidence = detect_apex_from_speed_v2(
            distance, speed, nominal_apex=400, search_margin=50
        )

        assert confidence == "high"

    def test_low_confidence_far_from_nominal(self):
        """Apex far from nominal should have low confidence."""
        distance = np.linspace(0, 500, 100)
        # Minimum speed at 350m, but nominal is 400m
        speed = np.abs(distance - 350) + 100

        apex_dist, apex_speed, confidence = detect_apex_from_speed_v2(
            distance, speed, nominal_apex=400, search_margin=100
        )

        assert confidence in ["medium", "low"]

    def test_returns_nominal_when_no_data(self):
        """Should return nominal apex when no data in search window."""
        distance = np.linspace(0, 100, 50)  # Only 0-100m
        speed = np.full(50, 200.0)

        apex_dist, apex_speed, confidence = detect_apex_from_speed_v2(
            distance, speed, nominal_apex=500, search_margin=50
        )

        assert apex_dist == 500  # Returns nominal
        assert confidence == "low"


# =============================================================================
# Test detect_braking_zone_v2()
# =============================================================================

class TestDetectBrakingZoneV2:
    """Tests for detect_braking_zone_v2 function."""

    def test_two_stage_detection(self, sample_telemetry, default_config):
        """Should use two-stage detection when brake signal available."""
        distance, speed, brake = sample_telemetry
        decel = compute_deceleration(distance, speed)

        brake_dist, confidence, metadata = detect_braking_zone_v2(
            distance, brake, speed, decel,
            apex_distance=400, config=default_config
        )

        # Should detect braking point
        assert 240 <= brake_dist <= 270  # Near expected braking zone
        assert metadata["stage"] in ["two_stage", "decel_only"]

    def test_decel_only_fallback(self, default_config):
        """Should use decel-only when no brake signal."""
        distance = np.linspace(0, 500, 100)
        speed = np.concatenate([
            np.full(50, 300),  # High speed
            np.linspace(300, 100, 50)  # Braking
        ])
        brake = np.zeros(100)  # No brake signal
        decel = compute_deceleration(distance, speed)

        brake_dist, confidence, metadata = detect_braking_zone_v2(
            distance, brake, speed, decel,
            apex_distance=400, config=default_config
        )

        assert metadata["stage"] in ["decel_only", "fallback"]

    def test_confidence_based_on_alignment(self, sample_telemetry, default_config):
        """Confidence should reflect boolean/decel alignment."""
        distance, speed, brake = sample_telemetry
        decel = compute_deceleration(distance, speed)

        _, confidence, metadata = detect_braking_zone_v2(
            distance, brake, speed, decel,
            apex_distance=400, config=default_config
        )

        assert confidence in ["high", "medium", "low"]


# =============================================================================
# Test detect_exit_zone_v2()
# =============================================================================

class TestDetectExitZoneV2:
    """Tests for detect_exit_zone_v2 function."""

    def test_detects_exit_via_acceleration(self, default_config):
        """Should detect exit via sustained acceleration."""
        distance = np.linspace(300, 500, 50)
        # Speed increases after apex at 400m
        speed = np.where(distance < 400, 100, 100 + (distance - 400) * 2)
        decel = compute_deceleration(distance, speed)

        apex_idx = np.searchsorted(distance, 400)
        exit_dist, confidence = detect_exit_zone_v2(
            distance, speed, decel,
            apex_idx=apex_idx, entry_speed=300, config=default_config
        )

        # Should detect exit after apex
        assert exit_dist > 400

    def test_detects_exit_via_speed_recovery(self, default_config):
        """Should detect exit when speed recovers to threshold."""
        distance = np.linspace(300, 600, 100)
        # Speed drops to 100, then recovers to 255 (85% of 300)
        speed = np.zeros(100)
        for i, d in enumerate(distance):
            if d < 400:
                speed[i] = 100  # Apex speed
            else:
                speed[i] = min(100 + (d - 400) * 1, 260)  # Recover

        decel = compute_deceleration(distance, speed)
        apex_idx = np.searchsorted(distance, 400)

        exit_dist, confidence = detect_exit_zone_v2(
            distance, speed, decel,
            apex_idx=apex_idx, entry_speed=300, config=default_config
        )

        # Speed target is 300 * 0.85 = 255
        # Should detect exit when speed reaches 255
        assert exit_dist > 400


# =============================================================================
# Test validate_against_sectors()
# =============================================================================

class TestValidateAgainstSectors:
    """Tests for validate_against_sectors function."""

    def test_validates_matching_sectors(self):
        """Should validate when corner deltas match sector deltas."""
        # Create corner results that sum to sector deltas
        corner_results = [
            CornerResult(
                corner_number=1, name="T1", apex_distance=500,
                brake_distance=400, zone_start=380, zone_end=600,
                delta_change=0.05, cause="braking", confidence="high"
            ),
            CornerResult(
                corner_number=5, name="T5", apex_distance=1800,
                brake_distance=1700, zone_start=1680, zone_end=1900,
                delta_change=0.03, cause="apex", confidence="high"
            ),
            CornerResult(
                corner_number=10, name="T10", apex_distance=3200,
                brake_distance=3100, zone_start=3080, zone_end=3300,
                delta_change=-0.02, cause="exit", confidence="medium"
            ),
        ]

        # Sector boundaries at 1500m and 3000m
        # Sector deltas: S1=+0.05, S2=+0.03, S3=-0.02
        validations, conf_adj = validate_against_sectors(
            corner_results,
            sector_boundaries=(1500, 3000),
            ref_sectors=(30.0, 35.0, 25.0),
            comp_sectors=(30.05, 35.03, 24.98),
            tolerance=0.100
        )

        # All sectors should validate
        assert all(v.is_valid for v in validations)
        assert conf_adj == 1.0  # 3/3 sectors valid

    def test_fails_on_mismatch(self):
        """Should fail validation when corner deltas don't match sectors."""
        corner_results = [
            CornerResult(
                corner_number=1, name="T1", apex_distance=500,
                brake_distance=400, zone_start=380, zone_end=600,
                delta_change=0.5,  # Very large delta
                cause="braking", confidence="high"
            ),
        ]

        # Sector delta is much smaller than corner delta
        validations, conf_adj = validate_against_sectors(
            corner_results,
            sector_boundaries=(1500, 3000),
            ref_sectors=(30.0, 35.0, 25.0),
            comp_sectors=(30.05, 35.0, 25.0),  # Only +0.05s in S1
            tolerance=0.100
        )

        # Sector 1 should fail (corner shows 0.5s, official is 0.05s)
        assert not validations[0].is_valid
        assert conf_adj < 1.0

    def test_confidence_adjustment_range(self):
        """Confidence adjustment should be between 0.5 and 1.0."""
        corner_results = [
            CornerResult(
                corner_number=1, name="T1", apex_distance=500,
                brake_distance=400, zone_start=380, zone_end=600,
                delta_change=0.0, cause="braking", confidence="high"
            ),
        ]

        _, conf_adj = validate_against_sectors(
            corner_results,
            sector_boundaries=(1500, 3000),
            ref_sectors=(30.0, 35.0, 25.0),
            comp_sectors=(30.0, 35.0, 25.0),
            tolerance=0.100
        )

        assert 0.5 <= conf_adj <= 1.0


# =============================================================================
# Test analyze_single_corner_v2()
# =============================================================================

class TestAnalyzeSingleCornerV2:
    """Tests for analyze_single_corner_v2 function."""

    def test_returns_corner_result_v2(self, sample_telemetry, sample_delta_result, default_config):
        """Should return CornerResultV2 with v2-specific fields."""
        distance, speed, brake = sample_telemetry

        corner = CornerInput(
            corner_number=1, apex_distance=400,
            corner_type="left", name="Test Corner"
        )

        result = analyze_single_corner_v2(
            delta_result=sample_delta_result,
            ref_distance=distance,
            ref_brake=brake,
            ref_speed=speed,
            comp_distance=distance,
            comp_brake=brake,
            comp_speed=speed,
            corner=corner,
            config=default_config
        )

        assert isinstance(result, CornerResultV2)
        assert result.detected_apex != 0.0
        assert result.entry_speed != 0.0
        assert result.apex_speed != 0.0

    def test_dynamic_zone_detection(self, sample_telemetry, sample_delta_result, default_config):
        """Zone boundaries should be dynamically detected."""
        distance, speed, brake = sample_telemetry

        corner = CornerInput(
            corner_number=1, apex_distance=400,
            corner_type="left", name="Test Corner"
        )

        result = analyze_single_corner_v2(
            delta_result=sample_delta_result,
            ref_distance=distance,
            ref_brake=brake,
            ref_speed=speed,
            comp_distance=distance,
            comp_brake=brake,
            comp_speed=speed,
            corner=corner,
            config=default_config
        )

        # Zone should be based on detected brake point
        assert result.zone_start < result.zone_end
        assert result.zone_start < 400  # Before apex


# =============================================================================
# Test analyze_corners_v2()
# =============================================================================

class TestAnalyzeCornersV2:
    """Tests for analyze_corners_v2 function."""

    def test_analyzes_all_corners(self, sample_delta_result):
        """Should analyze all provided corners."""
        distance = np.linspace(0, 1000, 200)
        speed = 200 - 50 * np.sin(distance / 100)  # Wave pattern
        brake = np.where(speed < 180, 100.0, 0.0)

        corners = [
            CornerInput(corner_number=1, apex_distance=200, corner_type="left"),
            CornerInput(corner_number=2, apex_distance=500, corner_type="right"),
            CornerInput(corner_number=3, apex_distance=800, corner_type="left"),
        ]

        result = analyze_corners_v2(
            delta_result=sample_delta_result,
            ref_distance=list(distance),
            ref_brake=list(brake),
            ref_speed=list(speed),
            comp_distance=list(distance),
            comp_brake=list(brake),
            comp_speed=list(speed),
            corners=corners,
            circuit_id=""
        )

        assert len(result.corner_results) == 3

    def test_uses_circuit_config(self, sample_delta_result):
        """Should use circuit-specific config when provided."""
        distance = np.linspace(0, 500, 100)
        speed = np.full(100, 200.0)
        brake = np.zeros(100)

        corners = [
            CornerInput(corner_number=1, apex_distance=400, corner_type="left"),
        ]

        # Monaco has different config
        result = analyze_corners_v2(
            delta_result=sample_delta_result,
            ref_distance=list(distance),
            ref_brake=list(brake),
            ref_speed=list(speed),
            comp_distance=list(distance),
            comp_brake=list(brake),
            comp_speed=list(speed),
            corners=corners,
            circuit_id="monaco"
        )

        # Should complete without error
        assert len(result.corner_results) == 1


# =============================================================================
# Test Configuration
# =============================================================================

class TestCornerConfig:
    """Tests for corner configuration module."""

    def test_default_config_values(self):
        """Default config should have expected values."""
        config = CornerAnalysisConfig()

        assert config.braking_decel_threshold == -5.0
        assert config.acceleration_threshold == 2.0
        assert config.apex_search_margin == 50.0

    def test_circuit_specific_config(self):
        """Should return circuit-specific config when available."""
        monza_config = get_config_for_circuit("monza")

        assert monza_config.braking_decel_threshold == -6.0  # Heavier braking

    def test_unknown_circuit_returns_default(self):
        """Unknown circuits should return default config."""
        config = get_config_for_circuit("unknown_track")
        default = CornerAnalysisConfig()

        assert config.braking_decel_threshold == default.braking_decel_threshold


# =============================================================================
# Integration Tests
# =============================================================================

class TestV2Integration:
    """Integration tests for v2 corner analysis pipeline."""

    def test_full_pipeline(self):
        """Test complete v2 analysis pipeline."""
        # Create realistic telemetry
        distance = np.linspace(0, 1000, 200)

        # Ref driver: smooth, consistent
        ref_speed = np.zeros(200)
        for i, d in enumerate(distance):
            if d < 300:
                ref_speed[i] = 300
            elif d < 500:
                ref_speed[i] = 300 - (d - 300) * 1.0  # Brake
            else:
                ref_speed[i] = 100 + (d - 500) * 0.4  # Accelerate

        # Comp driver: late braker
        comp_speed = np.zeros(200)
        for i, d in enumerate(distance):
            if d < 350:
                comp_speed[i] = 300
            elif d < 500:
                comp_speed[i] = 300 - (d - 350) * 1.33  # Later, harder brake
            else:
                comp_speed[i] = 100 + (d - 500) * 0.4

        ref_brake = np.where(ref_speed < 290, 100.0, 0.0)
        comp_brake = np.where(comp_speed < 290, 100.0, 0.0)

        delta_result = DeltaResult(
            reference_driver="REF",
            compare_driver="CMP",
            distance=list(distance),
            delta=[0.0] * 200,
            raw_delta=[0.0] * 200,
            official_gap=0.0,
            scaling_factor=1.0,
            telemetry_gap=0.0,
            confidence=1.0
        )

        corners = [
            CornerInput(corner_number=1, apex_distance=500, corner_type="left", name="T1"),
        ]

        result = analyze_corners_v2(
            delta_result=delta_result,
            ref_distance=list(distance),
            ref_brake=list(ref_brake),
            ref_speed=list(ref_speed),
            comp_distance=list(distance),
            comp_brake=list(comp_brake),
            comp_speed=list(comp_speed),
            corners=corners,
            circuit_id=""
        )

        assert len(result.corner_results) == 1
        assert result.corner_results[0].corner_number == 1
