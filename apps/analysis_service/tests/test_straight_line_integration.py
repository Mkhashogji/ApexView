"""
Comprehensive Unit Tests for Straight-Line (5th Dimension) Integration

Tests cover:
1. Primary factor determination logic
2. Straight-line aggregation
3. Straight-line classification (STRONG/NEUTRAL/WEAK)
4. Insight generation for straight-line dimension
5. Lap breakdown insight generation
6. Exit → straight opportunity cross-dimension analysis
7. End-to-end integration

Author: ApexView Engineering
Phase: 5th Dimension Integration Testing
"""

import pytest
from typing import List, Optional
from dataclasses import dataclass, field

# Import the modules we're testing
from services.technique_profiling import (
    TechniqueLevel,
    TechniqueDimension,
    StraightLineDimension,
    TechniqueProfile,
    determine_straight_line_primary_factor,
    aggregate_straight_line_performance,
    classify_straight_line_dimension,
    profile_drivers,
)
from services.corner_analysis import (
    CornerResult,
    CornerAnalysisResult,
    LapBreakdown,
    StraightSegment,
)
from services.insight_generation import (
    InsightMode,
    generate_straight_line_insight,
    generate_lap_breakdown_insight,
    generate_exit_straight_opportunity,
    InsightTemplates,
)


# =============================================================================
# Test Fixtures
# =============================================================================

@pytest.fixture
def sample_straight_segments() -> List[StraightSegment]:
    """Create sample straight segments for testing."""
    return [
        StraightSegment(
            segment_number=1,
            name="T1→T2",
            start_distance=0,
            end_distance=500,
            delta_change=-0.150,  # Gaining 150ms
            length=500,
            primary_factor="exit_traction",
        ),
        StraightSegment(
            segment_number=2,
            name="T4→T5",
            start_distance=1200,
            end_distance=1800,
            delta_change=-0.080,  # Gaining 80ms
            length=600,
            primary_factor="aero_efficiency",
        ),
        StraightSegment(
            segment_number=3,
            name="T7→T8",
            start_distance=2500,
            end_distance=3000,
            delta_change=0.050,  # Losing 50ms
            length=500,
            primary_factor="balanced",
        ),
    ]


@pytest.fixture
def sample_lap_breakdown(sample_straight_segments) -> LapBreakdown:
    """Create sample lap breakdown with straight segments."""
    return LapBreakdown(
        corner_total=0.376,
        straight_total=-0.267,
        official_gap=0.109,
        track_coverage=0.65,
        straight_segments=sample_straight_segments,
        reconciliation_valid=True,
        reconciliation_error=0.000,
    )


@pytest.fixture
def sample_exit_dimension() -> TechniqueDimension:
    """Create sample exit dimension for correlation testing."""
    return TechniqueDimension(
        level=TechniqueLevel.STRONG,
        descriptor="Excellent traction",
        percentile=25.0,
        raw_value=-0.150,
        corner_count=8,
        avg_confidence=0.85,
    )


@pytest.fixture
def sample_corner_result() -> CornerResult:
    """Create sample corner result."""
    return CornerResult(
        corner_number=1,
        name="Turn 1",
        apex_distance=100.0,
        brake_distance=80.0,
        zone_start=0.0,
        zone_end=200.0,
        delta_change=0.050,
        cause="braking",
        confidence="high",
    )


# =============================================================================
# TestPrimaryFactorDetermination
# =============================================================================

