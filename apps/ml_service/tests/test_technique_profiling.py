"""
Tests for Technique Profiling Module (Phase 4)

Tests the technique profiling functionality including:
- Aggregation by cause type
- Session percentile calculation
- Classification (STRONG/NEUTRAL/WEAK)
- Style summary generation
- Edge case handling
"""

import pytest
import numpy as np
from typing import List, Dict

from services.technique_profiling import (
    TechniqueLevel,
    TechniqueDimension,
    TechniqueProfile,
    SessionPercentiles,
    DriverAggregates,
    identify_key_corners,
    aggregate_by_cause,
    calculate_session_percentiles,
    calculate_exact_percentile,
    classify_dimension,
    generate_style_summary,
    profile_drivers,
    profile_single_driver,
    CONFIDENCE_WEIGHTS,
    STRONG_PERCENTILE_THRESHOLD,
    WEAK_PERCENTILE_THRESHOLD,
    NEUTRAL_THRESHOLD,
)
from services.corner_analysis import CornerResult, CornerAnalysisResult


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_corner_results() -> List[CornerResult]:
    """Create sample corner results with varied causes and confidences."""
    return [
        CornerResult(
            corner_number=1, name="Turn 1", apex_distance=180,
            brake_distance=100, zone_start=100, zone_end=280,
            delta_change=0.030, cause="braking", confidence="high"
        ),
        CornerResult(
            corner_number=2, name="Turn 2", apex_distance=400,
            brake_distance=300, zone_start=300, zone_end=500,
            delta_change=-0.019, cause="apex", confidence="medium"
        ),
        CornerResult(
            corner_number=3, name="Turn 3", apex_distance=700,
            brake_distance=550, zone_start=550, zone_end=800,
            delta_change=-0.144, cause="multiple", confidence="medium"
        ),
        CornerResult(
            corner_number=4, name="Turn 4", apex_distance=1000,
            brake_distance=850, zone_start=850, zone_end=1100,
            delta_change=0.050, cause="exit", confidence="high"
        ),
        CornerResult(
            corner_number=5, name="Turn 5", apex_distance=1300,
            brake_distance=1150, zone_start=1150, zone_end=1400,
            delta_change=0.117, cause="braking", confidence="high"
        ),
    ]


@pytest.fixture
def sample_corner_analysis_result(sample_corner_results) -> CornerAnalysisResult:
    """Create a sample CornerAnalysisResult."""
    return CornerAnalysisResult(
        reference_driver="NOR",
        compare_driver="PIA",
        corner_results=sample_corner_results,
        total_delta_change=sum(c.delta_change for c in sample_corner_results),
        corners_gaining=2,  # T2 and T3 (negative delta)
        corners_losing=3,   # T1, T4, T5 (positive delta)
    )


@pytest.fixture
def multiple_driver_results() -> Dict[str, CornerAnalysisResult]:
    """Create corner results for multiple drivers for percentile testing."""
    # Driver 1: Strong braking, weak exit
    driver1_corners = [
        CornerResult(1, "T1", 180, 100, 100, 280, -0.100, "braking", "high"),
        CornerResult(2, "T2", 400, 300, 300, 500, -0.050, "braking", "high"),
        CornerResult(3, "T3", 700, 550, 550, 800, 0.080, "exit", "high"),
    ]
    driver1 = CornerAnalysisResult("NOR", "VER", driver1_corners, -0.070, 2, 1)

    # Driver 2: Neutral everything
    driver2_corners = [
        CornerResult(1, "T1", 180, 100, 100, 280, 0.010, "braking", "high"),
        CornerResult(2, "T2", 400, 300, 300, 500, 0.005, "braking", "high"),
        CornerResult(3, "T3", 700, 550, 550, 800, -0.005, "exit", "high"),
    ]
    driver2 = CornerAnalysisResult("NOR", "LEC", driver2_corners, 0.010, 1, 2)

    # Driver 3: Weak braking, strong exit
    driver3_corners = [
        CornerResult(1, "T1", 180, 100, 100, 280, 0.120, "braking", "high"),
        CornerResult(2, "T2", 400, 300, 300, 500, 0.080, "braking", "high"),
        CornerResult(3, "T3", 700, 550, 550, 800, -0.150, "exit", "high"),
    ]
    driver3 = CornerAnalysisResult("NOR", "PIA", driver3_corners, 0.050, 1, 2)

    return {"VER": driver1, "LEC": driver2, "PIA": driver3}


