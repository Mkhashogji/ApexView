"""
Tests for Natural Language Insight Generation Module (Phase 5)

Tests the insight generation functionality including:
- Confidence classification (HIGH/MEDIUM/LOW/INSUFFICIENT)
- Profile validation
- Dimension insight generation (engineer and driver modes)
- Corner insights
- Opportunity insights
- Template-based text generation
- Anti-hallucination verification (all values from input)
- Edge cases and batch processing
"""

import pytest
import numpy as np
from typing import List, Dict

from services.insight_generation import (
    InsightMode,
    ConfidenceLevel,
    CornerInsight,
    DimensionInsight,
    NaturalLanguageInsight,
    InsightGenerationResult,
    BatchInsightResult,
    InsightTemplates,
    classify_confidence,
    validate_profile_for_insight,
    generate_dimension_insight_engineer,
    generate_dimension_insight_driver,
    generate_corner_insights,
    generate_opportunity_insights,
    generate_engineer_summary,
    generate_driver_summary,
    generate_insights,
    generate_insights_batch,
    CONFIDENCE_THRESHOLDS,
    MIN_CORNERS_FOR_INSIGHT,
    MIN_CORNERS_FOR_DIMENSION,
    MAX_CORNER_INSIGHTS,
)
from services.technique_profiling import (
    TechniqueLevel,
    TechniqueDimension,
    TechniqueProfile,
    SessionPercentiles,
)


# ============================================================================
# Fixtures
# ============================================================================

@pytest.fixture
def sample_dimension_strong() -> TechniqueDimension:
    """Create a sample STRONG technique dimension."""
    return TechniqueDimension(
        level=TechniqueLevel.STRONG,
        descriptor="Strong under braking",
        percentile=15.0,
        raw_value=-0.085,
        corner_count=5,
        avg_confidence=0.9,
    )


@pytest.fixture
def sample_dimension_weak() -> TechniqueDimension:
    """Create a sample WEAK technique dimension."""
    return TechniqueDimension(
        level=TechniqueLevel.WEAK,
        descriptor="Loses time under braking",
        percentile=82.0,
        raw_value=0.120,
        corner_count=5,
        avg_confidence=0.85,
    )


@pytest.fixture
def sample_dimension_neutral() -> TechniqueDimension:
    """Create a sample NEUTRAL technique dimension."""
    return TechniqueDimension(
        level=TechniqueLevel.NEUTRAL,
        descriptor="Balanced braking",
        percentile=50.0,
        raw_value=0.010,
        corner_count=4,
        avg_confidence=0.8,
    )


@pytest.fixture
def sample_profile_high_confidence(
    sample_dimension_strong,
    sample_dimension_weak,
    sample_dimension_neutral
) -> TechniqueProfile:
    """Create a sample profile with high confidence data."""
    return TechniqueProfile(
        driver="PIA",
        reference_driver="NOR",
        braking=sample_dimension_strong,
        apex=sample_dimension_neutral,
        exit=sample_dimension_weak,
        consistency=sample_dimension_neutral,
        top_gaining_corners=["Turn 3", "Turn 7", "Turn 12"],
        top_losing_corners=["Turn 1", "Turn 5", "Turn 17"],
        style_summary="Aggressive entry, struggles with traction",
        overall_confidence=0.87,
        total_corners_analyzed=19,
    )


@pytest.fixture
def sample_profile_medium_confidence() -> TechniqueProfile:
    """Create a sample profile with medium confidence data."""
    medium_dim = TechniqueDimension(
        level=TechniqueLevel.NEUTRAL,
        descriptor="Balanced",
        percentile=50.0,
        raw_value=0.02,
        corner_count=3,
        avg_confidence=0.65,
    )
    return TechniqueProfile(
        driver="VER",
        reference_driver="NOR",
        braking=medium_dim,
        apex=medium_dim,
        exit=medium_dim,
        consistency=medium_dim,
        top_gaining_corners=["Turn 2"],
        top_losing_corners=["Turn 4"],
        style_summary="Well-rounded technique",
        overall_confidence=0.65,
        total_corners_analyzed=7,
    )


