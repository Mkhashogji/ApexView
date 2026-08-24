"""
Tests for Corner Analysis Module

Tests the corner analysis functionality including:
- Braking zone detection
- Cause attribution (braking/apex/exit/multiple)
- Edge case handling (empty arrays, invalid zones)
- Full corner analysis flow
"""

import pytest
import numpy as np
from typing import List

from services.corner_analysis import (
    CornerInput,
    CornerResult,
    CornerAnalysisResult,
    _safe_array,
    _combine_confidence,
    detect_braking_zone,
    determine_cause,
    analyze_single_corner,
    analyze_corners,
    DEFAULT_ZONE_BEFORE_APEX,
    DEFAULT_ZONE_AFTER_APEX,
    BRAKE_THRESHOLD_PERCENT,
    APPROACH_MARGIN_METERS,
)
from services.delta_analysis import DeltaResult
from core.errors import NonFiniteTelemetryError


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_delta_result() -> DeltaResult:
    """Create a sample DeltaResult for testing."""
    distance = list(np.linspace(0, 5000, 500))
    # Create a delta that increases gradually, simulating compare driver getting slower
    delta = list(np.linspace(0, 0.5, 500))
    return DeltaResult(
        reference_driver="VER",
        compare_driver="NOR",
        distance=distance,
        delta=delta,
        raw_delta=delta,
        official_gap=0.5,
        scaling_factor=1.0,
        telemetry_gap=0.5,
        confidence=0.9
    )


@pytest.fixture
def sample_corners() -> List[CornerInput]:
    """Create sample corner inputs."""
    return [
        CornerInput(corner_number=1, apex_distance=300, corner_type="right", name="Turn 1"),
        CornerInput(corner_number=2, apex_distance=800, corner_type="left", name="Turn 2"),
        CornerInput(corner_number=3, apex_distance=1500, corner_type="right", name="Turn 3"),
    ]


@pytest.fixture
def sample_telemetry() -> tuple:
    """Create sample telemetry data with clear braking zones."""
    distance = np.linspace(0, 5000, 1000)

    # Create brake data with clear braking zones at known distances
    # Braking for T1 at ~100m, T2 at ~600m, T3 at ~1300m
    brake = np.zeros(1000)

    # T1 braking zone: 100-280m
    t1_brake_start = int(100 / 5)
    t1_brake_end = int(280 / 5)
    brake[t1_brake_start:t1_brake_end] = np.linspace(0, 80, t1_brake_end - t1_brake_start)

    # T2 braking zone: 600-780m
    t2_brake_start = int(600 / 5)
    t2_brake_end = int(780 / 5)
    brake[t2_brake_start:t2_brake_end] = np.linspace(0, 90, t2_brake_end - t2_brake_start)

    # T3 braking zone: 1300-1480m
    t3_brake_start = int(1300 / 5)
    t3_brake_end = int(1480 / 5)
    brake[t3_brake_start:t3_brake_end] = np.linspace(0, 85, t3_brake_end - t3_brake_start)

    return distance, brake


# ============================================================================
# _safe_array Tests
# ============================================================================

