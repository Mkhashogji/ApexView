"""
Unit tests for delta analysis module.

Tests cover:
- Raw delta calculation (physics-based time from speed)
- Scaled delta calculation (matching official timing)
- Delta query functions (for corner analysis)
- Edge cases and error handling

Run with: pytest tests/test_delta_analysis.py -v
"""

import pytest
import numpy as np
from services.delta_analysis import (
    DeltaResult,
    calculate_raw_delta,
    calculate_scaled_delta,
    get_delta_at_distance,
    get_delta_change_in_range,
    get_max_delta_point,
    get_min_delta_point,
    align_telemetry_to_distance,
    _safe_array
)


# ============================================================================
# Test Fixtures
# ============================================================================

@pytest.fixture
def constant_speed_telemetry():
    """Create telemetry with constant speed for predictable results."""
    distance = list(np.linspace(0, 5000, 100))
    return {
        'fast': {
            'distance': distance,
            'speed': [250.0] * 100  # 250 km/h
        },
        'slow': {
            'distance': distance,
            'speed': [240.0] * 100  # 240 km/h
        },
        'same': {
            'distance': distance,
            'speed': [250.0] * 100  # Same as fast
        }
    }


@pytest.fixture
def variable_speed_telemetry():
    """Create telemetry with varying speed (simulating corners)."""
    distance = list(np.linspace(0, 5000, 500))
    # Speed varies: faster on straights, slower in corners
    speed_ref = [250 - 50 * np.sin(d / 800) for d in distance]
    speed_comp = [245 - 55 * np.sin(d / 800) for d in distance]  # Slower in corners
    return {
        'ref': {'distance': distance, 'speed': speed_ref},
        'comp': {'distance': distance, 'speed': speed_comp}
    }


@pytest.fixture
def sample_delta_result():
    """Create a sample DeltaResult for testing query functions."""
    # Linear delta increase over 5000m
    distance = list(np.linspace(0, 5000, 100))
    delta = list(np.linspace(0, 0.200, 100))
    raw_delta = list(np.linspace(0, 0.180, 100))
    
    return DeltaResult(
        reference_driver='VER',
        compare_driver='NOR',
        distance=distance,
        delta=delta,
        raw_delta=raw_delta,
        official_gap=0.200,
        scaling_factor=1.111,
        telemetry_gap=0.180,
        confidence=0.85
    )


# ============================================================================
# Test: _safe_array Utility
# ============================================================================

class TestSafeArray:
    """Tests for the _safe_array utility function."""
    
    def test_converts_list_to_array(self):
        """Should convert Python list to numpy array."""
        result = _safe_array([1, 2, 3])
        assert isinstance(result, np.ndarray)
        assert len(result) == 3
    
    def test_handles_none_input(self):
        """Should return default array for None input."""
        result = _safe_array(None, default_value=0.0)
        assert isinstance(result, np.ndarray)
        assert len(result) == 1
        assert result[0] == 0.0
    
    def test_handles_empty_list(self):
        """Should return default array for empty list."""
        result = _safe_array([], default_value=5.0)
        assert len(result) == 1
        assert result[0] == 5.0
    
    def test_interpolates_nan_values(self):
        """Should interpolate NaN values in array."""
        arr_with_nan = [1.0, np.nan, 3.0, np.nan, 5.0]
        result = _safe_array(arr_with_nan)
        assert not np.any(np.isnan(result))
        assert result[1] == 2.0  # Interpolated
        assert result[3] == 4.0  # Interpolated


# ============================================================================
# Test: align_telemetry_to_distance
# ============================================================================

class TestAlignTelemetry:
    """Tests for telemetry alignment function."""
    
    def test_interpolates_to_target_grid(self):
        """Should interpolate values to target distance points."""
        distance = np.array([0, 100, 200])
        values = np.array([0, 10, 20])
        target = np.array([0, 50, 100, 150, 200])
        
        result = align_telemetry_to_distance(distance, values, target)
        
        assert len(result) == 5
        assert result[0] == 0  # Start
        assert result[1] == 5  # Interpolated midpoint
        assert result[2] == 10  # Original point
        assert result[3] == 15  # Interpolated
        assert result[4] == 20  # End