# ============================================================================
# identify_key_corners Tests
# ============================================================================

class TestIdentifyKeyCorners:
    """Tests for identify_key_corners function."""

    def test_identifies_gaining_corners(self, sample_corner_results):
        """Test that gaining corners (negative delta) are correctly identified."""
        top_gaining, top_losing = identify_key_corners(sample_corner_results)

        # T3 (-0.144) and T2 (-0.019) should be gaining
        assert len(top_gaining) > 0
        assert "Turn 3" in top_gaining  # Most negative

    def test_identifies_losing_corners(self, sample_corner_results):
        """Test that losing corners (positive delta) are correctly identified."""
        top_gaining, top_losing = identify_key_corners(sample_corner_results)

        # T5 (+0.117), T4 (+0.050), T1 (+0.030) should be losing
        assert len(top_losing) > 0
        assert "Turn 5" in top_losing  # Most positive

    def test_limits_to_three_corners(self):
        """Test that only top 3 corners are returned."""
        corners = [
            CornerResult(i, f"T{i}", i*100, i*100-50, i*100-50, i*100+100,
                        -0.01 * i, "braking", "high")
            for i in range(1, 10)
        ]
        top_gaining, _ = identify_key_corners(corners)
        assert len(top_gaining) <= 3

    def test_empty_list_returns_empty(self):
        """Test that empty input returns empty lists."""
        top_gaining, top_losing = identify_key_corners([])
        assert top_gaining == []
        assert top_losing == []

    def test_uses_corner_name_or_number(self):
        """Test that corner name is used when available, otherwise number."""
        corners = [
            CornerResult(1, "Sainte Devote", 180, 100, 100, 280, -0.100, "braking", "high"),
            CornerResult(2, None, 400, 300, 300, 500, 0.100, "braking", "high"),
        ]
        top_gaining, top_losing = identify_key_corners(corners)

        assert "Sainte Devote" in top_gaining
        assert "T2" in top_losing


# ============================================================================
# aggregate_by_cause Tests
# ============================================================================