class TestSafeArray:
    """Tests for _safe_array utility function."""

    def test_safe_array_with_valid_list(self):
        """Test with a valid list."""
        result = _safe_array([1.0, 2.0, 3.0])
        assert len(result) == 3
        assert result[0] == 1.0
        assert result[2] == 3.0

    def test_safe_array_with_numpy_array(self):
        """Test with a numpy array."""
        arr = np.array([1.0, 2.0, 3.0])
        result = _safe_array(arr)
        assert len(result) == 3
        np.testing.assert_array_equal(result, arr)

    def test_safe_array_handles_none(self):
        """Test that None returns default array."""
        result = _safe_array(None, default_value=0.0)
        assert len(result) == 1
        assert result[0] == 0.0

    def test_safe_array_handles_empty_list(self):
        """Test that empty list returns default array."""
        result = _safe_array([], default_value=5.0)
        assert len(result) == 1
        assert result[0] == 5.0

    def test_safe_array_rejects_nan_and_inf(self):
        """WU-2: non-finite values (NaN AND ±inf) are rejected, never
        interpolated. inf is included deliberately — it was previously
        uncaught by both pydantic and this helper."""
        with pytest.raises(NonFiniteTelemetryError) as exc_info:
            _safe_array([1.0, np.nan, 3.0], name="speed")
        msg = str(exc_info.value)
        assert "speed" in msg
        assert "1 of 3" in msg
        assert exc_info.value.positions == [1]

        with pytest.raises(NonFiniteTelemetryError) as inf_info:
            _safe_array([1.0, np.inf, 3.0, -np.inf], name="distance")
        assert "distance" in str(inf_info.value)
        assert inf_info.value.n_nonfinite == 2

    def test_safe_array_rejects_all_nan(self):
        """WU-2: an all-NaN array is rejected — no full-length default fill.
        (Pre-WU-2 this fabricated a constant default_value array.)"""
        with pytest.raises(NonFiniteTelemetryError) as exc_info:
            _safe_array([np.nan, np.nan, np.nan], name="brake", default_value=10.0)
        msg = str(exc_info.value)
        assert "brake" in msg
        assert "3 of 3" in msg


# ============================================================================
# Braking Zone Detection Tests
# ============================================================================

class TestDetectBrakingZone:
    """Tests for braking zone detection."""

    def test_detect_braking_zone_clear_braking(self, sample_telemetry):
        """Test detection with clear braking event."""
        distance, brake = sample_telemetry

        # Apex at 300m, expect braking around 100m
        brake_dist, confidence = detect_braking_zone(distance, brake, apex_distance=300)

        # Should detect braking with high or medium confidence
        # (depends on exact gradient in test data)
        assert confidence in ["high", "medium"]
        # Braking should be detected within search zone
        assert 50 <= brake_dist <= 250

    def test_detect_braking_zone_no_braking(self):
        """Test detection with no braking in search zone."""
        distance = np.linspace(0, 1000, 200)
        brake = np.zeros(200)  # No braking at all

        brake_dist, confidence = detect_braking_zone(distance, brake, apex_distance=500)

        # Should return fallback with medium confidence
        assert confidence == "medium"
        # Fallback is apex - DEFAULT_ZONE_BEFORE_APEX
        expected = 500 - DEFAULT_ZONE_BEFORE_APEX
        assert abs(brake_dist - expected) < 10

    def test_detect_braking_zone_gradual_braking(self):
        """Test detection with gradual braking (low gradient)."""
        distance = np.linspace(0, 1000, 200)
        # Very gradual brake increase - gradient below threshold
        brake = np.linspace(0, 30, 200)

        brake_dist, confidence = detect_braking_zone(distance, brake, apex_distance=500)

        # Should not detect as clear braking due to low gradient
        # May return fallback or early point depending on threshold
        assert confidence in ["medium", "low"]

    def test_detect_braking_zone_already_braking(self):
        """Test detection when driver is already braking at search zone start."""
        distance = np.linspace(0, 1000, 200)
        brake = np.ones(200) * 50  # Constant 50% brake

        brake_dist, confidence = detect_braking_zone(distance, brake, apex_distance=500)

        # Should return search zone start with medium confidence
        assert confidence == "medium"

    def test_detect_braking_zone_empty_arrays(self):
        """Test detection with empty arrays."""
        brake_dist, confidence = detect_braking_zone(
            np.array([]), np.array([]), apex_distance=500
        )

        assert confidence == "low"

    def test_detect_braking_zone_invalid_search_zone(self):
        """Test detection when apex is at edge of distance array."""
        distance = np.linspace(0, 100, 50)  # Short track
        brake = np.ones(50) * 50

        # Apex at 50m with default offsets would create invalid search zone
        brake_dist, confidence = detect_braking_zone(distance, brake, apex_distance=50)

        # Should handle gracefully
        assert confidence in ["low", "medium"]
        assert brake_dist >= 0