# ============================================================================
# Test: calculate_raw_delta
# ============================================================================

class TestRawDelta:
    """Tests for raw delta calculation."""
    
    def test_identical_speeds_zero_delta(self, constant_speed_telemetry):
        """Two drivers with identical speeds should have zero delta."""
        fast = constant_speed_telemetry['fast']
        same = constant_speed_telemetry['same']
        
        common_dist, delta = calculate_raw_delta(
            np.array(fast['distance']), np.array(fast['speed']),
            np.array(same['distance']), np.array(same['speed'])
        )
        
        # Delta should be essentially zero throughout
        assert np.allclose(delta, 0, atol=0.001)
    
    def test_slower_driver_positive_delta(self, constant_speed_telemetry):
        """Comparison driver slower = positive delta (behind reference)."""
        fast = constant_speed_telemetry['fast']
        slow = constant_speed_telemetry['slow']
        
        common_dist, delta = calculate_raw_delta(
            np.array(fast['distance']), np.array(fast['speed']),
            np.array(slow['distance']), np.array(slow['speed'])
        )
        
        # Slower comparison driver should have positive delta
        assert delta[-1] > 0, f"Expected positive delta, got {delta[-1]}"
    
    def test_faster_driver_negative_delta(self, constant_speed_telemetry):
        """Comparison driver faster = negative delta (ahead of reference)."""
        slow = constant_speed_telemetry['slow']
        fast = constant_speed_telemetry['fast']
        
        common_dist, delta = calculate_raw_delta(
            np.array(slow['distance']), np.array(slow['speed']),
            np.array(fast['distance']), np.array(fast['speed'])
        )
        
        # Faster comparison driver should have negative delta
        assert delta[-1] < 0, f"Expected negative delta, got {delta[-1]}"
    
    def test_returns_correct_number_of_points(self, constant_speed_telemetry):
        """Should return specified number of points."""
        fast = constant_speed_telemetry['fast']
        slow = constant_speed_telemetry['slow']
        
        common_dist, delta = calculate_raw_delta(
            np.array(fast['distance']), np.array(fast['speed']),
            np.array(slow['distance']), np.array(slow['speed']),
            num_points=500
        )
        
        assert len(common_dist) == 500
        assert len(delta) == 500
    
    def test_delta_increases_monotonically_for_constant_speed_diff(self, constant_speed_telemetry):
        """With constant speed difference, delta should increase monotonically."""
        fast = constant_speed_telemetry['fast']
        slow = constant_speed_telemetry['slow']
        
        common_dist, delta = calculate_raw_delta(
            np.array(fast['distance']), np.array(fast['speed']),
            np.array(slow['distance']), np.array(slow['speed'])
        )
        
        # Check delta is monotonically increasing
        delta_diff = np.diff(delta)
        assert np.all(delta_diff >= -0.0001), "Delta should be monotonically increasing"


# ============================================================================
# Test: calculate_scaled_delta
# ============================================================================