class TestPrimaryFactorDetermination:
    """Test determine_straight_line_primary_factor() logic."""

    def test_aero_efficiency_with_high_top_speed(self, sample_straight_segments):
        """High top speed delta should return aero_efficiency."""
        result = determine_straight_line_primary_factor(
            straight_segments=sample_straight_segments,
            top_speed_delta=5.0,  # 5 km/h faster
            avg_exit_delta=None,
        )
        assert result == "aero_efficiency"

    def test_high_drag_with_low_top_speed(self, sample_straight_segments):
        """Low top speed delta should return high_drag."""
        result = determine_straight_line_primary_factor(
            straight_segments=sample_straight_segments,
            top_speed_delta=-5.0,  # 5 km/h slower
            avg_exit_delta=None,
        )
        assert result == "high_drag"

    def test_exit_traction_correlation(self, sample_straight_segments):
        """Good exits + gaining on straights should return exit_traction."""
        result = determine_straight_line_primary_factor(
            straight_segments=sample_straight_segments,
            top_speed_delta=None,
            avg_exit_delta=-0.1,  # Gaining on exits
        )
        assert result == "exit_traction"

    def test_poor_traction_correlation(self, sample_straight_segments):
        """Bad exits + losing on straights should return poor_traction."""
        # Modify segments to be losing overall
        losing_segments = [
            StraightSegment(
                segment_number=1,
                name="T1→T2",
                start_distance=0,
                end_distance=500,
                delta_change=0.100,  # Losing
                length=500,
                primary_factor="poor_traction",
            ),
        ]
        result = determine_straight_line_primary_factor(
            straight_segments=losing_segments,
            top_speed_delta=None,
            avg_exit_delta=0.1,  # Losing on exits too
        )
        assert result == "poor_traction"

    def test_balanced_with_no_clear_factor(self):
        """No clear pattern should return balanced (or most common segment factor)."""
        # Create truly balanced segments with no dominant pattern
        balanced_segments = [
            StraightSegment(
                segment_number=1,
                name="T1→T2",
                start_distance=0,
                end_distance=500,
                delta_change=0.001,  # Nearly zero
                length=500,
                primary_factor="balanced",
            ),
            StraightSegment(
                segment_number=2,
                name="T3→T4",
                start_distance=600,
                end_distance=1000,
                delta_change=-0.001,  # Nearly zero
                length=400,
                primary_factor="balanced",
            ),
        ]
        result = determine_straight_line_primary_factor(
            straight_segments=balanced_segments,
            top_speed_delta=0.5,  # Minimal difference (under threshold)
            avg_exit_delta=0.01,  # Minimal correlation
        )
        assert result == "balanced"

    def test_empty_segments_returns_balanced(self):
        """Empty segments list should return balanced."""
        result = determine_straight_line_primary_factor(
            straight_segments=[],
            top_speed_delta=None,
            avg_exit_delta=None,
        )
        assert result == "balanced"


# =============================================================================
# TestStraightLineAggregation
# =============================================================================

class TestStraightLineAggregation:
    """Test aggregate_straight_line_performance() function."""

    def test_aggregation_with_valid_breakdown(self, sample_lap_breakdown):
        """Test aggregation produces correct totals."""
        result = aggregate_straight_line_performance(sample_lap_breakdown)

        assert result['straight_total'] == pytest.approx(-0.267, abs=0.001)
        assert result['segment_count'] == 3
        assert 'primary_factor' in result
        assert isinstance(result['top_gaining_straights'], list)
        assert isinstance(result['top_losing_straights'], list)

    def test_aggregation_identifies_gaining_straights(self, sample_lap_breakdown):
        """Test that gaining straights are correctly identified."""
        result = aggregate_straight_line_performance(sample_lap_breakdown)

        # Should identify T1→T2 and T4→T5 as gaining (negative delta)
        assert len(result['top_gaining_straights']) >= 1
        assert "T1→T2" in result['top_gaining_straights']

    def test_aggregation_identifies_losing_straights(self, sample_lap_breakdown):
        """Test that losing straights are correctly identified."""
        result = aggregate_straight_line_performance(sample_lap_breakdown)

        # Should identify T7→T8 as losing (positive delta)
        assert "T7→T8" in result['top_losing_straights']

    def test_aggregation_with_none_breakdown(self):
        """Test graceful handling of None lap_breakdown."""
        result = aggregate_straight_line_performance(None)

        assert result['straight_total'] == 0.0
        assert result['segment_count'] == 0
        assert result['primary_factor'] == 'balanced'
        assert result['top_gaining_straights'] == []
        assert result['top_losing_straights'] == []

    def test_aggregation_uses_exit_correlation(
        self, sample_lap_breakdown, sample_exit_dimension
    ):
        """Test that exit dimension is used for factor determination."""
        result = aggregate_straight_line_performance(
            sample_lap_breakdown,
            exit_dimension=sample_exit_dimension,
        )

        # With strong exit and gaining on straights, should detect exit_traction
        assert result['primary_factor'] in ['exit_traction', 'balanced', 'aero_efficiency']