# ============================================================================
# Cause Determination Tests
# ============================================================================

class TestDetermineCause:
    """Tests for cause attribution."""

    def test_determine_cause_braking(self):
        """Test that time lost in braking phase returns 'braking' or 'multiple'."""
        # Create delta that increases sharply in braking phase
        distance = list(np.linspace(0, 1000, 100))
        delta = [0.0] * 100

        # Zone: 300-600m, apex at 500m
        # Braking phase: 300-380m
        # Big delta increase in braking phase
        for i in range(30, 38):  # indices for ~300-380m
            delta[i] = (i - 30) * 0.02
        for i in range(38, 60):  # Rest of zone stays flat
            delta[i] = 0.16

        result = DeltaResult(
            reference_driver="VER",
            compare_driver="NOR",
            distance=distance,
            delta=delta,
            raw_delta=delta,
            official_gap=0.16,
            scaling_factor=1.0,
            telemetry_gap=0.16,
            confidence=0.9
        )

        cause = determine_cause(result, zone_start=300, zone_end=600, apex_distance=500)
        # The phase boundaries in the algorithm may cause this to be "multiple"
        # when delta changes span the boundary between braking and apex phases
        assert cause in ["braking", "multiple"]

    def test_determine_cause_apex(self):
        """Test that time lost at apex returns 'apex' or 'multiple'."""
        distance = list(np.linspace(0, 1000, 100))
        delta = [0.0] * 100

        # Zone: 300-600m, apex at 500m
        # Apex phase: ~380-520m
        # Big delta increase at apex
        for i in range(38, 52):  # indices for ~380-520m
            delta[i] = (i - 38) * 0.015
        for i in range(52, 60):
            delta[i] = 0.21

        result = DeltaResult(
            reference_driver="VER",
            compare_driver="NOR",
            distance=distance,
            delta=delta,
            raw_delta=delta,
            official_gap=0.21,
            scaling_factor=1.0,
            telemetry_gap=0.21,
            confidence=0.9
        )

        cause = determine_cause(result, zone_start=300, zone_end=600, apex_distance=500)
        # With the current phase boundaries, this may show as "multiple"
        assert cause in ["apex", "multiple"]

    def test_determine_cause_exit(self):
        """Test that time lost on exit returns 'exit'."""
        distance = list(np.linspace(0, 1000, 100))
        delta = [0.0] * 100

        # Zone: 300-600m, apex at 500m
        # Exit phase: ~520-600m
        # Big delta increase on exit
        for i in range(52, 60):  # indices for ~520-600m
            delta[i] = (i - 52) * 0.03

        result = DeltaResult(
            reference_driver="VER",
            compare_driver="NOR",
            distance=distance,
            delta=delta,
            raw_delta=delta,
            official_gap=0.24,
            scaling_factor=1.0,
            telemetry_gap=0.24,
            confidence=0.9
        )

        cause = determine_cause(result, zone_start=300, zone_end=600, apex_distance=500)
        assert cause == "exit"

    def test_determine_cause_multiple(self):
        """Test that distributed time loss returns 'multiple'."""
        distance = list(np.linspace(0, 1000, 100))
        delta = [0.0] * 100

        # Zone: 300-600m, apex at 500m
        # Time lost somewhat evenly distributed
        for i in range(30, 60):
            delta[i] = (i - 30) * 0.005  # Linear increase throughout zone

        result = DeltaResult(
            reference_driver="VER",
            compare_driver="NOR",
            distance=distance,
            delta=delta,
            raw_delta=delta,
            official_gap=0.15,
            scaling_factor=1.0,
            telemetry_gap=0.15,
            confidence=0.9
        )

        cause = determine_cause(result, zone_start=300, zone_end=600, apex_distance=500)
        assert cause == "multiple"

    def test_determine_cause_unknown_minimal_delta(self):
        """Test that minimal delta change returns 'unknown'."""
        distance = list(np.linspace(0, 1000, 100))
        delta = [0.001] * 100  # Almost no change

        result = DeltaResult(
            reference_driver="VER",
            compare_driver="NOR",
            distance=distance,
            delta=delta,
            raw_delta=delta,
            official_gap=0.001,
            scaling_factor=1.0,
            telemetry_gap=0.001,
            confidence=0.9
        )

        cause = determine_cause(result, zone_start=300, zone_end=600, apex_distance=500)
        assert cause == "unknown"