@pytest.fixture
def sample_profile_low_confidence() -> TechniqueProfile:
    """Create a sample profile with low confidence data."""
    weak_dim = TechniqueDimension(
        level=TechniqueLevel.NEUTRAL,
        descriptor="Insufficient data",
        percentile=50.0,
        raw_value=0.0,
        corner_count=1,
        avg_confidence=0.4,
    )
    return TechniqueProfile(
        driver="TSU",
        reference_driver="NOR",
        braking=weak_dim,
        apex=weak_dim,
        exit=weak_dim,
        consistency=weak_dim,
        top_gaining_corners=[],
        top_losing_corners=["Turn 1"],
        style_summary="Insufficient data",
        overall_confidence=0.35,
        total_corners_analyzed=4,
    )


@pytest.fixture
def sample_profile_insufficient() -> TechniqueProfile:
    """Create a sample profile with insufficient data."""
    weak_dim = TechniqueDimension(
        level=TechniqueLevel.NEUTRAL,
        descriptor="No data",
        percentile=50.0,
        raw_value=0.0,
        corner_count=0,
        avg_confidence=0.2,
    )
    return TechniqueProfile(
        driver="SAR",
        reference_driver="NOR",
        braking=weak_dim,
        apex=weak_dim,
        exit=weak_dim,
        consistency=weak_dim,
        top_gaining_corners=[],
        top_losing_corners=[],
        style_summary="No data",
        overall_confidence=0.2,
        total_corners_analyzed=2,
    )


# ============================================================================
# TestClassifyConfidence
# ============================================================================

class TestClassifyConfidence:
    """Tests for classify_confidence function."""

    def test_high_confidence_classification(self):
        """Test that high confidence + many corners = HIGH."""
        level, reason = classify_confidence(
            avg_confidence=0.9,
            corner_count=15,
            dimension_corner_counts={"braking": 5, "apex": 4, "exit": 6}
        )
        assert level == ConfidenceLevel.HIGH
        assert reason == ""

    def test_medium_confidence_classification(self):
        """Test that moderate confidence = MEDIUM."""
        level, reason = classify_confidence(
            avg_confidence=0.6,
            corner_count=8,
            dimension_corner_counts={"braking": 3, "apex": 2, "exit": 3}
        )
        assert level == ConfidenceLevel.MEDIUM

    def test_low_confidence_classification(self):
        """Test that low confidence = LOW."""
        level, reason = classify_confidence(
            avg_confidence=0.4,
            corner_count=4,
            dimension_corner_counts={"braking": 1, "apex": 1, "exit": 2}
        )
        assert level == ConfidenceLevel.LOW

    def test_insufficient_corners(self):
        """Test that too few corners = INSUFFICIENT."""
        level, reason = classify_confidence(
            avg_confidence=0.9,
            corner_count=2,
            dimension_corner_counts={"braking": 1, "apex": 0, "exit": 1}
        )
        assert level == ConfidenceLevel.INSUFFICIENT
        assert "2 corners" in reason

    def test_insufficient_confidence(self):
        """Test that very low confidence = INSUFFICIENT."""
        level, reason = classify_confidence(
            avg_confidence=0.2,
            corner_count=10,
            dimension_corner_counts={"braking": 4, "apex": 3, "exit": 3}
        )
        assert level == ConfidenceLevel.INSUFFICIENT
        assert "too low" in reason

    def test_no_dimension_counts(self):
        """Test classification without dimension counts."""
        level, reason = classify_confidence(
            avg_confidence=0.85,
            corner_count=12,
            dimension_corner_counts=None
        )
        assert level == ConfidenceLevel.HIGH


# ============================================================================
# TestValidateProfile
# ============================================================================

class TestValidateProfile:
    """Tests for validate_profile_for_insight function."""

    def test_valid_profile_passes(self, sample_profile_high_confidence):
        """Test that a valid profile passes validation."""
        is_valid, reason = validate_profile_for_insight(sample_profile_high_confidence)
        assert is_valid is True
        assert reason == ""

    def test_insufficient_corners_fails(self, sample_profile_insufficient):
        """Test that too few corners fails validation."""
        is_valid, reason = validate_profile_for_insight(sample_profile_insufficient)
        assert is_valid is False
        assert "corners" in reason.lower()

    def test_low_confidence_fails(self):
        """Test that very low confidence fails validation."""
        dim = TechniqueDimension(
            level=TechniqueLevel.NEUTRAL,
            descriptor="test",
            percentile=50.0,
            raw_value=0.0,
            corner_count=2,
            avg_confidence=0.1,
        )
        profile = TechniqueProfile(
            driver="TEST",
            reference_driver="REF",
            braking=dim,
            apex=dim,
            exit=dim,
            consistency=dim,
            top_gaining_corners=[],
            top_losing_corners=[],
            style_summary="test",
            overall_confidence=0.1,
            total_corners_analyzed=5,
        )
        is_valid, reason = validate_profile_for_insight(profile)
        assert is_valid is False
        assert "confidence" in reason.lower()