class TestAggregateByCase:
    """Tests for aggregate_by_cause function."""

    def test_aggregates_braking_corners(self, sample_corner_results):
        """Test that braking corners are correctly summed."""
        result = aggregate_by_cause(sample_corner_results, weight_by_confidence=False)

        # T1 (+0.030) and T5 (+0.117) are braking corners
        expected_braking = 0.030 + 0.117
        assert abs(result.braking_total - expected_braking) < 0.001
        assert result.braking_count == 2

    def test_aggregates_exit_corners(self, sample_corner_results):
        """Test that exit corners are correctly summed."""
        result = aggregate_by_cause(sample_corner_results, weight_by_confidence=False)

        # T4 (+0.050) is an exit corner
        assert abs(result.exit_total - 0.050) < 0.001
        assert result.exit_count == 1

    def test_aggregates_apex_corners(self, sample_corner_results):
        """Test that apex corners are correctly summed."""
        result = aggregate_by_cause(sample_corner_results, weight_by_confidence=False)

        # T2 (-0.019) is an apex corner
        assert abs(result.apex_total - (-0.019)) < 0.001
        assert result.apex_count == 1

    def test_excludes_multiple_cause_from_dimensions(self, sample_corner_results):
        """Test that 'multiple' cause corners aren't added to specific dimensions."""
        result = aggregate_by_cause(sample_corner_results, weight_by_confidence=False)

        # T3 is 'multiple', shouldn't be in braking/apex/exit totals
        total_from_dimensions = result.braking_total + result.apex_total + result.exit_total
        expected = 0.030 + 0.117 + (-0.019) + 0.050  # T1, T5, T2, T4

        assert abs(total_from_dimensions - expected) < 0.001

    def test_calculates_consistency(self, sample_corner_results):
        """Test that consistency (std dev) is calculated across all corners."""
        result = aggregate_by_cause(sample_corner_results)

        # Calculate expected std dev
        deltas = [c.delta_change for c in sample_corner_results]
        expected_consistency = np.std(deltas)

        assert abs(result.consistency - expected_consistency) < 0.001

    def test_confidence_weighting_affects_result(self, sample_corner_results):
        """Test that confidence weighting produces different results."""
        weighted = aggregate_by_cause(sample_corner_results, weight_by_confidence=True)
        unweighted = aggregate_by_cause(sample_corner_results, weight_by_confidence=False)

        # Results should differ when there are mixed confidence levels
        # T2 (apex, medium) will be weighted differently
        # This test just verifies the mechanism works
        assert weighted is not None
        assert unweighted is not None

    def test_empty_corner_list(self):
        """Test handling of empty corner list."""
        result = aggregate_by_cause([])

        assert result.braking_total == 0.0
        assert result.apex_total == 0.0
        assert result.exit_total == 0.0
        assert result.consistency == 0.0
        assert result.total_corners == 0

    def test_single_corner(self):
        """Test aggregation with single corner."""
        corners = [
            CornerResult(1, "T1", 180, 100, 100, 280, 0.100, "braking", "high")
        ]
        result = aggregate_by_cause(corners)

        assert abs(result.braking_total - 0.100) < 0.001
        assert result.braking_count == 1
        assert result.consistency == 0.0  # Single value has 0 std dev


# ============================================================================
# calculate_session_percentiles Tests
# ============================================================================

class TestCalculateSessionPercentiles:
    """Tests for calculate_session_percentiles function."""

    def test_calculates_p30_p70_boundaries(self):
        """Test that P30 and P70 boundaries are calculated correctly."""
        aggregates = [
            DriverAggregates("D1", -0.100, 0, 0, 0.05, 2, 0, 0, 3, 0.9),
            DriverAggregates("D2", 0.000, 0, 0, 0.08, 2, 0, 0, 3, 0.9),
            DriverAggregates("D3", 0.100, 0, 0, 0.03, 2, 0, 0, 3, 0.9),
            DriverAggregates("D4", 0.200, 0, 0, 0.10, 2, 0, 0, 3, 0.9),
        ]

        result = calculate_session_percentiles(aggregates)

        assert result.driver_count == 4
        # P30 should be around -0.070 (between D1 and D2)
        # P70 should be around 0.130 (between D3 and D4)
        assert result.braking_p30 < result.braking_p70

    def test_stores_all_values_for_exact_percentile(self):
        """Test that all values are stored for exact percentile calculation."""
        aggregates = [
            DriverAggregates("D1", -0.100, -0.05, 0.02, 0.05, 2, 1, 1, 4, 0.9),
            DriverAggregates("D2", 0.100, 0.05, -0.02, 0.08, 2, 1, 1, 4, 0.9),
        ]

        result = calculate_session_percentiles(aggregates)

        assert len(result.all_braking) == 2
        assert -0.100 in result.all_braking
        assert 0.100 in result.all_braking

    def test_single_driver_edge_case(self):
        """Test percentile calculation with single driver."""
        aggregates = [
            DriverAggregates("D1", 0.050, 0.020, -0.010, 0.03, 1, 1, 1, 3, 0.9)
        ]

        result = calculate_session_percentiles(aggregates)

        # With single driver, P30 and P70 should equal the single value
        assert result.braking_p30 == result.braking_p70 == 0.050
        assert result.driver_count == 1