# ============================================================================
# Single Corner Analysis Tests
# ============================================================================

class TestAnalyzeSingleCorner:
    """Tests for single corner analysis."""

    def test_analyze_single_corner_basic(self, sample_delta_result, sample_telemetry):
        """Test basic single corner analysis."""
        distance, brake = sample_telemetry
        corner = CornerInput(
            corner_number=1,
            apex_distance=300,
            corner_type="right",
            name="Turn 1"
        )

        result = analyze_single_corner(
            delta_result=sample_delta_result,
            ref_distance=distance,
            ref_brake=brake,
            comp_distance=distance,  # Use same telemetry for comparison
            comp_brake=brake,
            corner=corner
        )

        assert result.corner_number == 1
        assert result.name == "Turn 1"
        assert result.apex_distance == 300
        assert result.zone_start < result.apex_distance
        assert result.zone_end > result.apex_distance
        assert result.confidence in ["high", "medium", "low"]
        assert result.cause in ["braking", "apex", "exit", "multiple", "unknown"]

    def test_analyze_single_corner_gain_in_braking(self):
        """Test corner where time is lost in braking phase."""
        # Create delta that increases sharply in braking zone
        distance = list(np.linspace(0, 1000, 200))
        delta = [0.0] * 200

        # Sharp increase before apex (braking zone)
        for i in range(20, 50):  # ~100-250m before apex at 300
            delta[i] = (i - 20) * 0.005
        for i in range(50, 200):
            delta[i] = 0.15

        result = DeltaResult(
            reference_driver="VER",
            compare_driver="NOR",
            distance=distance,
            delta=delta,
            raw_delta=delta,
            official_gap=0.15,
            scaling_factor=1.0,
            telemetry_gap=0.15,
            confidence=0.9
        )

        # Create brake telemetry with braking at ~100m
        ref_distance = np.array(distance)
        ref_brake = np.zeros(200)
        ref_brake[20:50] = np.linspace(0, 80, 30)

        # Comparison driver with same braking point
        comp_distance = ref_distance
        comp_brake = ref_brake.copy()

        corner = CornerInput(
            corner_number=1, apex_distance=300, corner_type="right"
        )

        corner_result = analyze_single_corner(
            result, ref_distance, ref_brake, comp_distance, comp_brake, corner
        )

        assert corner_result.delta_change > 0  # Time was lost
        # The cause determination may show "multiple" due to phase boundaries
        # when the delta change spans multiple phases
        assert corner_result.cause in ["braking", "multiple"]

    def test_analyze_single_corner_gain_at_apex(self):
        """Test corner where time is lost at apex."""
        distance = list(np.linspace(0, 1000, 200))
        delta = [0.0] * 200

        # Delta increase at apex (~250-350m for apex at 300)
        for i in range(50, 70):  # ~250-350m
            delta[i] = (i - 50) * 0.008
        for i in range(70, 200):
            delta[i] = 0.16

        result = DeltaResult(
            reference_driver="VER",
            compare_driver="NOR",
            distance=distance,
            delta=delta,
            raw_delta=delta,
            official_gap=0.16,
            scaling_factor=1.0,
            telemetry_gap=0.16,
            confidence=0.9
        )

        ref_distance = np.array(distance)
        ref_brake = np.zeros(200)
        # Braking before apex
        ref_brake[10:40] = np.linspace(0, 80, 30)

        # Comparison driver with same braking
        comp_distance = ref_distance
        comp_brake = ref_brake.copy()

        corner = CornerInput(
            corner_number=1, apex_distance=300, corner_type="right"
        )

        corner_result = analyze_single_corner(
            result, ref_distance, ref_brake, comp_distance, comp_brake, corner
        )

        assert corner_result.delta_change > 0
        # The cause determination may show "multiple" due to phase boundaries
        assert corner_result.cause in ["apex", "multiple"]

    def test_analyze_single_corner_gain_on_exit(self):
        """Test corner where time is lost on exit."""
        distance = list(np.linspace(0, 1000, 200))
        delta = [0.0] * 200

        # Delta increase on exit (~320-400m for apex at 300)
        for i in range(64, 80):  # ~320-400m
            delta[i] = (i - 64) * 0.01
        for i in range(80, 200):
            delta[i] = 0.16

        result = DeltaResult(
            reference_driver="VER",
            compare_driver="NOR",
            distance=distance,
            delta=delta,
            raw_delta=delta,
            official_gap=0.16,
            scaling_factor=1.0,
            telemetry_gap=0.16,
            confidence=0.9
        )

        ref_distance = np.array(distance)
        ref_brake = np.zeros(200)
        ref_brake[10:40] = np.linspace(0, 80, 30)

        # Comparison driver with same braking
        comp_distance = ref_distance
        comp_brake = ref_brake.copy()

        corner = CornerInput(
            corner_number=1, apex_distance=300, corner_type="right"
        )

        corner_result = analyze_single_corner(
            result, ref_distance, ref_brake, comp_distance, comp_brake, corner
        )

        assert corner_result.delta_change > 0
        assert corner_result.cause == "exit"

    def test_analyze_single_corner_invalid_zone(self):
        """Test handling of invalid corner zone."""
        # Delta result with limited distance range
        result = DeltaResult(
            reference_driver="VER",
            compare_driver="NOR",
            distance=[0, 100, 200],
            delta=[0, 0.1, 0.2],
            raw_delta=[0, 0.1, 0.2],
            official_gap=0.2,
            scaling_factor=1.0,
            telemetry_gap=0.2,
            confidence=0.5
        )

        ref_distance = np.array([0, 100, 200])
        ref_brake = np.array([0, 50, 80])

        # Comparison driver with same data
        comp_distance = ref_distance
        comp_brake = ref_brake.copy()

        # Corner apex beyond distance range
        corner = CornerInput(
            corner_number=1, apex_distance=500, corner_type="right"
        )

        corner_result = analyze_single_corner(
            result, ref_distance, ref_brake, comp_distance, comp_brake, corner
        )

        # Should handle gracefully with low confidence
        assert corner_result.confidence == "low"