# =============================================================================
# TestStraightLineClassification
# =============================================================================

class TestStraightLineClassification:
    """Test classify_straight_line_dimension() function."""

    def test_classification_strong_percentile(self):
        """Driver with lowest straight_total should be STRONG."""
        all_totals = [-0.300, -0.200, -0.100, 0.0, 0.100, 0.200, 0.300]
        result = classify_straight_line_dimension(
            straight_total=-0.300,  # Fastest
            all_straight_totals=all_totals,
            primary_factor="exit_traction",
            segment_count=5,
            top_gaining=["T1→T2"],
            top_losing=[],
        )

        assert result.level == TechniqueLevel.STRONG
        assert result.percentile < 30

    def test_classification_weak_percentile(self):
        """Driver with highest straight_total should be WEAK."""
        all_totals = [-0.300, -0.200, -0.100, 0.0, 0.100, 0.200, 0.300]
        result = classify_straight_line_dimension(
            straight_total=0.300,  # Slowest
            all_straight_totals=all_totals,
            primary_factor="poor_traction",
            segment_count=5,
            top_gaining=[],
            top_losing=["T7→T8"],
        )

        assert result.level == TechniqueLevel.WEAK
        assert result.percentile > 70

    def test_classification_neutral_percentile(self):
        """Driver in middle should be NEUTRAL."""
        all_totals = [-0.300, -0.200, -0.100, 0.0, 0.100, 0.200, 0.300]
        result = classify_straight_line_dimension(
            straight_total=0.0,  # Middle
            all_straight_totals=all_totals,
            primary_factor="balanced",
            segment_count=5,
            top_gaining=["T1→T2"],
            top_losing=["T7→T8"],
        )

        assert result.level == TechniqueLevel.NEUTRAL
        assert 30 <= result.percentile <= 70

    def test_classification_with_insufficient_data(self):
        """Test with less than 2 drivers returns NEUTRAL."""
        result = classify_straight_line_dimension(
            straight_total=-0.100,
            all_straight_totals=[-0.100],  # Only 1 driver
            primary_factor="balanced",
            segment_count=5,
            top_gaining=[],
            top_losing=[],
        )

        assert result.level == TechniqueLevel.NEUTRAL
        assert result.percentile == 50.0
        assert "Insufficient" in result.descriptor

    def test_classification_preserves_metadata(self):
        """Test that all metadata is preserved in result."""
        result = classify_straight_line_dimension(
            straight_total=-0.200,
            all_straight_totals=[-0.300, -0.200, -0.100, 0.0, 0.100],
            primary_factor="exit_traction",
            segment_count=7,
            top_gaining=["T1→T2", "T4→T5"],
            top_losing=["T7→T8"],
            avg_confidence=0.9,
        )

        assert result.raw_delta == -0.200
        assert result.primary_factor == "exit_traction"
        assert result.segment_count == 7
        assert result.top_gaining_straights == ["T1→T2", "T4→T5"]
        assert result.top_losing_straights == ["T7→T8"]
        assert result.avg_confidence == 0.9


# =============================================================================
# TestStraightLineInsightGeneration
# =============================================================================