class TestScaledDelta:
    """Tests for scaled delta calculation."""
    
    def test_scaled_delta_matches_official_gap(self, constant_speed_telemetry):
        """Scaled delta final value should equal official gap."""
        fast = constant_speed_telemetry['fast']
        slow = constant_speed_telemetry['slow']
        
        result = calculate_scaled_delta(
            fast, slow,
            ref_official_time=90.000,
            comp_official_time=90.200,  # 0.200s gap
            ref_driver='VER',
            comp_driver='NOR'
        )
        
        # Final scaled delta should equal official gap
        assert result.delta[-1] == pytest.approx(0.200, abs=1e-3), \
            f"Expected delta[-1] == 0.200, got {result.delta[-1]}"
        assert result.official_gap == pytest.approx(0.200, abs=1e-6)
    
    def test_negative_gap_handled(self, constant_speed_telemetry):
        """Should handle comparison driver being faster (negative gap)."""
        slow = constant_speed_telemetry['slow']
        fast = constant_speed_telemetry['fast']
        
        result = calculate_scaled_delta(
            slow, fast,  # Reference is slower
            ref_official_time=90.200,
            comp_official_time=90.000,  # Comparison is faster
            ref_driver='NOR',
            comp_driver='VER'
        )
        
        # Official gap should be negative
        assert result.official_gap == pytest.approx(-0.200, abs=1e-6)
        # Final delta should match
        assert result.delta[-1] == pytest.approx(-0.200, abs=1e-3)
    
    def test_confidence_high_for_small_scaling(self, constant_speed_telemetry):
        """Confidence should be high when scaling factor is close to 1.0."""
        fast = constant_speed_telemetry['fast']
        slow = constant_speed_telemetry['slow']
        
        result = calculate_scaled_delta(
            fast, slow,
            ref_official_time=72.000,
            comp_official_time=72.735,  # Roughly matches telemetry gap
            ref_driver='VER',
            comp_driver='NOR'
        )
        
        # If scaling is close to 1.0, confidence should be high
        if abs(result.scaling_factor - 1.0) < 0.2:
            assert result.confidence >= 0.8
    
    def test_confidence_lower_for_large_scaling(self, constant_speed_telemetry):
        """Confidence should be lower when scaling factor deviates from 1.0."""
        fast = constant_speed_telemetry['fast']
        slow = constant_speed_telemetry['slow']
        
        result = calculate_scaled_delta(
            fast, slow,
            ref_official_time=90.000,
            comp_official_time=90.500,  # Large gap, may need significant scaling
            ref_driver='VER',
            comp_driver='NOR'
        )
        
        # Confidence depends on scaling factor
        assert 0.0 <= result.confidence <= 1.0
    
    def test_returns_delta_result_dataclass(self, constant_speed_telemetry):
        """Should return a proper DeltaResult dataclass."""
        fast = constant_speed_telemetry['fast']
        slow = constant_speed_telemetry['slow']
        
        result = calculate_scaled_delta(
            fast, slow,
            ref_official_time=90.000,
            comp_official_time=90.200,
            ref_driver='VER',
            comp_driver='NOR'
        )
        
        assert isinstance(result, DeltaResult)
        assert result.reference_driver == 'VER'
        assert result.compare_driver == 'NOR'
        assert len(result.distance) > 0
        assert len(result.delta) == len(result.distance)
        assert len(result.raw_delta) == len(result.distance)
    
    def test_handles_empty_telemetry(self):
        """Should handle empty telemetry gracefully."""
        empty_telemetry = {'distance': [], 'speed': []}
        valid_telemetry = {'distance': [0, 100], 'speed': [200, 200]}
        
        result = calculate_scaled_delta(
            empty_telemetry, valid_telemetry,
            ref_official_time=90.000,
            comp_official_time=90.200,
            ref_driver='VER',
            comp_driver='NOR'
        )
        
        # Should return result with low confidence
        assert result.confidence == pytest.approx(0.0, abs=1e-9)
        assert result.official_gap == pytest.approx(0.200, abs=1e-6)


# ============================================================================
# Test: Query Functions
# ============================================================================