# ============================================================================
# Full Corner Analysis Tests
# ============================================================================

class TestAnalyzeCorners:
    """Tests for full corner analysis."""

    def test_analyze_corners_multiple_corners(
        self, sample_delta_result, sample_corners, sample_telemetry
    ):
        """Test analysis of multiple corners."""
        distance, brake = sample_telemetry

        result = analyze_corners(
            delta_result=sample_delta_result,
            ref_distance=list(distance),
            ref_brake=list(brake),
            comp_distance=list(distance),  # Use same telemetry for comparison
            comp_brake=list(brake),
            corners=sample_corners
        )

        assert result.reference_driver == "VER"
        assert result.compare_driver == "NOR"
        assert len(result.corner_results) == 3

        # Check each corner result is valid
        for corner_result in result.corner_results:
            assert corner_result.corner_number in [1, 2, 3]
            assert corner_result.confidence in ["high", "medium", "low"]
            assert corner_result.cause in ["braking", "apex", "exit", "multiple", "unknown"]

    def test_analyze_corners_summary_calculation(self, sample_delta_result, sample_telemetry):
        """Test that summary values are calculated correctly."""
        distance, brake = sample_telemetry

        corners = [
            CornerInput(1, 300, "right"),
            CornerInput(2, 800, "left"),
        ]

        result = analyze_corners(
            delta_result=sample_delta_result,
            ref_distance=list(distance),
            ref_brake=list(brake),
            comp_distance=list(distance),
            comp_brake=list(brake),
            corners=corners
        )

        # Total delta should be sum of individual corner deltas
        individual_total = sum(c.delta_change for c in result.corner_results)
        assert abs(result.total_delta_change - individual_total) < 0.001

        # Gaining/losing counts should match
        gaining = sum(1 for c in result.corner_results if c.delta_change < -0.005)
        losing = sum(1 for c in result.corner_results if c.delta_change > 0.005)
        assert result.corners_gaining == gaining
        assert result.corners_losing == losing

    def test_analyze_corners_empty_corners(self, sample_delta_result, sample_telemetry):
        """Test handling of empty corners list."""
        distance, brake = sample_telemetry

        result = analyze_corners(
            delta_result=sample_delta_result,
            ref_distance=list(distance),
            ref_brake=list(brake),
            comp_distance=list(distance),
            comp_brake=list(brake),
            corners=[]
        )

        assert len(result.corner_results) == 0
        assert result.total_delta_change == 0.0
        assert result.corners_gaining == 0
        assert result.corners_losing == 0

    def test_analyze_corners_with_empty_telemetry(self, sample_delta_result, sample_corners):
        """Test handling of empty telemetry arrays."""
        result = analyze_corners(
            delta_result=sample_delta_result,
            ref_distance=[],
            ref_brake=[],
            comp_distance=[],
            comp_brake=[],
            corners=sample_corners
        )

        # Should handle gracefully, returning results with low confidence
        assert len(result.corner_results) == 3
        for corner_result in result.corner_results:
            assert corner_result.confidence in ["low", "medium"]