# ============================================================================
# TestDimensionInsightEngineer
# ============================================================================

class TestDimensionInsightEngineer:
    """Tests for generate_dimension_insight_engineer function."""

    def test_strong_braking_insight(self, sample_dimension_strong):
        """Test engineer insight for STRONG braking."""
        insight = generate_dimension_insight_engineer(
            sample_dimension_strong, "braking", "NOR"
        )
        assert insight.dimension == "braking"
        assert insight.level == "strong"
        assert "STRONG" in insight.text
        assert "15" in insight.text  # Percentile

    def test_weak_dimension_insight(self, sample_dimension_weak):
        """Test engineer insight for WEAK dimension."""
        insight = generate_dimension_insight_engineer(
            sample_dimension_weak, "exit", "NOR"
        )
        assert "WEAK" in insight.text
        assert insight.raw_value_ms == 120  # 0.120 * 1000

    def test_includes_percentile(self, sample_dimension_neutral):
        """Test that percentile is included in engineer insights."""
        insight = generate_dimension_insight_engineer(
            sample_dimension_neutral, "apex", "NOR"
        )
        assert "P50" in insight.text or "50" in insight.text

    def test_includes_corner_count(self, sample_dimension_strong):
        """Test that corner count is included."""
        insight = generate_dimension_insight_engineer(
            sample_dimension_strong, "braking", "NOR"
        )
        assert insight.corner_count == 5

    def test_all_dimensions_produce_output(self, sample_dimension_neutral):
        """Test all dimension names produce valid output."""
        for dim_name in ["braking", "apex", "exit", "consistency"]:
            insight = generate_dimension_insight_engineer(
                sample_dimension_neutral, dim_name, "NOR"
            )
            assert insight.text is not None
            assert len(insight.text) > 10


# ============================================================================
# TestDimensionInsightDriver
# ============================================================================

class TestDimensionInsightDriver:
    """Tests for generate_dimension_insight_driver function."""

    def test_strong_insight_positive_language(self, sample_dimension_strong):
        """Test driver insight uses positive language for strengths."""
        insight = generate_dimension_insight_driver(
            sample_dimension_strong, "braking", "NOR"
        )
        positive_words = ["strength", "excellent", "strong", "great", "later"]
        assert any(word in insight.text.lower() for word in positive_words)

    def test_weak_insight_actionable_language(self, sample_dimension_weak):
        """Test driver insight uses actionable language for weaknesses."""
        insight = generate_dimension_insight_driver(
            sample_dimension_weak, "exit", "NOR"
        )
        actionable_words = ["try", "focus", "losing", "earlier"]
        assert any(word in insight.text.lower() for word in actionable_words)

    def test_neutral_insight(self, sample_dimension_neutral):
        """Test driver insight for NEUTRAL dimension."""
        insight = generate_dimension_insight_driver(
            sample_dimension_neutral, "braking", "NOR"
        )
        assert insight.level == "neutral"
        assert len(insight.text) > 10

    def test_all_dimensions_produce_output(self, sample_dimension_neutral):
        """Test all dimension names produce valid output in driver mode."""
        for dim_name in ["braking", "apex", "exit", "consistency"]:
            insight = generate_dimension_insight_driver(
                sample_dimension_neutral, dim_name, "NOR"
            )
            assert insight.text is not None
            assert len(insight.text) > 5


# ============================================================================
# TestCornerInsights
# ============================================================================