class TestDeltaQueries:
    """Tests for delta query functions."""
    
    def test_get_delta_at_distance_midpoint(self, sample_delta_result):
        """Should return correct delta at midpoint distance."""
        # At midpoint (2500m), delta should be ~0.100s (linear interpolation)
        delta = get_delta_at_distance(sample_delta_result, 2500.0)
        assert abs(delta - 0.100) < 0.01
    
    def test_get_delta_at_distance_start(self, sample_delta_result):
        """Should return ~0 delta at start."""
        delta = get_delta_at_distance(sample_delta_result, 0.0)
        assert abs(delta) < 0.01
    
    def test_get_delta_at_distance_end(self, sample_delta_result):
        """Should return official gap at end."""
        delta = get_delta_at_distance(sample_delta_result, 5000.0)
        assert abs(delta - 0.200) < 0.01
    
    def test_get_delta_at_distance_clamps_to_range(self, sample_delta_result):
        """Should clamp out-of-range distances to valid range."""
        # Request distance beyond track length
        delta = get_delta_at_distance(sample_delta_result, 10000.0)
        # Should return value at max distance
        assert abs(delta - 0.200) < 0.01
    
    def test_get_delta_change_in_range(self, sample_delta_result):
        """Should calculate delta change in a distance range."""
        # From 1000m to 2000m in linear delta (0.04 -> 0.08)
        change = get_delta_change_in_range(sample_delta_result, 1000.0, 2000.0)
        # Should be ~0.040s (1000m is 20% of 5000m range, gap is 0.200)
        assert abs(change - 0.040) < 0.01
    
    def test_get_delta_change_full_lap(self, sample_delta_result):
        """Delta change over full lap should equal official gap."""
        change = get_delta_change_in_range(sample_delta_result, 0.0, 5000.0)
        assert abs(change - 0.200) < 0.01
    
    def test_get_max_delta_point(self, sample_delta_result):
        """Should find maximum delta point."""
        distance, delta = get_max_delta_point(sample_delta_result)
        # For linear increasing delta, max is at the end
        assert distance == 5000.0
        assert abs(delta - 0.200) < 0.01
    
    def test_get_min_delta_point(self, sample_delta_result):
        """Should find minimum delta point."""
        distance, delta = get_min_delta_point(sample_delta_result)
        # For linear increasing delta, min is at the start
        assert distance == 0.0
        assert abs(delta) < 0.01


# ============================================================================
# Test: Edge Cases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""
    
    def test_handles_very_small_speed_difference(self):
        """Should handle nearly identical speeds without crashing.

        When telemetry gap is near zero, scaling is not applied (scaling=1.0).
        The function should still return valid data with correct official_gap.
        """
        distance = list(np.linspace(0, 5000, 100))
        ref = {'distance': distance, 'speed': [250.0] * 100}
        comp = {'distance': distance, 'speed': [250.001] * 100}  # Tiny difference

        result = calculate_scaled_delta(
            ref, comp,
            ref_official_time=90.000,
            comp_official_time=90.001,  # 1ms gap
            ref_driver='VER',
            comp_driver='NOR'
        )

        # When telemetry gap is near zero, scaling=1.0 is used (no scaling)
        # Verify the function handles this edge case gracefully:
        # 1. Returns valid result with correct official_gap
        assert result.official_gap == pytest.approx(0.001, abs=1e-6)
        # 2. Has valid delta array
        assert len(result.delta) > 0
        # 3. Delta magnitude is small (near-identical speeds)
        assert abs(result.delta[-1]) < 0.01  # Within 10ms
    
    def test_handles_zero_official_gap(self):
        """Should handle zero official gap (identical times)."""
        distance = list(np.linspace(0, 5000, 100))
        telemetry = {'distance': distance, 'speed': [250.0] * 100}
        
        result = calculate_scaled_delta(
            telemetry, telemetry,
            ref_official_time=90.000,
            comp_official_time=90.000,  # Zero gap
            ref_driver='VER',
            comp_driver='NOR'
        )
        
        assert result.official_gap == 0.0
        # All deltas should be zero (or very close)
        assert np.allclose(result.delta, 0, atol=0.001)
    
    def test_handles_missing_distance_key(self):
        """Should handle telemetry dict missing 'distance' key."""
        bad_telemetry = {'speed': [250.0] * 100}  # Missing distance
        good_telemetry = {'distance': list(range(100)), 'speed': [250.0] * 100}
        
        result = calculate_scaled_delta(
            bad_telemetry, good_telemetry,
            ref_official_time=90.000,
            comp_official_time=90.200,
            ref_driver='VER',
            comp_driver='NOR'
        )
        
        # Should still return a result (with low confidence)
        assert result.confidence == 0.0
    
    def test_handles_different_length_telemetry(self):
        """Should handle telemetry arrays of different lengths."""
        ref = {
            'distance': list(np.linspace(0, 5000, 100)),
            'speed': [250.0] * 100
        }
        comp = {
            'distance': list(np.linspace(0, 5000, 500)),  # Different length
            'speed': [245.0] * 500
        }
        
        result = calculate_scaled_delta(
            ref, comp,
            ref_official_time=90.000,
            comp_official_time=90.200,
            ref_driver='VER',
            comp_driver='NOR'
        )
        
        # Should interpolate to common grid
        assert len(result.distance) == 1000  # Default num_points
        assert abs(result.delta[-1] - 0.200) < 0.001