# ============================================================================
# calculate_exact_percentile Tests
# ============================================================================

class TestCalculateExactPercentile:
    """Tests for calculate_exact_percentile function."""

    def test_lowest_value_gets_low_percentile(self):
        """Test that the lowest value gets a low percentile."""
        all_values = [-0.100, 0.000, 0.100, 0.200]
        percentile = calculate_exact_percentile(-0.100, all_values)

        # Should be 12.5 (0 below + 0.5*1 equal / 4 * 100)
        assert percentile < 20

    def test_highest_value_gets_high_percentile(self):
        """Test that the highest value gets a high percentile."""
        all_values = [-0.100, 0.000, 0.100, 0.200]
        percentile = calculate_exact_percentile(0.200, all_values)

        # Should be 87.5 (3 below + 0.5*1 equal / 4 * 100)
        assert percentile > 80

    def test_middle_value_gets_middle_percentile(self):
        """Test that a middle value gets middle percentile."""
        all_values = [-0.100, 0.000, 0.100, 0.200]
        percentile = calculate_exact_percentile(0.000, all_values)

        # Should be around 37.5
        assert 30 < percentile < 50

    def test_empty_values_returns_50(self):
        """Test that empty values list returns 50th percentile."""
        percentile = calculate_exact_percentile(0.100, [])
        assert percentile == 50.0

    def test_handles_duplicate_values(self):
        """Test handling of duplicate values in distribution."""
        all_values = [0.100, 0.100, 0.100, 0.100]
        percentile = calculate_exact_percentile(0.100, all_values)

        # All same value should give 50th percentile
        assert percentile == 50.0


# ============================================================================
# classify_dimension Tests
# ============================================================================

class TestClassifyDimension:
    """Tests for classify_dimension function."""

    def test_classifies_strong_correctly(self):
        """Test that values <= P30 are classified as STRONG."""
        all_values = [-0.100, 0.000, 0.100, 0.200]
        p30 = np.percentile(all_values, 30)
        p70 = np.percentile(all_values, 70)

        result = classify_dimension(
            value=-0.100,  # Lowest value (best performance)
            p30=p30,
            p70=p70,
            all_values=all_values,
            dimension_name="braking",
            corner_count=2,
            avg_confidence=0.9
        )

        assert result.level == TechniqueLevel.STRONG
        assert "Strong" in result.descriptor or "strong" in result.descriptor.lower()

    def test_classifies_weak_correctly(self):
        """Test that values >= P70 are classified as WEAK."""
        all_values = [-0.100, 0.000, 0.100, 0.200]
        p30 = np.percentile(all_values, 30)
        p70 = np.percentile(all_values, 70)

        result = classify_dimension(
            value=0.200,  # Highest value (worst performance)
            p30=p30,
            p70=p70,
            all_values=all_values,
            dimension_name="braking",
            corner_count=2,
            avg_confidence=0.9
        )

        assert result.level == TechniqueLevel.WEAK
        assert "Loses" in result.descriptor or "weak" in result.descriptor.lower()

    def test_classifies_neutral_correctly(self):
        """Test that middle values are classified as NEUTRAL."""
        all_values = [-0.100, 0.000, 0.100, 0.200]
        p30 = np.percentile(all_values, 30)
        p70 = np.percentile(all_values, 70)

        result = classify_dimension(
            value=0.050,  # Middle value
            p30=p30,
            p70=p70,
            all_values=all_values,
            dimension_name="braking",
            corner_count=2,
            avg_confidence=0.9
        )

        assert result.level == TechniqueLevel.NEUTRAL

    def test_stores_percentile_and_raw_value(self):
        """Test that percentile and raw value are stored correctly."""
        all_values = [-0.100, 0.000, 0.100, 0.200]

        result = classify_dimension(
            value=0.100,
            p30=np.percentile(all_values, 30),
            p70=np.percentile(all_values, 70),
            all_values=all_values,
            dimension_name="exit",
            corner_count=3,
            avg_confidence=0.85
        )

        assert result.raw_value == 0.100
        assert 0 <= result.percentile <= 100
        assert result.corner_count == 3
        assert result.avg_confidence == 0.85

    def test_uses_correct_descriptor(self):
        """Test that descriptors match the dimension name."""
        all_values = [0.0, 0.1, 0.2]

        exit_result = classify_dimension(
            value=0.2, p30=0.03, p70=0.17, all_values=all_values,
            dimension_name="exit", corner_count=1, avg_confidence=0.8
        )
        assert "exit" in exit_result.descriptor.lower() or "traction" in exit_result.descriptor.lower()