class TestCornerInsights:
    """Tests for generate_corner_insights function."""

    def test_generates_corner_insights(self, sample_profile_high_confidence):
        """Test that corner insights are generated."""
        insights = generate_corner_insights(sample_profile_high_confidence)
        assert len(insights) > 0

    def test_includes_gaining_and_losing(self, sample_profile_high_confidence):
        """Test that both gaining and losing corners are included."""
        insights = generate_corner_insights(sample_profile_high_confidence)
        directions = [i.direction for i in insights]
        assert "gaining" in directions
        assert "losing" in directions

    def test_respects_max_limit(self, sample_profile_high_confidence):
        """Test that max corners limit is respected."""
        insights = generate_corner_insights(
            sample_profile_high_confidence,
            mode=InsightMode.ENGINEER,
            max_corners=2
        )
        assert len(insights) <= 2

    def test_engineer_mode(self, sample_profile_high_confidence):
        """Test corner insights in engineer mode."""
        insights = generate_corner_insights(
            sample_profile_high_confidence,
            mode=InsightMode.ENGINEER
        )
        assert len(insights) > 0
        for insight in insights:
            assert insight.corner_name in (
                sample_profile_high_confidence.top_gaining_corners +
                sample_profile_high_confidence.top_losing_corners
            )

    def test_driver_mode(self, sample_profile_high_confidence):
        """Test corner insights in driver mode."""
        insights = generate_corner_insights(
            sample_profile_high_confidence,
            mode=InsightMode.DRIVER
        )
        assert len(insights) > 0

    def test_empty_corners_handled(self, sample_profile_insufficient):
        """Test handling when no corners exist."""
        insights = generate_corner_insights(sample_profile_insufficient)
        assert insights == []


# ============================================================================
# TestOpportunityInsights
# ============================================================================

class TestOpportunityInsights:
    """Tests for generate_opportunity_insights function."""

    def test_strong_strong_opportunity(self):
        """Test opportunity text for STRONG/STRONG profile."""
        dim_strong = TechniqueDimension(
            level=TechniqueLevel.STRONG,
            descriptor="Strong",
            percentile=15.0,
            raw_value=-0.05,
            corner_count=5,
            avg_confidence=0.9,
        )
        profile = TechniqueProfile(
            driver="TEST",
            reference_driver="REF",
            braking=dim_strong,
            apex=dim_strong,
            exit=dim_strong,
            consistency=dim_strong,
            top_gaining_corners=[],
            top_losing_corners=[],
            style_summary="Complete package",
            overall_confidence=0.9,
            total_corners_analyzed=19,
        )
        text = generate_opportunity_insights(profile, "REF")
        assert "excellent" in text.lower() or "consistency" in text.lower()

    def test_weak_weak_opportunity(self):
        """Test opportunity text for WEAK/WEAK profile."""
        dim_weak = TechniqueDimension(
            level=TechniqueLevel.WEAK,
            descriptor="Weak",
            percentile=85.0,
            raw_value=0.10,
            corner_count=5,
            avg_confidence=0.8,
        )
        profile = TechniqueProfile(
            driver="TEST",
            reference_driver="REF",
            braking=dim_weak,
            apex=dim_weak,
            exit=dim_weak,
            consistency=dim_weak,
            top_gaining_corners=[],
            top_losing_corners=[],
            style_summary="Needs work",
            overall_confidence=0.8,
            total_corners_analyzed=19,
        )
        text = generate_opportunity_insights(profile, "REF")
        assert "braking" in text.lower() or "entry" in text.lower()

    def test_weak_braking_strong_exit(self, sample_profile_high_confidence):
        """Test opportunity for weak braking, strong exit combination."""
        # Modify profile for this test
        sample_profile_high_confidence.braking = TechniqueDimension(
            level=TechniqueLevel.WEAK,
            descriptor="Weak braking",
            percentile=82.0,
            raw_value=0.12,
            corner_count=5,
            avg_confidence=0.9,
        )
        sample_profile_high_confidence.exit = TechniqueDimension(
            level=TechniqueLevel.STRONG,
            descriptor="Strong exit",
            percentile=15.0,
            raw_value=-0.08,
            corner_count=5,
            avg_confidence=0.9,
        )
        text = generate_opportunity_insights(sample_profile_high_confidence, "NOR")
        # Should mention leveraging exit strength or braking improvement
        assert "exit" in text.lower() or "brake" in text.lower()

    def test_all_level_combinations_produce_output(self):
        """Test that all 9 braking x exit combinations have templates."""
        for braking_level in TechniqueLevel:
            for exit_level in TechniqueLevel:
                dim = TechniqueDimension(
                    level=TechniqueLevel.NEUTRAL,
                    descriptor="test",
                    percentile=50.0,
                    raw_value=0.0,
                    corner_count=5,
                    avg_confidence=0.8,
                )
                profile = TechniqueProfile(
                    driver="TEST",
                    reference_driver="REF",
                    braking=TechniqueDimension(
                        level=braking_level,
                        descriptor="",
                        percentile=50.0,
                        raw_value=0.0,
                        corner_count=5,
                        avg_confidence=0.8,
                    ),
                    apex=dim,
                    exit=TechniqueDimension(
                        level=exit_level,
                        descriptor="",
                        percentile=50.0,
                        raw_value=0.0,
                        corner_count=5,
                        avg_confidence=0.8,
                    ),
                    consistency=dim,
                    top_gaining_corners=[],
                    top_losing_corners=[],
                    style_summary="Test",
                    overall_confidence=0.8,
                    total_corners_analyzed=19,
                )
                text = generate_opportunity_insights(profile, "REF")
                assert len(text) > 0, f"No text for {braking_level}, {exit_level}"