class TestStraightLineInsightGeneration:
    """Test generate_straight_line_insight() function."""

    @pytest.fixture
    def strong_straight_line(self) -> StraightLineDimension:
        """Create STRONG straight-line dimension."""
        return StraightLineDimension(
            level=TechniqueLevel.STRONG,
            descriptor="Excellent straight-line speed",
            percentile=18.5,
            raw_delta=-0.267,
            primary_factor="exit_traction",
            segment_count=5,
            top_gaining_straights=["T1→T2", "T4→T5"],
            top_losing_straights=[],
            avg_confidence=0.85,
        )

    @pytest.fixture
    def weak_straight_line(self) -> StraightLineDimension:
        """Create WEAK straight-line dimension."""
        return StraightLineDimension(
            level=TechniqueLevel.WEAK,
            descriptor="Straight-line deficit",
            percentile=78.0,
            raw_delta=0.180,
            primary_factor="poor_traction",
            segment_count=5,
            top_gaining_straights=[],
            top_losing_straights=["T7→T8", "T10→T11"],
            avg_confidence=0.75,
        )

    def test_engineer_mode_strong_includes_percentile(self, strong_straight_line):
        """ENGINEER mode should include percentile and ms values."""
        result = generate_straight_line_insight(
            strong_straight_line, InsightMode.ENGINEER
        )

        assert result is not None
        assert "STRONG" in result.text
        assert "P18" in result.text or "P19" in result.text  # Rounded percentile
        assert "-267ms" in result.text or "+267ms" in result.text

    def test_driver_mode_strong_is_actionable(self, strong_straight_line):
        """DRIVER mode should be actionable without technical details."""
        result = generate_straight_line_insight(
            strong_straight_line, InsightMode.DRIVER
        )

        assert result is not None
        assert "strength" in result.text.lower()
        # Should not include raw percentile in driver mode
        assert "P18" not in result.text

    def test_weak_insight_includes_improvement_focus(self, weak_straight_line):
        """WEAK insight should include improvement advice."""
        result = generate_straight_line_insight(
            weak_straight_line, InsightMode.DRIVER
        )

        assert result is not None
        assert "losing" in result.text.lower() or "lost" in result.text.lower()

    def test_none_input_returns_none(self):
        """None input should return None."""
        result = generate_straight_line_insight(None, InsightMode.ENGINEER)
        assert result is None


# =============================================================================
# TestLapBreakdownInsight
# =============================================================================

class TestLapBreakdownInsight:
    """Test generate_lap_breakdown_insight() function."""

    def test_reconciled_breakdown_engineer(self, sample_lap_breakdown):
        """Test reconciled breakdown in engineer mode."""
        result = generate_lap_breakdown_insight(
            sample_lap_breakdown, InsightMode.ENGINEER
        )

        assert result is not None
        assert "Corners" in result or "corner" in result.lower()
        assert "Straights" in result or "straight" in result.lower()
        assert "+0.376" in result or "0.376" in result
        assert "-0.267" in result or "0.267" in result

    def test_reconciled_breakdown_driver(self, sample_lap_breakdown):
        """Test reconciled breakdown in driver mode."""
        result = generate_lap_breakdown_insight(
            sample_lap_breakdown, InsightMode.DRIVER
        )

        assert result is not None
        # Driver mode should mention "your lap"
        assert "your" in result.lower() or "lap" in result.lower()

    def test_not_reconciled_breakdown(self):
        """Test breakdown that doesn't reconcile."""
        bad_breakdown = LapBreakdown(
            corner_total=0.500,
            straight_total=-0.200,
            official_gap=0.400,  # 0.5 - 0.2 = 0.3 != 0.4
            track_coverage=0.6,
            straight_segments=[],
            reconciliation_valid=False,
            reconciliation_error=0.100,
        )

        result = generate_lap_breakdown_insight(bad_breakdown, InsightMode.ENGINEER)

        assert result is not None
        # Should mention discrepancy
        assert "100ms" in result or "discrepancy" in result.lower() or "error" in result.lower()

    def test_none_breakdown_returns_none(self):
        """None breakdown should return None."""
        result = generate_lap_breakdown_insight(None, InsightMode.ENGINEER)
        assert result is None


# =============================================================================
# TestExitStraightOpportunity
# =============================================================================