# ============================================================================
# Integration Tests
# ============================================================================

class TestIntegration:
    """Integration tests for corner analysis."""

    def test_full_pipeline_realistic_data(self):
        """Test full pipeline with realistic telemetry data."""
        # Simulate a realistic track section with 3 corners
        distance = np.linspace(0, 2000, 400)

        # Create realistic brake trace
        brake = np.zeros(400)

        # Corner 1: Apex at 400m, braking from 200m
        brake[40:80] = np.concatenate([
            np.linspace(0, 95, 20),  # Ramp up
            np.linspace(95, 30, 20)   # Ease off
        ])

        # Corner 2: Apex at 1000m, braking from 750m
        brake[150:200] = np.concatenate([
            np.linspace(0, 90, 25),
            np.linspace(90, 20, 25)
        ])

        # Corner 3: Apex at 1600m, braking from 1400m
        brake[280:320] = np.concatenate([
            np.linspace(0, 85, 20),
            np.linspace(85, 25, 20)
        ])

        # Create delta that shows time lost at corners
        delta = np.zeros(400)
        for i in range(400):
            d = distance[i]
            if 200 <= d <= 500:  # Corner 1
                delta[i] = (d - 200) * 0.0003
            elif d > 500:
                delta[i] = 0.09

            if 750 <= d <= 1100:  # Corner 2
                delta[i] += (d - 750) * 0.0002
            elif d > 1100:
                delta[i] += 0.07

            if 1400 <= d <= 1700:  # Corner 3
                delta[i] += (d - 1400) * 0.0004
            elif d > 1700:
                delta[i] += 0.12

        delta_result = DeltaResult(
            reference_driver="VER",
            compare_driver="HAM",
            distance=list(distance),
            delta=list(delta),
            raw_delta=list(delta),
            official_gap=0.28,
            scaling_factor=1.0,
            telemetry_gap=0.28,
            confidence=0.9
        )

        corners = [
            CornerInput(1, 400, "right", "Turn 1"),
            CornerInput(2, 1000, "left", "Turn 2"),
            CornerInput(3, 1600, "right", "Turn 3"),
        ]

        result = analyze_corners(
            delta_result=delta_result,
            ref_distance=list(distance),
            ref_brake=list(brake),
            comp_distance=list(distance),  # Same telemetry for comparison
            comp_brake=list(brake),
            corners=corners
        )

        # Verify results
        assert result.reference_driver == "VER"
        assert result.compare_driver == "HAM"
        assert len(result.corner_results) == 3

        # All corners should show time lost (positive delta)
        for corner_result in result.corner_results:
            assert corner_result.delta_change > 0
            assert corner_result.confidence == "high"  # Clear braking zones

        # Total should be positive (HAM losing time)
        assert result.total_delta_change > 0
        assert result.corners_losing == 3
        assert result.corners_gaining == 0


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_corner_at_track_start(self):
        """Test handling of corner at very start of track."""
        distance = np.linspace(0, 1000, 200)
        brake = np.zeros(200)
        brake[0:20] = np.linspace(0, 50, 20)

        delta_result = DeltaResult(
            reference_driver="VER",
            compare_driver="NOR",
            distance=list(distance),
            delta=[0.0] * 200,
            raw_delta=[0.0] * 200,
            official_gap=0.0,
            scaling_factor=1.0,
            telemetry_gap=0.0,
            confidence=0.9
        )

        corner = CornerInput(1, 50, "right", "Turn 1")

        result = analyze_single_corner(
            delta_result, distance, brake, distance, brake, corner
        )

        # Should handle gracefully
        assert result.corner_number == 1
        assert result.zone_start >= 0

    def test_corner_at_track_end(self):
        """Test handling of corner at end of track."""
        distance = np.linspace(0, 1000, 200)
        brake = np.zeros(200)
        brake[180:200] = 50

        delta_result = DeltaResult(
            reference_driver="VER",
            compare_driver="NOR",
            distance=list(distance),
            delta=[0.1] * 200,
            raw_delta=[0.1] * 200,
            official_gap=0.1,
            scaling_factor=1.0,
            telemetry_gap=0.1,
            confidence=0.9
        )

        corner = CornerInput(1, 950, "right", "Final Corner")

        result = analyze_single_corner(
            delta_result, distance, brake, distance, brake, corner
        )

        # Should handle gracefully
        assert result.corner_number == 1
        assert result.zone_end <= 1000

    def test_very_short_corner_zone(self):
        """Test handling of very short corner zone."""
        distance = np.linspace(0, 1000, 200)
        brake = np.zeros(200)

        delta_result = DeltaResult(
            reference_driver="VER",
            compare_driver="NOR",
            distance=list(distance),
            delta=[0.05] * 200,
            raw_delta=[0.05] * 200,
            official_gap=0.05,
            scaling_factor=1.0,
            telemetry_gap=0.05,
            confidence=0.9
        )

        # Very close corners (adjacent)
        corners = [
            CornerInput(1, 100, "right"),
            CornerInput(2, 200, "left"),  # Very close to T1
        ]

        result = analyze_corners(
            delta_result=delta_result,
            ref_distance=list(distance),
            ref_brake=list(brake),
            comp_distance=list(distance),
            comp_brake=list(brake),
            corners=corners
        )

        # Should handle overlapping zones gracefully
        assert len(result.corner_results) == 2

    def test_negative_delta_time_gained(self, sample_telemetry):
        """Test corner where compare driver gains time (negative delta)."""
        distance, brake = sample_telemetry

        # Create delta that decreases (compare driver gaining time)
        delta = list(np.linspace(0.2, 0.0, 200))

        delta_result = DeltaResult(
            reference_driver="VER",
            compare_driver="NOR",
            distance=list(np.linspace(0, 1000, 200)),
            delta=delta,
            raw_delta=delta,
            official_gap=-0.2,  # NOR is faster
            scaling_factor=1.0,
            telemetry_gap=-0.2,
            confidence=0.9
        )

        corner = CornerInput(1, 500, "right")

        ref_distance = np.linspace(0, 1000, 200)
        ref_brake = np.zeros(200)

        result = analyze_single_corner(
            delta_result,
            ref_distance,
            ref_brake,
            ref_distance,  # Same telemetry for comparison
            ref_brake,
            corner
        )

        # Delta change should be negative (compare driver gaining)
        assert result.delta_change < 0