# ============================================================================
# TestGenerateSummaries
# ============================================================================

class TestGenerateSummaries:
    """Tests for summary generation functions."""

    def test_engineer_summary_contains_driver(self, sample_profile_high_confidence):
        """Test engineer summary contains driver code."""
        summary = generate_engineer_summary(
            sample_profile_high_confidence,
            ConfidenceLevel.HIGH,
            "",
            {}
        )
        assert "PIA" in summary

    def test_engineer_summary_contains_reference(self, sample_profile_high_confidence):
        """Test engineer summary contains reference driver."""
        summary = generate_engineer_summary(
            sample_profile_high_confidence,
            ConfidenceLevel.HIGH,
            "",
            {}
        )
        assert "NOR" in summary

    def test_engineer_summary_contains_style(self, sample_profile_high_confidence):
        """Test engineer summary contains style summary."""
        summary = generate_engineer_summary(
            sample_profile_high_confidence,
            ConfidenceLevel.HIGH,
            "",
            {}
        )
        assert "Aggressive" in summary or "traction" in summary

    def test_driver_summary_contains_style(self, sample_profile_high_confidence):
        """Test driver summary contains style summary."""
        summary = generate_driver_summary(
            sample_profile_high_confidence,
            ConfidenceLevel.HIGH,
            {}
        )
        assert "Aggressive" in summary or "traction" in summary

    def test_session_context_included(self, sample_profile_high_confidence):
        """Test session context is included when provided."""
        summary = generate_engineer_summary(
            sample_profile_high_confidence,
            ConfidenceLevel.HIGH,
            "",
            {"circuit": "Monaco", "session": "Q3"}
        )
        assert "Monaco" in summary


# ============================================================================
# TestGenerateInsights (Integration)
# ============================================================================

class TestGenerateInsights:
    """Integration tests for generate_insights function."""

    def test_engineer_mode_produces_insight(self, sample_profile_high_confidence):
        """Test that engineer mode produces complete insight."""
        result = generate_insights(
            sample_profile_high_confidence,
            mode=InsightMode.ENGINEER
        )
        assert result.success is True
        assert result.insight is not None
        assert result.insight.mode == InsightMode.ENGINEER
        assert result.insight.driver == "PIA"
        assert result.insight.summary != ""
        assert len(result.insight.dimension_insights) == 4

    def test_driver_mode_produces_insight(self, sample_profile_high_confidence):
        """Test that driver mode produces complete insight."""
        result = generate_insights(
            sample_profile_high_confidence,
            mode=InsightMode.DRIVER
        )
        assert result.success is True
        assert result.insight.mode == InsightMode.DRIVER

    def test_confidence_level_assigned(self, sample_profile_high_confidence):
        """Test that confidence level is assigned."""
        result = generate_insights(sample_profile_high_confidence)
        assert result.insight.confidence_level in ConfidenceLevel

    def test_session_context_included(self, sample_profile_high_confidence):
        """Test that session context is included when provided."""
        result = generate_insights(
            sample_profile_high_confidence,
            session_context={"circuit": "Monaco", "session": "Q3"}
        )
        assert result.insight.session_context.get("circuit") == "Monaco"

    def test_style_summary_preserved(self, sample_profile_high_confidence):
        """Test that style summary from Phase 4 is preserved."""
        result = generate_insights(sample_profile_high_confidence)
        assert result.insight.style_summary == "Aggressive entry, struggles with traction"

    def test_corner_insights_populated(self, sample_profile_high_confidence):
        """Test that corner insights are populated."""
        result = generate_insights(sample_profile_high_confidence)
        assert len(result.insight.corner_insights) > 0

    def test_opportunity_text_populated(self, sample_profile_high_confidence):
        """Test that opportunity text is populated."""
        result = generate_insights(sample_profile_high_confidence)
        assert len(result.insight.opportunity_text) > 0

    def test_medium_confidence_has_hedging(self, sample_profile_medium_confidence):
        """Test that medium confidence produces hedging."""
        result = generate_insights(sample_profile_medium_confidence)
        assert result.insight.confidence_level in [ConfidenceLevel.MEDIUM, ConfidenceLevel.LOW]

    def test_low_confidence_profile(self, sample_profile_low_confidence):
        """Test insight generation for low confidence profile."""
        result = generate_insights(sample_profile_low_confidence)
        assert result.success is True
        assert result.insight.confidence_level in [ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM]