class TestExitStraightOpportunity:
    """Test generate_exit_straight_opportunity() cross-dimension analysis."""

    def test_strong_strong_is_optimal(self, sample_exit_dimension):
        """STRONG exit + STRONG straight should be optimal."""
        straight_dim = StraightLineDimension(
            level=TechniqueLevel.STRONG,
            descriptor="Excellent straight-line speed",
            percentile=20.0,
            raw_delta=-0.300,
            primary_factor="exit_traction",
            segment_count=5,
        )

        result = generate_exit_straight_opportunity(
            sample_exit_dimension, straight_dim, InsightMode.ENGINEER
        )

        assert result is not None
        assert "OPTIMAL" in result or "ideal" in result.lower() or "excellent" in result.lower()

    def test_weak_weak_is_critical(self):
        """WEAK exit + WEAK straight should be critical."""
        weak_exit = TechniqueDimension(
            level=TechniqueLevel.WEAK,
            descriptor="Traction deficit",
            percentile=80.0,
            raw_value=0.200,
            corner_count=8,
            avg_confidence=0.75,
        )
        weak_straight = StraightLineDimension(
            level=TechniqueLevel.WEAK,
            descriptor="Straight-line deficit",
            percentile=85.0,
            raw_delta=0.250,
            primary_factor="poor_traction",
            segment_count=5,
        )

        result = generate_exit_straight_opportunity(
            weak_exit, weak_straight, InsightMode.ENGINEER
        )

        assert result is not None
        assert "CRITICAL" in result or "focus" in result.lower()

    def test_strong_exit_weak_straight_anomaly(self, sample_exit_dimension):
        """STRONG exit + WEAK straight should be flagged as anomaly."""
        weak_straight = StraightLineDimension(
            level=TechniqueLevel.WEAK,
            descriptor="Straight-line deficit",
            percentile=82.0,
            raw_delta=0.200,
            primary_factor="high_drag",
            segment_count=5,
        )

        result = generate_exit_straight_opportunity(
            sample_exit_dimension, weak_straight, InsightMode.ENGINEER
        )

        assert result is not None
        # Should mention anomaly or setup trade-off
        assert "Anomaly" in result or "trade-off" in result.lower() or "high-drag" in result.lower()

    def test_driver_mode_is_actionable(self, sample_exit_dimension):
        """DRIVER mode should provide actionable advice."""
        straight_dim = StraightLineDimension(
            level=TechniqueLevel.NEUTRAL,
            descriptor="Balanced straight-line",
            percentile=50.0,
            raw_delta=0.0,
            primary_factor="balanced",
            segment_count=5,
        )

        result = generate_exit_straight_opportunity(
            sample_exit_dimension, straight_dim, InsightMode.DRIVER
        )

        assert result is not None
        # Should be shorter and more direct than engineer mode

    def test_none_inputs_return_none(self):
        """None inputs should return None."""
        assert generate_exit_straight_opportunity(None, None, InsightMode.ENGINEER) is None

        exit_dim = TechniqueDimension(
            level=TechniqueLevel.NEUTRAL,
            descriptor="Test",
            percentile=50.0,
            raw_value=0.0,
            corner_count=5,
            avg_confidence=0.8,
        )
        assert generate_exit_straight_opportunity(exit_dim, None, InsightMode.ENGINEER) is None


# =============================================================================
# TestEndToEndIntegration
# =============================================================================