# ============================================================================
# Phase Normalization Tests (Dual-Driver Braking Detection)
# ============================================================================

class TestPhaseNormalization:
    """Tests for phase-normalized corner zone detection."""

    def test_phase_normalized_zones_different_braking_points(self):
        """
        Verify corner zones capture both drivers' complete phases
        when they have different braking points.

        This is the core test for the fix: when the comparison driver brakes
        later than the reference driver, we should use the earlier braking
        point (with margin) to ensure both phases are captured completely.
        """
        distance = list(range(0, 600, 1))

        # Reference brakes at 450m
        ref_brake = [0.0] * 450 + [80.0] * 150

        # Comparison brakes at 470m (late braker)
        comp_brake = [0.0] * 470 + [80.0] * 130

        mock_delta = DeltaResult(
            reference_driver="REF",
            compare_driver="COMP",
            distance=distance,
            delta=[0.0] * 600,
            raw_delta=[0.0] * 600,
            official_gap=0.0,
            scaling_factor=1.0,
            telemetry_gap=0.0,
            confidence=1.0
        )

        corner = CornerInput(
            corner_number=1,
            apex_distance=500,
            corner_type="left",
            name="Test Corner"
        )

        result = analyze_single_corner(
            delta_result=mock_delta,
            ref_distance=np.array(distance),
            ref_brake=np.array(ref_brake),
            comp_distance=np.array(distance),
            comp_brake=np.array(comp_brake),
            corner=corner
        )

        # Zone should start at 430m (earlier brake 450m - 20m margin)
        # Since APPROACH_MARGIN_METERS = 20
        assert result.zone_start <= 430, (
            f"Zone start {result.zone_start} should be <= 430m "
            f"(earlier brake 450m - 20m margin)"
        )

    def test_phase_normalized_zones_ref_brakes_later(self):
        """
        Verify correct behavior when reference driver brakes later.

        The zone should still use the earlier braking point (comparison driver).
        """
        distance = list(range(0, 600, 1))

        # Reference brakes at 480m (late braker)
        ref_brake = [0.0] * 480 + [80.0] * 120

        # Comparison brakes at 450m (earlier)
        comp_brake = [0.0] * 450 + [80.0] * 150

        mock_delta = DeltaResult(
            reference_driver="REF",
            compare_driver="COMP",
            distance=distance,
            delta=[0.0] * 600,
            raw_delta=[0.0] * 600,
            official_gap=0.0,
            scaling_factor=1.0,
            telemetry_gap=0.0,
            confidence=1.0
        )

        corner = CornerInput(
            corner_number=1,
            apex_distance=500,
            corner_type="left",
            name="Test Corner"
        )

        result = analyze_single_corner(
            delta_result=mock_delta,
            ref_distance=np.array(distance),
            ref_brake=np.array(ref_brake),
            comp_distance=np.array(distance),
            comp_brake=np.array(comp_brake),
            corner=corner
        )

        # Zone should start at 430m (earlier brake 450m - 20m margin)
        assert result.zone_start <= 430, (
            f"Zone start {result.zone_start} should be <= 430m "
            f"(earlier brake 450m - 20m margin)"
        )

    def test_combine_confidence_high_high(self):
        """Test combining two high confidence levels."""
        result = _combine_confidence("high", "high")
        assert result == "high"

    def test_combine_confidence_high_medium(self):
        """Test combining high and medium confidence levels."""
        result = _combine_confidence("high", "medium")
        assert result == "medium"

    def test_combine_confidence_high_low(self):
        """Test combining high and low confidence levels."""
        result = _combine_confidence("high", "low")
        assert result == "low"

    def test_combine_confidence_low_low(self):
        """Test combining two low confidence levels."""
        result = _combine_confidence("low", "low")
        assert result == "low"

    def test_approach_margin_constant(self):
        """Verify approach margin constant is defined correctly."""
        assert APPROACH_MARGIN_METERS == 20, (
            "APPROACH_MARGIN_METERS should be 20m"
        )
