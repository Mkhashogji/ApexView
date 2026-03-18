"""
Tests for Performance Orchestrator Module (Phase 6).

Tests the unified performance insights pipeline that chains
Phases 2-5 into a single API call.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import numpy as np

from services.performance_orchestrator import (
    PerformanceInsightsConfig,
    DriverPerformanceResult,
    PhaseTimingInfo,
    PerformanceInsightsResult,
    run_phase2_delta,
    run_phase3_corner,
    run_phase4_technique,
    run_phase5_insight,
    _technique_profile_to_dict,
    _session_percentiles_to_dict,
    _insight_to_dict,
    _corner_result_to_dict,
)
from services.corner_analysis import CornerInput, CornerResult, CornerAnalysisResult
from services.delta_analysis import DeltaResult
from services.technique_profiling import (
    TechniqueProfile,
    TechniqueDimension,
    TechniqueLevel,
    SessionPercentiles,
)
from services.insight_generation import (
    InsightMode,
    NaturalLanguageInsight,
    ConfidenceLevel,
    DimensionInsight,
    CornerInsight,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_telemetry():
    """Create sample telemetry data for testing."""
    distance = list(np.linspace(0, 5000, 100))
    return {
        "distance": distance,
        "speed": [200 + np.sin(i / 10) * 50 for i in range(100)],
        "brake": [50 if 20 < i < 40 else 0 for i in range(100)],
        "throttle": [100 if i < 20 or i > 50 else 50 for i in range(100)],
        "lap_time": 90.5,
    }


@pytest.fixture
def sample_corners():
    """Create sample corner definitions."""
    return [
        CornerInput(corner_number=1, apex_distance=500, corner_type="right", name="Turn 1"),
        CornerInput(corner_number=2, apex_distance=1200, corner_type="left", name="Turn 2"),
        CornerInput(corner_number=3, apex_distance=2000, corner_type="right", name="Turn 3"),
        CornerInput(corner_number=4, apex_distance=3000, corner_type="left", name="Turn 4"),
        CornerInput(corner_number=5, apex_distance=4000, corner_type="right", name="Turn 5"),
    ]


@pytest.fixture
def sample_config(sample_corners):
    """Create sample orchestrator config."""
    return PerformanceInsightsConfig(
        session_id="2025_24_Qualifying",
        reference_driver="NOR",
        compare_drivers=["PIA", "VER"],
        corners=sample_corners,
        mode="engineer",
        session_part="Q3",
        circuit_name="Bahrain International Circuit",
        include_telemetry=True,
    )


@pytest.fixture
def sample_delta_result():
    """Create sample delta result."""
    distance = list(np.linspace(0, 5000, 100))
    delta = list(np.linspace(0, 0.2, 100))
    return DeltaResult(
        reference_driver="NOR",
        compare_driver="PIA",
        distance=distance,
        delta=delta,
        raw_delta=delta,
        official_gap=0.2,
        scaling_factor=1.0,
        telemetry_gap=0.2,
        confidence=0.9,
    )


@pytest.fixture
def sample_corner_result():
    """Create sample corner analysis result."""
    return CornerAnalysisResult(
        reference_driver="NOR",
        compare_driver="PIA",
        corner_results=[
            CornerResult(
                corner_number=1,
                name="Turn 1",
                apex_distance=500,
                brake_distance=350,
                zone_start=350,
                zone_end=600,
                delta_change=0.05,
                cause="braking",
                confidence="high",
            ),
            CornerResult(
                corner_number=2,
                name="Turn 2",
                apex_distance=1200,
                brake_distance=1000,
                zone_start=1000,
                zone_end=1300,
                delta_change=-0.03,
                cause="exit",
                confidence="medium",
            ),
        ],
        total_delta_change=0.02,
        corners_gaining=1,
        corners_losing=1,
    )


@pytest.fixture
def sample_technique_dimension():
    """Create sample technique dimension."""
    return TechniqueDimension(
        level=TechniqueLevel.STRONG,
        descriptor="Strong under braking",
        percentile=25.0,
        raw_value=-0.05,
        corner_count=3,
        avg_confidence=0.8,
    )


@pytest.fixture
def sample_technique_profile(sample_technique_dimension):
    """Create sample technique profile."""
    return TechniqueProfile(
        driver="PIA",
        reference_driver="NOR",
        braking=sample_technique_dimension,
        apex=sample_technique_dimension,
        exit=sample_technique_dimension,
        consistency=sample_technique_dimension,
        top_gaining_corners=["Turn 1", "Turn 3"],
        top_losing_corners=["Turn 2"],
        style_summary="Complete package — excels in all phases",
        overall_confidence=0.85,
        total_corners_analyzed=5,
    )


@pytest.fixture
def sample_session_percentiles():
    """Create sample session percentiles."""
    return SessionPercentiles(
        braking_p30=-0.03,
        braking_p70=0.03,
        apex_p30=-0.02,
        apex_p70=0.02,
        exit_p30=-0.02,
        exit_p70=0.02,
        consistency_p30=0.01,
        consistency_p70=0.03,
        driver_count=5,
        all_braking=[-0.05, -0.02, 0.0, 0.02, 0.05],
        all_apex=[-0.03, -0.01, 0.0, 0.01, 0.03],
        all_exit=[-0.04, -0.01, 0.0, 0.02, 0.04],
        all_consistency=[0.01, 0.015, 0.02, 0.025, 0.03],
    )


@pytest.fixture
def sample_insight():
    """Create sample natural language insight."""
    return NaturalLanguageInsight(
        driver="PIA",
        reference_driver="NOR",
        mode=InsightMode.ENGINEER,
        confidence_level=ConfidenceLevel.HIGH,
        summary="PIA vs NOR: Complete package. Analysis based on 5 corners with high confidence.",
        dimension_insights=[
            DimensionInsight(
                dimension="braking",
                level="strong",
                percentile=25.0,
                text="Braking: STRONG (P25) — -50ms",
                raw_value_ms=-50,
                corner_count=3,
            ),
        ],
        corner_insights=[
            CornerInsight(
                corner_name="Turn 1",
                delta_ms=-50,
                direction="gaining",
                cause="braking",
                text="Gaining 50ms at Turn 1 under braking",
                confidence="high",
            ),
        ],
        opportunity_text="Technique is excellent across all phases.",
        hedging_prefix="",
        total_corners=5,
        session_context={"circuit": "Bahrain"},
        style_summary="Complete package",
    )


# =============================================================================
# Config Tests
# =============================================================================

class TestPerformanceInsightsConfig:
    """Tests for PerformanceInsightsConfig dataclass."""

    def test_default_values(self, sample_corners):
        """Test default config values."""
        config = PerformanceInsightsConfig(
            session_id="2025_1_Qualifying",
            reference_driver="VER",
            compare_drivers=["HAM"],
            corners=sample_corners,
        )

        assert config.mode == "engineer"
        assert config.session_part is None
        assert config.circuit_name is None
        assert config.include_telemetry is True

    def test_custom_values(self, sample_config):
        """Test config with custom values."""
        assert sample_config.session_id == "2025_24_Qualifying"
        assert sample_config.reference_driver == "NOR"
        assert sample_config.compare_drivers == ["PIA", "VER"]
        assert len(sample_config.corners) == 5
        assert sample_config.mode == "engineer"
        assert sample_config.session_part == "Q3"
        assert sample_config.circuit_name == "Bahrain International Circuit"


# =============================================================================
# Phase Execution Tests
# =============================================================================

class TestPhase2Delta:
    """Tests for Phase 2 delta analysis execution."""

    def test_run_phase2_delta_success(self, sample_telemetry):
        """Test successful Phase 2 execution."""
        ref_telemetry = sample_telemetry.copy()
        comp_telemetry = sample_telemetry.copy()
        comp_telemetry["lap_time"] = 90.7  # 0.2s slower

        result, error = run_phase2_delta(
            ref_telemetry, comp_telemetry, "NOR", "PIA"
        )

        assert error is None
        assert result is not None
        assert result.reference_driver == "NOR"
        assert result.compare_driver == "PIA"
        assert result.official_gap == pytest.approx(0.2, abs=0.01)

    def test_run_phase2_delta_missing_telemetry(self):
        """Test Phase 2 with missing telemetry data."""
        ref_telemetry = {"distance": [], "speed": [], "lap_time": 90.0}
        comp_telemetry = {"distance": [], "speed": [], "lap_time": 90.2}

        result, error = run_phase2_delta(
            ref_telemetry, comp_telemetry, "NOR", "PIA"
        )

        # Should still return result with confidence=0 for empty data
        assert result is not None
        assert result.confidence == 0.0


class TestPhase3Corner:
    """Tests for Phase 3 corner analysis execution."""

    def test_run_phase3_corner_success(self, sample_delta_result, sample_telemetry, sample_corners):
        """Test successful Phase 3 execution."""
        result, error = run_phase3_corner(
            sample_delta_result, sample_telemetry, sample_telemetry, sample_corners
        )

        assert error is None
        assert result is not None
        assert len(result.corner_results) == len(sample_corners)

    def test_run_phase3_corner_empty_corners(self, sample_delta_result, sample_telemetry):
        """Test Phase 3 with no corners."""
        result, error = run_phase3_corner(
            sample_delta_result, sample_telemetry, sample_telemetry, []
        )

        assert error is None
        assert result is not None
        assert len(result.corner_results) == 0


class TestPhase4Technique:
    """Tests for Phase 4 technique profiling execution."""

    def test_run_phase4_technique_success(self, sample_corner_result):
        """Test successful Phase 4 execution."""
        corner_results = {"PIA": sample_corner_result}

        profiles, percentiles, error = run_phase4_technique(
            corner_results, "NOR"
        )

        assert error is None
        assert len(profiles) == 1
        assert profiles[0].driver == "PIA"
        assert percentiles is not None

    def test_run_phase4_technique_multiple_drivers(self, sample_corner_result):
        """Test Phase 4 with multiple drivers."""
        # Create modified result for second driver
        ver_result = CornerAnalysisResult(
            reference_driver="NOR",
            compare_driver="VER",
            corner_results=sample_corner_result.corner_results,
            total_delta_change=-0.05,  # VER is faster
            corners_gaining=2,
            corners_losing=0,
        )

        corner_results = {
            "PIA": sample_corner_result,
            "VER": ver_result,
        }

        profiles, percentiles, error = run_phase4_technique(
            corner_results, "NOR"
        )

        assert error is None
        assert len(profiles) == 2
        assert percentiles.driver_count == 2

    def test_run_phase4_technique_empty_input(self):
        """Test Phase 4 with no drivers."""
        profiles, percentiles, error = run_phase4_technique({}, "NOR")

        assert error is None
        assert len(profiles) == 0
        assert percentiles.driver_count == 0


class TestPhase5Insight:
    """Tests for Phase 5 insight generation execution."""

    def test_run_phase5_insight_engineer_mode(self, sample_technique_profile):
        """Test Phase 5 in engineer mode."""
        insight, error = run_phase5_insight(
            sample_technique_profile, InsightMode.ENGINEER
        )

        assert error is None
        assert insight is not None
        assert insight.mode == InsightMode.ENGINEER
        assert insight.driver == "PIA"

    def test_run_phase5_insight_driver_mode(self, sample_technique_profile):
        """Test Phase 5 in driver mode."""
        insight, error = run_phase5_insight(
            sample_technique_profile, InsightMode.DRIVER
        )

        assert error is None
        assert insight is not None
        assert insight.mode == InsightMode.DRIVER

    def test_run_phase5_insight_with_context(self, sample_technique_profile):
        """Test Phase 5 with session context."""
        context = {"circuit": "Monaco", "session": "Q3"}

        insight, error = run_phase5_insight(
            sample_technique_profile, InsightMode.ENGINEER, context
        )

        assert error is None
        assert insight is not None
        assert insight.session_context == context


# =============================================================================
# Conversion Function Tests
# =============================================================================

class TestConversionFunctions:
    """Tests for dataclass to dict conversion functions."""

    def test_technique_profile_to_dict(self, sample_technique_profile):
        """Test TechniqueProfile to dict conversion."""
        result = _technique_profile_to_dict(sample_technique_profile)

        assert result["driver"] == "PIA"
        assert result["reference_driver"] == "NOR"
        assert result["braking"]["level"] == "strong"
        assert result["style_summary"] == "Complete package — excels in all phases"
        assert len(result["top_gaining_corners"]) == 2

    def test_session_percentiles_to_dict(self, sample_session_percentiles):
        """Test SessionPercentiles to dict conversion."""
        result = _session_percentiles_to_dict(sample_session_percentiles)

        assert result["braking_p30"] == pytest.approx(-0.03)
        assert result["braking_p70"] == pytest.approx(0.03)
        assert result["driver_count"] == 5

    def test_insight_to_dict(self, sample_insight):
        """Test NaturalLanguageInsight to dict conversion."""
        result = _insight_to_dict(sample_insight)

        assert result["driver"] == "PIA"
        assert result["mode"] == "engineer"
        assert result["confidence_level"] == "high"
        assert len(result["dimension_insights"]) == 1
        assert len(result["corner_insights"]) == 1

    def test_corner_result_to_dict(self):
        """Test CornerResult to dict conversion."""
        corner = CornerResult(
            corner_number=1,
            name="Turn 1",
            apex_distance=500,
            brake_distance=350,
            zone_start=350,
            zone_end=600,
            delta_change=0.05,
            cause="braking",
            confidence="high",
        )

        result = _corner_result_to_dict(corner)

        assert result["corner_number"] == 1
        assert result["name"] == "Turn 1"
        assert result["delta_change"] == pytest.approx(0.05)
        assert result["cause"] == "braking"


# =============================================================================
# Result Dataclass Tests
# =============================================================================

class TestResultDataclasses:
    """Tests for result dataclasses."""

    def test_phase_timing_info(self):
        """Test PhaseTimingInfo dataclass."""
        timing = PhaseTimingInfo(
            phase="delta_analysis",
            duration_ms=150,
            success=True,
            error=None,
        )

        assert timing.phase == "delta_analysis"
        assert timing.duration_ms == 150
        assert timing.success is True
        assert timing.error is None

    def test_phase_timing_info_with_error(self):
        """Test PhaseTimingInfo with error."""
        timing = PhaseTimingInfo(
            phase="telemetry_fetch",
            duration_ms=5000,
            success=False,
            error="Timeout fetching telemetry",
        )

        assert timing.success is False
        assert "Timeout" in timing.error

    def test_driver_performance_result_defaults(self):
        """Test DriverPerformanceResult default values."""
        result = DriverPerformanceResult(
            driver="PIA",
            official_gap=0.2,
            scaling_confidence=0.9,
        )

        assert result.driver == "PIA"
        assert result.delta is None
        assert result.distance is None
        assert result.corners_gaining == 0
        assert result.corners_losing == 0
        assert result.technique_profile is None
        assert result.insight is None

    def test_performance_insights_result(self):
        """Test PerformanceInsightsResult dataclass."""
        result = PerformanceInsightsResult(
            session_id="2025_1_Qualifying",
            reference_driver="NOR",
            circuit_name="Bahrain",
            mode="engineer",
            results=[],
            total_drivers_requested=2,
            total_drivers_processed=2,
            total_corners=15,
            total_duration_ms=500,
        )

        assert result.session_id == "2025_1_Qualifying"
        assert result.total_drivers_requested == 2
        assert result.total_duration_ms == 500
        assert len(result.errors) == 0
        assert len(result.warnings) == 0


# =============================================================================
# Integration Tests (Mocked)
# =============================================================================

class TestOrchestrationIntegration:
    """Integration tests with mocked HTTP calls."""

    @pytest.mark.asyncio
    async def test_orchestration_handles_missing_reference_driver(self, sample_config):
        """Test orchestration handles missing reference driver gracefully."""
        from services.performance_orchestrator import orchestrate_performance_insights

        # Mock client that returns empty telemetry
        mock_client = AsyncMock()
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.json.return_value = []
        mock_client.get.return_value = mock_response

        result = await orchestrate_performance_insights(sample_config, mock_client)

        assert len(result.errors) > 0
        assert result.total_drivers_processed == 0

    @pytest.mark.asyncio
    async def test_orchestration_timeout_handling(self, sample_config):
        """Test orchestration handles timeouts gracefully."""
        import httpx
        from services.performance_orchestrator import orchestrate_performance_insights

        # Mock client that raises timeout
        mock_client = AsyncMock()
        mock_client.get.side_effect = httpx.TimeoutException("Connection timeout")

        result = await orchestrate_performance_insights(sample_config, mock_client)

        assert len(result.errors) > 0
        assert result.total_drivers_processed == 0


# =============================================================================
# Edge Case Tests
# =============================================================================

class TestEdgeCases:
    """Tests for edge cases and error handling."""

    def test_empty_corners_list(self, sample_telemetry):
        """Test with empty corners list."""
        ref_telem = sample_telemetry
        comp_telem = sample_telemetry.copy()
        comp_telem["lap_time"] = 90.7

        delta_result, _ = run_phase2_delta(ref_telem, comp_telem, "NOR", "PIA")
        corner_result, error = run_phase3_corner(delta_result, ref_telem, comp_telem, [])

        assert error is None
        assert corner_result.corners_gaining == 0
        assert corner_result.corners_losing == 0

    def test_single_driver_profiling(self, sample_corner_result):
        """Test profiling with single driver."""
        corner_results = {"PIA": sample_corner_result}

        profiles, percentiles, error = run_phase4_technique(corner_results, "NOR")

        assert error is None
        assert len(profiles) == 1
        # Single driver should have NEUTRAL classification (P50)
        assert percentiles.driver_count == 1

    def test_very_large_delta(self, sample_telemetry):
        """Test handling of very large lap time differences."""
        ref_telem = sample_telemetry.copy()
        ref_telem["lap_time"] = 80.0

        comp_telem = sample_telemetry.copy()
        comp_telem["lap_time"] = 100.0  # 20 seconds slower

        result, error = run_phase2_delta(ref_telem, comp_telem, "NOR", "PIA")

        assert error is None
        assert result.official_gap == pytest.approx(20.0)
        # Should still have some confidence despite extreme scaling
        assert 0 <= result.confidence <= 1.0

    def test_identical_laps(self, sample_telemetry):
        """Test handling of identical lap times."""
        ref_telem = sample_telemetry.copy()
        comp_telem = sample_telemetry.copy()

        result, error = run_phase2_delta(ref_telem, comp_telem, "NOR", "PIA")

        assert error is None
        assert result.official_gap == pytest.approx(0.0)


# =============================================================================
# Performance Tests
# =============================================================================

class TestPerformance:
    """Performance-related tests."""

    def test_delta_calculation_performance(self, sample_telemetry):
        """Test delta calculation completes in reasonable time."""
        import time

        ref_telem = sample_telemetry
        comp_telem = sample_telemetry.copy()
        comp_telem["lap_time"] = 90.7

        start = time.time()
        for _ in range(10):
            run_phase2_delta(ref_telem, comp_telem, "NOR", "PIA")
        elapsed = time.time() - start

        # 10 calculations should complete in under 1 second
        assert elapsed < 1.0

    def test_corner_analysis_performance(self, sample_delta_result, sample_telemetry, sample_corners):
        """Test corner analysis completes in reasonable time."""
        import time

        start = time.time()
        for _ in range(10):
            run_phase3_corner(sample_delta_result, sample_telemetry, sample_telemetry, sample_corners)
        elapsed = time.time() - start

        # 10 analyses should complete in under 1 second
        assert elapsed < 1.0