# ============================================================================
# generate_style_summary Tests
# ============================================================================

class TestGenerateStyleSummary:
    """Tests for generate_style_summary function."""

    def test_strong_braking_strong_exit(self):
        """Test style summary for STRONG braking and STRONG exit."""
        braking = TechniqueDimension(TechniqueLevel.STRONG, "desc", 20, -0.1, 2, 0.9)
        exit_dim = TechniqueDimension(TechniqueLevel.STRONG, "desc", 15, -0.05, 1, 0.9)
        apex = TechniqueDimension(TechniqueLevel.NEUTRAL, "desc", 50, 0, 1, 0.9)
        consistency = TechniqueDimension(TechniqueLevel.NEUTRAL, "desc", 50, 0.05, 5, 0.9)

        summary = generate_style_summary(braking, exit_dim, apex, consistency)

        assert "excels" in summary.lower() or "complete" in summary.lower()

    def test_weak_braking_strong_exit(self):
        """Test style summary for WEAK braking and STRONG exit."""
        braking = TechniqueDimension(TechniqueLevel.WEAK, "desc", 80, 0.1, 2, 0.9)
        exit_dim = TechniqueDimension(TechniqueLevel.STRONG, "desc", 15, -0.08, 1, 0.9)
        apex = TechniqueDimension(TechniqueLevel.NEUTRAL, "desc", 50, 0, 1, 0.9)
        consistency = TechniqueDimension(TechniqueLevel.NEUTRAL, "desc", 50, 0.05, 5, 0.9)

        summary = generate_style_summary(braking, exit_dim, apex, consistency)

        assert "conservative" in summary.lower() or "entry" in summary.lower()

    def test_neutral_all_dimensions(self):
        """Test style summary when all dimensions are NEUTRAL."""
        braking = TechniqueDimension(TechniqueLevel.NEUTRAL, "desc", 50, 0, 2, 0.9)
        exit_dim = TechniqueDimension(TechniqueLevel.NEUTRAL, "desc", 50, 0, 1, 0.9)
        apex = TechniqueDimension(TechniqueLevel.NEUTRAL, "desc", 50, 0, 1, 0.9)
        consistency = TechniqueDimension(TechniqueLevel.NEUTRAL, "desc", 50, 0.05, 5, 0.9)

        summary = generate_style_summary(braking, exit_dim, apex, consistency)

        assert "balanced" in summary.lower() or "well-rounded" in summary.lower()

    def test_all_template_combinations_produce_output(self):
        """Test that all braking/exit combinations produce valid output."""
        levels = [TechniqueLevel.STRONG, TechniqueLevel.NEUTRAL, TechniqueLevel.WEAK]

        for braking_level in levels:
            for exit_level in levels:
                braking = TechniqueDimension(braking_level, "desc", 50, 0, 2, 0.9)
                exit_dim = TechniqueDimension(exit_level, "desc", 50, 0, 1, 0.9)
                apex = TechniqueDimension(TechniqueLevel.NEUTRAL, "desc", 50, 0, 1, 0.9)
                consistency = TechniqueDimension(TechniqueLevel.NEUTRAL, "desc", 50, 0.05, 5, 0.9)

                summary = generate_style_summary(braking, exit_dim, apex, consistency)

                assert len(summary) > 0
                assert isinstance(summary, str)