# ============================================================================
# TestDataBinding (Anti-Hallucination)
# ============================================================================

class TestDataBinding:
    """Tests to verify anti-hallucination principle."""

    def test_summary_contains_driver_code(self, sample_profile_high_confidence):
        """Test that summary contains actual driver code."""
        result = generate_insights(sample_profile_high_confidence)
        assert "PIA" in result.insight.summary or sample_profile_high_confidence.driver in result.insight.summary

    def test_summary_contains_reference_driver(self, sample_profile_high_confidence):
        """Test that summary contains reference driver."""
        result = generate_insights(sample_profile_high_confidence)
        assert "NOR" in result.insight.summary

    def test_dimension_values_match_profile(self, sample_profile_high_confidence):
        """Test that dimension insight values match profile data."""
        result = generate_insights(sample_profile_high_confidence, InsightMode.ENGINEER)
        braking_insight = next(d for d in result.insight.dimension_insights if d.dimension == "braking")
        assert braking_insight.percentile == sample_profile_high_confidence.braking.percentile
        assert braking_insight.level == sample_profile_high_confidence.braking.level.value

    def test_no_invented_corner_names(self, sample_profile_high_confidence):
        """Test that corner insights only use actual corner names from profile."""
        result = generate_insights(sample_profile_high_confidence)
        valid_corners = (
            sample_profile_high_confidence.top_gaining_corners +
            sample_profile_high_confidence.top_losing_corners
        )
        for corner_insight in result.insight.corner_insights:
            assert corner_insight.corner_name in valid_corners

    def test_raw_values_match_profile(self, sample_profile_high_confidence):
        """Test that raw values in insights match profile values."""
        result = generate_insights(sample_profile_high_confidence, InsightMode.ENGINEER)
        for dim_insight in result.insight.dimension_insights:
            profile_dim = getattr(sample_profile_high_confidence, dim_insight.dimension)
            expected_ms = int(profile_dim.raw_value * 1000)
            assert dim_insight.raw_value_ms == expected_ms


# ============================================================================
# TestEdgeCases
# ============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_gaining_corners_handled(self, sample_profile_high_confidence):
        """Test handling when no gaining corners exist."""
        sample_profile_high_confidence.top_gaining_corners = []
        result = generate_insights(sample_profile_high_confidence)
        assert result.success is True

    def test_empty_losing_corners_handled(self, sample_profile_high_confidence):
        """Test handling when no losing corners exist."""
        sample_profile_high_confidence.top_losing_corners = []
        result = generate_insights(sample_profile_high_confidence)
        assert result.success is True

    def test_all_neutral_dimensions(self):
        """Test insight generation when all dimensions are NEUTRAL."""
        dim = TechniqueDimension(
            level=TechniqueLevel.NEUTRAL,
            descriptor="Neutral",
            percentile=50.0,
            raw_value=0.01,
            corner_count=5,
            avg_confidence=0.8,
        )
        profile = TechniqueProfile(
            driver="TEST",
            reference_driver="REF",
            braking=dim,
            apex=dim,
            exit=dim,
            consistency=dim,
            top_gaining_corners=["T1"],
            top_losing_corners=["T2"],
            style_summary="Well-rounded technique",
            overall_confidence=0.8,
            total_corners_analyzed=19,
        )
        result = generate_insights(profile)
        assert result.success is True
        # All neutral should have opportunity about targeting corners
        assert len(result.insight.opportunity_text) > 0

    def test_very_small_raw_values(self):
        """Test handling of very small raw values (near zero)."""
        dim = TechniqueDimension(
            level=TechniqueLevel.NEUTRAL,
            descriptor="test",
            percentile=50.0,
            raw_value=0.001,  # 1ms
            corner_count=5,
            avg_confidence=0.8,
        )
        profile = TechniqueProfile(
            driver="TEST",
            reference_driver="REF",
            braking=dim,
            apex=dim,
            exit=dim,
            consistency=dim,
            top_gaining_corners=[],
            top_losing_corners=[],
            style_summary="Test",
            overall_confidence=0.8,
            total_corners_analyzed=10,
        )
        result = generate_insights(profile)
        assert result.success is True