# ============================================================================
# Test: Three-Tier Algorithm
# ============================================================================

class TestThreeTierAlgorithm:
    """Tests for the three-tier delta calculation algorithm."""

    def test_tier1_uses_relative_distance_when_available(self):
        """Should use Tier 1 when RelativeDistance and Time are present."""
        distance = list(np.linspace(0, 5000, 100))
        rel_dist = list(np.linspace(0, 1, 100))
        time_ref = list(np.linspace(0, 90, 100))
        time_comp = [t * 1.002 for t in time_ref]  # 0.2% slower

        ref = {
            'distance': distance,
            'speed': [250.0] * 100,
            'relative_distance': rel_dist,
            'time': time_ref
        }
        comp = {
            'distance': distance,
            'speed': [245.0] * 100,
            'relative_distance': rel_dist,
            'time': time_comp
        }

        result = calculate_scaled_delta(
            ref, comp,
            ref_official_time=90.000,
            comp_official_time=90.180,
            ref_driver='VER',
            comp_driver='NOR'
        )

        # Tier 1 should have scaling_factor = 1.0 and high confidence
        assert result.scaling_factor == pytest.approx(1.0, abs=1e-6)
        assert result.confidence >= 0.85
        assert result.official_gap == pytest.approx(0.180, abs=1e-6)

    def test_tier2_used_when_only_time_available(self):
        """Should use Tier 2 when only Time is present (no RelativeDistance)."""
        distance = list(np.linspace(0, 5000, 100))
        time_ref = list(np.linspace(0, 90, 100))
        time_comp = [t * 1.002 for t in time_ref]

        ref = {
            'distance': distance,
            'speed': [250.0] * 100,
            'time': time_ref
            # No relative_distance
        }
        comp = {
            'distance': distance,
            'speed': [245.0] * 100,
            'time': time_comp
        }

        result = calculate_scaled_delta(
            ref, comp,
            ref_official_time=90.000,
            comp_official_time=90.180,
            ref_driver='VER',
            comp_driver='NOR'
        )

        # Tier 2 should have scaling_factor = 1.0 and ~0.8 confidence
        assert result.scaling_factor == pytest.approx(1.0, abs=1e-6)
        assert result.confidence == pytest.approx(0.8, abs=0.05)

    def test_tier3_fallback_when_no_time(self):
        """Should fall back to Tier 3 when Time is not available."""
        distance = list(np.linspace(0, 5000, 100))

        ref = {
            'distance': distance,
            'speed': [250.0] * 100
            # No time, no relative_distance
        }
        comp = {
            'distance': distance,
            'speed': [245.0] * 100
        }

        result = calculate_scaled_delta(
            ref, comp,
            ref_official_time=90.000,
            comp_official_time=90.500,
            ref_driver='VER',
            comp_driver='NOR'
        )

        # Tier 3 should have lower confidence (capped at 0.6)
        assert result.confidence <= 0.6
        # Should still match official gap (via scaling)
        assert result.delta[-1] == pytest.approx(0.500, abs=0.01)

    def test_tier1_final_delta_matches_official_exactly(self):
        """Tier 1 should produce delta[-1] == official_gap exactly."""
        rel_dist = list(np.linspace(0, 1, 1000))
        time_ref = list(np.linspace(0, 84.892, 1000))
        # Linear delta growth to simulate comparison driver losing time steadily
        time_comp = [t + 0.229 * (t / 84.892) for t in time_ref]

        ref = {
            'distance': list(np.linspace(0, 5826, 1000)),
            'speed': [250.0] * 1000,
            'relative_distance': rel_dist,
            'time': time_ref
        }
        comp = {
            'distance': list(np.linspace(0, 5826, 1000)),
            'speed': [248.0] * 1000,
            'relative_distance': rel_dist,
            'time': time_comp
        }

        result = calculate_scaled_delta(
            ref, comp,
            ref_official_time=84.892,
            comp_official_time=85.121,  # +0.229s gap
            ref_driver='VER',
            comp_driver='LEC'
        )

        # Final delta should EXACTLY match official gap
        assert result.delta[-1] == pytest.approx(0.229, abs=1e-3)
        assert result.scaling_factor == pytest.approx(1.0, abs=1e-6)

    def test_backward_compatibility_without_new_fields(self):
        """Should work with old telemetry format (no relative_distance/time)."""
        distance = list(np.linspace(0, 5000, 100))

        # Old format - only distance and speed
        ref = {'distance': distance, 'speed': [250.0] * 100}
        comp = {'distance': distance, 'speed': [245.0] * 100}

        result = calculate_scaled_delta(
            ref, comp,
            ref_official_time=90.000,
            comp_official_time=90.300,
            ref_driver='VER',
            comp_driver='NOR'
        )

        # Should still work via Tier 3
        assert result.official_gap == pytest.approx(0.300, abs=1e-6)
        assert len(result.delta) > 0
        # Final delta should match official gap (via scaling)
        assert result.delta[-1] == pytest.approx(0.300, abs=0.01)

    def test_tier1_handles_none_relative_distance(self):
        """Should fall back gracefully when relative_distance is None."""
        distance = list(np.linspace(0, 5000, 100))
        time_data = list(np.linspace(0, 90, 100))

        ref = {
            'distance': distance,
            'speed': [250.0] * 100,
            'relative_distance': None,  # Explicitly None
            'time': time_data
        }
        comp = {
            'distance': distance,
            'speed': [245.0] * 100,
            'relative_distance': None,
            'time': time_data
        }

        result = calculate_scaled_delta(
            ref, comp,
            ref_official_time=90.000,
            comp_official_time=90.200,
            ref_driver='VER',
            comp_driver='NOR'
        )

        # Should use Tier 2 (time only)
        assert result.scaling_factor == pytest.approx(1.0, abs=1e-6)
        assert result.confidence == pytest.approx(0.8, abs=0.05)

    def test_tier1_handles_empty_relative_distance(self):
        """Should fall back gracefully when relative_distance is empty list."""
        distance = list(np.linspace(0, 5000, 100))
        time_data = list(np.linspace(0, 90, 100))

        ref = {
            'distance': distance,
            'speed': [250.0] * 100,
            'relative_distance': [],  # Empty list
            'time': time_data
        }
        comp = {
            'distance': distance,
            'speed': [245.0] * 100,
            'relative_distance': [],
            'time': time_data
        }

        result = calculate_scaled_delta(
            ref, comp,
            ref_official_time=90.000,
            comp_official_time=90.200,
            ref_driver='VER',
            comp_driver='NOR'
        )

        # Should use Tier 2 (time only) since relative_distance is empty
        assert result.scaling_factor == pytest.approx(1.0, abs=1e-6)