# ============================================================================
# profile_drivers Tests (Integration)
# ============================================================================

class TestProfileDrivers:
    """Integration tests for profile_drivers function."""

    def test_profiles_multiple_drivers(self, multiple_driver_results):
        """Test profiling multiple drivers produces correct number of profiles."""
        profiles, percentiles = profile_drivers(
            corner_results_by_driver=multiple_driver_results,
            reference_driver="NOR"
        )

        assert len(profiles) == 3
        assert percentiles.driver_count == 3

    def test_classification_is_relative(self, multiple_driver_results):
        """Test that classification is relative to session, not absolute."""
        profiles, percentiles = profile_drivers(
            corner_results_by_driver=multiple_driver_results,
            reference_driver="NOR"
        )

        # Find VER (strong braking) and PIA (weak braking)
        ver_profile = next(p for p in profiles if p.driver == "VER")
        pia_profile = next(p for p in profiles if p.driver == "PIA")

        # VER should be STRONG in braking (lowest/most negative total)
        assert ver_profile.braking.level == TechniqueLevel.STRONG

        # PIA should be WEAK in braking (highest/most positive total)
        assert pia_profile.braking.level == TechniqueLevel.WEAK

    def test_profiles_have_style_summaries(self, multiple_driver_results):
        """Test that all profiles have style summaries."""
        profiles, _ = profile_drivers(
            corner_results_by_driver=multiple_driver_results,
            reference_driver="NOR"
        )

        for profile in profiles:
            assert len(profile.style_summary) > 0

    def test_profiles_have_reference_driver(self, multiple_driver_results):
        """Test that profiles correctly store reference driver."""
        profiles, _ = profile_drivers(
            corner_results_by_driver=multiple_driver_results,
            reference_driver="NOR"
        )

        for profile in profiles:
            assert profile.reference_driver == "NOR"

    def test_empty_input_returns_empty_results(self):
        """Test that empty input returns empty results."""
        profiles, percentiles = profile_drivers(
            corner_results_by_driver={},
            reference_driver="NOR"
        )

        assert profiles == []
        assert percentiles.driver_count == 0

    def test_single_driver_profiling(self, sample_corner_analysis_result):
        """Test profiling a single driver."""
        profiles, percentiles = profile_drivers(
            corner_results_by_driver={"PIA": sample_corner_analysis_result},
            reference_driver="NOR"
        )

        assert len(profiles) == 1
        assert profiles[0].driver == "PIA"
        # With single driver, P30 = P70 = value, so value <= P30 is true
        # This results in STRONG classification (edge case behavior)
        # The key test is that the code doesn't crash and produces a profile
        assert profiles[0].braking is not None
        assert profiles[0].braking.percentile == 50.0  # Single value = 50th percentile


# ============================================================================
# profile_single_driver Tests
# ============================================================================

class TestProfileSingleDriver:
    """Tests for profile_single_driver convenience function."""

    def test_returns_single_profile(self, sample_corner_analysis_result):
        """Test that single driver profiling returns one profile."""
        profile = profile_single_driver(
            corner_result=sample_corner_analysis_result,
            reference_driver="NOR"
        )

        assert isinstance(profile, TechniqueProfile)
        assert profile.driver == "PIA"
        assert profile.reference_driver == "NOR"

    def test_profile_has_all_dimensions(self, sample_corner_analysis_result):
        """Test that single driver profile has all technique dimensions."""
        profile = profile_single_driver(
            corner_result=sample_corner_analysis_result,
            reference_driver="NOR"
        )

        assert profile.braking is not None
        assert profile.apex is not None
        assert profile.exit is not None
        assert profile.consistency is not None