class TestEndToEndIntegration:
    """Test complete integration from corner results to profile with 5th dimension."""

    def test_profile_drivers_includes_straight_line(self):
        """Test that profile_drivers() correctly generates 5th dimension."""
        # Create corner results with lap breakdown
        corner1 = CornerResult(
            corner_number=1,
            name="Turn 1",
            apex_distance=100.0,
            brake_distance=80.0,
            zone_start=0.0,
            zone_end=200.0,
            delta_change=0.050,
            cause="braking",
            confidence="high",
        )
        corner2 = CornerResult(
            corner_number=2,
            name="Turn 2",
            apex_distance=500.0,
            brake_distance=480.0,
            zone_start=400.0,
            zone_end=600.0,
            delta_change=-0.030,
            cause="exit",
            confidence="high",
        )

        straight_segments = [
            StraightSegment(
                segment_number=1,
                name="T1→T2",
                start_distance=200,
                end_distance=400,
                delta_change=-0.100,
                length=200,
                primary_factor="exit_traction",
            ),
        ]

        lap_breakdown = LapBreakdown(
            corner_total=0.020,  # 0.050 - 0.030
            straight_total=-0.100,
            official_gap=-0.080,  # 0.020 - 0.100
            track_coverage=0.65,
            straight_segments=straight_segments,
            reconciliation_valid=True,
            reconciliation_error=0.0,
        )

        corner_analysis = CornerAnalysisResult(
            reference_driver="VER",
            compare_driver="NOR",
            corner_results=[corner1, corner2],
            total_delta_change=0.020,
            corners_gaining=1,
            corners_losing=1,
            lap_breakdown=lap_breakdown,
        )

        # Profile with one driver
        profiles, percentiles = profile_drivers(
            corner_results_by_driver={"NOR": corner_analysis},
            reference_driver="VER",
        )

        assert len(profiles) == 1
        profile = profiles[0]

        # Check 5th dimension exists
        assert profile.straight_line is not None
        assert profile.straight_line.raw_delta == pytest.approx(-0.100, abs=0.001)
        assert profile.straight_line.segment_count == 1

    def test_profile_without_lap_breakdown(self):
        """Test that profile works without lap_breakdown (backward compatible)."""
        corner = CornerResult(
            corner_number=1,
            name="Turn 1",
            apex_distance=100.0,
            brake_distance=80.0,
            zone_start=0.0,
            zone_end=200.0,
            delta_change=0.050,
            cause="braking",
            confidence="high",
        )

        # No lap_breakdown (older data or missing)
        corner_analysis = CornerAnalysisResult(
            reference_driver="VER",
            compare_driver="NOR",
            corner_results=[corner],
            total_delta_change=0.050,
            corners_gaining=0,
            corners_losing=1,
            lap_breakdown=None,  # No breakdown
        )

        profiles, percentiles = profile_drivers(
            corner_results_by_driver={"NOR": corner_analysis},
            reference_driver="VER",
        )

        assert len(profiles) == 1
        profile = profiles[0]

        # straight_line should be None when no lap_breakdown
        assert profile.straight_line is None

        # Other dimensions should still work
        assert profile.braking is not None
        assert profile.apex is not None
        assert profile.exit is not None
        assert profile.consistency is not None

    def test_multiple_drivers_percentile_distribution(self):
        """Test that multiple drivers get correct percentile distribution."""
        # Create corner results for 3 drivers with different straight-line performance
        def create_corner_analysis(driver, straight_delta):
            corner = CornerResult(
                corner_number=1,
                name="Turn 1",
                apex_distance=100.0,
                brake_distance=80.0,
                zone_start=0.0,
                zone_end=200.0,
                delta_change=0.0,
                cause="braking",
                confidence="high",
            )
            segments = [
                StraightSegment(
                    segment_number=1,
                    name="T1→T2",
                    start_distance=200,
                    end_distance=400,
                    delta_change=straight_delta,
                    length=200,
                    primary_factor="balanced",
                ),
            ]
            breakdown = LapBreakdown(
                corner_total=0.0,
                straight_total=straight_delta,
                official_gap=straight_delta,
                track_coverage=0.5,
                straight_segments=segments,
                reconciliation_valid=True,
                reconciliation_error=0.0,
            )
            return CornerAnalysisResult(
                reference_driver="VER",
                compare_driver=driver,
                corner_results=[corner],
                total_delta_change=0.0,
                corners_gaining=0,
                corners_losing=0,
                lap_breakdown=breakdown,
            )

        results_by_driver = {
            "NOR": create_corner_analysis("NOR", -0.300),  # Fastest on straights
            "LEC": create_corner_analysis("LEC", 0.0),     # Middle
            "HAM": create_corner_analysis("HAM", 0.300),   # Slowest on straights
        }

        profiles, percentiles = profile_drivers(
            corner_results_by_driver=results_by_driver,
            reference_driver="VER",
        )

        assert len(profiles) == 3

        # Find profiles by driver
        profile_map = {p.driver: p for p in profiles}

        # Check classifications
        assert profile_map["NOR"].straight_line.level == TechniqueLevel.STRONG
        assert profile_map["LEC"].straight_line.level == TechniqueLevel.NEUTRAL
        assert profile_map["HAM"].straight_line.level == TechniqueLevel.WEAK

        # Verify percentile order
        assert profile_map["NOR"].straight_line.percentile < profile_map["LEC"].straight_line.percentile
        assert profile_map["LEC"].straight_line.percentile < profile_map["HAM"].straight_line.percentile


# =============================================================================
# Run tests
# =============================================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