# ============================================================================
# TestBatchGeneration
# ============================================================================

class TestBatchGeneration:
    """Tests for generate_insights_batch function."""

    def test_batch_processes_multiple_profiles(self, sample_profile_high_confidence, sample_profile_medium_confidence):
        """Test that batch processing handles multiple profiles."""
        profiles = [sample_profile_high_confidence, sample_profile_medium_confidence]
        result = generate_insights_batch(profiles, InsightMode.ENGINEER)
        assert len(result.insights) == 2
        assert result.metadata["drivers_processed"] == 2

    def test_batch_handles_empty_list(self):
        """Test batch processing with empty list."""
        result = generate_insights_batch([], InsightMode.ENGINEER)
        assert result.insights == []
        assert result.metadata["drivers_processed"] == 0

    def test_batch_preserves_mode(self, sample_profile_high_confidence):
        """Test that batch preserves the requested mode."""
        result = generate_insights_batch(
            [sample_profile_high_confidence],
            InsightMode.DRIVER
        )
        assert result.insights[0].mode == InsightMode.DRIVER

    def test_batch_includes_session_context(self, sample_profile_high_confidence):
        """Test that batch includes session context."""
        result = generate_insights_batch(
            [sample_profile_high_confidence],
            InsightMode.ENGINEER,
            {"circuit": "Spa"}
        )
        assert result.insights[0].session_context.get("circuit") == "Spa"


# ============================================================================
# TestTemplates
# ============================================================================

class TestTemplates:
    """Tests for InsightTemplates class."""

    def test_all_confidence_levels_have_engineer_openings(self):
        """Test that all confidence levels have engineer opening templates."""
        for level in ConfidenceLevel:
            assert level in InsightTemplates.ENGINEER_OPENINGS

    def test_all_confidence_levels_have_driver_openings(self):
        """Test that all confidence levels have driver opening templates."""
        for level in ConfidenceLevel:
            assert level in InsightTemplates.DRIVER_OPENINGS

    def test_all_dimensions_have_engineer_templates(self):
        """Test all dimensions have engineer templates for all levels."""
        dimensions = ["braking", "apex", "exit", "consistency"]
        for dim in dimensions:
            assert dim in InsightTemplates.ENGINEER_DIMENSION
            for level in TechniqueLevel:
                assert level in InsightTemplates.ENGINEER_DIMENSION[dim]

    def test_all_dimensions_have_driver_templates(self):
        """Test all dimensions have driver templates for all levels."""
        dimensions = ["braking", "apex", "exit", "consistency"]
        for dim in dimensions:
            assert dim in InsightTemplates.DRIVER_DIMENSION
            for level in TechniqueLevel:
                assert level in InsightTemplates.DRIVER_DIMENSION[dim]

    def test_all_causes_have_corner_templates(self):
        """Test all causes have corner templates."""
        causes = ["braking", "apex", "exit", "multiple", "unknown"]
        for cause in causes:
            assert cause in InsightTemplates.CORNER_GAINING
            assert cause in InsightTemplates.CORNER_LOSING

    def test_opportunity_templates_cover_all_combinations(self):
        """Test opportunity templates cover all braking x exit combinations."""
        for braking in TechniqueLevel:
            for exit_level in TechniqueLevel:
                key = (braking, exit_level)
                assert key in InsightTemplates.OPPORTUNITY_TEMPLATES, f"Missing template for {key}"