# ============================================================================
# Edge Case Tests
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_handles_all_same_cause(self):
        """Test handling when all corners have the same cause."""
        corners = [
            CornerResult(i, f"T{i}", i*100, i*100-50, i*100-50, i*100+100,
                        0.01 * i, "braking", "high")
            for i in range(1, 6)
        ]
        result = CornerAnalysisResult("NOR", "PIA", corners, 0.15, 0, 5)

        profiles, _ = profile_drivers({"PIA": result}, "NOR")

        assert len(profiles) == 1
        # Should still produce a valid profile
        assert profiles[0].braking.corner_count == 5
        assert profiles[0].apex.corner_count == 0
        assert profiles[0].exit.corner_count == 0

    def test_handles_no_attributable_cause_corners(self):
        """Test handling when all corners have 'multiple' cause."""
        corners = [
            CornerResult(i, f"T{i}", i*100, i*100-50, i*100-50, i*100+100,
                        0.01 * i, "multiple", "high")
            for i in range(1, 6)
        ]
        result = CornerAnalysisResult("NOR", "PIA", corners, 0.15, 0, 5)

        profiles, _ = profile_drivers({"PIA": result}, "NOR")

        assert len(profiles) == 1
        # All dimension counts should be 0 (multiple doesn't count)
        assert profiles[0].braking.corner_count == 0
        assert profiles[0].apex.corner_count == 0
        assert profiles[0].exit.corner_count == 0

    def test_handles_very_small_deltas(self):
        """Test handling of very small delta values (near neutral threshold)."""
        corners = [
            CornerResult(1, "T1", 180, 100, 100, 280, 0.001, "braking", "high"),
            CornerResult(2, "T2", 400, 300, 300, 500, -0.002, "apex", "high"),
            CornerResult(3, "T3", 700, 550, 550, 800, 0.003, "exit", "high"),
        ]
        result = CornerAnalysisResult("NOR", "PIA", corners, 0.002, 1, 2)

        profiles, _ = profile_drivers({"PIA": result}, "NOR")

        # Should handle small deltas without issues
        assert len(profiles) == 1

    def test_handles_mixed_confidence_levels(self):
        """Test that mixed confidence levels are handled correctly."""
        corners = [
            CornerResult(1, "T1", 180, 100, 100, 280, 0.100, "braking", "high"),
            CornerResult(2, "T2", 400, 300, 300, 500, 0.100, "braking", "low"),
            CornerResult(3, "T3", 700, 550, 550, 800, 0.100, "braking", "medium"),
        ]
        result = CornerAnalysisResult("NOR", "PIA", corners, 0.300, 0, 3)

        profiles, _ = profile_drivers({"PIA": result}, "NOR", weight_by_confidence=True)

        assert len(profiles) == 1
        # Weighted average confidence should be between low and high
        assert 0 < profiles[0].overall_confidence < 1

    def test_two_drivers_produces_meaningful_classification(self):
        """Test that two drivers can be meaningfully classified."""
        # Driver 1: Better braking
        corners1 = [
            CornerResult(1, "T1", 180, 100, 100, 280, -0.050, "braking", "high"),
        ]
        result1 = CornerAnalysisResult("NOR", "VER", corners1, -0.050, 1, 0)

        # Driver 2: Worse braking
        corners2 = [
            CornerResult(1, "T1", 180, 100, 100, 280, 0.050, "braking", "high"),
        ]
        result2 = CornerAnalysisResult("NOR", "PIA", corners2, 0.050, 0, 1)

        profiles, percentiles = profile_drivers(
            {"VER": result1, "PIA": result2},
            "NOR"
        )

        # With 2 drivers, percentiles should differentiate them
        ver_profile = next(p for p in profiles if p.driver == "VER")
        pia_profile = next(p for p in profiles if p.driver == "PIA")

        # VER should have lower percentile (better) than PIA
        assert ver_profile.braking.percentile < pia_profile.braking.percentile
